# ============================================================
# SLH Spark — Project Status API Endpoints
# Provides real-time data for project-map dashboard
# ============================================================

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Optional
from datetime import datetime
import json

router = APIRouter(prefix="/api/project", tags=["project"])

# ============================================================
# GET ENDPOINTS — Read-only data for dashboard
# ============================================================

@router.get("/status")
async def get_project_status():
    """
    Get current project status with all metrics
    Returns: {
        "totalPages": 50,
        "metrics": {...},
        "features": {...},
        "systems": [...],
        "timeline": [...],
        "lastUpdated": "2026-04-18T..."
    }
    """
    return {
        "totalPages": 50,
        "metrics": {
            "complete": 2,
            "inProgress": 15,
            "needsWork": 33,
            "averageScore": 2.6,
            "completion": 36
        },
        "features": {
            "theme": 20,
            "i18n": 56,
            "analytics": 100,
            "ai": 0
        },
        "systems": [
            {"name": "NIFTII Bot", "status": "online", "emoji": "🤖"},
            {"name": "Guardian Bot", "status": "online", "emoji": "🛡️"},
            {"name": "PostgreSQL", "status": "healthy", "emoji": "🗄️"},
            {"name": "Redis", "status": "healthy", "emoji": "⚡"},
            {"name": "Railway API", "status": "running", "emoji": "🚀"},
            {"name": "Broadcast", "status": "scheduled", "emoji": "📢"}
        ],
        "timeline": [
            {"date": "Apr 18", "event": "✅ Core systems live", "status": "completed", "progress": 36},
            {"date": "Apr 24", "event": "⚙️ Website pages 50%", "status": "in-progress", "progress": 45},
            {"date": "May 15", "event": "📊 Full feature coverage", "status": "pending", "progress": 60},
            {"date": "Jun 30", "event": "🚀 Launch ready", "status": "pending", "progress": 95}
        ],
        "lastUpdated": datetime.now().isoformat()
    }


@router.get("/page/{page_id}")
async def get_page_status(page_id: str):
    """
    Get status of specific page
    Example: /api/project/page/admin.html
    """
    # In production, query database
    return {
        "pageId": page_id,
        "score": 5,
        "theme": True,
        "i18n": True,
        "analytics": True,
        "ai": False,
        "lastUpdated": datetime.now().isoformat()
    }


@router.get("/achievements")
async def get_achievements():
    """Get all completed achievements"""
    return {
        "Bots & Systems": [
            "NIFTII Bot marketplace live",
            "Guardian Bot anti-fraud active",
            "Broadcast automation ready",
            "25 bots deployed"
        ],
        "Infrastructure": [
            "PostgreSQL + Redis healthy",
            "113 API endpoints",
            "8 registered users",
            "Audit log active"
        ],
        "Hardware (ESP32)": [
            "WiFi selector complete",
            "Backlight control fixed",
            "Baud rate optimized"
        ]
    }


# ============================================================
# POST ENDPOINTS — Log task completions from admin
# ============================================================

@router.post("/task-complete")
async def log_task_completion(task_data: dict):
    """
    Log task completion from admin panel
    Called when admin checks off a task

    Example payload:
    {
        "taskType": "page_update",
        "pageId": "admin.html",
        "component": "payment_tracking",
        "status": "complete",
        "score": 5,
        "adminUser": "224223270"
    }
    """

    # Log to audit system
    log_entry = {
        "type": "TASK_COMPLETE",
        "task": task_data.get("taskType"),
        "page": task_data.get("pageId"),
        "component": task_data.get("component"),
        "status": task_data.get("status"),
        "timestamp": datetime.now().isoformat(),
        "admin": task_data.get("adminUser")
    }

    # TODO: Save to audit_log table in PostgreSQL
    # db.execute("""
    #     INSERT INTO audit_log (event_type, payload_json, created_at)
    #     VALUES ('PROJECT_TASK_COMPLETE', %s, NOW())
    # """, json.dumps(log_entry))

    # Trigger dashboard update
    await notify_dashboard_update(log_entry)

    return {
        "status": "success",
        "message": f"Task logged: {task_data.get('pageId')}/{task_data.get('component')}",
        "timestamp": datetime.now().isoformat()
    }


@router.post("/page-score-update")
async def update_page_score(update: dict):
    """
    Update score for a specific page

    Example:
    {
        "pageId": "admin.html",
        "theme": true,
        "i18n": true,
        "analytics": true,
        "ai": false,
        "adminUser": "224223270"
    }
    """

    # Calculate new score
    components_complete = sum([
        update.get("theme", False),
        update.get("i18n", False),
        update.get("analytics", False),
        update.get("ai", False),
        update.get("nav", False)
    ])

    new_score = (components_complete / 5) * 5

    # TODO: Update pages table in database
    # db.execute("""
    #     UPDATE pages
    #     SET score = %s, has_theme = %s, has_i18n = %s, ...
    #     WHERE page_id = %s
    # """, new_score, ...)

    # Notify dashboard
    await notify_dashboard_update({
        "type": "PAGE_SCORE_UPDATE",
        "page": update.get("pageId"),
        "newScore": new_score
    })

    return {
        "status": "success",
        "page": update.get("pageId"),
        "newScore": new_score,
        "timestamp": datetime.now().isoformat()
    }


@router.post("/system-status")
async def update_system_status(system_data: dict):
    """
    Update system status from monitoring

    Example:
    {
        "system": "NIFTII Bot",
        "status": "online",
        "uptime": 86400,
        "healthCheck": true
    }
    """

    # TODO: Store in Redis cache
    # redis.hset("project:systems", system_data.get("system"), json.dumps(system_data))

    # Notify dashboard
    await notify_dashboard_update({
        "type": "SYSTEM_STATUS",
        "system": system_data.get("system"),
        "status": system_data.get("status")
    })

    return {
        "status": "success",
        "system": system_data.get("system"),
        "timestamp": datetime.now().isoformat()
    }


# ============================================================
# WebSocket — Real-time updates
# ============================================================

from fastapi import WebSocket

active_connections: List[WebSocket] = []

@router.websocket("/ws/project-status")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket for real-time project status updates
    Clients connect and receive instant updates
    """
    await websocket.accept()
    active_connections.append(websocket)

    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()

            if data == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })

    except Exception as e:
        active_connections.remove(websocket)


async def notify_dashboard_update(update_data: dict):
    """
    Broadcast update to all connected WebSocket clients
    """
    for connection in active_connections:
        try:
            await connection.send_json({
                "type": "status_update",
                "data": update_data,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            print(f"Failed to send update: {e}")


# ============================================================
# Helper endpoints for admin integration
# ============================================================

@router.get("/admin/pending-tasks")
async def get_pending_tasks():
    """Get all pending tasks for admin dashboard"""
    return {
        "pending": [
            {
                "id": "admin-payment",
                "title": "admin.html — Add payment tracking",
                "priority": "HIGH",
                "estimate": "3-4 hours",
                "assignedTo": "Osif"
            },
            {
                "id": "pay-fixes",
                "title": "pay.html — Fix 3 bugs",
                "priority": "HIGH",
                "estimate": "1 hour",
                "assignedTo": "Osif"
            },
            {
                "id": "project-map",
                "title": "project-map.html — Update metrics",
                "priority": "HIGH",
                "estimate": "2 hours",
                "assignedTo": "Osif"
            },
            {
                "id": "community-dm",
                "title": "community.html — Add DM feature",
                "priority": "MEDIUM",
                "estimate": "6 hours",
                "assignedTo": "Team"
            }
        ]
    }


@router.post("/admin/mark-task-done")
async def mark_task_complete(task_id: str, notes: Optional[str] = None):
    """
    Admin marks a task as done
    Automatically updates metrics and notifies dashboard
    """

    task_updates = {
        "admin-payment": {
            "page": "admin.html",
            "addedScore": 1.5,
            "featureAdded": "payment_tracking"
        },
        "pay-fixes": {
            "page": "pay.html",
            "addedScore": 1.0,
            "bugsFixes": 3
        },
        "project-map": {
            "page": "project-map.html",
            "addedScore": 1.0,
            "featureAdded": "achievement_tracking"
        }
    }

    task_info = task_updates.get(task_id)
    if not task_info:
        raise HTTPException(status_code=404, detail="Task not found")

    # Log completion
    await log_task_completion({
        "taskType": "admin_completion",
        "pageId": task_info["page"],
        "component": task_info.get("featureAdded"),
        "status": "complete",
        "notes": notes
    })

    # Trigger update
    await notify_dashboard_update({
        "type": "TASK_COMPLETED",
        "taskId": task_id,
        "page": task_info["page"]
    })

    return {
        "status": "success",
        "taskId": task_id,
        "updated": True,
        "timestamp": datetime.now().isoformat()
    }


# ============================================================
# Register router in main app
# ============================================================
# In main.py:
# from fastapi import FastAPI
# from .routes import project
# app = FastAPI()
# app.include_router(project.router)
