"""
SLH Dating — Quality-gated matchmaking
========================================
For @G4meb0t_bot_bot + website/dating.html.

Built around Osif's real goals: verified-experts, deep values,
not Tinder-style. Age 18+ required. Minors blocked by age field.

Endpoints:
  POST /api/dating/profile            — create or update profile
  GET  /api/dating/profile/{user_id}  — get my profile (private)
  GET  /api/dating/profile/{user_id}/public — public view of another user
  POST /api/dating/match/candidates   — return 10 potential matches
  POST /api/dating/match/action       — like/pass/superlike
  GET  /api/dating/matches/{user_id}  — mutual matches (can chat)
  GET  /api/dating/stats              — global (not personal)

Privacy:
- Phone/email NEVER exposed in public profile
- Chat happens via Telegram deep-link after mutual match
- Minors (<18) get 400 on profile create
"""

from __future__ import annotations

import os
import json
import random
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/dating", tags=["Dating"])

_pool = None
def set_pool(pool):
    global _pool
    _pool = pool


VALID_LOOKING_FOR = {"serious_relationship", "friendship", "partnership", "community"}
VALID_INTERESTS = {
    "yoga", "meditation", "music", "conducting", "philosophy",
    "neuroscience", "psychology", "extreme_sports", "climbing",
    "surfing", "parenting", "family", "hiking", "leadership",
    "entrepreneurship", "crypto", "cooking", "vegan", "kosher",
    "literature", "chess", "art", "therapy", "writing",
    "travel", "running", "nature", "spirituality",
}
MIN_AGE = 18
MAX_AGE = 99


async def _ensure_dating_tables(conn):
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS dating_profiles (
            user_id BIGINT PRIMARY KEY,
            display_name TEXT NOT NULL,
            tg_username TEXT,
            age INTEGER NOT NULL CHECK (age >= 18 AND age <= 99),
            gender TEXT,
            seeking_gender TEXT,
            city TEXT,
            country_code TEXT DEFAULT 'IL',
            bio TEXT,
            interests TEXT[],
            looking_for TEXT NOT NULL DEFAULT 'serious_relationship',
            has_children BOOLEAN,
            wants_children BOOLEAN,
            profession TEXT,
            languages TEXT[] DEFAULT ARRAY['he'],
            photo_url TEXT,
            verified BOOLEAN DEFAULT FALSE,
            active BOOLEAN DEFAULT TRUE,
            last_seen TIMESTAMPTZ DEFAULT now(),
            created_at TIMESTAMPTZ DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_dating_active ON dating_profiles(active, last_seen DESC);
        CREATE INDEX IF NOT EXISTS idx_dating_interests ON dating_profiles USING gin(interests);

        CREATE TABLE IF NOT EXISTS dating_actions (
            id BIGSERIAL PRIMARY KEY,
            from_user_id BIGINT NOT NULL,
            to_user_id BIGINT NOT NULL,
            action TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT now(),
            UNIQUE(from_user_id, to_user_id)
        );
        CREATE INDEX IF NOT EXISTS idx_dating_actions_to ON dating_actions(to_user_id, action);

        CREATE TABLE IF NOT EXISTS dating_matches (
            id BIGSERIAL PRIMARY KEY,
            user_a_id BIGINT NOT NULL,
            user_b_id BIGINT NOT NULL,
            matched_at TIMESTAMPTZ DEFAULT now(),
            conversation_started BOOLEAN DEFAULT FALSE,
            UNIQUE(user_a_id, user_b_id)
        );
        """
    )


class ProfileReq(BaseModel):
    user_id: int
    display_name: str
    tg_username: Optional[str] = None
    age: int
    gender: Optional[str] = None
    seeking_gender: Optional[str] = None
    city: Optional[str] = None
    country_code: Optional[str] = "IL"
    bio: Optional[str] = None
    interests: List[str] = []
    looking_for: str = "serious_relationship"
    has_children: Optional[bool] = None
    wants_children: Optional[bool] = None
    profession: Optional[str] = None
    languages: List[str] = ["he"]
    photo_url: Optional[str] = None


@router.post("/profile")
async def create_or_update_profile(req: ProfileReq):
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    if req.age < MIN_AGE or req.age > MAX_AGE:
        raise HTTPException(400, f"age must be {MIN_AGE}-{MAX_AGE}. Minors not allowed.")
    if req.looking_for not in VALID_LOOKING_FOR:
        raise HTTPException(400, f"looking_for must be one of {sorted(VALID_LOOKING_FOR)}")
    interests = [i.strip().lower() for i in (req.interests or []) if i.strip()]
    for i in interests:
        if i not in VALID_INTERESTS:
            raise HTTPException(400, f"unknown interest '{i}'. See /api/dating/interests/list for valid values.")

    async with _pool.acquire() as conn:
        await _ensure_dating_tables(conn)
        await conn.execute(
            """
            INSERT INTO dating_profiles
            (user_id, display_name, tg_username, age, gender, seeking_gender, city, country_code,
             bio, interests, looking_for, has_children, wants_children, profession, languages, photo_url)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16)
            ON CONFLICT (user_id) DO UPDATE SET
              display_name=EXCLUDED.display_name, tg_username=EXCLUDED.tg_username,
              age=EXCLUDED.age, gender=EXCLUDED.gender, seeking_gender=EXCLUDED.seeking_gender,
              city=EXCLUDED.city, country_code=EXCLUDED.country_code, bio=EXCLUDED.bio,
              interests=EXCLUDED.interests, looking_for=EXCLUDED.looking_for,
              has_children=EXCLUDED.has_children, wants_children=EXCLUDED.wants_children,
              profession=EXCLUDED.profession, languages=EXCLUDED.languages, photo_url=EXCLUDED.photo_url,
              last_seen=now()
            """,
            req.user_id, req.display_name, req.tg_username, req.age, req.gender, req.seeking_gender,
            req.city, req.country_code, req.bio, interests, req.looking_for,
            req.has_children, req.wants_children, req.profession, req.languages, req.photo_url,
        )
    return {"ok": True, "user_id": req.user_id, "message": "פרופיל נשמר. נסה למצוא התאמות."}


@router.get("/profile/{user_id}")
async def get_my_profile(user_id: int):
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_dating_tables(conn)
        row = await conn.fetchrow("SELECT * FROM dating_profiles WHERE user_id=$1", user_id)
    if not row:
        return {"exists": False, "user_id": user_id}
    return {"exists": True, **dict(row), "created_at": row["created_at"].isoformat(), "last_seen": row["last_seen"].isoformat()}


@router.get("/profile/{user_id}/public")
async def get_public_profile(user_id: int):
    """Public view — no phone/email/contact details."""
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_dating_tables(conn)
        row = await conn.fetchrow(
            """
            SELECT user_id, display_name, age, gender, city, country_code,
                   bio, interests, looking_for, has_children, wants_children,
                   profession, languages, photo_url, verified, last_seen
            FROM dating_profiles WHERE user_id=$1 AND active=TRUE
            """,
            user_id,
        )
    if not row:
        raise HTTPException(404, "profile not found or inactive")
    return {**dict(row), "last_seen": row["last_seen"].isoformat()}


class CandidatesReq(BaseModel):
    user_id: int
    limit: int = 10


@router.post("/match/candidates")
async def find_candidates(req: CandidatesReq):
    """Return N potential matches based on interest overlap + looking_for compatibility.
    Excludes: self, already-liked, already-passed, users with ZUZ > 50 (if available)."""
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    limit = max(1, min(req.limit, 20))
    async with _pool.acquire() as conn:
        await _ensure_dating_tables(conn)
        me = await conn.fetchrow("SELECT interests, looking_for, seeking_gender FROM dating_profiles WHERE user_id=$1", req.user_id)
        if not me:
            raise HTTPException(404, "create your profile first via POST /api/dating/profile")

        my_interests = list(me["interests"] or [])
        # Candidates: active, not me, not already acted on, compatible looking_for
        candidates = await conn.fetch(
            """
            SELECT p.user_id, p.display_name, p.age, p.gender, p.city, p.bio,
                   p.interests, p.looking_for, p.photo_url, p.verified,
                   COALESCE(array_length(
                     ARRAY(SELECT UNNEST(p.interests) INTERSECT SELECT UNNEST($2::text[])), 1
                   ), 0) AS overlap_count
            FROM dating_profiles p
            WHERE p.user_id != $1
              AND p.active = TRUE
              AND p.looking_for = $3
              AND ($4::text IS NULL OR p.gender = $4)
              AND NOT EXISTS (
                  SELECT 1 FROM dating_actions a
                  WHERE a.from_user_id = $1 AND a.to_user_id = p.user_id
              )
            ORDER BY overlap_count DESC, p.verified DESC, p.last_seen DESC
            LIMIT $5
            """,
            req.user_id, my_interests, me["looking_for"], me["seeking_gender"], limit,
        )

    return {
        "candidates": [
            {
                "user_id": c["user_id"], "display_name": c["display_name"],
                "age": c["age"], "gender": c["gender"], "city": c["city"],
                "bio": c["bio"], "interests": list(c["interests"] or []),
                "looking_for": c["looking_for"], "photo_url": c["photo_url"],
                "verified": c["verified"], "overlap_count": c["overlap_count"],
            }
            for c in candidates
        ],
    }


class ActionReq(BaseModel):
    from_user_id: int
    to_user_id: int
    action: str  # like | pass | superlike


@router.post("/match/action")
async def match_action(req: ActionReq):
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    if req.action not in ("like", "pass", "superlike"):
        raise HTTPException(400, "action must be like | pass | superlike")
    if req.from_user_id == req.to_user_id:
        raise HTTPException(400, "cannot act on yourself")

    async with _pool.acquire() as conn:
        await _ensure_dating_tables(conn)
        # Record action (idempotent via UNIQUE constraint)
        await conn.execute(
            """
            INSERT INTO dating_actions (from_user_id, to_user_id, action)
            VALUES ($1, $2, $3)
            ON CONFLICT (from_user_id, to_user_id) DO UPDATE SET action=EXCLUDED.action
            """,
            req.from_user_id, req.to_user_id, req.action,
        )

        # Check for mutual like → match
        is_match = False
        if req.action in ("like", "superlike"):
            reciprocal = await conn.fetchval(
                """
                SELECT action FROM dating_actions
                WHERE from_user_id=$1 AND to_user_id=$2 AND action IN ('like','superlike')
                """,
                req.to_user_id, req.from_user_id,
            )
            if reciprocal:
                is_match = True
                # Record match (smaller id first for consistency)
                a, b = sorted([req.from_user_id, req.to_user_id])
                await conn.execute(
                    """
                    INSERT INTO dating_matches (user_a_id, user_b_id)
                    VALUES ($1, $2) ON CONFLICT DO NOTHING
                    """,
                    a, b,
                )

    return {
        "ok": True,
        "action": req.action,
        "is_match": is_match,
        "message": "🎉 התאמה הדדית! אתם יכולים לדבר עכשיו." if is_match else "הפעולה נשמרה.",
    }


@router.get("/matches/{user_id}")
async def my_matches(user_id: int):
    """All mutual matches — people who liked you back."""
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_dating_tables(conn)
        rows = await conn.fetch(
            """
            SELECT
              m.id, m.matched_at, m.conversation_started,
              CASE WHEN m.user_a_id = $1 THEN m.user_b_id ELSE m.user_a_id END AS other_id,
              p.display_name, p.age, p.city, p.photo_url, p.tg_username, p.bio, p.verified
            FROM dating_matches m
            JOIN dating_profiles p ON p.user_id = (
              CASE WHEN m.user_a_id = $1 THEN m.user_b_id ELSE m.user_a_id END
            )
            WHERE m.user_a_id = $1 OR m.user_b_id = $1
            ORDER BY m.matched_at DESC
            """,
            user_id,
        )
    return {
        "matches": [
            {
                "match_id": r["id"],
                "other_user_id": r["other_id"],
                "display_name": r["display_name"],
                "age": r["age"],
                "city": r["city"],
                "bio": r["bio"],
                "photo_url": r["photo_url"],
                "tg_username": r["tg_username"],
                "verified": r["verified"],
                "matched_at": r["matched_at"].isoformat(),
                "tg_link": f"https://t.me/{r['tg_username']}" if r["tg_username"] else None,
            }
            for r in rows
        ],
    }


@router.get("/stats")
async def dating_stats():
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_dating_tables(conn)
        row = await conn.fetchrow(
            """
            SELECT
              COUNT(*) FILTER (WHERE active) AS active_profiles,
              COUNT(*) AS total_profiles,
              COUNT(*) FILTER (WHERE verified) AS verified_profiles,
              (SELECT COUNT(*) FROM dating_matches) AS total_matches,
              (SELECT COUNT(*) FROM dating_matches WHERE matched_at > now() - interval '7 days') AS matches_this_week
            FROM dating_profiles
            """
        )
    return dict(row)


@router.get("/interests/list")
async def list_interests():
    return {"interests": sorted(VALID_INTERESTS), "looking_for_options": sorted(VALID_LOOKING_FOR)}
