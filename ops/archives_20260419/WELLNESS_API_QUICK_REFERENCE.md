# SLH Wellness API - Quick Reference

## All Endpoints at a Glance

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| **POST** | `/api/wellness/course-upload` | Upload wellness course | Admin |
| **POST** | `/api/wellness/task-create` | Create wellness task | Admin |
| **POST** | `/api/wellness/schedule-task` | Schedule task broadcast | Admin |
| **POST** | `/api/wellness/broadcast-task` | Broadcast task immediately | Admin |
| **GET** | `/api/wellness/courses` | List published courses | Public |
| **GET** | `/api/wellness/tasks` | List all tasks | Public |
| **GET** | `/api/wellness/schedules` | List active schedules | Admin |
| **GET** | `/api/wellness/progress/:user_id` | Get user progress | Public |

---

## Quick Examples

### Create a Task (2 minutes)
```bash
curl -X POST https://slh-api-production.up.railway.app/api/wellness/task-create \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: slh2026admin" \
  -d '{
    "title": "5-Min Meditation",
    "task_type": "meditation",
    "description": "Quick breathing exercise",
    "duration_minutes": 5,
    "reward_zvk": 5,
    "reward_rep": 10,
    "reward_slh": 0.1
  }'
```

### Schedule Daily Broadcast (08:00 UTC)
```bash
curl -X POST https://slh-api-production.up.railway.app/api/wellness/schedule-task \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: slh2026admin" \
  -d '{
    "schedule_name": "Morning Wellness",
    "schedule_type": "daily",
    "cron_expression": "0 8 * * *",
    "task_ids": [1, 2, 3],
    "broadcast_time": "08:00"
  }'
```

### Broadcast Task Now
```bash
curl -X POST https://slh-api-production.up.railway.app/api/wellness/broadcast-task \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: slh2026admin" \
  -d '{
    "task_id": 5,
    "force_now": true
  }'
```

### Get User Progress
```bash
curl https://slh-api-production.up.railway.app/api/wellness/progress/224223270
```

---

## Admin Panel Quick Access

1. Login to `/admin.html`
2. Enter admin password
3. Click **🧘 Wellness** in sidebar
4. Use forms to:
   - 📚 Upload Course
   - ✨ Create Task
   - ⏰ Schedule Task
   - 📢 Broadcast Now

---

## Common Cron Expressions

```
0 8 * * *     Every day at 8 AM
0 8 * * 1-5   Weekdays at 8 AM
0 8,14,20 * * * At 8 AM, 2 PM, 8 PM daily
*/30 * * * *   Every 30 minutes
0 0 1 * *     First day of month at midnight
0 9 * * 0     Sunday at 9 AM
0 12 * * *    Noon every day
```

---

## Token Amounts (Adjustable)

Default per task completion:
- **ZVK:** 5 tokens (~22 ILS equivalent at 4.4 ILS each)
- **REP:** 10 points (builds toward tier milestones)
- **SLH:** 0.1 tokens (~44 ILS equivalent at 444 ILS each)

---

## Database Tables

```
wellness_courses       → Published courses (45, fitness, nutrition)
wellness_tasks         → Reusable tasks (5-30 min activities)
wellness_schedules     → Cron-scheduled broadcasts
wellness_completions   → Task completion records
wellness_user_progress → User streaks & cumulative rewards
```

---

## Key Fields

### Course
```json
{
  "title": "Beginner Meditation",
  "slug": "beginner-meditation",
  "category": "meditation|fitness|nutrition|wellness",
  "difficulty": "beginner|intermediate|advanced",
  "duration_minutes": 45,
  "price_zvk": 10,
  "student_count": 24,
  "rating": 4.8,
  "published": true
}
```

### Task
```json
{
  "title": "Morning Stretch",
  "type": "meditation|exercise|nutrition|affirmation",
  "duration_minutes": 5,
  "reward_zvk": 5,
  "reward_rep": 10,
  "reward_slh": 0.1
}
```

### Schedule
```json
{
  "name": "Daily Wellness",
  "type": "daily|weekly|custom",
  "cron_expression": "0 8 * * *",
  "task_ids": [1, 2, 3],
  "enabled": true,
  "next_run": "2026-04-19T08:00:00"
}
```

---

## Error Codes

| Code | Meaning | Fix |
|------|---------|-----|
| 401 | No admin key | Add `X-Admin-Key` header |
| 400 | Invalid request | Check JSON format & required fields |
| 404 | Resource not found | Verify ID exists in database |
| 500 | Server error | Check Railway logs |

---

## Deployment

1. **Code:** Push to `github.com/osifeu-prog/slh-api` (master branch)
2. **Railway:** Auto-deploys within 1 minute
3. **Database:** Tables auto-create on first startup
4. **Scheduler:** Auto-loads all enabled schedules on startup

---

## Performance Notes

- **Broadcast:** ~150-500 users = 2-5 seconds
- **Schedule:** Fires at exact cron time (±5 seconds)
- **Database:** Indexes on `category`, `slug`, `user_id`, `enabled`

---

**API Base:** `https://slh-api-production.up.railway.app`  
**Auth:** `X-Admin-Key` header (copy from admin password)  
**Format:** JSON (Content-Type: application/json)
