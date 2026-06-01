# SLH Spark Ecosystem — Claude Code Instructions v2.0
**Updated:** 2026-05-04 | **Owner:** Osif Kaufman Ungar (@osifeu_prog, ID: 224223270)

---

## 👤 Who is the user
- **Osif Kaufman Ungar** — solo Hebrew-speaking developer, builds nights (~22:00–05:00)
- Prefers direct action. "כן לכל ההצעות" = proceed with all suggestions
- UI in Hebrew. Code/commits in English
- 10+ institutional investors interested (1M+ ILS each)

---

## 🗺️ Ground Truth — Single Source of Truth

### 2 Active Repos (SLH.co.il is DEPRECATED)
| Repo | Branch | Deploys To | Use For |
|------|--------|------------|---------|
| `github.com/osifeu-prog/slh-api` | master | Railway `slh-fastapi` | **API + Bots** ← main repo |
| `github.com/osifeu-prog/osifeu-prog.github.io` | main | GitHub Pages `slh-nft.com` | **Frontend** |
| `github.com/osifeu-prog/SLH.co.il` | main | Railway `slhcoil` | ⚠️ DEPRECATED — legacy http.server, do not update |

### Local Path
```
D:\SLH_ECOSYSTEM\          ← main repo (slh-api)
D:\SLH_ECOSYSTEM\website\  ← frontend repo (osifeu-prog.github.io)
```

### Critical: main.py sync
Railway builds from ROOT main.py, not api/main.py. Always sync before push:
```bash
cp api/main.py main.py
git add main.py api/main.py
git commit -m "sync: api → root main.py"
git push origin master
```

---

## 🏗️ Architecture

```
D:\SLH_ECOSYSTEM\
├── api/main.py          ← FastAPI v2.0 (modular — ~150 lines, routers only)
├── main.py              ← ROOT COPY (Railway builds from here!)
├── routes/              ← 33 route modules + 20 new extracted from main.py
├── shared/              ← bot_template · payments · guardian · wallet_engine
├── bots/                ← all 26 bots consolidated (NEW structure)
│   ├── _shared/         ← base_bot.py, slh_payments/, bot_heartbeat.py
│   ├── admin/           ← @MY_SUPER_ADMIN_bot
│   ├── academia/        ← @SLH_Academia_bot
│   └── [others...]
├── docker-compose.yml   ← 26 services
├── docs/                ← 5 docs (replaces ops/ 305 files)
│   ├── ARCHITECTURE.md
│   ├── API_REFERENCE.md
│   ├── BOTS_GUIDE.md
│   ├── SECURITY.md
│   └── CHANGELOG.md
├── archive/             ← bak_files/, ops_snapshots/ (read-only history)
├── CLAUDE.md            ← this file
└── .env                 ← never push to git!
```

---

## 🚀 Session Start Checklist (5 steps)

```bash
# 1. API health
curl https://slh-fastapi-production.up.railway.app/api/health
# Expected: {"status":"ok","db":"connected","version":"2.0.0"}

# 2. Bot registry
curl https://slh-fastapi-production.up.railway.app/api/bots/active/count

# 3. Git status (both repos)
cd D:\SLH_ECOSYSTEM && git status && git log --oneline -3
cd D:\SLH_ECOSYSTEM\website && git status && git log --oneline -3

# 4. Railway deploy status (if recent push)
# Check Railway dashboard or: railway logs --tail 20

# 5. Ask user: what's priority today?
```

---

## 💰 5-Token Economy — Ground Truth

| Token | Supply | Contract / Network | Price | Purpose |
|-------|--------|--------------------|-------|---------|
| **SLH** | **110,750,000** | `0xACb0A09414CEA1C879c67bB7A877E4e19480f022` · BSC BEP-20 · 15 decimals | 444 ₪ target | Premium / Governance |
| **MNH** | unlimited | Internal | 1 ₪ peg | Stablecoin |
| **ZVK** | unlimited | Internal | ~4.4 ₪ | Activity rewards |
| **REP** | 0–1000+ | Internal | N/A | Reputation score |
| **ZUZ** | unlimited | Internal | N/A | Anti-fraud marker (auto-ban @100) |

**PancakeSwap Pool:** `0xacea26b6e132cd45f2b8a4754170d4d0d3b8bbee`  
**Genesis Wallet:** `0xd061de73B06d5E91bfA46b35EfB7B08b16903da4`  
**Main MetaMask:** `0xD0617B54FB4b6b66307846f217b4D685800E3dA4`

---

## 🤖 Bot Fleet — 26 Services

| Container | Bot | Purpose |
|-----------|-----|---------|
| `slh-core-bot` | @SLH_Academia_bot | Core community + academia |
| `slh-guardian-bot` | Guardian | Anti-fraud · ZUZ system |
| `slh-botshop` | @Buy_My_Shop_bot | Bot marketplace |
| `slh-test-bot` | Test | Dev testing |
| `slh-claude-bot` | @SLH_Claude_bot | AI assistant (Claude-powered) |
| `slh-academia-bot` | Academia | Courses + ZVK rewards |
| admin-bot | @MY_SUPER_ADMIN_bot | Admin control |
| wallet | @SLH_Wallet_bot | TON + BSC wallet |
| airdrop | @AIRDROP_bot | Token distribution |
| campaign-bot | Campaign | Marketing + affiliates |
| g4mebot | @G4meb0t_bot_bot | Gaming + dating |
| tonmnh-bot | TonMNH | TON/MNH marketplace |
| nfty-bot | NIFTI_Publisher | NFT publishing |
| expertnet-bot | ExpertNet | Expert verification |
| match-bot | Match | Dating/matching |
| school | School | Education |
| fun | @SLH_Fun_bot | Promo + fun |
| factory | @Osifs_Factory_bot | Investment tools |
| userinfo-bot | UserInfo | User data |
| wellness-bot | Wellness | Health scheduler |
| osif-shop | Osif Shop | E-commerce |
| + postgres | DB | PostgreSQL 15 |
| + redis | Cache | Redis 7 |

**Start/Stop:**
```powershell
docker-compose up -d        # start all
docker-compose down         # stop all
docker-compose logs -f admin-bot --tail 50  # live logs
docker-compose restart <service>            # restart one
```

---

## 📋 Work Rules

### Always Do
- Read this file at session start
- Check API health (step 1 above)
- Hebrew UI text, English code/commits
- Sync `api/main.py → main.py` before every push
- Push website changes to `website/` repo (main branch)
- Push API/bot changes to root repo (master branch)
- Log key decisions in `docs/CHANGELOG.md`

### Never Do
- Never push `.env` to git
- Never hardcode passwords/tokens in HTML (use localStorage + API)
- Never show mock data as real — use `[DEMO]` tag or `test_` prefix
- Never give away 50+ SLH as reward (444 ₪ each)
- Never add to `ops/` — write to `docs/` instead
- Never put code in `SLH.co.il` repo — it's deprecated
- Never use `_ensure_tables` — tables created at lifespan startup
- Never assume `display_name` column exists — use try/except fallback

### Data Conventions
| Marker | Meaning |
|--------|---------|
| `test_` prefix | Test/demo data |
| `[DEMO]` | Placeholder content |
| `[SEED]` | Initial seed data |
| `--` | No data available |
| `N/A` | Not applicable |

### Admin Auth
- Admin panel at `/admin.html` — password in `localStorage.slh_admin_password`
- API uses `X-Admin-Key: <value>` header
- Admin keys set via `ADMIN_API_KEYS` env var (comma-separated)

---

## 🔧 Pending Items

### 🔴 P0 — Must fix before IDO
- [ ] Railway env vars: JWT_SECRET, ADMIN_API_KEYS, ENCRYPTION_KEY (see docs/SECURITY.md)
- [ ] Rotate Binance EXCHANGE_API_KEY/EXCHANGE_SECRET
- [ ] Rotate 30 Telegram bot tokens (1/31 done)
- [ ] Fix bot registry: `init_bot_registry failed: missing pool`
- [ ] Fix: `init_admin_rotate failed: missing pool`
- [ ] Fix: Wellness scheduler TypeError
- [ ] Deploy FastAPI as new Railway service `slh-fastapi`
- [ ] Fix `/tokens.html` 404

### 🟠 P1 — Important
- [ ] JWT auth on sensitive endpoints: /api/user/{id}, /api/user/wallet/{id}
- [ ] Migrate 109 pages to `data-theme="neural"`
- [ ] i18n: 100 pages missing translations.js
- [ ] Webhook migration (all 26 bots still polling)
- [ ] Fix `/bots.html` empty ("Coming Soon")
- [ ] Supply consistency: use 110,750,000 everywhere (currently 3 different numbers)
- [ ] Staking disclaimer: add asterisk to "4-5.4% monthly" claims

### 🟢 P2 — Nice to have
- [ ] GitHub Actions CI/CD for both repos
- [ ] Archive/clean `ops/` → 5 docs structure
- [ ] ESP32 firmware → sends HTTP to API (WiFi test works, API calls pending)
- [ ] Webhook migration for all bots

---

## 👥 Key People
| Name | Role | Telegram ID |
|------|------|-------------|
| **Osif Kaufman Ungar** | Owner / Lead Developer | 224223270 |
| **Tzvika** | Co-founder / Crypto Trader | — |
| **Zohar Shefa Dror** | Active Contributor / QA | — |
| **Eli** | Contributor | — |
| **Yakir Lisha** | Contributor | — |

---

## 📊 System Stats (2026-05-04)
- API: FastAPI ~230 endpoints · 11,780 lines in api/main.py (pre-split)
- Frontend: 164 HTML pages · neural theme 21/164 (13%) · i18n 64/164 (39%)
- Bots: 26 Docker services · all polling · bot registry shows 0 (broken)
- Users registered: 9 · Genesis raised: 0.08 BNB
- Routes: 33 route files + ~20 to extract from main.py
