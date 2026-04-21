"""
SLH Wellness Task Scheduler - APScheduler Integration
Handles cron-based task broadcasting and token distribution
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

import asyncpg
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

class WellnessScheduler:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.scheduler = AsyncIOScheduler()
        self.pool: Optional[asyncpg.Pool] = None

    async def start(self):
        """Initialize database connection and start scheduler"""
        # Phase 0B (2026-04-21): unified fail-fast pool via shared_db_core.
        # max_size standardized 10→4 per Phase 0B plan.
        try:
            from shared_db_core import init_db_pool as _shared_init_db_pool
            self.pool = await _shared_init_db_pool(self.database_url)
        except Exception as _shared_err:
            logger.warning(f"shared_db_core unavailable, direct pool: {_shared_err}")
            self.pool = await asyncpg.create_pool(self.database_url, min_size=2, max_size=10)

        # Load all existing schedules from database
        await self._load_schedules()

        # Start the scheduler
        self.scheduler.start()
        logger.info("[Wellness] Scheduler started with APScheduler")

    async def stop(self):
        """Stop scheduler and close database connection"""
        self.scheduler.shutdown()
        if self.pool:
            await self.pool.close()
        logger.info("[Wellness] Scheduler stopped")

    async def _load_schedules(self):
        """Load all active schedules from database and register them"""
        if not self.pool:
            return

        async with self.pool.acquire() as conn:
            schedules = await conn.fetch(
                "SELECT * FROM wellness_schedules WHERE enabled = TRUE"
            )

            for schedule in schedules:
                try:
                    task_ids = json.loads(schedule['task_ids']) if schedule['task_ids'] else []

                    # Create a trigger from cron expression
                    trigger = CronTrigger.from_crontab(schedule['cron_expression'])

                    # Register the job
                    self.scheduler.add_job(
                        self._broadcast_schedule_tasks,
                        trigger=trigger,
                        args=(schedule['id'], task_ids),
                        id=f"wellness_schedule_{schedule['id']}",
                        name=schedule['name'],
                        replace_existing=True,
                        coalesce=True,
                        max_instances=1
                    )
                    logger.info(f"[Wellness] Loaded schedule: {schedule['name']} (ID: {schedule['id']})")
                except Exception as e:
                    logger.error(f"[Wellness] Failed to load schedule {schedule['id']}: {str(e)}")

    async def _broadcast_schedule_tasks(self, schedule_id: int, task_ids: list):
        """Broadcast tasks to all users and award tokens"""
        if not self.pool:
            logger.error("[Wellness] Database pool not initialized")
            return

        async with self.pool.acquire() as conn:
            try:
                # Get all registered users
                users = await conn.fetch(
                    "SELECT telegram_id FROM web_users WHERE is_registered = TRUE"
                )

                sent_count = 0
                failed_count = 0

                for user_row in users:
                    user_id = user_row['telegram_id']

                    for task_id in task_ids:
                        try:
                            # Get task details
                            task = await conn.fetchrow(
                                "SELECT * FROM wellness_tasks WHERE id = $1",
                                task_id
                            )

                            if not task:
                                continue

                            # Record completion
                            await conn.execute("""
                                INSERT INTO wellness_completions
                                (user_id, task_id, tokens_awarded, rep_awarded, slh_awarded)
                                VALUES ($1, $2, $3, $4, $5)
                            """,
                            user_id, task['id'], task['reward_zvk'],
                            task['reward_rep'], float(task['reward_slh'])
                            )

                            # Update user progress
                            await conn.execute("""
                                INSERT INTO wellness_user_progress
                                (user_id, total_rewards_zvk, total_rewards_rep, total_rewards_slh, last_completion)
                                VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP)
                                ON CONFLICT (user_id) DO UPDATE SET
                                    total_rewards_zvk = total_rewards_zvk + $2,
                                    total_rewards_rep = total_rewards_rep + $3,
                                    total_rewards_slh = total_rewards_slh + $4,
                                    last_completion = CURRENT_TIMESTAMP,
                                    updated_at = CURRENT_TIMESTAMP
                            """,
                            user_id, task['reward_zvk'],
                            task['reward_rep'], float(task['reward_slh'])
                            )

                            sent_count += 1

                        except Exception as e:
                            failed_count += 1
                            logger.error(f"[Wellness] Failed to send task {task_id} to user {user_id}: {str(e)}")

                # Update schedule last_run
                next_run = self.scheduler.get_job(f"wellness_schedule_{schedule_id}").next_run_time
                await conn.execute("""
                    UPDATE wellness_schedules
                    SET last_run = CURRENT_TIMESTAMP, next_run = $2
                    WHERE id = $1
                """, schedule_id, next_run)

                logger.info(f"[Wellness] Schedule {schedule_id} broadcast: {sent_count} sent, {failed_count} failed")

            except Exception as e:
                logger.error(f"[Wellness] Broadcast failed for schedule {schedule_id}: {str(e)}")

    async def add_schedule(self, schedule_id: int, name: str, cron_expr: str, task_ids: list):
        """Dynamically add a new schedule (called via API)"""
        try:
            trigger = CronTrigger.from_crontab(cron_expr)
            self.scheduler.add_job(
                self._broadcast_schedule_tasks,
                trigger=trigger,
                args=(schedule_id, task_ids),
                id=f"wellness_schedule_{schedule_id}",
                name=name,
                replace_existing=True,
                coalesce=True,
                max_instances=1
            )
            logger.info(f"[Wellness] Added schedule: {name} (ID: {schedule_id})")
        except Exception as e:
            logger.error(f"[Wellness] Failed to add schedule {schedule_id}: {str(e)}")

    async def remove_schedule(self, schedule_id: int):
        """Remove a schedule (called via API)"""
        try:
            job_id = f"wellness_schedule_{schedule_id}"
            self.scheduler.remove_job(job_id)
            logger.info(f"[Wellness] Removed schedule {schedule_id}")
        except Exception as e:
            logger.error(f"[Wellness] Failed to remove schedule {schedule_id}: {str(e)}")


# Global scheduler instance
_wellness_scheduler: Optional[WellnessScheduler] = None

async def init_wellness_scheduler(database_url: str):
    """Initialize the global wellness scheduler"""
    global _wellness_scheduler
    _wellness_scheduler = WellnessScheduler(database_url)
    await _wellness_scheduler.start()

def get_wellness_scheduler() -> WellnessScheduler:
    """Get the global wellness scheduler instance"""
    if not _wellness_scheduler:
        raise RuntimeError("Wellness scheduler not initialized")
    return _wellness_scheduler
