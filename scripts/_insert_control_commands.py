# -*- coding: utf-8 -*-
"""One-shot patcher: insert 8 control commands into admin-bot/main.py.

Uses ASCII anchor 'async def main():' (unique) to avoid mojibake matching.
Run once, delete after successful commit.
"""
from pathlib import Path

ADMIN_BOT = Path("admin-bot/main.py")

NEW_CODE = '''# ====================================================================
# Control Center commands (added 2026-04-25)
# 8 read-only commands - system status console for Osif (whitelist gated)
# ====================================================================

async def _http_get(url, headers=None, timeout=10):
    """Fetch JSON or text with safe error handling."""
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, headers=headers or {}, timeout=aiohttp.ClientTimeout(total=timeout)) as r:
                ct = r.headers.get("Content-Type", "")
                if "application/json" in ct:
                    return r.status, await r.json()
                return r.status, await r.text()
    except Exception as e:
        return 0, str(e)[:200]


def _md_escape(s):
    if not isinstance(s, str):
        return str(s)
    return s.replace("_", "\\\\_").replace("*", "\\\\*").replace("`", "\\\\`").replace("[", "\\\\[")


@dp.message(Command("status"))
async def control_status_cmd(m):
    if not is_admin(m.from_user.id):
        return
    await m.answer("\u23F3 \u05DE\u05D0\u05E1\u05E3 \u05E0\u05EA\u05D5\u05E0\u05D9\u05DD...")

    sc1, health = await _http_get(f"{API_BASE}/api/health")
    health_line = (
        f"v{health.get('version','?')} db={health.get('db','?')}"
        if isinstance(health, dict) else f"err {sc1}"
    )

    sc2, mini = await _http_get(f"{API_BASE}/api/miniapp/health")
    bot_token_set = mini.get("primary_bot_token_set", False) if isinstance(mini, dict) else False

    sc3, reality = await _http_get(
        f"{API_BASE}/api/ops/reality",
        headers={"X-Broadcast-Key": SLH_BROADCAST_KEY}
    )
    users_obj = reality.get("users", {}) if isinstance(reality, dict) else {}
    founders = len(users_obj.get("founders", []) or [])
    community = len(users_obj.get("community", []) or [])
    payments_count = len(reality.get("payments", []) or []) if isinstance(reality, dict) else 0

    sc4, devs = await _http_get(
        f"{API_BASE}/api/admin/devices/list",
        headers={"X-Admin-Key": SLH_ADMIN_API_KEY}
    )
    if isinstance(devs, dict):
        d_list = devs.get("devices", []) if isinstance(devs.get("devices"), list) else []
    elif isinstance(devs, list):
        d_list = devs
    else:
        d_list = []
    devices_count = len(d_list)

    sc5, ev = await _http_get(
        f"{API_BASE}/api/admin/events?limit=1",
        headers={"X-Admin-Key": SLH_ADMIN_API_KEY}
    )
    total_events = ev.get("total_events", "?") if isinstance(ev, dict) else "?"
    events_24h = ev.get("events_24h_by_type", {}) if isinstance(ev, dict) else {}
    events_24h_summary = ", ".join(f"{k}={v}" for k, v in list(events_24h.items())[:3]) or "--"

    bot_token_emoji = "\U0001F7E2" if bot_token_set else "\U0001F7E1"

    text = (
        "\U0001F4CA *SLH STATUS*\\n"
        "\\n"
        f"\U0001F7E2 API: {health_line}\\n"
        f"{bot_token_emoji} Mini-App: token_set={bot_token_set}\\n"
        "\\n"
        f"\U0001F465 Users: {founders} founders + {community} community\\n"
        f"\U0001F4B0 Revenue: \u20AA0 (\u05D0\u05D9\u05DF \u05DC\u05E7\u05D5\u05D7 \u05DE\u05E9\u05DC\u05DD)\\n"
        f"\U0001F4DF Devices: {devices_count}\\n"
        f"\U0001F4DC Events lifetime: {total_events}\\n"
        f"\U0001F4DC Events 24h: {events_24h_summary}\\n"
        f"\U0001F4B3 Payments: {payments_count}\\n"
        "\\n"
        f"\U0001F517 [CONTROL]({OPS_VIEWER_BASE}CONTROL.md) | "
        f"[Agents]({OPS_VIEWER_BASE}SYSTEM_ALIGNMENT_20260424.md)"
    )
    await m.answer(text, parse_mode="Markdown", disable_web_page_preview=True)


@dp.message(Command("control"))
async def control_links_cmd(m):
    if not is_admin(m.from_user.id):
        return
    await m.answer(
        "\U0001F3AF *Control Center*\\n"
        "\\n"
        f"\U0001F4CB [CONTROL.md]({OPS_VIEWER_BASE}CONTROL.md)\\n"
        f"\U0001F4E1 [Agents alignment]({OPS_VIEWER_BASE}SYSTEM_ALIGNMENT_20260424.md)\\n"
        f"\U0001F464 [Customer prospectus DEMO]({OPS_VIEWER_BASE}CUSTOMER_PROSPECTUS_DEMO.md)\\n"
        f"\U0001F6E0 [Ops runbook]({OPS_VIEWER_BASE}OPS_RUNBOOK.md)\\n"
        f"\U0001F4E8 [Followup templates]({OPS_VIEWER_BASE}FOLLOWUP_TEMPLATES.md)\\n"
        f"\U0001F9EA [Test payment guide]({OPS_VIEWER_BASE}TEST_PAYMENT_GUIDE.md)\\n"
        "\\n"
        f"\U0001F310 [Website](https://slh-nft.com)\\n"
        f"\u26A1 [Mission Control](https://slh-nft.com/admin/mission-control.html)",
        parse_mode="Markdown", disable_web_page_preview=True
    )


@dp.message(Command("agents"))
async def control_agents_cmd(m):
    if not is_admin(m.from_user.id):
        return
    sc, txt = await _http_get(f"{WEBSITE_OPS_BASE}/SYSTEM_ALIGNMENT_20260424.md")
    if sc != 200 or not isinstance(txt, str):
        await m.answer(f"\u274C alignment HTTP {sc}")
        return
    agents = []
    for line in txt.split("\\n"):
        if line.startswith("### Agent:"):
            agents.append(line.replace("### Agent:", "").strip()[:90])
    if not agents:
        await m.answer("\U0001F4E1 No agents registered")
        return
    body = "\\n".join(f"- {_md_escape(a)}" for a in agents[:15])
    await m.answer(f"\U0001F4E1 *Active agents:*\\n\\n{body}", parse_mode="Markdown")


@dp.message(Command("devices"))
async def control_devices_cmd(m):
    if not is_admin(m.from_user.id):
        return
    sc, dev = await _http_get(
        f"{API_BASE}/api/admin/devices/list",
        headers={"X-Admin-Key": SLH_ADMIN_API_KEY}
    )
    if sc != 200:
        await m.answer(f"\u274C HTTP {sc}: {str(dev)[:200]}")
        return
    devices = dev.get("devices", []) if isinstance(dev, dict) else (dev if isinstance(dev, list) else [])
    if not devices:
        await m.answer("\U0001F4DF No devices")
        return
    lines = ["\U0001F4DF *ESP32 Fleet:*\\n"]
    for d in devices[:10]:
        last = (d.get("last_seen") or "--")[:19]
        paired = d.get("paired_user_id") or "--"
        did = _md_escape(d.get("device_id", "?"))
        lines.append(f"- `{did}` last={last} user={paired}")
    if len(devices) > 10:
        lines.append(f"\\n_+ {len(devices) - 10} more_")
    await m.answer("\\n".join(lines), parse_mode="Markdown")


@dp.message(Command("git_log"))
async def control_git_cmd(m):
    if not is_admin(m.from_user.id):
        return
    sc, commits = await _http_get(
        f"{GITHUB_API_REPO}/commits?per_page=5",
        headers={"Accept": "application/vnd.github.v3+json"}
    )
    if sc != 200 or not isinstance(commits, list):
        await m.answer(f"\u274C GitHub HTTP {sc}")
        return
    lines = ["\U0001F4E6 *Last 5 commits (slh-api master):*\\n"]
    for c in commits[:5]:
        sha = c.get("sha", "")[:7]
        full_msg = c.get("commit", {}).get("message", "?").split("\\n")[0][:60]
        date = c.get("commit", {}).get("author", {}).get("date", "")[:10]
        lines.append(f"- `{sha}` _{date}_\\n  {_md_escape(full_msg)}")
    await m.answer("\\n".join(lines), parse_mode="Markdown")


@dp.message(Command("audit_status"))
async def control_audit_cmd(m):
    if not is_admin(m.from_user.id):
        return
    await m.answer(
        "\U0001F50D *Data Integrity Audit*\\n"
        "\\n"
        "Last logged state:\\n"
        "- HIGH: 1 (slh-skeleton.js lib default - legit)\\n"
        "- MED: 306 (`|| 0` benign)\\n"
        "- LOW: 327\\n"
        "\\n"
        "Fresh run (PowerShell):\\n"
        "`python scripts/audit_data_integrity.py --severity HIGH`",
        parse_mode="Markdown"
    )


@dp.message(Command("customer"))
async def control_customer_cmd(m):
    if not is_admin(m.from_user.id):
        return
    targets = [
        (1185887485, "Tzvika"),
        (8088324234, "Eliezer"),
        (590733872,  "Yaara"),
        (920721513,  "Rami"),
        (480100522,  "Zohar"),
        (1518680802, "Idan"),
    ]
    lines = ["\U0001F465 *Outreach status:*\\n"]
    for tid, name in targets:
        lines.append(f"- {name} (`{tid}`) bot DM 22.4")
    lines.append("\\n_WhatsApp personal: Yaara 24.4 | others pending_")
    lines.append(f"\\n\U0001F4CB Followups: {OPS_VIEWER_BASE}FOLLOWUP_TEMPLATES.md")
    await m.answer("\\n".join(lines), parse_mode="Markdown", disable_web_page_preview=True)


@dp.message(Command("help_control"))
async def control_help_cmd(m):
    if not is_admin(m.from_user.id):
        return
    await m.answer(
        "\U0001F3AF *Control Commands*\\n"
        "\\n"
        "/status        - system snapshot\\n"
        "/control       - links to ops docs\\n"
        "/agents        - active agents\\n"
        "/devices       - ESP32 fleet\\n"
        "/git_log       - 5 last commits\\n"
        "/audit_status  - audit findings\\n"
        "/customer      - outreach status\\n"
        "/help_control  - this menu\\n"
        "\\n"
        "_All commands whitelisted to admin only._",
        parse_mode="Markdown"
    )


'''


def main():
    data = ADMIN_BOT.read_bytes()
    anchor = b"async def main():"
    cnt = data.count(anchor)
    if cnt != 1:
        print(f"ABORT: anchor 'async def main():' found {cnt} times (need exactly 1)")
        return 1

    # Don't double-insert
    if b"control_status_cmd" in data:
        print("Already patched (control_status_cmd present). No-op.")
        return 0

    new_payload = NEW_CODE.encode("utf-8")
    new_data = data.replace(anchor, new_payload + anchor, 1)
    ADMIN_BOT.write_bytes(new_data)
    print(f"OK: inserted {len(new_payload)} bytes. {len(data)} -> {len(new_data)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
