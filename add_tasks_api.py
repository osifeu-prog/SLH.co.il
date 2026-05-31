with open("bot.py", "r", encoding="utf-8") as f:
    content = f.read()

api_code = '''
# ═══ TASKS API ═══
@web_app.get("/api/tasks")
async def api_tasks(user_id: int = None):
    if not user_id:
        return JSONResponse({"tasks": []})
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT id, description, done, created_at FROM tasks WHERE user_id=%s ORDER BY created_at DESC LIMIT 50", (user_id,))
    tasks = [{"id": r[0], "title": r[1], "done": r[2], "created_at": str(r[3])} for r in cur.fetchall()]
    cur.close(); conn.close()
    return JSONResponse({"tasks": tasks})

@web_app.patch("/api/tasks/{task_id}")
async def api_patch_task(task_id: int, request: Request):
    data = await request.json()
    done = data.get("done", None)
    if done is not None:
        conn = get_db(); cur = conn.cursor()
        cur.execute("UPDATE tasks SET done=%s WHERE id=%s", (done, task_id))
        conn.commit(); cur.close(); conn.close()
    return JSONResponse({"ok": True})
'''
if "# ═══ TASKS API ═══" not in content:
    content = content.replace("# ── WEB DASHBOARD ──", api_code + "\n# ── WEB DASHBOARD ──")

with open("bot.py", "w", encoding="utf-8") as f:
    f.write(content)
print("✅ Tasks API added")