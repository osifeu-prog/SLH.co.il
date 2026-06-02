from services.db import get_db
import json

def emit_event(user_id: int, event_type: str, source: str = "telegram", entity_type: str = None, entity_id: str = None, metadata: dict = None):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO events (user_id, event_type, source, entity_type, entity_id, metadata)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (user_id, event_type, source, entity_type, entity_id, json.dumps(metadata or {})))
    conn.commit()
    conn.close()
