# -*- coding: utf-8 -*-
import psycopg2
from typing import Optional, Dict, Any

def tc_get_conn(DB_NAME, DB_USER, DB_PASS, DB_HOST, DB_PORT):
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        port=DB_PORT
    )

def tc_get_code(DB_NAME, DB_USER, DB_PASS, DB_HOST, DB_PORT, code: str) -> Optional[Dict[str, Any]]:
    conn = tc_get_conn(DB_NAME, DB_USER, DB_PASS, DB_HOST, DB_PORT)
    cur = conn.cursor()
    cur.execute("""
        SELECT code, grant_type, is_active, max_uses, used_count, notes, expires_at
        FROM access_codes
        WHERE code = %s
        LIMIT 1
    """, (code,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return None

    return {
        "code": row[0],
        "grant_type": row[1],
        "is_active": row[2],
        "max_uses": row[3],
        "used_count": row[4],
        "notes": row[5],
        "expires_at": row[6],
    }

def tc_mark_redemption(DB_NAME, DB_USER, DB_PASS, DB_HOST, DB_PORT, code: str, user_id: int, username: Optional[str], result_status: str):
    conn = tc_get_conn(DB_NAME, DB_USER, DB_PASS, DB_HOST, DB_PORT)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO access_code_redemptions (code, user_id, username, result_status)
        VALUES (%s, %s, %s, %s)
    """, (code, user_id, username, result_status))
    conn.commit()
    cur.close()
    conn.close()

def tc_increment_use(DB_NAME, DB_USER, DB_PASS, DB_HOST, DB_PORT, code: str):
    conn = tc_get_conn(DB_NAME, DB_USER, DB_PASS, DB_HOST, DB_PORT)
    cur = conn.cursor()
    cur.execute("""
        UPDATE access_codes
        SET used_count = used_count + 1
        WHERE code = %s
    """, (code,))
    conn.commit()
    cur.close()
    conn.close()

def tc_code_is_usable(row: Optional[Dict[str, Any]]) -> bool:
    if not row:
        return False
    if not bool(row["is_active"]):
        return False
    if row["expires_at"] is not None:
        return False
    if row["max_uses"] is not None and int(row["used_count"] or 0) >= int(row["max_uses"]):
        return False
    return True