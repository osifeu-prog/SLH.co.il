# SLH Spark · Agent Coordination Protocol · 2026-04-24

**Purpose:** Single source of truth that every AI agent (Claude / ChatGPT / Gemini / future) reads BEFORE touching the project. Osif passes this verbatim to each active session.

**Core rule:** There are many agents. There is **one** project. Coordinate through Mission Control, not through Osif's copy-paste.

---

## 1. Agent Check-In Protocol (fill + return to Osif)

Every agent, at the START of any new conversation, answers:

```
Agent ID:        [Claude Sonnet 4.7 / ChatGPT o1 / Gemini 2.0 / ...]
Session started: [ISO datetime]
Context source:  [ops/AGENT_COORDINATION_20260424.md + Mission Control]
My current task: [read from Mission Control or stated by Osif]
Scope boundary:  [what I will NOT touch without checking]
Handoff target:  [human Osif / another agent / queue]
```

Osif's assistant (Claude in Claude Code) shares the sync log. Before any write action, agent runs:

```bash
curl -H "X-Admin-Key: <KEY>" https://slh-api-production.up.railway.app/api/admin/overview
# gives live snapshot of all 35 tasks
```

---

## 2. Canonical State · as of 2026-04-24 15:20 UTC

### 2.1 What is LIVE (production)

| Layer | Endpoint / URL | Status |
|-------|----------------|--------|
| API | https://slh-api-production.up.railway.app/api/health | 200 db:connected |
| Website | https://slh-nft.com | 200 |
| Mission Control | https://slh-nft.com/admin/mission-control.html | 200 (needs admin key) |
| Mission Control API | /api/admin/tasks + /api/admin/overview | 200, 35 tasks seeded |
| Mini App Dashboard | https://slh-nft.com/miniapp/dashboard.html | 200 |
| Mini App Wallet | https://slh-nft.com/miniapp/wallet.html | 200 |
| Mini App Device | https://slh-nft.com/miniapp/device.html | 200 |
| Voice Vision | https://slh-nft.com/voice.html | 200 (Phase 2 Vision — not commercial) |
| Swarm Vision | https://slh-nft.com/swarm.html | 200 (Phase 2 Vision — not commercial) |
| Ambassador CRM | /api/ambassador/contacts | 403 (endpoint live, needs key) |
| Network Map | https://slh-nft.com/network.html | 200 (61 nodes) |
| Ops Dashboard | https://slh-nft.com/ops-dashboard.html | 200 |
| Reality endpoint | /api/ops/reality | 200 (X-Broadcast-Key) |

### 2.2 What is IN PROGRESS / BLOCKED

| Item | Status | Blocker |
|------|--------|---------|
| 35 Mission Control tasks | 30 open, 3 blocked, 2 done | See `/api/admin/overview` for live numbers |
| ESP `esp32-14335C6C32C0` | online, NOT paired | Waiting for Osif to complete pair page |
| SMS provider | Code deployed (api/sms_provider.py) | Osif to choose + set Railway env vars |
| Bot Father Mini App URL | Not set on @WEWORK_teamviwer_bot | Osif manual step |
| 10 leaked secrets | 1/11 rotated | Osif rotations pending |

### 2.3 Two separate Railway projects — DO NOT CONFUSE

| Project | URL | Contents |
|---------|-----|----------|
| **slh-api** | slh-api-production.up.railway.app | FastAPI main, 114+ endpoints, deploys from `osifeu-prog/slh-api` master, builds root `main.py` |
| **diligent-radiance** | www.slh.co.il + monitor.slh.co.il | Separate project: @SLH_macro_bot (ROI tracker), deploys from `osifeu-prog/SLH.co.il` |

They share an owner but nothing else. Never push SLH.co.il code to slh-api repo or vice versa.

---

## 3. Authorization Boundaries · what agents MAY and MAY NOT do

### Freely allowed (no confirmation needed)

- Read files, grep, analyze
- Run `/api/admin/tasks` GET / POST / PATCH for task management
- Write `.md` docs in `ops/`
- Edit code in `routes/`, `website/`, `scripts/` with clear attribution
- Commit with env-var authorship `user.name="Osif Kaufman Ungar" user.email="osif.erez.ungar@gmail.com"`
- Push to **slh-api master** (Railway auto-deploys)
- Push to **osifeu-prog.github.io main** (Pages auto-deploys)

### Confirm first with Osif

- Force push, hard reset, branch deletion
- Rotate env vars or secrets
- BotFather changes (Mini App URL, token revoke)
- Railway env var changes that affect other services
- Deleting production data
- Sending broadcasts to `segment:all` (>3/day limit)
- Anything involving money flow or user accounts

### Never (hard blocks)

- Hardcoding passwords/tokens in HTML or committed files
- Using `segment:all` without rate-limit check
- Generating fake numbers / phantom fallbacks (always `--` or error card)
- `git commit --no-verify` or `--no-gpg-sign`
- Writing unicode ✓ ✗ to Windows stdout (encoding crashes) — use `[OK]` / `[FAIL]`
- Cross-project commits (SLH_ECOSYSTEM ≠ SLH.co.il)
- Parallel edits to the same file in two agent sessions without `git pull` first

---

## 4. Mission Control · shared task pipeline

**URL:** https://slh-nft.com/admin/mission-control.html
**API base:** https://slh-api-production.up.railway.app/api/admin
**Auth:** `X-Admin-Key: slh_admin_2026_rotated_04_20` (OR `slh_ops_2026_rotated_04_20` backup)

### 4.1 Task lifecycle

```
open → in_progress → done
                 ↓
              blocked (with blocker reason)
                 ↓
           (unblock when dependency resolves)
```

### 4.2 Before starting work

```bash
# Claim a task
curl -X PATCH -H "X-Admin-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"status":"in_progress","assignee_name":"claude","actor_name":"claude"}' \
  "$API/api/admin/tasks/<id>"
```

### 4.3 When done

```bash
curl -X PATCH -H "X-Admin-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"status":"done","actor_name":"claude","description":"<what shipped + commit SHA>"}' \
  "$API/api/admin/tasks/<id>"
```

### 4.4 When blocked

```bash
curl -X PATCH -H "X-Admin-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"status":"blocked","blocker":"<why + who unblocks>","actor_name":"claude"}' \
  "$API/api/admin/tasks/<id>"
```

### 4.5 Adding a new task

```bash
curl -X POST -H "X-Admin-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"title":"...","category":"code|infra|owner|qa|security|...","priority":"P0|P1|P2","source":"<manual/audit/agent>","description":"..."}' \
  "$API/api/admin/tasks"
```

### 4.6 Adding a comment (visible in event log)

```bash
curl -X POST -H "X-Admin-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"event_type":"commented","actor_name":"claude","payload":{"text":"note..."}}' \
  "$API/api/admin/tasks/<id>/events"
```

---

## 5. Communication patterns between sessions

### 5.1 Inbox-style handoff

When one agent finishes something important, write a comment on the relevant Mission Control task:

```
event_type: handoff
payload: {
  from: "claude-sonnet",
  to: "next-agent",
  summary: "Shipped commit X. Next agent: verify endpoint Y responds 200."
}
```

### 5.2 Never silently duplicate

Before writing a new route / page / doc, grep for the topic first:

```bash
grep -rn "your-topic" D:/SLH_ECOSYSTEM/routes/ D:/SLH_ECOSYSTEM/website/
grep "your-topic" D:/SLH_ECOSYSTEM/ops/*.md
```

If something similar exists — extend or replace with clear commit message, don't duplicate.

### 5.3 When in doubt — open a Mission Control task, don't just DM Osif

Osif doesn't want to be a message queue. If you have a question for another agent, create a P2 task titled "Question: ..." with `assignee_name=<target-agent>`. Next agent reads it at check-in.

---

## 6. Open P0 items · top priority (live snapshot)

```bash
curl -s -H "X-Admin-Key: $KEY" \
  "$API/api/admin/tasks?priority=P0&status=open&limit=20" \
  | python -c "import sys,json; [print(f'#{t[\"id\"]} {t[\"title\"][:70]}') for t in json.load(sys.stdin)['tasks']]"
```

As of 2026-04-24 these are the 10 P0 items (2 done, 8 open):

- ✅ #1 Railway Redeploy (CLOSED)
- #2 Push website/miniapp + marketplace.html + team.html (Osif)
- #3 Fix global git config — 'Your Name' authorship (Osif)
- #4 Rotate 10 leaked secrets (Osif)
- #12 3 admin endpoints bypass _require_admin() (code)
- #13 _dev_code leaks in /api/device/verify (code)
- #14 /api/events/public returns event_log_unavailable (code)
- ✅ #15 initShared() 121 pages (CLOSED)
- #7 Docker rebuild 9 Phase 0B bots (Idan)
- #8 Fix ledger-bot TOKEN crash loop (Idan)

---

## 7. Agents currently active (as of 2026-04-24)

| Agent | Session type | Primary role | Last commits |
|-------|--------------|--------------|--------------|
| Claude (Claude Code) | terminal-based, file-access | Architecture + code + Mission Control | 523333a, bf88a19, 9e49313, 006723b, 2ec7245 |
| ChatGPT (browser) | conversational | Brainstorming + strategy | afc2354 (SMS gateway code) |
| Gemini (browser) | conversational | Vision docs + Voice/Swarm design | ccd8281 (Phase 2 vision pages) |

**Known multi-session incident:** 2026-04-24 — parallel ChatGPT session (commit `afc2354`) overwrote Claude's `routes/tasks.py` router wiring in `main.py`/`api/main.py`. Recovered via commit `006723b`. **Lesson:** before editing `main.py` or `api/main.py`, `git pull` first; if two agents target same file same day, one waits.

---

## 8. What each agent brings (recommended specialization)

| Agent | Best for | Avoid |
|-------|----------|-------|
| Claude (Claude Code) | Terminal operations, Python/JS code, git, file ops, direct API calls, Mission Control ops, Railway CLI, complex multi-file changes | Pure brainstorming (slower than chat) |
| ChatGPT (browser) | Brainstorming, marketing copy, quick snippets, diagrams, alternative architectures | Committing code (no file access) |
| Gemini (browser) | Long-form vision docs, competitive analysis, research, market positioning | Same as ChatGPT — can produce code but can't commit |

**Osif's rule of thumb:** Use chat AI for thinking. Use Claude Code for building + shipping. One terminal-agent per day, max.

---

## 9. Reports each agent should file at end of session

Every active agent, before closing a session, writes to `ops/SESSION_LOG_<agent>_<date>.md`:

```markdown
# Session Log · <agent> · <YYYY-MM-DD>

## What I did
- <bullet per concrete change, with file path + commit SHA if any>

## Mission Control tasks I touched
- #<id> status=<new status> (was <old>)
- #<id> created as P<n> <category>

## Commits
- <sha> <repo> — <one-line summary>

## Handoff
- To next agent: <what to verify / continue>
- To Osif: <what needs human decision>

## Questions left open
- <bullet>
```

Osif reads the log. Next agent reads it too. This replaces the copy-paste of huge transcripts between sessions.

---

## 10. Quick reference — ports, paths, SHAs

```
Owner:          Osif Kaufman Ungar (@osifeu_prog, Telegram 224223270, osif.erez.ungar@gmail.com)
Main repo:      D:\SLH_ECOSYSTEM\   (local: osifeu-prog/slh-api on GitHub, master → Railway slh-api project)
Website repo:   D:\SLH_ECOSYSTEM\website\   (osifeu-prog/osifeu-prog.github.io on GitHub, main → Pages at slh-nft.com)
Launcher:       D:\SLH_ECOSYSTEM\ops\slh-start.ps1
Auto-memory:    C:\Users\Giga Store\.claude\projects\D--\memory\  (Claude-specific)
Railway CLI:    installed, Osif logged in as osif.e.u@gmail.com, 5 projects visible
Admin keys:     slh_admin_2026_rotated_04_20 (primary), slh_ops_2026_rotated_04_20 (backup)
Broadcast key:  slh-broadcast-2026-change-me (default — needs rotation)
```

---

## 11. Last-mile: if you're an agent reading this

1. Fill the check-in block at section 1
2. Open Mission Control `/api/admin/overview` to see the live state
3. Don't create work that already exists — search first
4. Update tasks as you work (`in_progress` → `done` / `blocked`)
5. At end of session, write `ops/SESSION_LOG_<you>_<date>.md`
6. Handoff via Mission Control comments, not DM

**Welcome to the team. Now go check section 6 and pick something.**

---

**Document version:** 1.0
**Authored:** 2026-04-24 by Claude (Claude Code, model `claude-opus-4-7`)
**Next review:** after 48h or when structure materially changes
