# SLH GENESIS

*The foundational archive of the SLH Ecosystem.*

---

## What this is

This folder is the **historical and conceptual backbone** of the SLH Spark universe. It is not code. It is not production. It is the **living archive** — the "lab notebook" of a project that grew from a musician's Telegram bot into a 6-token, 225-endpoint, 25-bot ecosystem.

## What this contains

- **LOGS/** — append-only history
  - `timeline.md` — chronological events (every significant shipping moment)
  - `decisions.md` — architectural decisions with reasoning
  - `experiments.md` — things we tried, what worked, what didn't

- **ART/** — the creative identity
  - `ascii/` — ASCII art drafts and banners
  - `animations/` — terminal reveals, flip/scramble concepts
  - `concepts/` — brand explorations, visual identity notes

- **TERMINAL_SHOW/** — scripted demos
  - `slh_reveal.ps1` — the dramatic terminal reveal (PowerShell)
  - `assets/` — assets referenced by shows
  - `drafts/` — work-in-progress scripts

- **PROMPTS/** — AI agent prompts
  - `central_agent.md` — the Master Documentation Agent (reads this repo, updates LOGS/)
  - `assistants/` — per-task agent prompts
  - `system_design/` — prompts for architectural exploration

- **NOTES/** — free-form thinking
  - `ideas.md` — the brain dump
  - `architecture.md` — big-picture system maps
  - `future.md` — what we haven't built yet, but want to

## The rule

**Append, never overwrite.** History is value. When a decision changes, write a NEW entry in `decisions.md` that supersedes the old one. Never edit the original. Over time, this repo becomes your most valuable asset — a traceable record of how a real working system got built.

## Relation to the main ecosystem

- **Production code:** `github.com/osifeu-prog/slh-api` (Railway deploy)
- **Live website:** `github.com/osifeu-prog/osifeu-prog.github.io` (GitHub Pages)
- **Operations docs:** `D:\SLH_ECOSYSTEM\ops\`
- **This archive:** `D:\SLH_ECOSYSTEM\slh-genesis\`

`slh-genesis` is the "historical memory." `ops/` is the "active playbook." The two complement: when a decision is archived here, the current playbook reflects it.

## The central agent

Use `PROMPTS/central_agent.md` as the system prompt for any AI that writes to this folder. It enforces append-only discipline, neutral tone, and canonical naming.

---

**Born:** 2026-04-17 · **Author of first entry:** Claude Opus 4.7 (Claude Code) commissioned by Osif Kaufman Ungar
