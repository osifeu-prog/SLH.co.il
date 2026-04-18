# 🚀 SLH Spark Complete Integration — Master Workplan
**Date:** 2026-04-18  
**Goal:** Deliver WhatsApp + Safety Network + Wellness Admin + SLH Genesis by EOD  
**Status:** ACTIVE

---

## 📊 Timeline Overview

| Phase | Duration | Parallel Tasks | Deadline |
|-------|----------|-----------------|----------|
| **Phase 1: Setup & Infrastructure** | 1.5 hours | DB Schema + API stubs + Agent briefs | 15:30 |
| **Phase 2: WhatsApp + Safety Network** | 3 hours | Agent 1 + Agent 2 (parallel) | 18:30 |
| **Phase 3: Wellness Admin + Genesis** | 2.5 hours | Agent 3 + Agent 4 (parallel) | 21:00 |
| **Phase 4: Integration & Testing** | 1 hour | Core coordination | 22:00 |
| **COMPLETION** | **8 hours total** | ✅ | **22:00** |

---

## 🎯 Work Streams (4 Parallel Agents)

### **AGENT 1: WhatsApp Integration**
**Lead Time:** 3 hours  
**Output:** Twilio API endpoints, contact DB, fraud tagging, invite dispatch

**Tasks:**
1. ✅ Database schema: `whatsapp_contacts` + `fraud_flags`
2. ✅ API endpoints: `/api/whatsapp/invite-send`, `/api/whatsapp/mark-fraud`
3. ✅ Twilio gateway setup in main.py
4. ✅ Contact management UI in admin.html
5. ✅ Automated invite dispatch (with message templates)
6. ✅ Fraud flag integration with ZUZ system

**Input:** Will receive DB schema + Twilio credentials  
**Output:** Deliver 5 endpoints + 3 database tables + admin UI widget

---

### **AGENT 2: Safety Network Integration**
**Lead Time:** 3 hours  
**Output:** Telegram sync API, alert ingestion, ZUZ marking, security bridging

**Tasks:**
1. ✅ Database schema: `safety_alerts` + `threat_intel` + `community_groups`
2. ✅ Telegram API client for group monitoring
3. ✅ Alert ingestion pipeline (t.me/F7Bp00MKc3 + custom groups)
4. ✅ ZUZ auto-marking on fraud alerts
5. ✅ Security org bridging API endpoints
6. ✅ Alert dashboard in admin.html

**Input:** Will receive Telegram bot token + group IDs + ZUZ system docs  
**Output:** Deliver 4 endpoints + 3 database tables + monitoring UI

---

### **AGENT 3: Wellness Admin Panel**
**Lead Time:** 2.5 hours  
**Output:** Admin dashboard, course upload, task scheduler, broadcast system

**Tasks:**
1. ✅ Database schema: `wellness_courses` + `wellness_tasks` + `wellness_schedules`
2. ✅ Admin UI: Course upload form + task scheduler + broadcast panel
3. ✅ API endpoints: `/api/wellness/course-upload`, `/api/wellness/schedule-task`, `/api/wellness/broadcast`
4. ✅ Token distribution logic on task completion
5. ✅ Real-time progress tracking
6. ✅ Integration with existing Wellness bot (slh-wellness)

**Input:** Will receive existing bot code + token economics  
**Output:** Deliver 3 endpoints + admin panel section + scheduling engine

---

### **AGENT 4: SLH Genesis Documentation**
**Lead Time:** 1.5 hours  
**Output:** PRIMITIVES folder structure, slh-flip.js documentation, version tracking

**Tasks:**
1. ✅ Create `/slh-genesis/PRIMITIVES/text/slh-flip/` folder structure
2. ✅ Write comprehensive README.md (API + usage + philosophy)
3. ✅ Create CHANGELOG.md (v1.0-flip release notes)
4. ✅ Build demo.html with examples
5. ✅ Document integration path for website
6. ✅ Create upgrade-tracker system

**Input:** Will receive slh-flip.js code  
**Output:** Complete documentation package + demo + upgrade path

---

## 🗄️ **Database Schemas to Create**

### WhatsApp Layer
```sql
-- whatsapp_contacts
CREATE TABLE whatsapp_contacts (
  id SERIAL PRIMARY KEY,
  phone_number VARCHAR(15) UNIQUE NOT NULL,
  user_id INT REFERENCES users(id),
  name VARCHAR(100),
  invited_at TIMESTAMP,
  last_contacted TIMESTAMP,
  contact_source VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW()
);

-- fraud_flags (WhatsApp)
CREATE TABLE fraud_flags (
  id SERIAL PRIMARY KEY,
  phone_number VARCHAR(15),
  user_id INT REFERENCES users(id),
  fraud_type VARCHAR(50),
  severity INT (1-10),
  reported_by INT REFERENCES users(id),
  proof_url TEXT,
  zuz_penalty INT DEFAULT 5,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
);

-- whatsapp_invites
CREATE TABLE whatsapp_invites (
  id SERIAL PRIMARY KEY,
  phone_number VARCHAR(15),
  invite_type VARCHAR(50), -- 'website', 'bot', 'course'
  message_template VARCHAR(500),
  sent_at TIMESTAMP,
  delivered BOOLEAN,
  clicked BOOLEAN,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### Safety Network
```sql
-- safety_alerts
CREATE TABLE safety_alerts (
  id SERIAL PRIMARY KEY,
  source_group VARCHAR(100), -- 't.me/F7Bp00MKc3' or custom
  source_user VARCHAR(100),
  alert_title VARCHAR(200),
  alert_description TEXT,
  threat_level INT (1-10),
  associated_phones TEXT[], -- JSON array of phone numbers
  associated_users INT[],
  zuz_mark_triggered BOOLEAN DEFAULT FALSE,
  zuz_penalties_issued INT DEFAULT 0,
  reported_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

-- threat_intel
CREATE TABLE threat_intel (
  id SERIAL PRIMARY KEY,
  phone_number VARCHAR(15),
  threat_score FLOAT (0-100),
  last_flagged TIMESTAMP,
  flagged_count INT DEFAULT 0,
  alert_ids INT[],
  auto_banned BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW()
);

-- community_groups
CREATE TABLE community_groups (
  id SERIAL PRIMARY KEY,
  group_name VARCHAR(100),
  telegram_id VARCHAR(50),
  group_type VARCHAR(50), -- 'public_safety', 'crime_alert', 'custom'
  is_monitored BOOLEAN DEFAULT TRUE,
  members_count INT,
  last_sync TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### Wellness System
```sql
-- wellness_courses
CREATE TABLE wellness_courses (
  id SERIAL PRIMARY KEY,
  course_title VARCHAR(200),
  course_description TEXT,
  course_content TEXT,
  price_slh FLOAT,
  price_zvk INT,
  video_url VARCHAR(500),
  duration_minutes INT,
  difficulty VARCHAR(20), -- 'beginner', 'intermediate', 'advanced'
  created_by INT REFERENCES users(id),
  published BOOLEAN DEFAULT FALSE,
  published_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

-- wellness_tasks
CREATE TABLE wellness_tasks (
  id SERIAL PRIMARY KEY,
  task_title VARCHAR(100),
  task_description TEXT,
  task_type VARCHAR(50), -- 'meditation', 'exercise', 'nutrition', 'affirmation'
  reward_slh FLOAT DEFAULT 0.1,
  reward_zvk INT DEFAULT 1,
  reward_rep INT DEFAULT 1,
  schedule_id INT REFERENCES wellness_schedules(id),
  created_at TIMESTAMP DEFAULT NOW()
);

-- wellness_schedules
CREATE TABLE wellness_schedules (
  id SERIAL PRIMARY KEY,
  schedule_name VARCHAR(100),
  schedule_type VARCHAR(50), -- 'daily', 'weekly', 'custom'
  cron_expression VARCHAR(50),
  task_ids INT[],
  is_active BOOLEAN DEFAULT TRUE,
  created_by INT REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW()
);

-- wellness_completions
CREATE TABLE wellness_completions (
  id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(id),
  task_id INT REFERENCES wellness_tasks(id),
  completed_at TIMESTAMP,
  tokens_awarded JSON,
  streak_count INT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🔌 **API Endpoints to Create**

### WhatsApp Endpoints (Agent 1)
```
POST   /api/whatsapp/contact-add
POST   /api/whatsapp/contact-bulk-import
GET    /api/whatsapp/contacts
POST   /api/whatsapp/send-invite
POST   /api/whatsapp/mark-fraud
GET    /api/whatsapp/fraud-flags
POST   /api/whatsapp/broadcast-message
```

### Safety Network Endpoints (Agent 2)
```
GET    /api/safety/alerts
POST   /api/safety/report-alert
GET    /api/safety/threat-intel/{phone}
POST   /api/safety/monitor-group
GET    /api/safety/community-groups
POST   /api/safety/security-org-bridge
GET    /api/safety/zuz-marks
```

### Wellness Admin Endpoints (Agent 3)
```
POST   /api/wellness/course-upload
GET    /api/wellness/courses
POST   /api/wellness/schedule-task
GET    /api/wellness/schedules
POST   /api/wellness/broadcast-task
GET    /api/wellness/completions/{user_id}
POST   /api/wellness/reward-distribute
```

---

## 📦 **Admin Panel Updates**

New sections in `admin.html`:

1. **WhatsApp Management Tab**
   - Contact upload form
   - Fraud flag dashboard
   - Invite dispatch center
   - Message template builder

2. **Safety Network Tab**
   - Alert monitoring board
   - Threat intel viewer
   - Group monitoring settings
   - ZUZ auto-mark stats

3. **Wellness Admin Tab**
   - Course upload form
   - Task scheduler
   - Broadcast composer
   - Completion analytics
   - Token distribution tracker

4. **Genesis Documentation Tab**
   - Primitives registry
   - Version tracker
   - Module roadmap
   - Integration guide

---

## 🔗 **Integration Points**

```
┌─────────────────────────────────────────┐
│   SLH Spark Ecosystem Master Hub        │
├─────────────────────────────────────────┤
│                                         │
│  ┌─ WhatsApp Integration                │
│  │   └─> Fraud Flags ──────┐           │
│  │                          │           │
│  ├─ Safety Network          │           │
│  │   └─> ZUZ Auto-Marking ──┼─> Guardian Bot
│  │   └─> Alert Ingestion ───┤           │
│  │                          │           │
│  ├─ Wellness Admin          │           │
│  │   └─> Token Distribution │           │
│  │   └─> Task Broadcast ────┤           │
│  │                          │           │
│  └─ SLH Genesis             │           │
│      └─> Primitives ────────┘           │
│                                         │
└─────────────────────────────────────────┘
```

---

## 🎬 **Phase Breakdown**

### **PHASE 1: Setup (15:30) — Core Tasks**
- [ ] Create all database tables (SQL scripts)
- [ ] Write API stub endpoints (empty functions)
- [ ] Prepare agent briefs with all context
- [ ] Set up folder structure for Genesis docs
- [ ] Write this coordination document ✅

**Owner:** You (core)  
**Time:** 1.5 hours

---

### **PHASE 2: Main Development (15:30 → 18:30)**

**AGENT 1 (WhatsApp) — 3 hours**
- Create WhatsApp contact management system
- Integrate Twilio API
- Build fraud flag database + endpoints
- Create invite dispatch automation
- Build admin UI widget
- Test all 6 endpoints

**AGENT 2 (Safety Network) — 3 hours**
- Create Telegram group monitoring API
- Build alert ingestion pipeline
- Implement ZUZ auto-marking logic
- Create security org integration points
- Build alert dashboard UI
- Test all 6 endpoints

**PARALLEL: You + Agent 3 + Agent 4**

**AGENT 3 (Wellness Admin) — 2.5 hours**
- Create course upload system
- Build task scheduler
- Implement broadcast integration
- Create token distribution logic
- Build admin panel section
- Test all 4 endpoints

**AGENT 4 (Genesis Docs) — 1.5 hours**
- Organize PRIMITIVES folder
- Write full README for slh-flip.js
- Create demo.html with examples
- Write version tracking system
- Build upgrade path documentation

---

### **PHASE 3: Integration (18:30 → 21:00)**

**Core Tasks:**
- [ ] Verify all database tables created
- [ ] Test cross-system integrations
- [ ] Validate token distribution flow
- [ ] Confirm Telegram + WhatsApp pipelines
- [ ] Ensure ZUZ marking works end-to-end
- [ ] Verify admin panel functionality

**Time:** 1.5 hours

---

### **PHASE 4: Testing & Deployment (21:00 → 22:00)**

- [ ] End-to-end system test
- [ ] User acceptance criteria
- [ ] Performance validation
- [ ] Documentation review
- [ ] Deploy to Railway
- [ ] Update website pages
- [ ] Notify stakeholders

**Time:** 1 hour

---

## 📋 **Agent Brief Templates**

### **AGENT 1 BRIEF: WhatsApp Integration**

You are building the WhatsApp contact and fraud detection system for SLH Spark.

**Deliverables:**
1. Database: 3 tables (contacts, fraud_flags, invites)
2. API: 6 endpoints with full error handling
3. Admin UI: Contact upload + fraud dashboard
4. Integration: Twilio API connection
5. Automation: Bulk invite dispatcher with message templates

**Context:**
- Osif wants to invite customers to the website and bots
- Fraud detection marks suspicious numbers
- Connected to ZUZ token penalty system (Guardian Bot)
- All data syncs with main PostgreSQL

**Constraints:**
- Use localStorage for Twilio API key (not hardcoded)
- Follow SLH naming conventions
- Write in Hebrew for UI, English for code
- Return JSON responses
- Log all operations to audit_log

**Success Criteria:**
- All 6 endpoints working
- Contact upload processes 100+ numbers
- Fraud marks auto-trigger ZUZ penalties
- Admin dashboard functional
- Telegram logs confirmed

---

### **AGENT 2 BRIEF: Safety Network Integration**

You are building the public safety and crime alert system for SLH Spark.

**Deliverables:**
1. Database: 3 tables (alerts, threat_intel, groups)
2. Telegram API: Monitor groups + ingest alerts
3. API: 6 endpoints for alert management
4. ZUZ Integration: Auto-mark fraud flagged users
5. Admin UI: Alert dashboard + group monitoring

**Context:**
- Source: t.me/F7Bp00MKc3 (public safety group)
- Goal: Build community-based threat intel network
- Integration: Alert users, mark threats, coordinate with security orgs
- Connected to Guardian Bot (ZUZ penalties)

**Constraints:**
- Respect user privacy + data sensitivity
- Implement rate limiting on alert ingestion
- Validate phone numbers before flagging
- Only authorized users can mark threats
- Audit log all actions

**Success Criteria:**
- Telegram group syncing working
- Alerts ingested successfully
- ZUZ marks applied correctly
- 0 false positives in testing
- Dashboard displays all data

---

### **AGENT 3 BRIEF: Wellness Admin Panel**

You are building the course + task management system for SLH Wellness Bot.

**Deliverables:**
1. Database: 4 tables (courses, tasks, schedules, completions)
2. Admin UI: Upload + scheduler + broadcaster
3. API: 4 endpoints (course, schedule, broadcast, rewards)
4. Token Distribution: Auto-reward on task completion
5. Integration: Sync with existing Wellness bot

**Context:**
- Existing Wellness bot broadcasts meditation, exercise, nutrition tasks
- Osif wants to upload courses + schedule tasks + broadcast
- Token rewards: SLH, ZVK, REP on completion
- Real-time website + bot synchronization

**Constraints:**
- Task durations must be realistic
- Token amounts follow economy rules (SLH = 444 ILS value)
- UI must be intuitive for non-technical users
- Schedule uses cron expressions
- Broadcast to all users simultaneously

**Success Criteria:**
- Course upload system functional
- Scheduler creates valid cron expressions
- Broadcast reaches 100% of users
- Tokens distributed correctly
- Website + bot sync verified

---

### **AGENT 4 BRIEF: SLH Genesis Documentation**

You are documenting the first SLH Primitive (slh-flip.js) in the official Genesis library.

**Deliverables:**
1. Folder: `/slh-genesis/PRIMITIVES/text/slh-flip/`
2. README.md: Complete API documentation
3. CHANGELOG.md: Version history (v1.0-flip)
4. demo.html: Working examples
5. Integration guide: How to use on website pages
6. Upgrade tracker: Version management system

**Context:**
- slh-flip.js is a text animation primitive (flip + scramble)
- It's the FIRST official SLH primitive → must set standard
- Used on website pages for visual identity
- Upgrade path: v1.1, v2.0 planned
- This establishes pattern for all future primitives

**Constraints:**
- Documentation must be production-quality
- Include accessibility (prefers-reduced-motion)
- Version all future changes
- Track page usage in meta tags
- Build upgrade-tracker for auto-migration

**Success Criteria:**
- All files created with quality content
- demo.html renders perfectly
- Documentation covers 100% of API
- Integration guide is clear + actionable
- Upgrade tracker system implemented

---

## 💻 **Tech Stack Reference**

| Component | Technology | Location |
|-----------|-----------|----------|
| Database | PostgreSQL 15 | Railway |
| API Framework | FastAPI (Python) | Railway |
| Frontend | HTML/CSS/JS | GitHub Pages |
| Messaging | Telegram aiogram 3.x | Docker |
| WhatsApp | Twilio API | Integration |
| Admin Panel | admin.html | website/ repo |
| Bots | 25 bots, Docker Compose | Local |

---

## 📞 **Communication Protocol**

**Checkpoints:**
- **15:30** — Phase 1 complete, agents briefed
- **17:00** — Agents report progress (50% done)
- **18:30** — Phase 2 complete, integration starts
- **20:00** — Phase 3 complete, testing begins
- **22:00** — FINAL: All systems live

**Status Format:**
```
[AGENT X] Status: [% complete]
- Completed: [list]
- In Progress: [list]
- Blocked By: [if any]
- ETA: [time]
```

---

## ✅ **Completion Checklist**

### Deliverables
- [ ] Database: 10 tables created + seeded
- [ ] API: 16 endpoints tested + documented
- [ ] Admin Panel: 4 new tabs functional
- [ ] Genesis Docs: PRIMITIVES folder complete
- [ ] Integration: All systems connected
- [ ] Testing: End-to-end verified
- [ ] Deployment: All changes pushed
- [ ] Updates: Website pages updated

### Documentation
- [ ] API docs (Swagger)
- [ ] Admin user guide
- [ ] Database schema diagrams
- [ ] Integration architecture
- [ ] Agent handoff docs

### Quality
- [ ] Zero hardcoded secrets
- [ ] All errors logged
- [ ] Audit trail complete
- [ ] Performance validated
- [ ] Mobile responsive

---

## 🎯 **Success Definition**

**By 22:00 today (4/18/2026):**

1. ✅ WhatsApp integration live (invite dispatch + fraud marking)
2. ✅ Safety network monitoring t.me/F7Bp00MKc3 + custom groups
3. ✅ Wellness admin panel deployed (course upload + scheduler)
4. ✅ SLH Genesis PRIMITIVES library established
5. ✅ All systems synchronized + tested
6. ✅ Admin dashboard fully functional
7. ✅ Website pages updated with new features

**Next Phase (Tomorrow):**
- Device control API for ESP32 firmware
- Advanced device dashboard
- OTA firmware updates
- Real-time monitoring system

---

**אוסיף, תוכן התוכנית:**
- 4 agents במקביל (3 שעות כל אחד)
- 16 API endpoints חדשים
- 10 טבלאות database
- 4 כרטיסיות admin חדשות
- מערכת PRIMITIVES רשמית

**מוכן לשיגור?** 🚀
