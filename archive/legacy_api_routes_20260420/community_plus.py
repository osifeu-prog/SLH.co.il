"""
SLH Community Plus â€” Layer 1 chat upgrade
==========================================
Reactions (6 emoji types), threaded replies, last-seen presence.

Endpoints:
  POST /api/community/posts/{post_id}/react        â€” toggle/change emoji reaction
  GET  /api/community/posts/{post_id}/reactions    â€” counts by type + my reaction
  POST /api/community/comments/{comment_id}/reply  â€” reply to a comment (1 level nest)
  GET  /api/community/posts/{post_id}/threaded     â€” post + nested comments tree
  POST /api/presence/heartbeat                     â€” touch user last_seen
  GET  /api/presence/{user_id}                     â€” user last_seen + online status

Added 2026-04-17 (layer 1 chat upgrade).
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["Community Plus"])

_pool = None
def set_pool(pool):
    global _pool
    _pool = pool


REACTION_TYPES = {"like", "love", "laugh", "wow", "sad", "angry"}
ONLINE_WINDOW_SECONDS = 180  # treat "online" if heartbeat within 3 min


async def _ensure_plus_tables(conn):
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS post_reactions (
            id BIGSERIAL PRIMARY KEY,
            post_id BIGINT NOT NULL REFERENCES community_posts(id) ON DELETE CASCADE,
            username TEXT NOT NULL,
            reaction_type TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(post_id, username)
        );
        CREATE INDEX IF NOT EXISTS idx_post_reactions_post ON post_reactions(post_id);
        CREATE INDEX IF NOT EXISTS idx_post_reactions_user ON post_reactions(username);

        ALTER TABLE community_comments ADD COLUMN IF NOT EXISTS parent_comment_id BIGINT REFERENCES community_comments(id) ON DELETE CASCADE;
        CREATE INDEX IF NOT EXISTS idx_community_comments_parent ON community_comments(parent_comment_id);

        CREATE TABLE IF NOT EXISTS user_presence (
            username TEXT PRIMARY KEY,
            user_id BIGINT,
            last_seen TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_user_presence_last_seen ON user_presence(last_seen DESC);
        """
    )


class ReactReq(BaseModel):
    username: str
    reaction_type: str  # like|love|laugh|wow|sad|angry


@router.post("/api/community/posts/{post_id}/react")
async def post_react(post_id: int, req: ReactReq):
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    rtype = (req.reaction_type or "").strip().lower()
    if rtype not in REACTION_TYPES:
        raise HTTPException(400, f"invalid reaction_type; allowed: {sorted(REACTION_TYPES)}")
    uname = (req.username or "").strip()
    if not uname:
        raise HTTPException(400, "username required")

    async with _pool.acquire() as conn:
        await _ensure_plus_tables(conn)
        exists = await conn.fetchval("SELECT id FROM community_posts WHERE id=$1", post_id)
        if not exists:
            raise HTTPException(404, "Post not found")

        existing = await conn.fetchrow(
            "SELECT id, reaction_type FROM post_reactions WHERE post_id=$1 AND username=$2",
            post_id, uname,
        )
        if existing and existing["reaction_type"] == rtype:
            # Same reaction â€” toggle off (remove)
            await conn.execute("DELETE FROM post_reactions WHERE id=$1", existing["id"])
            action = "removed"
        elif existing:
            # Change reaction type
            await conn.execute(
                "UPDATE post_reactions SET reaction_type=$1, created_at=now() WHERE id=$2",
                rtype, existing["id"],
            )
            action = "changed"
        else:
            # New reaction
            await conn.execute(
                "INSERT INTO post_reactions (post_id, username, reaction_type) VALUES ($1, $2, $3)",
                post_id, uname, rtype,
            )
            action = "added"

        # Refresh likes_count to match total reactions (backward compat)
        total = await conn.fetchval("SELECT COUNT(*) FROM post_reactions WHERE post_id=$1", post_id)
        await conn.execute("UPDATE community_posts SET likes_count=$1 WHERE id=$2", total, post_id)

    return {"action": action, "reaction_type": rtype, "post_id": post_id}


@router.get("/api/community/posts/{post_id}/reactions")
async def post_reactions_list(post_id: int, my_username: Optional[str] = None):
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_plus_tables(conn)
        counts = await conn.fetch(
            "SELECT reaction_type, COUNT(*) as c FROM post_reactions WHERE post_id=$1 GROUP BY reaction_type",
            post_id,
        )
        counts_by_type = {t: 0 for t in REACTION_TYPES}
        for row in counts:
            counts_by_type[row["reaction_type"]] = row["c"]

        my_reaction = None
        if my_username:
            my_reaction = await conn.fetchval(
                "SELECT reaction_type FROM post_reactions WHERE post_id=$1 AND username=$2",
                post_id, my_username,
            )

        recent = await conn.fetch(
            "SELECT username, reaction_type, created_at FROM post_reactions WHERE post_id=$1 ORDER BY created_at DESC LIMIT 20",
            post_id,
        )
    return {
        "post_id": post_id,
        "counts": counts_by_type,
        "total": sum(counts_by_type.values()),
        "my_reaction": my_reaction,
        "recent": [{"username": r["username"], "reaction_type": r["reaction_type"], "created_at": r["created_at"].isoformat()} for r in recent],
    }


class ReplyReq(BaseModel):
    username: str
    text: str


@router.post("/api/community/comments/{comment_id}/reply")
async def reply_to_comment(comment_id: int, req: ReplyReq):
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    text = (req.text or "").strip()
    uname = (req.username or "").strip()
    if not text or not uname:
        raise HTTPException(400, "username and text required")
    if len(text) > 2000:
        raise HTTPException(413, "reply too long (max 2000 chars)")

    async with _pool.acquire() as conn:
        await _ensure_plus_tables(conn)
        parent = await conn.fetchrow("SELECT id, post_id, parent_comment_id FROM community_comments WHERE id=$1", comment_id)
        if not parent:
            raise HTTPException(404, "Parent comment not found")
        # Resolve to top-level comment: if parent already has a parent_comment_id, reply attaches to the root
        root_id = parent["parent_comment_id"] or parent["id"]

        row = await conn.fetchrow(
            """
            INSERT INTO community_comments (post_id, username, text, parent_comment_id)
            VALUES ($1, $2, $3, $4)
            RETURNING id, post_id, username, text, created_at, parent_comment_id
            """,
            parent["post_id"], uname, text, root_id,
        )
        reply = dict(row)
        reply["created_at"] = reply["created_at"].isoformat()
    return reply


@router.get("/api/community/posts/{post_id}/threaded")
async def post_threaded(post_id: int):
    """Return post + all comments nested by parent_comment_id (1 level deep)."""
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_plus_tables(conn)
        post = await conn.fetchrow(
            "SELECT id, username, telegram_id, text, category, image_data, likes_count, created_at FROM community_posts WHERE id=$1",
            post_id,
        )
        if not post:
            raise HTTPException(404, "Post not found")
        all_comments = await conn.fetch(
            """
            SELECT id, post_id, username, text, parent_comment_id, created_at
            FROM community_comments WHERE post_id=$1 ORDER BY created_at ASC
            """,
            post_id,
        )

    # Build tree
    by_id = {}
    roots = []
    for c in all_comments:
        item = {
            "id": c["id"], "username": c["username"], "text": c["text"],
            "created_at": c["created_at"].isoformat(), "replies": [],
            "parent_comment_id": c["parent_comment_id"],
        }
        by_id[c["id"]] = item
        if c["parent_comment_id"] is None:
            roots.append(item)

    for c in all_comments:
        if c["parent_comment_id"] is not None:
            parent = by_id.get(c["parent_comment_id"])
            if parent:
                parent["replies"].append(by_id[c["id"]])

    return {
        "post": {
            "id": post["id"], "username": post["username"], "telegram_id": post["telegram_id"],
            "text": post["text"], "category": post["category"], "image_data": post["image_data"],
            "likes_count": post["likes_count"], "created_at": post["created_at"].isoformat(),
        },
        "comments": roots,
    }


class PresenceReq(BaseModel):
    username: str
    user_id: Optional[int] = None


@router.post("/api/presence/heartbeat")
async def presence_heartbeat(req: PresenceReq):
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    uname = (req.username or "").strip()
    if not uname:
        raise HTTPException(400, "username required")
    async with _pool.acquire() as conn:
        await _ensure_plus_tables(conn)
        await conn.execute(
            """
            INSERT INTO user_presence (username, user_id, last_seen, updated_at)
            VALUES ($1, $2, now(), now())
            ON CONFLICT (username) DO UPDATE SET
                last_seen = now(), updated_at = now(),
                user_id = COALESCE(EXCLUDED.user_id, user_presence.user_id)
            """,
            uname, req.user_id,
        )
    return {"ok": True, "username": uname, "last_seen": datetime.utcnow().isoformat() + "Z"}


@router.get("/api/presence/{username}")
async def presence_get(username: str):
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_plus_tables(conn)
        row = await conn.fetchrow("SELECT last_seen FROM user_presence WHERE username=$1", username)
    if not row:
        return {"username": username, "online": False, "last_seen": None}
    now = datetime.now(row["last_seen"].tzinfo)
    online = (now - row["last_seen"]).total_seconds() <= ONLINE_WINDOW_SECONDS
    return {
        "username": username,
        "online": online,
        "last_seen": row["last_seen"].isoformat(),
        "seconds_ago": int((now - row["last_seen"]).total_seconds()),
    }


@router.get("/api/presence/bulk")
async def presence_bulk(usernames: str):
    """Comma-separated list of usernames â†’ online status for each."""
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    names = [n.strip() for n in usernames.split(",") if n.strip()][:100]
    if not names:
        return {"users": []}
    async with _pool.acquire() as conn:
        await _ensure_plus_tables(conn)
        rows = await conn.fetch(
            "SELECT username, last_seen FROM user_presence WHERE username = ANY($1::text[])",
            names,
        )
    out = []
    found = {r["username"]: r for r in rows}
    now_ref = datetime.now().astimezone()
    for n in names:
        r = found.get(n)
        if r:
            now = datetime.now(r["last_seen"].tzinfo)
            secs = int((now - r["last_seen"]).total_seconds())
            out.append({
                "username": n,
                "online": secs <= ONLINE_WINDOW_SECONDS,
                "seconds_ago": secs,
                "last_seen": r["last_seen"].isoformat(),
            })
        else:
            out.append({"username": n, "online": False, "seconds_ago": None, "last_seen": None})
    return {"users": out}


@router.get("/api/presence/online/count")
async def presence_online_count():
    """Total users currently online (last_seen within window)."""
    if _pool is None:
        raise HTTPException(500, "db pool not initialized")
    async with _pool.acquire() as conn:
        await _ensure_plus_tables(conn)
        cnt = await conn.fetchval(
            "SELECT COUNT(*) FROM user_presence WHERE last_seen > now() - interval '3 minutes'"
        )
    return {"online_count": cnt or 0, "window_seconds": ONLINE_WINDOW_SECONDS}
