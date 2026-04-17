"""
SLH Sudoku — engagement + AIC earn
====================================
Play sudoku, earn AIC/REP. First solve of daily puzzle = bonus AIC.

Endpoints:
  POST /api/sudoku/start              — create session, returns puzzle (no solution)
  POST /api/sudoku/check              — validate current board (no reward)
  POST /api/sudoku/hint               — reveal one correct cell (costs 1 AIC)
  POST /api/sudoku/submit             — verify solution, award AIC + REP, log tx
  GET  /api/sudoku/daily              — today's shared puzzle (same for everyone)
  GET  /api/sudoku/my-stats/{uid}     — user's solve stats
  GET  /api/sudoku/leaderboard        — top solvers (weekly + all-time)
  GET  /api/sudoku/stats              — global

Pattern matches our codebase: module-level _pool, set_pool(pool) called from main.py.
No Depends/auth — user_id passed in request body (same as community + aic_tokens).
"""

from __future__ import annotations

import os
import random
import json
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, List, Tuple

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/sudoku", tags=["Sudoku"])

_pool = None
def set_pool(pool):
    global _pool
    _pool = pool


# ══════════════════ Sudoku engine (self-contained, no pypi dep) ══════════════════

def _is_valid(grid: List[List[int]], row: int, col: int, val: int) -> bool:
    for i in range(9):
        if grid[row][i] == val or grid[i][col] == val:
            return False
    br, bc = 3 * (row // 3), 3 * (col // 3)
    for i in range(br, br + 3):
        for j in range(bc, bc + 3):
            if grid[i][j] == val:
                return False
    return True


def _solve(grid: List[List[int]]) -> bool:
    for r in range(9):
        for c in range(9):
            if grid[r][c] == 0:
                nums = list(range(1, 10))
                random.shuffle(nums)
                for n in nums:
                    if _is_valid(grid, r, c, n):
                        grid[r][c] = n
                        if _solve(grid):
                            return True
                        grid[r][c] = 0
                return False
    return True


def _generate(difficulty: str, seed: Optional[int] = None) -> Tuple[List[List[int]], List[List[int]]]:
    """Returns (puzzle_grid, solution_grid). Both 9x9 of ints; 0 = empty in puzzle."""
    if seed is not None:
        random.seed(seed)
    # Generate solution
    solution = [[0] * 9 for _ in range(9)]
    _solve(solution)
    # Copy and remove cells based on difficulty
    holes = {"easy": 36, "medium": 48, "hard": 56}.get(difficulty.lower(), 48)
    puzzle = [row[:] for row in solution]
    positions = [(r, c) for r in range(9) for c in range(9)]
    random.shuffle(positions)
    for r, c in positions[:holes]:
        puzzle[r][c] = 0
    return puzzle, solution


def _grid_to_str(grid: List[List[int]]) -> str:
    return "".join(str(cell) for row in grid for cell in row)


def _str_to_grid(s: str) -> List[List[int]]:
    return [[int(s[i * 9 + j]) for j in range(9)] for i in range(9)]


# ══════════════════ DB + reward rules ══════════════════

REWARDS = {
    "easy":   {"aic": 1.0, "rep": 2,  "fast_bonus": 0.5},
    "medium": {"aic": 2.5, "rep": 5,  "fast_bonus": 1.0},
    "hard":   {"aic": 5.0, "rep": 12, "fast_bonus": 2.0},
}
FAST_SECONDS = 300        # <5 min = bonus
DAILY_FIRST_BONUS = 3.0   # extra AIC for first daily solve
DAILY_EARNING_CAP = 3     # max 3 puzzles/day earn AIC
HINT_COST = 1.0           # AIC per hint


async def _ensure_sudoku_tables(conn):
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sudoku_sessions (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            difficulty TEXT NOT NULL,
            puzzle_grid TEXT NOT NULL,
            solution_grid TEXT NOT NULL,
            started_at TIMESTAMPTZ DEFAULT now(),
            completed_at TIMESTAMPTZ,
            time_seconds INTEGER,
            hints_used INTEGER DEFAULT 0,
            solved BOOLEAN DEFAULT FALSE,
            aic_awarded NUMERIC(10,4) DEFAULT 0,
            rep_awarded INTEGER DEFAULT 0,
            is_daily BOOLEAN DEFAULT FALSE
        );
        CREATE INDEX IF NOT EXISTS idx_sudoku_user ON sudoku_sessions(user_id, started_at DESC);
        CREATE INDEX IF NOT EXISTS idx_sudoku_solved ON sudoku_sessions(solved, time_seconds) WHERE solved = TRUE;

        CREATE TABLE IF NOT EXISTS sudoku_daily (
            date DATE PRIMARY KEY,
            puzzle_grid TEXT NOT NULL,
            solution_grid TEXT NOT NULL,
            difficulty TEXT NOT NULL DEFAULT 'medium'
        );
        """
    )
    # Ensure AIC tables exist too (we call them directly)
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS aic_balances (
            user_id BIGINT PRIMARY KEY,
            balance NUMERIC(18,4) NOT NULL DEFAULT 0,
            lifetime_earned NUMERIC(18,4) NOT NULL DEFAULT 0,
            lifetime_spent NUMERIC(18,4) NOT NULL DEFAULT 0,
            updated_at TIMESTAMPTZ DEFAULT now()
        );
        CREATE TABLE IF NOT EXISTS aic_transactions (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            kind TEXT NOT NULL,
            amount NUMERIC(18,4) NOT NULL,
            reason TEXT NOT NULL,
            provider TEXT,
            tokens_consumed INTEGER,
            metadata JSONB DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ DEFAULT now()
        );
        """
    )


async def _aic_earn(conn, user_id: int, amount: float, reason: str, meta: Optional[dict] = None):
    """Credit AIC — idempotent at caller level. No earn cap check here (caller owns)."""
    await conn.execute(
        """
        INSERT INTO aic_balances (user_id, balance, lifetime_earned)
        VALUES ($1, $2, $2)
        ON CONFLICT (user_id) DO UPDATE SET
          balance = aic_balances.balance + EXCLUDED.balance,
          lifetime_earned = aic_balances.lifetime_earned + EXCLUDED.lifetime_earned,
          updated_at = now()
        """,
        user_id, Decimal(str(amount)),
    )
    await conn.execute(
        """
        INSERT INTO aic_transactions (user_id, kind, amount, reason, metadata)
        VALUES ($1, 'earn', $2, $3, $4::jsonb)
        """,
        user_id, Decimal(str(amount)), reason, json.dumps(meta or {}),
    )


async def _aic_spend(conn, user_id: int, amount: float, reason: str, meta: Optional[dict] = None):
    """Deduct AIC. Raises 402 if insufficient. Idempotent via caller."""
    bal = await conn.fetchval("SELECT balance FROM aic_balances WHERE user_id=$1 FOR UPDATE", user_id)
    if bal is None or float(bal) < amount:
        raise HTTPException(402, f"Insufficient AIC. Have {float(bal or 0)}, need {amount}.")
    await conn.execute(
        """
        UPDATE aic_balances SET
          balance = balance - $2,
          lifetime_spent = lifetime_spent + $2,
          updated_at = now()
        WHERE user_id = $1
        """,
        user_id, Decimal(str(amount)),
    )
    await conn.execute(
        """
        INSERT INTO aic_transactions (user_id, kind, amount, reason, metadata)
        VALUES ($1, 'spend', $2, $3, $4::jsonb)
        """,
        user_id, Decimal(str(amount)), reason, json.dumps(meta or {}),
    )


# ══════════════════ Endpoints ══════════════════

class StartReq(BaseModel):
    user_id: int
    difficulty: str = "medium"  # easy | medium | hard
    daily: bool = False  # if True, use today's shared puzzle


@router.post("/start")
async def sudoku_start(req: StartReq):
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    diff = (req.difficulty or "medium").lower()
    if diff not in REWARDS:
        raise HTTPException(400, "difficulty must be easy|medium|hard")

    async with _pool.acquire() as conn:
        await _ensure_sudoku_tables(conn)

        is_daily = bool(req.daily)
        if is_daily:
            today = date.today()
            daily = await conn.fetchrow("SELECT puzzle_grid, solution_grid, difficulty FROM sudoku_daily WHERE date=$1", today)
            if not daily:
                seed = int(today.strftime("%Y%m%d"))
                puzzle, solution = _generate("medium", seed=seed)
                await conn.execute(
                    "INSERT INTO sudoku_daily (date, puzzle_grid, solution_grid, difficulty) VALUES ($1, $2, $3, 'medium') ON CONFLICT DO NOTHING",
                    today, _grid_to_str(puzzle), _grid_to_str(solution),
                )
                diff = "medium"
            else:
                puzzle = _str_to_grid(daily["puzzle_grid"])
                solution = _str_to_grid(daily["solution_grid"])
                diff = daily["difficulty"]
        else:
            puzzle, solution = _generate(diff)

        row = await conn.fetchrow(
            """
            INSERT INTO sudoku_sessions (user_id, difficulty, puzzle_grid, solution_grid, is_daily)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, started_at
            """,
            req.user_id, diff, _grid_to_str(puzzle), _grid_to_str(solution), is_daily,
        )

    return {
        "session_id": row["id"],
        "puzzle": puzzle,
        "difficulty": diff,
        "is_daily": is_daily,
        "started_at": row["started_at"].isoformat(),
        "reward_preview": REWARDS[diff],
    }


class CheckReq(BaseModel):
    session_id: int
    board: List[List[int]]


@router.post("/check")
async def sudoku_check(req: CheckReq):
    """Validate current board — count errors, do NOT reveal solution or award."""
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    async with _pool.acquire() as conn:
        row = await conn.fetchrow("SELECT solution_grid, solved FROM sudoku_sessions WHERE id=$1", req.session_id)
        if not row:
            raise HTTPException(404, "session not found")
        solution = _str_to_grid(row["solution_grid"])
        errors = 0
        filled = 0
        for i in range(9):
            for j in range(9):
                v = req.board[i][j] if i < len(req.board) and j < len(req.board[i]) else 0
                if v != 0:
                    filled += 1
                    if v != solution[i][j]:
                        errors += 1
    return {"errors": errors, "filled": filled, "complete": filled == 81 and errors == 0}


class HintReq(BaseModel):
    session_id: int
    user_id: int


@router.post("/hint")
async def sudoku_hint(req: HintReq):
    """Deduct 1 AIC, return one empty cell with the correct answer."""
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_sudoku_tables(conn)
        row = await conn.fetchrow(
            "SELECT user_id, puzzle_grid, solution_grid, hints_used, solved FROM sudoku_sessions WHERE id=$1",
            req.session_id,
        )
        if not row or row["user_id"] != req.user_id:
            raise HTTPException(404, "session not found")
        if row["solved"]:
            raise HTTPException(400, "puzzle already solved")

        puzzle = _str_to_grid(row["puzzle_grid"])
        solution = _str_to_grid(row["solution_grid"])

        # Find empty cells from puzzle original — hint reveals one we haven't revealed before
        # To track "revealed", store hints_used count and pick deterministically
        empty_cells = [(r, c) for r in range(9) for c in range(9) if puzzle[r][c] == 0]
        if not empty_cells:
            raise HTTPException(400, "no empty cells remain")

        # Pick by hints_used index (deterministic, consistent)
        random.seed(req.session_id)
        random.shuffle(empty_cells)
        idx = row["hints_used"] % len(empty_cells)
        hr, hc = empty_cells[idx]

        # Deduct 1 AIC (raises 402 if insufficient)
        await _aic_spend(conn, req.user_id, HINT_COST, "sudoku_hint", {"session_id": req.session_id, "cell": [hr, hc]})

        # Increment hints_used
        await conn.execute(
            "UPDATE sudoku_sessions SET hints_used = hints_used + 1 WHERE id=$1",
            req.session_id,
        )

    return {
        "row": hr,
        "col": hc,
        "value": solution[hr][hc],
        "cost_aic": HINT_COST,
        "hints_used": row["hints_used"] + 1,
    }


class SubmitReq(BaseModel):
    session_id: int
    user_id: int
    board: List[List[int]]
    time_seconds: int


@router.post("/submit")
async def sudoku_submit(req: SubmitReq):
    """Verify solution, award AIC + REP if correct and within daily cap. Idempotent."""
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_sudoku_tables(conn)
        row = await conn.fetchrow(
            """
            SELECT id, user_id, difficulty, solution_grid, solved, aic_awarded, rep_awarded, is_daily, hints_used
            FROM sudoku_sessions WHERE id=$1
            """,
            req.session_id,
        )
        if not row:
            raise HTTPException(404, "session not found")
        if row["user_id"] != req.user_id:
            raise HTTPException(403, "not your session")

        solution = _str_to_grid(row["solution_grid"])

        # Verify correctness
        for i in range(9):
            for j in range(9):
                cell = req.board[i][j] if i < len(req.board) and j < len(req.board[i]) else 0
                if cell != solution[i][j]:
                    return {
                        "solved": False,
                        "errors_at": [i, j],
                        "message": "הלוח לא נכון. המשך לפתור.",
                    }

        # Already solved? return previous award
        if row["solved"]:
            return {
                "solved": True,
                "already_awarded": True,
                "aic_earned": float(row["aic_awarded"]),
                "rep_earned": row["rep_awarded"],
                "message": "כבר קיבלת תגמול על הלוח הזה.",
            }

        # Calculate reward
        diff = row["difficulty"]
        rule = REWARDS[diff]
        aic = rule["aic"]
        rep = rule["rep"]
        time_s = req.time_seconds
        if time_s < FAST_SECONDS:
            aic += rule["fast_bonus"]
        daily_first = False
        if row["is_daily"]:
            today = date.today()
            prior_daily = await conn.fetchval(
                """
                SELECT COUNT(*) FROM sudoku_sessions
                WHERE user_id=$1 AND is_daily=TRUE AND solved=TRUE
                  AND DATE(completed_at)=$2
                """,
                req.user_id, today,
            )
            if (prior_daily or 0) == 0:
                aic += DAILY_FIRST_BONUS
                daily_first = True

        # Daily earning cap (counts of earning solves today)
        today = date.today()
        earning_today = await conn.fetchval(
            """
            SELECT COUNT(*) FROM sudoku_sessions
            WHERE user_id=$1 AND solved=TRUE AND aic_awarded > 0
              AND DATE(completed_at) = $2
            """,
            req.user_id, today,
        )
        capped = False
        if (earning_today or 0) >= DAILY_EARNING_CAP:
            aic = 0.0
            rep = 0
            capped = True

        # Update session
        await conn.execute(
            """
            UPDATE sudoku_sessions SET
              solved = TRUE, completed_at = now(), time_seconds = $2,
              aic_awarded = $3, rep_awarded = $4
            WHERE id = $1
            """,
            req.session_id, time_s, Decimal(str(aic)), rep,
        )

        # Credit AIC + (future) REP if not capped
        if not capped and aic > 0:
            await _aic_earn(
                conn, req.user_id, aic, "sudoku_solve",
                {"difficulty": diff, "time_seconds": time_s, "daily_first": daily_first, "hints_used": row["hints_used"]},
            )

    return {
        "solved": True,
        "aic_earned": float(aic),
        "rep_earned": int(rep),
        "time_seconds": time_s,
        "daily_first_bonus": daily_first,
        "capped": capped,
        "message": (
            "🎉 פתרון מעולה! תגמול הוענק."
            if not capped else "פתרת — אבל עברת את מכסת 3 הפתרונות היומית. נסה מחר."
        ),
    }


@router.get("/daily")
async def sudoku_daily():
    """Today's shared puzzle (no solution exposed)."""
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    today = date.today()
    async with _pool.acquire() as conn:
        await _ensure_sudoku_tables(conn)
        daily = await conn.fetchrow(
            "SELECT puzzle_grid, difficulty FROM sudoku_daily WHERE date=$1",
            today,
        )
        if not daily:
            seed = int(today.strftime("%Y%m%d"))
            puzzle, solution = _generate("medium", seed=seed)
            await conn.execute(
                "INSERT INTO sudoku_daily (date, puzzle_grid, solution_grid, difficulty) VALUES ($1, $2, $3, 'medium') ON CONFLICT DO NOTHING",
                today, _grid_to_str(puzzle), _grid_to_str(solution),
            )
            return {"date": today.isoformat(), "puzzle": puzzle, "difficulty": "medium"}
        return {
            "date": today.isoformat(),
            "puzzle": _str_to_grid(daily["puzzle_grid"]),
            "difficulty": daily["difficulty"],
        }


@router.get("/my-stats/{user_id}")
async def sudoku_my_stats(user_id: int):
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_sudoku_tables(conn)
        stats = await conn.fetchrow(
            """
            SELECT
              COUNT(*) FILTER (WHERE solved) AS solved_count,
              COUNT(*) AS total_started,
              AVG(time_seconds) FILTER (WHERE solved) AS avg_time,
              SUM(aic_awarded) AS total_aic,
              SUM(rep_awarded) AS total_rep,
              MAX(completed_at) AS last_solve
            FROM sudoku_sessions WHERE user_id=$1
            """,
            user_id,
        )
        # Streak: count consecutive days with a solve
        dates = await conn.fetch(
            """
            SELECT DISTINCT DATE(completed_at) AS d FROM sudoku_sessions
            WHERE user_id=$1 AND solved=TRUE
              AND completed_at >= CURRENT_DATE - INTERVAL '60 days'
            ORDER BY d DESC
            """,
            user_id,
        )
        streak = 0
        if dates:
            expected = date.today()
            for row in dates:
                if row["d"] == expected or row["d"] == expected - timedelta(days=1):
                    streak += 1
                    expected = row["d"] - timedelta(days=1)
                else:
                    break

    return {
        "user_id": user_id,
        "solved_count": stats["solved_count"] or 0,
        "total_started": stats["total_started"] or 0,
        "avg_time_seconds": float(stats["avg_time"] or 0),
        "total_aic_earned": float(stats["total_aic"] or 0),
        "total_rep_earned": int(stats["total_rep"] or 0),
        "streak_days": streak,
        "last_solve": stats["last_solve"].isoformat() if stats["last_solve"] else None,
    }


@router.get("/leaderboard")
async def sudoku_leaderboard(period: str = "weekly", limit: int = 20):
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    limit = max(1, min(limit, 100))
    async with _pool.acquire() as conn:
        await _ensure_sudoku_tables(conn)
        since = "now() - interval '7 days'" if period == "weekly" else "'1900-01-01'"
        rows = await conn.fetch(
            f"""
            SELECT user_id,
                   COUNT(*) FILTER (WHERE solved) AS solves,
                   AVG(time_seconds) FILTER (WHERE solved) AS avg_time,
                   SUM(aic_awarded) AS total_aic
            FROM sudoku_sessions
            WHERE completed_at >= {since} OR completed_at IS NULL
            GROUP BY user_id
            HAVING COUNT(*) FILTER (WHERE solved) > 0
            ORDER BY solves DESC, avg_time ASC NULLS LAST
            LIMIT $1
            """,
            limit,
        )
    return {
        "period": period,
        "leaders": [
            {
                "rank": i + 1,
                "user_id": r["user_id"],
                "solves": r["solves"],
                "avg_time": float(r["avg_time"] or 0),
                "aic_earned": float(r["total_aic"] or 0),
            }
            for i, r in enumerate(rows)
        ],
    }


@router.get("/stats")
async def sudoku_global_stats():
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_sudoku_tables(conn)
        row = await conn.fetchrow(
            """
            SELECT
              COUNT(*) AS total_sessions,
              COUNT(*) FILTER (WHERE solved) AS total_solved,
              COUNT(DISTINCT user_id) FILTER (WHERE solved) AS unique_solvers,
              SUM(aic_awarded) AS total_aic_issued,
              AVG(time_seconds) FILTER (WHERE solved) AS avg_solve_time
            FROM sudoku_sessions
            """
        )
    return {
        "total_sessions": row["total_sessions"] or 0,
        "total_solved": row["total_solved"] or 0,
        "unique_solvers": row["unique_solvers"] or 0,
        "total_aic_issued": float(row["total_aic_issued"] or 0),
        "avg_solve_time": float(row["avg_solve_time"] or 0),
        "reward_rules": REWARDS,
        "daily_cap": DAILY_EARNING_CAP,
        "hint_cost": HINT_COST,
    }
