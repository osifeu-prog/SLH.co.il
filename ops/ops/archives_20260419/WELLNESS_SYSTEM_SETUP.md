# SLH Wellness System - Complete Setup Guide

## Overview

The SLH Wellness System is a comprehensive course, task, and scheduling platform integrated with the SLH token rewards ecosystem. It allows admins to:

- Upload and manage wellness courses (meditation, fitness, nutrition)
- Create reusable wellness tasks with token rewards
- Schedule automatic task broadcasting via cron expressions
- Manually broadcast tasks to all users
- Track user progress and streak counts
- Award ZVK, REP, and SLH tokens on task completion

**Status:** ✅ Production Ready  
**Deployment:** Railway (auto-synced from GitHub)  
**Database:** PostgreSQL (5 new tables)

---

## Installation & Setup

### 1. Add APScheduler to Requirements

The `requirements.txt` has been updated with:
```
apscheduler>=3.10.0
```

Deploy to Railway to install the dependency.

### 2. Database Tables (Auto-Created on Startup)

The following tables are created automatically when the API starts:

```sql
wellness_courses
  - id, title, slug, description, content
  - instructor_id, category (meditation/fitness/nutrition/wellness)
  - difficulty (beginner/intermediate/advanced)
  - duration_minutes, price_zvk
  - video_url, published, student_count, rating
  - created_at, updated_at

wellness_tasks
  - id, title, type (meditation/exercise/nutrition/affirmation)
  - description, duration_minutes
  - reward_zvk, reward_rep, reward_slh
  - created_at

wellness_schedules
  - id, name, type (daily/weekly/custom)
  - cron_expression, task_ids (JSON array)
  - broadcast_time, enabled
  - next_run, last_run
  - created_at, updated_at

wellness_completions
  - id, user_id, task_id
  - tokens_awarded, rep_awarded, slh_awarded
  - streak_count, completed_at

wellness_user_progress
  - user_id (PRIMARY KEY)
  - total_completed, current_streak, last_completion
  - total_rewards_zvk, total_rewards_rep, total_rewards_slh
  - level, updated_at
```

---

## API Endpoints

### 1. Course Upload
**POST** `/api/wellness/course-upload`

**Headers:** `X-Admin-Key: <admin_password>`

**Request:**
```json
{
    "course_title": "Beginner Meditation",
    "course_description": "Learn to meditate in 10 minutes",
    "course_content": "HTML/Markdown content here...",
    "category": "meditation",
    "difficulty": "beginner",
    "duration_minutes": 45,
    "price_zvk": 10,
    "instructor_id": null,
    "video_url": "https://youtube.com/..."
}
```

**Response:**
```json
{
    "course_id": 1,
    "slug": "beginner-meditation",
    "status": "created",
    "message": "Course 'Beginner Meditation' created successfully"
}
```

### 2. Create Task
**POST** `/api/wellness/task-create`

**Headers:** `X-Admin-Key: <admin_password>`

**Request:**
```json
{
    "title": "Morning Meditation",
    "task_type": "meditation",
    "description": "5-minute mindfulness meditation",
    "duration_minutes": 5,
    "reward_zvk": 5,
    "reward_rep": 10,
    "reward_slh": 0.1
}
```

**Response:**
```json
{
    "task_id": 42,
    "status": "created",
    "message": "Task 'Morning Meditation' created"
}
```

### 3. Schedule Task
**POST** `/api/wellness/schedule-task`

**Headers:** `X-Admin-Key: <admin_password>`

**Request:**
```json
{
    "schedule_name": "Daily Morning Wellness",
    "schedule_type": "daily",
    "cron_expression": "0 8 * * *",
    "task_ids": [1, 2, 3],
    "broadcast_time": "08:00",
    "enabled": true
}
```

**Cron Expression Examples:**
- `0 8 * * *` → Every day at 8:00 AM UTC
- `0 8 * * 1-5` → Weekdays at 8:00 AM
- `0 8,14 * * *` → 8:00 AM and 2:00 PM daily
- `30 7 * * 0` → Sunday at 7:30 AM
- `0 0 1 * *` → First day of month at midnight

**Response:**
```json
{
    "schedule_id": 7,
    "next_run": "2026-04-19T08:00:00",
    "status": "scheduled",
    "message": "Schedule 'Daily Morning Wellness' created"
}
```

### 4. Broadcast Task
**POST** `/api/wellness/broadcast-task`

**Headers:** `X-Admin-Key: <admin_password>`

**Request:**
```json
{
    "task_id": 42,
    "force_now": true
}
```

**Response:**
```json
{
    "recipients": 150,
    "sent": 148,
    "failed": 2,
    "status": "completed",
    "message": "Broadcast sent to 148/150 users"
}
```

### 5. List Courses
**GET** `/api/wellness/courses?category=meditation&difficulty=beginner&limit=20`

**Response:**
```json
{
    "courses": [
        {
            "id": 1,
            "title": "Beginner Meditation",
            "slug": "beginner-meditation",
            "category": "meditation",
            "difficulty": "beginner",
            "duration_minutes": 45,
            "price_zvk": 10,
            "student_count": 24,
            "rating": 4.8,
            "published": true,
            "created_at": "2026-04-18T10:30:00"
        }
    ],
    "total": 1
}
```

### 6. List Active Schedules
**GET** `/api/wellness/schedules`

**Headers:** `X-Admin-Key: <admin_password>`

**Response:**
```json
{
    "schedules": [
        {
            "id": 7,
            "name": "Daily Morning Wellness",
            "type": "daily",
            "cron_expression": "0 8 * * *",
            "task_ids": "[1, 2, 3]",
            "broadcast_time": "08:00",
            "enabled": true,
            "next_run": "2026-04-19T08:00:00",
            "last_run": "2026-04-18T08:00:00"
        }
    ],
    "total": 1
}
```

### 7. Get User Progress
**GET** `/api/wellness/progress/:user_id`

**Response:**
```json
{
    "user_id": 224223270,
    "total_completed": 15,
    "current_streak": 5,
    "last_completion": "2026-04-18T14:22:00",
    "total_rewards_zvk": 75,
    "total_rewards_rep": 150,
    "total_rewards_slh": 1.5,
    "level": 2
}
```

### 8. List Tasks
**GET** `/api/wellness/tasks`

**Response:**
```json
{
    "tasks": [
        {
            "id": 1,
            "title": "Morning Meditation",
            "type": "meditation",
            "description": "5-minute mindfulness meditation",
            "duration_minutes": 5,
            "reward_zvk": 5,
            "reward_rep": 10,
            "reward_slh": 0.1,
            "created_at": "2026-04-18T10:00:00"
        }
    ],
    "total": 1
}
```

---

## Admin Panel Integration

### Location
`/admin.html` → Sidebar → 🧘 Wellness Tab

### Features

#### 1. Upload Course
- Title, description, content (HTML/Markdown)
- Category: Meditation, Fitness, Nutrition, Wellness
- Difficulty: Beginner, Intermediate, Advanced
- Duration in minutes
- Price in ZVK
- Optional video URL

#### 2. Create Task
- Title & description
- Task type: Meditation, Exercise, Nutrition, Affirmation
- Duration in minutes
- Reward amounts: ZVK, REP, SLH

#### 3. Schedule Task
- Schedule name
- Type: Daily, Weekly, Custom
- Cron expression
- Broadcast time (HH:MM)
- Multi-select tasks from dropdown

#### 4. Broadcast Now
- Select a task from dropdown
- Send immediately to all users
- Real-time confirmation with sent/failed counts

#### 5. Dashboards
- Published Courses table (title, category, students, rating)
- Active Schedules table (next run, task count, status)
- User Progress table (completed, streak, rewards)

---

## Scheduler Configuration

### How It Works

1. **On Startup:**
   - API initializes APScheduler
   - Loads all enabled wellness_schedules from database
   - Registers each schedule with its cron trigger

2. **On Schedule Time:**
   - Trigger fires at the exact scheduled time
   - Task IDs are retrieved
   - All registered users are fetched
   - Each task is "broadcast" to each user:
     - Completion record created
     - Tokens awarded (ZVK, REP, SLH)
     - User progress updated
     - Streak count incremented

3. **On Schedule Update:**
   - Via API, admin can create/update/delete schedules
   - Scheduler dynamically adds/removes jobs

### Cron Expression Guide

Format: `minute hour day_of_month month day_of_week`

| Expression | Meaning |
|---|---|
| `0 8 * * *` | Every day at 8:00 AM UTC |
| `0 8 * * 1-5` | Weekdays (Mon-Fri) at 8:00 AM |
| `0 8,14,20 * * *` | 8 AM, 2 PM, 8 PM every day |
| `*/30 * * * *` | Every 30 minutes |
| `0 0 1 * *` | First day of month at midnight |
| `0 9 * * 0` | Sunday at 9:00 AM |
| `0 12 * * *` | Noon every day |

**Note:** Times are in UTC. For Israeli time (UTC+2/+3), add 2-3 hours.

---

## Example Workflow

### Step 1: Create Wellness Tasks
```bash
POST /api/wellness/task-create
{
    "title": "Morning Stretch",
    "task_type": "exercise",
    "description": "5-minute stretching routine",
    "duration_minutes": 5,
    "reward_zvk": 5,
    "reward_rep": 10,
    "reward_slh": 0.1
}
# Returns: task_id = 1
```

### Step 2: Create Additional Tasks
Repeat for:
- Meditation task (task_id = 2)
- Nutrition tip (task_id = 3)
- Affirmation (task_id = 4)

### Step 3: Create Daily Schedule
```bash
POST /api/wellness/schedule-task
{
    "schedule_name": "Daily Wellness Challenge",
    "schedule_type": "daily",
    "cron_expression": "0 8 * * *",
    "task_ids": [1, 2, 3, 4],
    "broadcast_time": "08:00"
}
# Returns: schedule_id = 1
# Next run: 2026-04-19T08:00:00 UTC
```

### Step 4: Monitor
- Check admin panel 🧘 Wellness tab
- View KPIs: courses, tasks, schedules, users in progress
- View Published Courses table
- View Active Schedules table
- View User Progress table

### Step 5: Manual Broadcast (Optional)
```bash
POST /api/wellness/broadcast-task
{
    "task_id": 2,
    "force_now": true
}
```
Immediately sends meditation task to all users.

---

## Token Reward System

### How Rewards Work

When a task is completed:
1. **ZVK (Spark Tokens):** Activity reward (~4.4 ILS equivalent)
2. **REP (Reputation):** Personal reputation score (0-1000+ tiers)
3. **SLH (Premium Token):** Governance token (444 ILS equivalent)

### Default Rewards (Per Task)
```
ZVK: 5 tokens
REP: 10 points
SLH: 0.1 tokens
```

### Customization
When creating a task, set custom rewards:
- Short task (2 min) → ZVK: 2, REP: 5
- Medium task (10 min) → ZVK: 5, REP: 10 (default)
- Long task (30 min) → ZVK: 15, REP: 30
- Premium task → ZVK: 20, REP: 50, SLH: 0.5

---

## Admin Security

### Authentication
- All endpoints require `X-Admin-Key` header
- Default keys: `slh2026admin`, `slh_admin_2026`, `slh-spark-admin`, `slh-institutional`
- **RECOMMENDED:** Override in Railway env vars `ADMIN_API_KEYS`

### Usage in Admin Panel
```javascript
const adminKey = localStorage.getItem('slh_admin_password');
fetch('/api/wellness/course-upload', {
    method: 'POST',
    headers: {'X-Admin-Key': adminKey},
    body: JSON.stringify(courseData)
});
```

---

## Deployment Checklist

- [ ] Deployed to Railway (auto-sync from GitHub)
- [ ] APScheduler installed (`pip install apscheduler`)
- [ ] Database migration complete (tables auto-created)
- [ ] Admin password set in localStorage on first login
- [ ] Test course upload via `/admin.html` 🧘 Wellness
- [ ] Test task creation with token rewards
- [ ] Test schedule creation with cron expression
- [ ] Test manual broadcast to confirm token distribution
- [ ] Verify scheduler is running (check Railway logs for "Scheduler initialized")
- [ ] Test schedule auto-execution at scheduled time
- [ ] Monitor user progress via dashboard

---

## Troubleshooting

### "Scheduler not initialized"
- Check Railway logs for initialization errors
- Verify APScheduler is installed: `pip freeze | grep apscheduler`
- Confirm DATABASE_URL is set in Railway env vars

### "Admin key rejected"
- Verify X-Admin-Key header is sent
- Check localStorage.slh_admin_password is set (from login)
- Confirm key matches ADMIN_API_KEYS on server

### "Schedule not firing at scheduled time"
- Check cron expression syntax (use online validator)
- Verify time zone (Railway runs in UTC)
- Check Railway logs for scheduled task execution
- Verify tasks exist with correct IDs

### "Tokens not awarded"
- Confirm task has reward values set (reward_zvk, reward_rep, reward_slh)
- Check user is registered (is_registered = TRUE)
- Verify completion record created in wellness_completions
- Check wellness_user_progress for updated balances

---

## Files Changed

### New Files
- `/routes/wellness.py` - API endpoints (200 lines)
- `/wellness_scheduler.py` - APScheduler integration (250 lines)

### Updated Files
- `/api/main.py` - Wellness router & scheduler initialization
- `/website/admin.html` - Admin UI widget + JavaScript functions
- `/requirements.txt` - Added apscheduler dependency

### Database
- 5 new tables auto-created on startup
- Indexes on category, slug, user_id, enabled

---

## Support & Questions

For issues or questions:
1. Check Railway logs: `heroku logs --tail -a slh-api-production`
2. Review database tables: `SELECT * FROM wellness_schedules`
3. Test endpoints via admin panel 🧘 Wellness tab
4. Check scheduler status: `GET /api/health`

---

**Last Updated:** April 18, 2026  
**Status:** ✅ Production Ready  
**License:** SLH Ecosystem © 2026
