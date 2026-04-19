"""
WhatsApp Integration Module
Contact management + fraud detection system with Twilio gateway
"""
import os
import re
import json
import logging
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Header, Request

# Twilio imports (optional, graceful degradation if not installed)
try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    TwilioClient = None

logger = logging.getLogger(__name__)

# Router
router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])

# Global connection pool (set by main.py)
_pool = None

def set_pool(pool):
    """Set the asyncpg pool for this module."""
    global _pool
    _pool = pool

async def init_whatsapp_tables():
    """Initialize WhatsApp tables on startup."""
    if not _pool:
        return
    async with _pool.acquire() as conn:
        await _ensure_whatsapp_tables(conn)

# ============================================================
# DATABASE INITIALIZATION
# ============================================================

async def _ensure_whatsapp_tables(conn):
    """Create all required WhatsApp tables."""
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS whatsapp_contacts (
            id BIGSERIAL PRIMARY KEY,
            phone_number VARCHAR(20) NOT NULL UNIQUE,
            user_id BIGINT,
            name VARCHAR(255),
            invited_at TIMESTAMP,
            contact_source VARCHAR(50) DEFAULT 'admin',
            invitation_status VARCHAR(50) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_whatsapp_contacts_phone
        ON whatsapp_contacts(phone_number);
        CREATE INDEX IF NOT EXISTS idx_whatsapp_contacts_user
        ON whatsapp_contacts(user_id);
        CREATE INDEX IF NOT EXISTS idx_whatsapp_contacts_status
        ON whatsapp_contacts(invitation_status);

        CREATE TABLE IF NOT EXISTS fraud_flags_whatsapp (
            id BIGSERIAL PRIMARY KEY,
            phone_number VARCHAR(20) NOT NULL,
            fraud_type VARCHAR(50) NOT NULL,
            severity INT DEFAULT 5,
            zuz_penalty INT DEFAULT 5,
            proof_url TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            flagged_by BIGINT,
            flagged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(phone_number, fraud_type)
        );
        CREATE INDEX IF NOT EXISTS idx_fraud_flags_phone
        ON fraud_flags_whatsapp(phone_number);
        CREATE INDEX IF NOT EXISTS idx_fraud_flags_active
        ON fraud_flags_whatsapp(is_active, severity DESC);

        CREATE TABLE IF NOT EXISTS whatsapp_invites (
            id BIGSERIAL PRIMARY KEY,
            phone_number VARCHAR(20) NOT NULL,
            invite_type VARCHAR(50) NOT NULL,
            message_template TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            delivered BOOLEAN DEFAULT FALSE,
            clicked BOOLEAN DEFAULT FALSE,
            delivery_status VARCHAR(50) DEFAULT 'pending',
            twilio_message_id VARCHAR(255),
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_whatsapp_invites_phone
        ON whatsapp_invites(phone_number);
        CREATE INDEX IF NOT EXISTS idx_whatsapp_invites_status
        ON whatsapp_invites(delivery_status, sent_at DESC);

        CREATE TABLE IF NOT EXISTS whatsapp_broadcast (
            id BIGSERIAL PRIMARY KEY,
            broadcast_title VARCHAR(255) NOT NULL,
            message TEXT NOT NULL,
            target_segment VARCHAR(50) DEFAULT 'all',
            scheduled_for TIMESTAMP,
            sent_at TIMESTAMP,
            total_recipients INT DEFAULT 0,
            successfully_sent INT DEFAULT 0,
            failed_count INT DEFAULT 0,
            created_by BIGINT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_whatsapp_broadcast_segment
        ON whatsapp_broadcast(target_segment, sent_at DESC);
        CREATE INDEX IF NOT EXISTS idx_whatsapp_broadcast_scheduled
        ON whatsapp_broadcast(scheduled_for) WHERE scheduled_for IS NOT NULL;
    """)

# ============================================================
# PYDANTIC MODELS
# ============================================================

class ContactAddRequest(BaseModel):
    phone_number: str
    name: Optional[str] = None
    contact_source: str = "admin"

class ContactBulkImportRequest(BaseModel):
    contacts: List[dict]

class SendInviteRequest(BaseModel):
    phone_number: str
    invite_type: str
    message: Optional[str] = None

class MarkFraudRequest(BaseModel):
    phone_number: str
    fraud_type: str
    severity: int = 5
    proof_url: Optional[str] = None

class BroadcastMessageRequest(BaseModel):
    title: str
    message: str
    target_segment: str = "all"
    scheduled_for: Optional[str] = None

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _validate_phone_number(phone: str) -> str:
    """Validate and normalize Israeli phone numbers to +972 format."""
    # Remove spaces, dashes, parentheses
    phone = re.sub(r'[\s\-\(\)]', '', phone)

    # Already has +
    if phone.startswith('+'):
        return phone

    # +972 format
    if phone.startswith('972'):
        return '+' + phone

    # 0xxx format (Israeli local)
    if phone.startswith('0'):
        return '+972' + phone[1:]

    # No prefix, assume Israeli
    if len(phone) >= 9:
        return '+972' + phone

    raise ValueError(f"Invalid phone format: {phone}")

async def _log_audit(conn, action: str, actor_user_id: int, resource_type: str,
                     resource_id: str, details: Optional[dict] = None):
    """Log action to audit table."""
    try:
        await conn.execute("""
            INSERT INTO institutional_audit
            (actor_user_id, actor_type, action, resource_type, resource_id, metadata)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, actor_user_id, 'admin', action, resource_type, resource_id,
        json.dumps(details or {}) if details else None)
    except Exception as e:
        logger.warning(f"Audit log failed for {action}: {e}")

def _get_twilio_client():
    """Get Twilio client if credentials are available."""
    if not TWILIO_AVAILABLE:
        return None

    sid = os.getenv('TWILIO_SID')
    token = os.getenv('TWILIO_TOKEN')

    if not sid or not token:
        logger.warning("Twilio credentials not configured (TWILIO_SID, TWILIO_TOKEN)")
        return None

    return TwilioClient(sid, token)

# ============================================================
# ENDPOINT 1: Add Single Contact
# ============================================================

async def _verify_admin_auth(authorization: Optional[str], x_admin_key: Optional[str]):
    """Verify admin authentication. Returns admin_id or raises HTTPException."""
    try:
        from main import ADMIN_API_KEYS, _require_admin
        return _require_admin(authorization, x_admin_key)
    except HTTPException:
        raise HTTPException(403, "Unauthorized")
    except:
        raise HTTPException(403, "Unauthorized")

@router.post("/contact-add")
async def whatsapp_contact_add(
    req: ContactAddRequest,
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None),
):
    """Add a single WhatsApp contact."""
    admin_id = await _verify_admin_auth(authorization, x_admin_key)

    # Validate phone
    try:
        phone = _validate_phone_number(req.phone_number)
    except ValueError as e:
        raise HTTPException(400, str(e))

    async with _pool.acquire() as conn:
        await _ensure_whatsapp_tables(conn)

        try:
            # Check if already exists
            existing = await conn.fetchrow(
                "SELECT id FROM whatsapp_contacts WHERE phone_number = $1",
                phone
            )
            if existing:
                raise HTTPException(409, f"Contact already exists: {phone}")

            # Insert
            contact_id = await conn.fetchval("""
                INSERT INTO whatsapp_contacts
                (phone_number, name, contact_source, invitation_status, created_at)
                VALUES ($1, $2, $3, $4, NOW())
                RETURNING id
            """, phone, req.name, req.contact_source, "pending")

            # Audit log
            await _log_audit(conn, "whatsapp.contact.add", admin_id,
                           "whatsapp_contact", str(contact_id),
                           {"phone": phone, "name": req.name})

            return {
                "id": contact_id,
                "phone_number": phone,
                "status": "added",
                "created_at": datetime.utcnow().isoformat()
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to add contact: {e}")
            raise HTTPException(500, f"Database error: {str(e)[:100]}")

# ============================================================
# ENDPOINT 2: Bulk Import Contacts
# ============================================================

@router.post("/contact-bulk-import")
async def whatsapp_bulk_import(
    req: ContactBulkImportRequest,
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None),
):
    """Bulk import contacts from CSV-like list."""
    admin_id = await _verify_admin_auth(authorization, x_admin_key)

    if not req.contacts or len(req.contacts) == 0:
        raise HTTPException(400, "Empty contacts list")

    success = 0
    failed = 0
    errors = []
    imported_ids = []

    async with _pool.acquire() as conn:
        await _ensure_whatsapp_tables(conn)

        for idx, contact in enumerate(req.contacts):
            try:
                phone = _validate_phone_number(contact.get('phone') or contact.get('phone_number'))
                name = contact.get('name', '')

                # Skip duplicates
                existing = await conn.fetchrow(
                    "SELECT id FROM whatsapp_contacts WHERE phone_number = $1", phone
                )
                if existing:
                    errors.append({
                        "row": idx,
                        "phone": phone,
                        "error": "duplicate"
                    })
                    failed += 1
                    continue

                # Insert
                contact_id = await conn.fetchval("""
                    INSERT INTO whatsapp_contacts
                    (phone_number, name, contact_source, invitation_status)
                    VALUES ($1, $2, $3, $4)
                    RETURNING id
                """, phone, name, "bulk_import", "pending")

                imported_ids.append(contact_id)
                success += 1

            except Exception as e:
                failed += 1
                errors.append({
                    "row": idx,
                    "phone": contact.get('phone', 'unknown'),
                    "error": str(e)[:50]
                })

        # Log bulk operation
        await _log_audit(conn, "whatsapp.contact.bulk_import", admin_id,
                       "whatsapp_contacts", f"batch_{len(imported_ids)}",
                       {"success": success, "failed": failed, "total": len(req.contacts)})

    return {
        "imported": len(req.contacts),
        "success": success,
        "failed": failed,
        "errors": errors[:10],  # Limit error details
        "created_ids": imported_ids
    }

# ============================================================
# ENDPOINT 3: Get All Contacts
# ============================================================

@router.get("/contacts")
async def whatsapp_get_contacts(
    limit: int = 100,
    offset: int = 0,
    status: Optional[str] = None,
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None),
):
    """Get paginated list of WhatsApp contacts."""
    admin_id = await _verify_admin_auth(authorization, x_admin_key)

    if limit > 1000:
        limit = 1000
    if offset > 100000:
        offset = 100000

    async with _pool.acquire() as conn:
        await _ensure_whatsapp_tables(conn)

        # Build query
        query = "SELECT * FROM whatsapp_contacts WHERE 1=1"
        params = []

        if status:
            params.append(status)
            query += f" AND invitation_status = ${len(params)}"

        params.append(limit)
        params.append(offset)
        query += f" ORDER BY created_at DESC LIMIT ${len(params)-1} OFFSET ${len(params)}"

        rows = await conn.fetch(query, *params)

        # Get total count
        count_query = "SELECT COUNT(*) as cnt FROM whatsapp_contacts WHERE 1=1"
        count_params = []
        if status:
            count_params.append(status)
            count_query += f" AND invitation_status = ${len(count_params)}"

        count_row = await conn.fetchrow(count_query, *count_params)
        total = count_row['cnt'] if count_row else 0

        return {
            "count": total,
            "limit": limit,
            "offset": offset,
            "contacts": [dict(r) for r in rows]
        }

# ============================================================
# ENDPOINT 4: Send Invite
# ============================================================

@router.post("/send-invite")
async def whatsapp_send_invite(
    req: SendInviteRequest,
    request: Request,
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None),
):
    """Send WhatsApp invite to a contact."""
    admin_id = await _verify_admin_auth(authorization, x_admin_key)

    # Validate phone
    try:
        phone = _validate_phone_number(req.phone_number)
    except ValueError as e:
        raise HTTPException(400, str(e))

    # Default messages
    messages = {
        "website": "ברוכים הבאים ל-SLH Spark! 🚀 בקרו בחזקות: https://slh-nft.com",
        "bot": "בואו להצטרף לבוט SLH שלנו ולהתחיל להשתמש בתוקנים: https://t.me/SLH_AIR_bot",
        "course": "קורס חדש זמין עכשיו! השתמשו בקוד SLH2026 להנחה:",
    }

    message_text = req.message or messages.get(req.invite_type, "ברוכים הבאים ל-SLH Spark!")

    twilio_message_id = None
    delivery_status = "pending"

    # Send via Twilio if available
    if TWILIO_AVAILABLE:
        twilio = _get_twilio_client()
        if twilio:
            try:
                twilio_phone = os.getenv('TWILIO_PHONE')
                msg = twilio.messages.create(
                    body=message_text,
                    from_=twilio_phone,
                    to=phone
                )
                twilio_message_id = msg.sid
                delivery_status = "sent"
            except Exception as e:
                logger.error(f"Twilio send failed: {e}")
                delivery_status = "failed"

    async with _pool.acquire() as conn:
        await _ensure_whatsapp_tables(conn)

        try:
            # Record in invites table
            invite_id = await conn.fetchval("""
                INSERT INTO whatsapp_invites
                (phone_number, invite_type, message_template, delivery_status, twilio_message_id)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """, phone, req.invite_type, message_text, delivery_status, twilio_message_id)

            # Update contact status
            await conn.execute("""
                UPDATE whatsapp_contacts
                SET invitation_status = $1, invited_at = NOW(), updated_at = NOW()
                WHERE phone_number = $2
            """, "invited", phone)

            # Audit log
            await _log_audit(conn, "whatsapp.invite.send", admin_id,
                           "whatsapp_invite", str(invite_id),
                           {"phone": phone, "type": req.invite_type, "status": delivery_status})

            return {
                "message_id": twilio_message_id or f"local_{invite_id}",
                "status": delivery_status,
                "timestamp": datetime.utcnow().isoformat(),
                "phone": phone
            }
        except Exception as e:
            logger.error(f"Failed to send invite: {e}")
            raise HTTPException(500, f"Error: {str(e)[:100]}")

# ============================================================
# ENDPOINT 5: Mark as Fraud
# ============================================================

@router.post("/mark-fraud")
async def whatsapp_mark_fraud(
    req: MarkFraudRequest,
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None),
):
    """Mark phone number as fraud and apply ZUZ penalty."""
    admin_id = await _verify_admin_auth(authorization, x_admin_key)

    # Validate phone
    try:
        phone = _validate_phone_number(req.phone_number)
    except ValueError as e:
        raise HTTPException(400, str(e))

    # Validate severity
    if not 1 <= req.severity <= 10:
        raise HTTPException(400, "Severity must be 1-10")

    if req.fraud_type not in ['spam', 'scam', 'identity_theft', 'other']:
        raise HTTPException(400, "Invalid fraud_type")

    zuz_penalty = 5  # Default penalty

    async with _pool.acquire() as conn:
        await _ensure_whatsapp_tables(conn)

        try:
            async with conn.transaction():
                # Insert/update fraud flag
                fraud_id = await conn.fetchval("""
                    INSERT INTO fraud_flags_whatsapp
                    (phone_number, fraud_type, severity, zuz_penalty, proof_url, flagged_by)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (phone_number, fraud_type)
                    DO UPDATE SET
                        severity = GREATEST(EXCLUDED.severity, fraud_flags_whatsapp.severity),
                        updated_at = NOW()
                    RETURNING id
                """, phone, req.fraud_type, req.severity, zuz_penalty, req.proof_url, admin_id)

                # Find user by phone and apply ZUZ penalty
                contact = await conn.fetchrow(
                    "SELECT user_id FROM whatsapp_contacts WHERE phone_number = $1",
                    phone
                )

                if contact and contact['user_id']:
                    user_id = contact['user_id']
                    # Apply ZUZ penalty
                    await conn.execute("""
                        INSERT INTO token_balances (user_id, token, balance)
                        VALUES ($1, 'ZUZ', $2)
                        ON CONFLICT (user_id, token)
                        DO UPDATE SET balance = balance + EXCLUDED.balance, updated_at = NOW()
                    """, user_id, zuz_penalty)

                # Audit log
                await _log_audit(conn, "whatsapp.fraud.mark", admin_id,
                               "fraud_flags_whatsapp", str(fraud_id),
                               {"phone": phone, "type": req.fraud_type,
                                "severity": req.severity, "zuz_penalty": zuz_penalty,
                                "user_id": contact['user_id'] if contact else None})

            return {
                "phone_number": phone,
                "fraud_type": req.fraud_type,
                "severity": req.severity,
                "zuz_penalty": zuz_penalty,
                "status": "flagged"
            }
        except Exception as e:
            logger.error(f"Failed to mark fraud: {e}")
            raise HTTPException(500, f"Error: {str(e)[:100]}")

# ============================================================
# ENDPOINT 6: Broadcast Message
# ============================================================

@router.post("/broadcast-message")
async def whatsapp_broadcast_message(
    req: BroadcastMessageRequest,
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None),
):
    """Broadcast message to contact segment."""
    admin_id = await _verify_admin_auth(authorization, x_admin_key)

    if len(req.message) < 5:
        raise HTTPException(400, "Message too short")

    if req.target_segment not in ['all', 'interested', 'not_invited', 'custom']:
        raise HTTPException(400, "Invalid target_segment")

    async with _pool.acquire() as conn:
        await _ensure_whatsapp_tables(conn)

        try:
            async with conn.transaction():
                # Get target contacts
                if req.target_segment == 'all':
                    contacts = await conn.fetch(
                        "SELECT phone_number FROM whatsapp_contacts WHERE invitation_status IN ('pending', 'invited')"
                    )
                elif req.target_segment == 'interested':
                    contacts = await conn.fetch(
                        "SELECT phone_number FROM whatsapp_contacts WHERE invitation_status = 'invited'"
                    )
                elif req.target_segment == 'not_invited':
                    contacts = await conn.fetch(
                        "SELECT phone_number FROM whatsapp_contacts WHERE invitation_status = 'pending'"
                    )
                else:
                    contacts = []

                successfully_sent = 0
                failed_count = 0

                # Send via Twilio
                if TWILIO_AVAILABLE:
                    twilio = _get_twilio_client()
                    if twilio:
                        twilio_phone = os.getenv('TWILIO_PHONE')
                        for contact in contacts:
                            try:
                                msg = twilio.messages.create(
                                    body=req.message,
                                    from_=twilio_phone,
                                    to=contact['phone_number']
                                )
                                successfully_sent += 1
                            except Exception as e:
                                logger.error(f"Broadcast send failed to {contact['phone_number']}: {e}")
                                failed_count += 1

                # Record broadcast
                broadcast_id = await conn.fetchval("""
                    INSERT INTO whatsapp_broadcast
                    (broadcast_title, message, target_segment, sent_at,
                     total_recipients, successfully_sent, failed_count, created_by)
                    VALUES ($1, $2, $3, NOW(), $4, $5, $6, $7)
                    RETURNING id
                """, req.title, req.message, req.target_segment,
                len(contacts), successfully_sent, failed_count, admin_id)

                # Audit log
                await _log_audit(conn, "whatsapp.broadcast.send", admin_id,
                               "whatsapp_broadcast", str(broadcast_id),
                               {"title": req.title, "segment": req.target_segment,
                                "recipients": len(contacts), "sent": successfully_sent})

                return {
                    "broadcast_id": broadcast_id,
                    "total_recipients": len(contacts),
                    "successfully_sent": successfully_sent,
                    "failed": failed_count,
                    "status": "sent"
                }
        except Exception as e:
            logger.error(f"Failed to broadcast: {e}")
            raise HTTPException(500, f"Error: {str(e)[:100]}")
