"""
SLH Community API — Real-time community backend
FastAPI + asyncpg on Railway PostgreSQL
"""

import os
import time
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional

import asyncpg
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# ── Config ──
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:svNeqdqVRohdWMyPTiaqLHmZXlzIneuD@junction.proxy.rlwy.net:17913/railway",
)
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "https://slh-nft.com,http://localhost").split(",")

app = FastAPI(title="SLH Community API", version="1.0.0")

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── DB Pool ──
pool: Optional[asyncpg.Pool] = None

# ── Rate limit store (in-memory) ──
rate_limits: dict[str, list[float]] = {}


# ── Pydantic Models ──
class PostCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=48)
    text: str = Field(..., min_length=1, max_length=4000)
    category: str = Field(default="general", max_length=32)
    telegram_id: Optional[str] = None


class LikeToggle(BaseModel):
    username: str = Field(..., min_length=1, max_length=48)


class CommentCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=48)
    text: str = Field(..., min_length=1, max_length=2000)


# ── Helpers ──
def check_rate_limit(key: str, max_per_hour: int) -> bool:
    """Returns True if under limit, False if exceeded."""
    now = time.time()
    cutoff = now - 3600
    entries = rate_limits.get(key, [])
    entries = [t for t in entries if t > cutoff]
    rate_limits[key] = entries
    if len(entries) >= max_per_hour:
        return False
    entries.append(now)
    return True


def row_to_dict(row):
    return dict(row)


# ── SQL Schema ──
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS community_posts (
    id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL,
    telegram_id TEXT,
    text TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'general',
    likes_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS community_likes (
    id BIGSERIAL PRIMARY KEY,
    post_id BIGINT NOT NULL REFERENCES community_posts(id) ON DELETE CASCADE,
    username TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(post_id, username)
);

CREATE TABLE IF NOT EXISTS community_comments (
    id BIGSERIAL PRIMARY KEY,
    post_id BIGINT NOT NULL REFERENCES community_posts(id) ON DELETE CASCADE,
    username TEXT NOT NULL,
    text TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_posts_created ON community_posts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_comments_post ON community_comments(post_id, created_at);
"""

# ── Seed Data ──
SEED_POSTS = [
    {
        "username": "SLH Official",
        "text": (
            "\U0001f4cc \u05de\u05d5\u05e6\u05de\u05d3\n\n"
            "\u05d1\u05e8\u05d5\u05e8 \u05e9\u05e4\u05e1\u05e4\u05e1\u05ea\u05dd \u05d0\u05ea \u05d4\u05d1\u05d9\u05d8\u05e7\u05d5\u05d9\u05d9\u05df,\n"
            "\u05dc\u05d0 \u05d4\u05d1\u05e0\u05ea\u05dd \u05de\u05d4 \u05d6\u05d4 \u05d0\u05d5\u05de\u05e8,\n"
            "\u05d1\u05d9\u05d8, \u05d0\u05d5 \u05e7\u05d5\u05d9\u05d9\u05df..\n\n"
            "\u05d4\u05d9\u05d5\u05dd \u05d0\u05ea\u05dd \u05de\u05e9\u05dc\u05de\u05d9\u05dd \u05d1\u05d1\u05d9\u05d8 \u05db\u05de\u05e2\u05d8 \u05d1\u05db\u05dc \u05e8\u05db\u05d9\u05e9\u05d4,\n"
            "\u05d0\u05d1\u05dc \u05e2\u05d3\u05d9\u05d9\u05df \u05dc\u05d0 \u05de\u05d1\u05d9\u05e0\u05d9\u05dd \u05e9\u05e7\u05d5\u05d9\u05d9\u05df \u2014 \u05d6\u05d4 \u05dc\u05de\u05e2\u05e9\u05d4 \u05d1\u05d7\u05d9\u05e8\u05d4.\n\n"
            "\u05de\u05d9 \u05e9\u05d9\u05e9\u05df \u05e2\u05dc \u05d4\u05d0\u05e3 \u05dc\u05d0 \u05d9\u05e8\u05d5\u05d5\u05d9\u05d7 \u05db\u05e1\u05e3,\n"
            "\u05d1\u05e2\u05d5\u05dc\u05dd \u05e9\u05dc \u05db\u05d9\u05e1\u05d5\u05e4\u05d9\u05dd..\n"
            "\u05de\u05d9 \u05e9\u05d9\u05e9\u05df \u05e2\u05dc \u05d4\u05d0\u05e3 \u05dc\u05d0 \u05d9\u05e7\u05d5\u05dd,\n"
            "\u05d1\u05e2\u05d5\u05dc\u05dd \u05e9\u05dc \u05de\u05ea\u05e2\u05d5\u05e8\u05e8\u05d9\u05dd...\n\n"
            "SLH \u05d6\u05d5 \u05d4\u05d1\u05d7\u05d9\u05e8\u05d4 \u05d4\u05d7\u05db\u05de\u05d4 \u2014 \u05e1\u05d5\u05e6\u05d9\u05d5\u05e7\u05e8\u05d8\u05d9\u05d4.\n"
            "\u05de\u05e0\u05d4\u05dc, \u05dc\u05d0 \u05de\u05e9\u05d8\u05e8 \u05d5\u05dc\u05d0 \u05de\u05de\u05e9\u05dc.\n"
            "\u05e7\u05d4\u05d9\u05dc\u05d4. \U0001f3db\ufe0f"
        ),
        "category": "slh",
        "likes_count": 147,
    },
    {
        "username": "AvivCrypto",
        "text": "\u05de\u05d9 \u05e2\u05d5\u05d3 \u05e2\u05e9\u05d4 staking \u05e9\u05dc SLH \u05d4\u05e9\u05d1\u05d5\u05e2? \u05d4\u05ea\u05e9\u05d5\u05d0\u05d5\u05ea \u05de\u05d8\u05d5\u05e8\u05e4\u05d5\u05ea! \U0001f680\n\u05db\u05d1\u05e8 3 \u05d7\u05d5\u05d3\u05e9\u05d9\u05dd \u05e9\u05d0\u05e0\u05d9 \u05d1-staking \u05d5\u05e8\u05d5\u05d0\u05d4 \u05ea\u05d5\u05e6\u05d0\u05d5\u05ea \u05de\u05e2\u05d5\u05dc\u05d5\u05ea.",
        "category": "slh",
        "likes_count": 24,
    },
    {
        "username": "MosheTrader",
        "text": "\u05e0\u05d9\u05ea\u05d5\u05d7 \u05e9\u05d5\u05e7 \u05d9\u05d5\u05de\u05d9:\nSLH \u05e0\u05e1\u05d7\u05e8 \u05d1-444\u20aa \u05e2\u05dd \u05e0\u05e4\u05d7 \u05de\u05e1\u05d7\u05e8 \u05d2\u05d1\u05d5\u05d4. \u05d4\u05de\u05d2\u05de\u05d4 \u05d7\u05d9\u05d5\u05d1\u05d9\u05ea \u05de\u05d0\u05d5\u05d3 \u05d5\u05d0\u05e0\u05d9 \u05e8\u05d5\u05d0\u05d4 \u05e4\u05d5\u05d8\u05e0\u05e6\u05d9\u05d0\u05dc \u05dc\u05d4\u05de\u05e9\u05da \u05e2\u05dc\u05d9\u05d9\u05d4.\n\u05e9\u05d9\u05de\u05d5 \u05dc\u05d1 \u05dc\u05e8\u05de\u05ea \u05d4\u05ea\u05de\u05d9\u05db\u05d4 \u05d1-420\u20aa.",
        "category": "investments",
        "likes_count": 31,
    },
    {
        "username": "NoaInvest",
        "text": "\u05e9\u05de\u05e2\u05ea\u05dd \u05e2\u05dc \u05d4\u05d1\u05d5\u05d8 \u05d4\u05d7\u05d3\u05e9 \u05e9\u05dc SLH? Guardian Bot \u05de\u05d2\u05df \u05e2\u05dc \u05d4\u05e7\u05d1\u05d5\u05e6\u05d5\u05ea \u05e9\u05dc\u05db\u05dd \u05d1\u05d8\u05dc\u05d2\u05e8\u05dd.\n\u05de\u05de\u05dc\u05d9\u05e6\u05d4 \u05d1\u05d7\u05d5\u05dd! \U0001f6e1\ufe0f",
        "category": "slh",
        "likes_count": 18,
    },
    {
        "username": "DanielDeFi",
        "text": "\u05d8\u05d9\u05e4 \u05dc\u05de\u05e9\u05e7\u05d9\u05e2\u05d9\u05dd \u05d7\u05d3\u05e9\u05d9\u05dd: \u05ea\u05de\u05d9\u05d3 \u05ea\u05e2\u05e9\u05d5 DYOR \u05dc\u05e4\u05e0\u05d9 \u05db\u05dc \u05d4\u05e9\u05e7\u05e2\u05d4. \u05d0\u05dc \u05ea\u05e9\u05e7\u05d9\u05e2\u05d5 \u05d9\u05d5\u05ea\u05e8 \u05de\u05de\u05d4 \u05e9\u05d0\u05ea\u05dd \u05d9\u05db\u05d5\u05dc\u05d9\u05dd \u05dc\u05d4\u05e4\u05e1\u05d9\u05d3.\n\u05d2\u05d9\u05d5\u05d5\u05df \u05ea\u05d9\u05e7 \u05d4\u05d4\u05e9\u05e7\u05e2\u05d5\u05ea \u05d4\u05d5\u05d0 \u05d4\u05de\u05e4\u05ea\u05d7 \u05dc\u05d4\u05e6\u05dc\u05d7\u05d4 \u05d0\u05e8\u05d5\u05db\u05ea \u05d8\u05d5\u05d5\u05d7.",
        "category": "investments",
        "likes_count": 45,
    },
    {
        "username": "YosiBlockchain",
        "text": "\u05de\u05d9\u05e9\u05d4\u05d5 \u05e8\u05d5\u05e6\u05d4 \u05dc\u05d4\u05e6\u05d8\u05e8\u05e3 \u05dc\u05de\u05d9\u05d8\u05d0\u05e4 \u05e9\u05dc \u05d4\u05e7\u05d4\u05d9\u05dc\u05d4 \u05d1\u05ea\u05dc \u05d0\u05d1\u05d9\u05d1 \u05d1\u05e9\u05d1\u05d5\u05e2 \u05d4\u05d1\u05d0?\n\u05e0\u05d3\u05d1\u05e8 \u05e2\u05dc DeFi, SLH \u05d5\u05e2\u05ea\u05d9\u05d3 \u05d4\u05d1\u05dc\u05d5\u05e7\u05e6'\u05d9\u05d9\u05df \u05d1\u05d9\u05e9\u05e8\u05d0\u05dc \U0001f1ee\U0001f1f1",
        "category": "general",
        "likes_count": 37,
    },
]


async def init_db():
    """Create pool, run schema, seed if empty."""
    global pool
    # Phase 0B (2026-04-21): unified fail-fast pool via shared_db_core.
    try:
        from shared_db_core import init_db_pool as _shared_init_db_pool
        pool = await _shared_init_db_pool(DATABASE_URL)
    except Exception:
        pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
    async with pool.acquire() as conn:
        await conn.execute(SCHEMA_SQL)
        # Seed if empty
        count = await conn.fetchval("SELECT count(*) FROM community_posts")
        if count == 0:
            for i, sp in enumerate(SEED_POSTS):
                await conn.execute(
                    """
                    INSERT INTO community_posts (username, text, category, likes_count, created_at)
                    VALUES ($1, $2, $3, $4, now() - interval '1 hour' * $5)
                    """,
                    sp["username"],
                    sp["text"],
                    sp["category"],
                    sp["likes_count"],
                    (len(SEED_POSTS) - i) * 4,  # stagger times
                )


@app.on_event("startup")
async def startup():
    await init_db()


@app.on_event("shutdown")
async def shutdown():
    global pool
    if pool:
        await pool.close()


# ── Endpoints ──


@app.get("/api/community/health")
async def health():
    try:
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=503)


@app.get("/api/community/posts")
async def get_posts(category: str = "all", limit: int = 50, offset: int = 0):
    limit = min(limit, 100)
    offset = max(offset, 0)

    async with pool.acquire() as conn:
        if category == "all":
            rows = await conn.fetch(
                """
                SELECT id, username, telegram_id, text, category, likes_count, created_at
                FROM community_posts
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
                """,
                limit,
                offset,
            )
        else:
            rows = await conn.fetch(
                """
                SELECT id, username, telegram_id, text, category, likes_count, created_at
                FROM community_posts
                WHERE category = $1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
                """,
                category,
                limit,
                offset,
            )

        posts = []
        for row in rows:
            post = dict(row)
            post["created_at"] = post["created_at"].isoformat()

            # Fetch comments for this post
            comments = await conn.fetch(
                """
                SELECT id, username, text, created_at
                FROM community_comments
                WHERE post_id = $1
                ORDER BY created_at ASC
                """,
                post["id"],
            )
            post["comments"] = [
                {
                    "id": c["id"],
                    "username": c["username"],
                    "text": c["text"],
                    "created_at": c["created_at"].isoformat(),
                }
                for c in comments
            ]

            posts.append(post)

    return {"posts": posts, "count": len(posts), "offset": offset}


@app.post("/api/community/posts")
async def create_post(body: PostCreate):
    # Rate limit: 10 posts / user / hour
    key = f"post:{body.username}"
    if not check_rate_limit(key, 10):
        raise HTTPException(429, "Rate limit exceeded: max 10 posts per hour")

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO community_posts (username, telegram_id, text, category)
            VALUES ($1, $2, $3, $4)
            RETURNING id, username, telegram_id, text, category, likes_count, created_at
            """,
            body.username,
            body.telegram_id,
            body.text,
            body.category,
        )
        post = dict(row)
        post["created_at"] = post["created_at"].isoformat()
        post["comments"] = []
        return post


@app.post("/api/community/posts/{post_id}/like")
async def toggle_like(post_id: int, body: LikeToggle):
    async with pool.acquire() as conn:
        # Check post exists
        exists = await conn.fetchval(
            "SELECT id FROM community_posts WHERE id = $1", post_id
        )
        if not exists:
            raise HTTPException(404, "Post not found")

        # Try to insert like; if duplicate, delete it (toggle)
        existing = await conn.fetchval(
            "SELECT id FROM community_likes WHERE post_id = $1 AND username = $2",
            post_id,
            body.username,
        )
        if existing:
            await conn.execute("DELETE FROM community_likes WHERE id = $1", existing)
            await conn.execute(
                "UPDATE community_posts SET likes_count = GREATEST(likes_count - 1, 0) WHERE id = $1",
                post_id,
            )
            return {"action": "unliked", "post_id": post_id}
        else:
            await conn.execute(
                "INSERT INTO community_likes (post_id, username) VALUES ($1, $2)",
                post_id,
                body.username,
            )
            await conn.execute(
                "UPDATE community_posts SET likes_count = likes_count + 1 WHERE id = $1",
                post_id,
            )
            return {"action": "liked", "post_id": post_id}


@app.post("/api/community/posts/{post_id}/comments")
async def add_comment(post_id: int, body: CommentCreate):
    # Rate limit: 50 comments / user / hour
    key = f"comment:{body.username}"
    if not check_rate_limit(key, 50):
        raise HTTPException(429, "Rate limit exceeded: max 50 comments per hour")

    async with pool.acquire() as conn:
        exists = await conn.fetchval(
            "SELECT id FROM community_posts WHERE id = $1", post_id
        )
        if not exists:
            raise HTTPException(404, "Post not found")

        row = await conn.fetchrow(
            """
            INSERT INTO community_comments (post_id, username, text)
            VALUES ($1, $2, $3)
            RETURNING id, post_id, username, text, created_at
            """,
            post_id,
            body.username,
            body.text,
        )
        comment = dict(row)
        comment["created_at"] = comment["created_at"].isoformat()
        return comment


@app.get("/api/community/stats")
async def get_stats():
    async with pool.acquire() as conn:
        total_posts = await conn.fetchval("SELECT count(*) FROM community_posts")
        total_users = await conn.fetchval(
            "SELECT count(DISTINCT username) FROM community_posts"
        )
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        active_today = await conn.fetchval(
            """
            SELECT count(DISTINCT username) FROM community_posts
            WHERE created_at >= $1
            """,
            today_start,
        )
        posts_today = await conn.fetchval(
            "SELECT count(*) FROM community_posts WHERE created_at >= $1",
            today_start,
        )

    return {
        "total_posts": total_posts,
        "total_users": total_users,
        "active_today": active_today,
        "posts_today": posts_today,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("community_api:app", host="0.0.0.0", port=8001, reload=True)
