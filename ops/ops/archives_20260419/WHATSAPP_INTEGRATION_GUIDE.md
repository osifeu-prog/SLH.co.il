# WhatsApp Integration System - Complete Implementation Guide

## Overview

Complete WhatsApp contact management + fraud detection system with Twilio gateway integration and ZUZ anti-fraud penalties.

**Status:** Production-ready | **Deployment:** Railway (auto)  
**Components:** 6 API endpoints | 4 database tables | Admin UI widget | Twilio gateway  
**Integration:** Audit logging | ZUZ token penalties | Institutional-grade compliance

---

## Architecture

### Database Tables

All tables created automatically on app startup.

#### 1. `whatsapp_contacts`
Core contact management.

```sql
CREATE TABLE whatsapp_contacts (
    id BIGSERIAL PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL UNIQUE,
    user_id BIGINT,
    name VARCHAR(255),
    invited_at TIMESTAMP,
    contact_source VARCHAR(50) DEFAULT 'admin',  -- 'admin', 'bulk_import', 'api', etc
    invitation_status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'invited', 'accepted', 'opted_out'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_whatsapp_contacts_phone ON whatsapp_contacts(phone_number);
CREATE INDEX idx_whatsapp_contacts_user ON whatsapp_contacts(user_id);
CREATE INDEX idx_whatsapp_contacts_status ON whatsapp_contacts(invitation_status);
```

#### 2. `fraud_flags_whatsapp`
Fraud marking with ZUZ penalties.

```sql
CREATE TABLE fraud_flags_whatsapp (
    id BIGSERIAL PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL,
    fraud_type VARCHAR(50) NOT NULL,  -- 'spam', 'scam', 'identity_theft', 'other'
    severity INT DEFAULT 5,  -- 1-10 severity rating
    zuz_penalty INT DEFAULT 5,  -- Auto-applied ZUZ penalty
    proof_url TEXT,  -- Optional evidence link
    is_active BOOLEAN DEFAULT TRUE,
    flagged_by BIGINT,  -- admin user_id who flagged
    flagged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(phone_number, fraud_type)
);
CREATE INDEX idx_fraud_flags_phone ON fraud_flags_whatsapp(phone_number);
CREATE INDEX idx_fraud_flags_active ON fraud_flags_whatsapp(is_active, severity DESC);
```

#### 3. `whatsapp_invites`
Message delivery tracking.

```sql
CREATE TABLE whatsapp_invites (
    id BIGSERIAL PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL,
    invite_type VARCHAR(50) NOT NULL,  -- 'website', 'bot', 'course', etc
    message_template TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    delivered BOOLEAN DEFAULT FALSE,
    clicked BOOLEAN DEFAULT FALSE,
    delivery_status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'sent', 'failed', 'bounced'
    twilio_message_id VARCHAR(255),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_whatsapp_invites_phone ON whatsapp_invites(phone_number);
CREATE INDEX idx_whatsapp_invites_status ON whatsapp_invites(delivery_status, sent_at DESC);
```

#### 4. `whatsapp_broadcast`
Broadcast campaign tracking.

```sql
CREATE TABLE whatsapp_broadcast (
    id BIGSERIAL PRIMARY KEY,
    broadcast_title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    target_segment VARCHAR(50) DEFAULT 'all',  -- 'all', 'interested', 'not_invited', 'custom'
    scheduled_for TIMESTAMP,  -- NULL = send immediately
    sent_at TIMESTAMP,
    total_recipients INT DEFAULT 0,
    successfully_sent INT DEFAULT 0,
    failed_count INT DEFAULT 0,
    created_by BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_whatsapp_broadcast_segment ON whatsapp_broadcast(target_segment, sent_at DESC);
CREATE INDEX idx_whatsapp_broadcast_scheduled ON whatsapp_broadcast(scheduled_for) WHERE scheduled_for IS NOT NULL;
```

---

## API Endpoints

All endpoints require `X-Admin-Key` header or JWT Authorization.

### 1. Add Single Contact

**POST** `/api/whatsapp/contact-add`

Add a single WhatsApp contact.

**Request:**
```json
{
    "phone_number": "972501234567",
    "name": "John Doe",
    "contact_source": "admin"  // optional, default: "admin"
}
```

**Response (200):**
```json
{
    "id": 123,
    "phone_number": "+972501234567",
    "status": "added",
    "created_at": "2026-04-18T14:30:00Z"
}
```

**Errors:**
- 400: Invalid phone format
- 409: Contact already exists
- 403: Unauthorized
- 500: Database error

**Phone Validation:**
- Accepts: `+972...`, `972...`, `0...`, bare digits
- Normalizes to: `+972...` (Israeli format)

---

### 2. Bulk Import Contacts

**POST** `/api/whatsapp/contact-bulk-import`

Import multiple contacts in one request.

**Request:**
```json
{
    "contacts": [
        {"phone": "972501234567", "name": "John Doe"},
        {"phone": "972502345678", "name": "Jane Smith"},
        {"phone_number": "0503456789", "name": "Tom Wilson"}
    ]
}
```

**Response (200):**
```json
{
    "imported": 3,
    "success": 3,
    "failed": 0,
    "errors": [],
    "created_ids": [123, 124, 125]
}
```

**Error Handling:**
- Duplicates: skip with error in response
- Invalid phone: skip with error message
- Returns summary of successes + failures
- Partial success supported (doesn't rollback)

**Audit Logging:**
Logged to `institutional_audit` table:
- Action: `whatsapp.contact.bulk_import`
- Metadata: `{success: N, failed: M, total: X}`

---

### 3. Get All Contacts

**GET** `/api/whatsapp/contacts?limit=100&offset=0&status=pending`

Retrieve paginated contact list.

**Query Parameters:**
- `limit`: max records (1-1000, default: 100)
- `offset`: pagination offset (default: 0)
- `status`: filter by status ('pending', 'invited', etc) - optional

**Response (200):**
```json
{
    "count": 256,
    "limit": 100,
    "offset": 0,
    "contacts": [
        {
            "id": 1,
            "phone_number": "+972501234567",
            "user_id": null,
            "name": "John Doe",
            "invited_at": null,
            "contact_source": "admin",
            "invitation_status": "pending",
            "created_at": "2026-04-18T14:30:00Z",
            "updated_at": "2026-04-18T14:30:00Z"
        }
        // ... more contacts
    ]
}
```

---

### 4. Send Invite

**POST** `/api/whatsapp/send-invite`

Send WhatsApp message to a contact (via Twilio if configured).

**Request:**
```json
{
    "phone_number": "+972501234567",
    "invite_type": "website",  // 'website', 'bot', 'course'
    "message": "Custom message text"  // optional, uses default if omitted
}
```

**Default Messages (by type):**
- `website`: "ברוכים הבאים ל-SLH Spark! 🚀 בקרו בחזקות: https://slh-nft.com"
- `bot`: "בואו להצטרף לבוט SLH שלנו ולהתחיל להשתמש בתוקנים: https://t.me/SLH_AIR_bot"
- `course`: "קורס חדש זמין עכשיו! השתמשו בקוד SLH2026 להנחה:"

**Response (200):**
```json
{
    "message_id": "SM123abc456def...",  // Twilio SID or local ID
    "status": "sent",  // 'sent', 'pending', 'failed'
    "timestamp": "2026-04-18T14:30:00Z",
    "phone": "+972501234567"
}
```

**Twilio Integration:**
- Requires: `TWILIO_SID`, `TWILIO_TOKEN`, `TWILIO_PHONE` env vars
- Falls back gracefully if not configured (status: 'pending')
- Message ID recorded in `whatsapp_invites` table
- Contact status updated to 'invited'

**Audit Logging:**
- Action: `whatsapp.invite.send`
- Metadata: `{phone, type, status}`

---

### 5. Mark as Fraud

**POST** `/api/whatsapp/mark-fraud`

Flag phone number as fraudulent and auto-apply ZUZ penalty.

**Request:**
```json
{
    "phone_number": "+972501234567",
    "fraud_type": "scam",  // 'spam', 'scam', 'identity_theft', 'other'
    "severity": 7,  // 1-10 (default: 5)
    "proof_url": "https://example.com/evidence.jpg"  // optional
}
```

**Response (200):**
```json
{
    "phone_number": "+972501234567",
    "fraud_type": "scam",
    "severity": 7,
    "zuz_penalty": 5,
    "status": "flagged"
}
```

**ZUZ Integration:**
- Auto-applies 5 ZUZ penalty to associated user
- Updates `token_balances` table: `ZUZ += 5`
- Only applies if user linked to phone number in `whatsapp_contacts`
- User can accumulate ZUZ (auto-ban at 100 points per Guardian system)

**Database Logic:**
- Inserts into `fraud_flags_whatsapp` (with UNIQUE constraint on phone+type)
- Looks up user_id from contact
- Inserts/updates ZUZ balance
- All wrapped in transaction

**Audit Logging:**
- Action: `whatsapp.fraud.mark`
- Metadata: `{phone, type, severity, zuz_penalty, user_id}`

---

### 6. Broadcast Message

**POST** `/api/whatsapp/broadcast-message`

Send message to all contacts in a segment.

**Request:**
```json
{
    "title": "Product Launch",
    "message": "זו הודעה חדשה עבורך",
    "target_segment": "all",  // 'all', 'interested', 'not_invited', 'custom'
    "scheduled_for": "2026-04-20T10:00:00Z"  // optional (NULL = send now)
}
```

**Segment Definitions:**
- `all`: All contacts (pending + invited)
- `interested`: Only invited contacts
- `not_invited`: Only pending contacts
- `custom`: For future use (currently same as 'all')

**Response (200):**
```json
{
    "broadcast_id": 456,
    "total_recipients": 150,
    "successfully_sent": 145,
    "failed": 5,
    "status": "sent"
}
```

**Twilio Integration:**
- Sends via Twilio API to each contact
- Catches and logs failures per contact
- Returns success/failure counts
- Records in `whatsapp_broadcast` table

**Scheduled Sends:**
- If `scheduled_for` provided and in future: stored for later processing
- Current implementation sends immediately (scheduling framework: TODO)
- Recommend: use Railway cron jobs for scheduled delivery

**Audit Logging:**
- Action: `whatsapp.broadcast.send`
- Metadata: `{title, segment, recipients, sent}`

---

## Admin UI Widget

Located in `/website/admin.html` under **Tools > WhatsApp** tab.

### Features

**1. Dashboard Metrics**
- Total Contacts
- Invited Count
- Fraud Flagged Count
- Broadcasts Sent Count

**2. Contact Upload**
- CSV file upload (format: `phone,name`)
- Real-time validation
- Success/failure summary

**3. Add Single Contact**
- Phone number + optional name
- Instant validation
- Confirmation feedback

**4. Send Invite**
- Phone selection
- Invite type dropdown (website, bot, course)
- Custom message textarea
- Real-time delivery status

**5. Fraud Marking**
- Phone input
- Fraud type selector (spam, scam, identity theft, other)
- Severity slider (1-10)
- Optional proof URL
- Red confirmation button

**6. Broadcast Sender**
- Title + message text
- Target segment selector
- Recipient count validation
- Confirmation before sending

**7. Contact List Table**
- Phone, Name, Status, Invited Date, Source
- Fraud flag indicator
- Status filter (pending, invited, all)
- Real-time refresh

### JavaScript Functions

```javascript
waRefreshContacts()        // Load contacts list from API
waAddContact()            // Add single contact
waUploadContacts()        // Bulk CSV import
waSendInvite()            // Send invite message
waMarkFraud()             // Flag as fraud
waBroadcast()             // Send broadcast
ensureWhatsAppLoaded()    // Auto-load on page switch
```

---

## Environment Configuration

### Required Environment Variables

```bash
# Database (already configured)
DATABASE_URL=postgresql://...

# Twilio Gateway (optional, graceful fallback if missing)
TWILIO_SID=ACxxxxxxxxxxxxx
TWILIO_TOKEN=your_auth_token_here
TWILIO_PHONE=+1234567890  # Twilio phone number for sending

# Admin Keys (existing)
ADMIN_API_KEYS=slh2026admin,slh_admin_2026,slh-spark-admin
```

### Setting Up Twilio

1. **Create Twilio Account**
   - Go to https://www.twilio.com
   - Sign up for free trial (gets $15 credit)

2. **Get Credentials**
   - Copy Account SID from dashboard → `TWILIO_SID`
   - Create Auth Token → `TWILIO_TOKEN`
   - Provision phone number → `TWILIO_PHONE` (format: +1234567890)

3. **Configure Railway Environment**
   ```bash
   railway service add
   # Add env vars to Railway project
   TWILIO_SID=ACxxxxx
   TWILIO_TOKEN=yyyyy
   TWILIO_PHONE=+1234567890
   
   # Deploy
   git push origin master  # Railway auto-deploys
   ```

4. **WhatsApp Sandboxing (Twilio)**
   - Twilio provides WhatsApp sandbox during development
   - Production: requires WhatsApp Business Account approval
   - Messages sent via Twilio are SMS fallback (WhatsApp beta)

### Graceful Degradation

If Twilio not configured:
- `send-invite` returns `status: "pending"` (message not actually sent)
- `broadcast-message` skips send (records to DB only)
- No errors thrown (allows testing without Twilio)
- Admin UI still functional for all operations

---

## ZUZ Integration

The fraud marking system integrates with the Guardian anti-fraud token system.

### How It Works

1. **Admin flags phone as fraud** via `/api/whatsapp/mark-fraud`
2. **System finds associated user** from `whatsapp_contacts.user_id`
3. **ZUZ penalty applied** to `token_balances` table
   - Penalty: 5 ZUZ per fraud flag
   - Query: `INSERT INTO token_balances (user_id, token, balance) VALUES (?, 'ZUZ', 5) ON CONFLICT DO UPDATE SET balance = balance + 5`
4. **User accumulates ZUZ** across all fraud reports
5. **Auto-ban triggered** at 100 ZUZ (Guardian system enforcement)

### ZUZ Penalty Levels

```
Severity 1-2: 3 ZUZ  (minor spam)
Severity 3-4: 5 ZUZ  (suspicious)
Severity 5-7: 5 ZUZ  (likely scam)
Severity 8-10: 5 ZUZ (confirmed fraud)
```

Future enhancement: Make penalty configurable by severity.

### Checking User ZUZ

```bash
# Query user's current ZUZ
SELECT balance FROM token_balances 
WHERE user_id = ? AND token = 'ZUZ'

# Get all flagged phones for a user
SELECT * FROM fraud_flags_whatsapp 
WHERE phone_number IN (
    SELECT phone_number FROM whatsapp_contacts 
    WHERE user_id = ?
)
```

---

## Implementation Details

### File Structure

```
/d/SLH_ECOSYSTEM/
├── main.py                      # Routes integrated here
├── routes/
│   └── whatsapp.py             # Complete implementation (500 lines)
├── website/
│   └── admin.html              # UI widget + JavaScript functions
└── database/
    └── (tables auto-created)
```

### Code Quality

- **Type hints:** Full Pydantic models + FastAPI validation
- **Error handling:** HTTP exceptions with proper status codes
- **Logging:** All actions logged to institutional_audit table
- **Rate limiting:** None implemented (TODO for production)
- **Transactions:** Used for multi-step operations (fraud marking)
- **Indexes:** Added for phone_number, status, user_id, severity
- **Auth:** Centralized `_verify_admin_auth()` helper

### Security Considerations

**✅ Implemented:**
- Admin key validation on all endpoints
- JWT authorization support
- Audit logging for compliance
- Phone number validation
- Input sanitization (Pydantic models)

**⚠️ Partial:**
- Rate limiting (TODO)
- DDoS protection via API gateway (Railway)

**🚀 Future:**
- Phone number whitelisting (opt-in only)
- Message template approval workflow
- Fraud flag appeal process
- Encrypted storage of proof URLs

---

## Testing

### Unit Testing

```bash
# Test contact addition
curl -X POST http://localhost:8000/api/whatsapp/contact-add \
  -H "X-Admin-Key: slh2026admin" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "972501234567", "name": "Test User"}'

# Test fraud marking
curl -X POST http://localhost:8000/api/whatsapp/mark-fraud \
  -H "X-Admin-Key: slh2026admin" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "972501234567", "fraud_type": "spam", "severity": 5}'

# Test contacts list
curl http://localhost:8000/api/whatsapp/contacts \
  -H "X-Admin-Key: slh2026admin"
```

### Integration Testing

1. **Add test contacts via admin UI**
2. **Send invite to one contact**
3. **Check twilio_message_id recorded**
4. **Mark one as fraud**
5. **Verify ZUZ penalty applied**
6. **Send broadcast**
7. **Check whatsapp_broadcast table**

### Load Testing

```bash
# Bulk import 1000 contacts
time curl -X POST http://localhost:8000/api/whatsapp/contact-bulk-import \
  -H "X-Admin-Key: slh2026admin" \
  -H "Content-Type: application/json" \
  -d '[{"phone":"972501234567","name":"Test"},...1000 times]'
```

Expected: < 5 seconds for 1000 imports

---

## Monitoring & Alerts

### Metrics to Track

```sql
-- Daily contact growth
SELECT DATE(created_at), COUNT(*) 
FROM whatsapp_contacts 
GROUP BY DATE(created_at)
ORDER BY DATE DESC LIMIT 30;

-- Fraud flag rate
SELECT fraud_type, COUNT(*) 
FROM fraud_flags_whatsapp 
WHERE flagged_at > NOW() - INTERVAL '7 days'
GROUP BY fraud_type;

-- Broadcast delivery rate
SELECT AVG(successfully_sent::float / total_recipients) as delivery_rate
FROM whatsapp_broadcast
WHERE sent_at > NOW() - INTERVAL '30 days';
```

### Alerting (TODO)

- If fraud flags > 10/day: notify admin
- If broadcast failures > 20%: alert ops team
- If table growth > 100K rows: notify DevOps

---

## Future Enhancements

### Phase 2 (Next Sprint)
- [ ] Rate limiting per admin key
- [ ] Scheduled broadcast delivery via Railway cron
- [ ] Message template library + approval workflow
- [ ] CSV export of contact lists
- [ ] Fraud appeal/dispute process

### Phase 3 (Q2 2026)
- [ ] WhatsApp Business API integration (replace Twilio)
- [ ] Phone number whitelist/blacklist
- [ ] Message encryption (E2E)
- [ ] User opt-in/opt-out tracking
- [ ] Broadcast analytics (delivery, read, click rates)

### Phase 4 (Q3 2026)
- [ ] Multi-language message templates (Russian, Arabic, English)
- [ ] AI sentiment analysis on proof URLs
- [ ] Automatic fraud detection (pattern matching)
- [ ] CRM integration (Salesforce, HubSpot)
- [ ] SMS fallback gateway (Vonage, AWS SNS)

---

## Troubleshooting

### Issue: "Unauthorized" on all endpoints
**Solution:** Verify `X-Admin-Key` header sent and matches `ADMIN_API_KEYS` in `.env`

### Issue: Twilio messages not sending
**Solution:** 
1. Verify `TWILIO_SID`, `TWILIO_TOKEN`, `TWILIO_PHONE` set in Railway
2. Check Twilio account has balance/credits
3. Verify phone number format (use admin UI validation)
4. Check `/api/audit/recent` for error details

### Issue: ZUZ not applied on fraud flag
**Solution:**
1. Verify user_id linked to phone_number in `whatsapp_contacts`
2. Check `token_balances` table directly
3. Review audit log: `SELECT * FROM institutional_audit WHERE action LIKE 'whatsapp.fraud%'`

### Issue: CSV upload fails silently
**Solution:**
1. Check file format: `phone,name` (header required)
2. Verify phone numbers are valid (use leading +972 or 0)
3. Check browser console for JavaScript errors
4. Review response status in Network tab

---

## API Reference Summary

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/api/whatsapp/contact-add` | POST | Required | Add single contact |
| `/api/whatsapp/contact-bulk-import` | POST | Required | Bulk import from list |
| `/api/whatsapp/contacts` | GET | Required | List contacts with pagination |
| `/api/whatsapp/send-invite` | POST | Required | Send WhatsApp invite (Twilio) |
| `/api/whatsapp/mark-fraud` | POST | Required | Flag phone + apply ZUZ penalty |
| `/api/whatsapp/broadcast-message` | POST | Required | Send broadcast to segment |

---

## Support & Documentation

- **API Docs:** /docs (FastAPI Swagger UI)
- **Audit Trail:** Admin > Institutional > Audit Log
- **Issues:** File bug at /admin-bugs.html
- **Slack:** #slh-ecosystem-api

---

**Last Updated:** 2026-04-18  
**Deployed:** Railway (auto-sync from master branch)  
**Status:** Production Ready
