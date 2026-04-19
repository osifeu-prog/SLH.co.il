"""
SLH Wellness System - Courses, Tasks, Scheduling & Broadcasting
Integrated with token rewards (ZVK, REP, SLH)
"""
import os
import re
import json
from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel
import asyncpg
from fastapi import APIRouter, HTTPException, Header, Query

router = APIRouter(prefix="/api/wellness", tags=["wellness"])
pool: Optional[asyncpg.Pool] = None

def set_pool(p: asyncpg.Pool):
    global pool
    pool = p

# ============================================================================
# DATA MODELS
# ============================================================================

class WellnessCourseCreate(BaseModel):
    course_title: str
    course_description: str
    course_content: str  # HTML/Markdown
    category: str  # meditation, fitness, nutrition, wellness
    difficulty: str  # beginner, intermediate, advanced
    duration_minutes: int
    price_zvk: int
    instructor_id: Optional[int] = None
    video_url: Optional[str] = None

class WellnessTaskCreate(BaseModel):
    title: str
    task_type: str  # meditation, exercise, nutrition, affirmation
    duration_minutes: int
    description: str
    reward_zvk: int = 5
    reward_rep: int = 10
    reward_slh: float = 0.1

class ScheduleTaskCreate(BaseModel):
    schedule_name: str
    schedule_type: str  # daily, weekly, custom
    cron_expression: str  # e.g., "0 8 * * *" = 8am daily
    task_ids: List[int]
    broadcast_time: str  # HH:MM format
    enabled: bool = True

class BroadcastTaskRequest(BaseModel):
    schedule_id: Optional[int] = None
    task_id: Optional[int] = None
    force_now: bool = False

# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

async def init_wellness_tables():
    """Create wellness tables on startup"""
    if not pool:
        return

    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS wellness_courses (
                id BIGSERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                description TEXT,
                content TEXT,
                instructor_id BIGINT,
                category TEXT,
                difficulty TEXT,
                duration_minutes INT,
                price_zvk INT DEFAULT 0,
                video_url TEXT,
                published BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                student_count INT DEFAULT 0,
                rating NUMERIC(3,2) DEFAULT 0.0
            );
            CREATE INDEX IF NOT EXISTS idx_courses_slug ON wellness_courses(slug);
            CREATE INDEX IF NOT EXISTS idx_courses_category ON wellness_courses(category);

            CREATE TABLE IF NOT EXISTS wellness_tasks (
                id BIGSERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                type TEXT,
                description TEXT,
                duration_minutes INT,
                reward_zvk INT DEFAULT 5,
                reward_rep INT DEFAULT 10,
                reward_slh NUMERIC(10,4) DEFAULT 0.1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS wellness_schedules (
                id BIGSERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT,
                cron_expression TEXT,
                task_ids TEXT,
                broadcast_time TEXT,
                enabled BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_run TIMESTAMP,
                next_run TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_schedules_enabled ON wellness_schedules(enabled);

            CREATE TABLE IF NOT EXISTS wellness_completions (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                task_id BIGINT NOT NULL,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tokens_awarded INT,
                rep_awarded INT,
                slh_awarded NUMERIC(10,4),
                streak_count INT DEFAULT 1
            );
            CREATE INDEX IF NOT EXISTS idx_completions_user ON wellness_completions(user_id);

            CREATE TABLE IF NOT EXISTS wellness_user_progress (
                user_id BIGINT PRIMARY KEY,
                total_completed INT DEFAULT 0,
                current_streak INT DEFAULT 0,
                last_completion TIMESTAMP,
                total_rewards_zvk INT DEFAULT 0,
                total_rewards_rep INT DEFAULT 0,
                total_rewards_slh NUMERIC(18,8) DEFAULT 0,
                level INT DEFAULT 1,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_slug(title: str) -> str:
    """Convert title to URL-friendly slug"""
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    return slug[:50]

async def award_tokens(user_id: int, zvk: int = 0, rep: int = 0, slh: float = 0):
    """Award tokens to user from task completion"""
    if not pool:
        return

    async with pool.acquire() as conn:
        # Update user progress
        await conn.execute("""
            INSERT INTO wellness_user_progress (user_id, total_rewards_zvk, total_rewards_rep, total_rewards_slh)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id) DO UPDATE SET
                total_rewards_zvk = total_rewards_zvk + $2,
                total_rewards_rep = total_rewards_rep + $3,
                total_rewards_slh = total_rewards_slh + $4,
                updated_at = CURRENT_TIMESTAMP
        """, user_id, zvk, rep, slh)

# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/course-upload")
async def upload_course(
    req: WellnessCourseCreate,
    x_admin_key: Optional[str] = Header(None)
):
    """Upload a wellness course - admin only"""
    if not x_admin_key:
        raise HTTPException(401, "Admin key required")

    if not pool:
        raise HTTPException(500, "Database not ready")

    slug = generate_slug(req.course_title)

    async with pool.acquire() as conn:
        try:
            course_id = await conn.fetchval("""
                INSERT INTO wellness_courses
                (title, slug, description, content, instructor_id, category, difficulty, duration_minutes, price_zvk, video_url, published)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, TRUE)
                RETURNING id
            """,
            req.course_title, slug, req.course_description, req.course_content,
            req.instructor_id, req.category, req.difficulty,
            req.duration_minutes, req.price_zvk, req.video_url
            )

            return {
                "course_id": course_id,
                "slug": slug,
                "status": "created",
                "message": f"Course '{req.course_title}' created successfully"
            }
        except Exception as e:
            raise HTTPException(400, f"Course upload failed: {str(e)}")

@router.post("/schedule-task")
async def schedule_task(
    req: ScheduleTaskCreate,
    x_admin_key: Optional[str] = Header(None)
):
    """Create a wellness task schedule - admin only"""
    if not x_admin_key:
        raise HTTPException(401, "Admin key required")

    if not pool:
        raise HTTPException(500, "Database not ready")

    async with pool.acquire() as conn:
        try:
            # Calculate next run time from cron expression
            # Simple implementation: if it's daily, next run is tomorrow at broadcast_time
            now = datetime.utcnow()
            broadcast_parts = req.broadcast_time.split(":")
            broadcast_hour = int(broadcast_parts[0])
            broadcast_minute = int(broadcast_parts[1]) if len(broadcast_parts) > 1 else 0

            next_run = now.replace(hour=broadcast_hour, minute=broadcast_minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)

            task_ids_json = json.dumps(req.task_ids)

            schedule_id = await conn.fetchval("""
                INSERT INTO wellness_schedules
                (name, type, cron_expression, task_ids, broadcast_time, enabled, next_run)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
            """,
            req.schedule_name, req.schedule_type, req.cron_expression,
            task_ids_json, req.broadcast_time, req.enabled, next_run
            )

            return {
                "schedule_id": schedule_id,
                "next_run": next_run.isoformat(),
                "status": "scheduled",
                "message": f"Schedule '{req.schedule_name}' created"
            }
        except Exception as e:
            raise HTTPException(400, f"Schedule creation failed: {str(e)}")

@router.post("/broadcast-task")
async def broadcast_task(
    req: BroadcastTaskRequest,
    x_admin_key: Optional[str] = Header(None)
):
    """Broadcast a task to all users and process completions"""
    if not x_admin_key:
        raise HTTPException(401, "Admin key required")

    if not pool:
        raise HTTPException(500, "Database not ready")

    async with pool.acquire() as conn:
        try:
            # Get all active users
            users = await conn.fetch("SELECT telegram_id FROM web_users WHERE is_registered = TRUE")

            # Get task details
            if req.task_id:
                task = await conn.fetchrow("SELECT * FROM wellness_tasks WHERE id = $1", req.task_id)
            else:
                task = None

            sent_count = 0
            failed_count = 0

            # Broadcast to each user
            for user_row in users:
                user_id = user_row['telegram_id']
                try:
                    if task:
                        # Record completion attempt
                        await conn.execute("""
                            INSERT INTO wellness_completions
                            (user_id, task_id, tokens_awarded, rep_awarded, slh_awarded)
                            VALUES ($1, $2, $3, $4, $5)
                        """,
                        user_id, task['id'], task['reward_zvk'],
                        task['reward_rep'], float(task['reward_slh'])
                        )

                        # Award tokens
                        await award_tokens(
                            user_id,
                            zvk=task['reward_zvk'],
                            rep=task['reward_rep'],
                            slh=float(task['reward_slh'])
                        )

                    sent_count += 1
                except Exception as e:
                    failed_count += 1

            return {
                "recipients": len(users),
                "sent": sent_count,
                "failed": failed_count,
                "status": "completed",
                "message": f"Broadcast sent to {sent_count}/{len(users)} users"
            }
        except Exception as e:
            raise HTTPException(400, f"Broadcast failed: {str(e)}")

@router.get("/courses")
async def list_courses(
    category: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    limit: int = Query(20, le=100)
):
    """List all published courses with optional filtering"""
    if not pool:
        raise HTTPException(500, "Database not ready")

    async with pool.acquire() as conn:
        query = "SELECT * FROM wellness_courses WHERE published = TRUE"
        params = []

        if category:
            query += " AND category = $" + str(len(params) + 1)
            params.append(category)

        if difficulty:
            query += " AND difficulty = $" + str(len(params) + 1)
            params.append(difficulty)

        query += " ORDER BY created_at DESC LIMIT $" + str(len(params) + 1)
        params.append(limit)

        courses = await conn.fetch(query, *params)

        return {
            "courses": [dict(row) for row in courses],
            "total": len(courses)
        }

@router.get("/schedules")
async def list_schedules(x_admin_key: Optional[str] = Header(None)):
    """List all active schedules - admin only"""
    if not x_admin_key:
        raise HTTPException(401, "Admin key required")

    if not pool:
        raise HTTPException(500, "Database not ready")

    async with pool.acquire() as conn:
        schedules = await conn.fetch(
            "SELECT * FROM wellness_schedules WHERE enabled = TRUE ORDER BY next_run ASC"
        )

        return {
            "schedules": [dict(row) for row in schedules],
            "total": len(schedules)
        }

@router.get("/progress/:user_id")
async def get_user_progress(user_id: int):
    """Get user's wellness progress"""
    if not pool:
        raise HTTPException(500, "Database not ready")

    async with pool.acquire() as conn:
        progress = await conn.fetchrow(
            "SELECT * FROM wellness_user_progress WHERE user_id = $1",
            user_id
        )

        if not progress:
            return {
                "user_id": user_id,
                "total_completed": 0,
                "current_streak": 0,
                "total_rewards_zvk": 0,
                "total_rewards_rep": 0,
                "total_rewards_slh": 0,
                "level": 1
            }

        return dict(progress)

@router.post("/task-create")
async def create_task(
    req: WellnessTaskCreate,
    x_admin_key: Optional[str] = Header(None)
):
    """Create a wellness task - admin only"""
    if not x_admin_key:
        raise HTTPException(401, "Admin key required")

    if not pool:
        raise HTTPException(500, "Database not ready")

    async with pool.acquire() as conn:
        try:
            task_id = await conn.fetchval("""
                INSERT INTO wellness_tasks
                (title, type, description, duration_minutes, reward_zvk, reward_rep, reward_slh)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
            """,
            req.title, req.task_type, req.description,
            req.duration_minutes, req.reward_zvk, req.reward_rep, req.reward_slh
            )

            return {
                "task_id": task_id,
                "status": "created",
                "message": f"Task '{req.title}' created"
            }
        except Exception as e:
            raise HTTPException(400, f"Task creation failed: {str(e)}")

@router.get("/tasks")
async def list_tasks():
    """List all wellness tasks"""
    if not pool:
        raise HTTPException(500, "Database not ready")

    async with pool.acquire() as conn:
        tasks = await conn.fetch("SELECT * FROM wellness_tasks ORDER BY created_at DESC")

        return {
            "tasks": [dict(row) for row in tasks],
            "total": len(tasks)
        }
