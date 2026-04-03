from pathlib import Path
import re

p = Path("worker.py")
s = p.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")

pattern = r'async def render_profile_text\(user_id: int\) -> str:\n(?:    .*\n)+?(?=@dp\.message\(F\.text == "Profile"\))'

replacement = '''async def render_profile_text(user_id: int) -> str:
    p = await get_user_profile(user_id)
    user = p["user"] or {}
    bal = p["balance"] or {}
    ref = p["referral"]
    daily = p["daily"] or {}

    available = float(bal.get("available", 0) or 0)
    locked = float(bal.get("locked", 0) or 0)
    available_mnh = int(round(available * 10000))
    xp_total = int(user.get("xp_total", 0) or 0)
    level = int(user.get("level", 1) or 1)
    streak = int(daily.get("streak", 0) or 0)

    lines = [
        "Profile",
        "",
        f"User ID: {user.get('user_id', user_id)}",
        f"Username: {user.get('username') or '-'}",
        f"Role: {user.get('role') or 'user'}",
        f"Available: {available:.8f} SLH",
        f"Locked: {locked:.8f} SLH",
        f"MNH: {available_mnh}",
        f"XP total: {xp_total}",
        f"Level: {level}",
        f"Daily streak: {streak}",
        f"Claims count: {p['claims_count']}",
        f"Invited count: {user.get('invited_count', 0)}",
        f"Joined at: {user.get('joined_at')}",
        f"Last claim: {user.get('last_claim')}",
    ]

    if user.get("last_active_at"):
        lines.append(f"Last active: {user.get('last_active_at')}")

    if ref:
        lines.extend([
            f"Invited by: {ref.get('inviter_user_id')}",
            f"Invite code: {ref.get('invite_code') or '-'}",
            f"Referral reward granted: {bool(ref.get('reward_granted'))}",
        ])
    else:
        lines.append(f"Referral link: https://t.me/TON_MNH_bot?start={user.get('user_id', user_id)}")

    return "\\n".join(lines)

'''

new_s, n = re.subn(pattern, replacement, s, count=1, flags=re.MULTILINE)
if n != 1:
    raise SystemExit("render_profile_text patch failed")

p.write_text(new_s, encoding="utf-8", newline="\n")
print("worker.py patched: render_profile_text")