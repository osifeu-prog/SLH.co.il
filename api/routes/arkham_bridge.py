"""
Threat Intelligence Integration — Arkham Bridge + Community Fraud Detection
Decentralized fraud detection powered by Arkham Intelligence + community verification
"""
import os
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Header, Request

logger = logging.getLogger(__name__)

# Router
router = APIRouter(prefix="/api/threat", tags=["threat-intelligence"])

# Global connection pool (set by main.py)
_pool = None

def set_pool(pool):
    """Set the asyncpg pool for this module."""
    global _pool
    _pool = pool

# ============================================================
# MODELS
# ============================================================

class ThreatCheckRequest(BaseModel):
    """Query a wallet/phone/user for threat level"""
    phone_number: Optional[str] = None
    wallet_address: Optional[str] = None
    user_id: Optional[int] = None

class FraudReportRequest(BaseModel):
    """Submit a fraud report"""
    reporter_user_id: int
    target_phone: Optional[str] = None
    target_wallet: Optional[str] = None
    target_user_id: Optional[int] = None
    fraud_type: str  # 'scam', 'stolen_funds', 'sanctioned', 'identity_theft', 'other'
    severity: int  # 1-10
    evidence_description: str
    evidence_url: Optional[str] = None

class FraudVerificationRequest(BaseModel):
    """Admin verifies a fraud report"""
    report_id: int
    verified: bool
    verification_notes: str

# ============================================================
# DATABASE INITIALIZATION
# ============================================================

async def _ensure_threat_tables(conn):
    """Create all required threat intelligence tables."""

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS threat_intel_arkham (
            id BIGSERIAL PRIMARY KEY,
            wallet_address VARCHAR(255),
            phone_number VARCHAR(20),
            user_id BIGINT,
            threat_score FLOAT DEFAULT 0.0,
            threat_category VARCHAR(50),
            arkham_entity_tags TEXT[],
            arkham_last_checked TIMESTAMP,
            community_reports_count INT DEFAULT 0,
            community_verified_count INT DEFAULT 0,
            combined_threat_score FLOAT DEFAULT 0.0,
            is_flagged BOOLEAN DEFAULT FALSE,
            flag_reason VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_wallet ON threat_intel_arkham(wallet_address),
            INDEX idx_phone ON threat_intel_arkham(phone_number),
            INDEX idx_threat_score ON threat_intel_arkham(combined_threat_score DESC),
            INDEX idx_flagged ON threat_intel_arkham(is_flagged)
        );

        CREATE TABLE IF NOT EXISTS fraud_reports_community (
            id BIGSERIAL PRIMARY KEY,
            reporter_user_id BIGINT REFERENCES users(id),
            target_phone VARCHAR(20),
            target_wallet VARCHAR(255),
            target_user_id BIGINT REFERENCES users(id),
            fraud_type VARCHAR(50) NOT NULL,
            severity INT CHECK (severity >= 1 AND severity <= 10),
            evidence_description TEXT,
            evidence_url TEXT,
            status VARCHAR(50) DEFAULT 'submitted',  -- submitted, verified, confirmed, dismissed
            verification_count INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_reporter ON fraud_reports_community(reporter_user_id),
            INDEX idx_status ON fraud_reports_community(status),
            INDEX idx_created ON fraud_reports_community(created_at DESC)
        );

        CREATE TABLE IF NOT EXISTS fraud_verification_queue (
            id BIGSERIAL PRIMARY KEY,
            report_id BIGINT REFERENCES fraud_reports_community(id),
            verifier_user_id BIGINT REFERENCES users(id),
            verified BOOLEAN,
            verification_notes TEXT,
            verified_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_report ON fraud_verification_queue(report_id),
            INDEX idx_verifier ON fraud_verification_queue(verifier_user_id)
        );

        CREATE TABLE IF NOT EXISTS fraud_community_reputation (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES users(id) NOT NULL,
            accurate_reports INT DEFAULT 0,
            total_reports INT DEFAULT 0,
            accuracy_score FLOAT DEFAULT 0.0,
            reputation_level VARCHAR(50) DEFAULT 'novice',  -- novice, contributor, investigator, expert
            rep_tokens_earned FLOAT DEFAULT 0.0,
            badges TEXT[],
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id),
            INDEX idx_accuracy ON fraud_community_reputation(accuracy_score DESC)
        );

        CREATE TABLE IF NOT EXISTS fraud_network_connections (
            id BIGSERIAL PRIMARY KEY,
            source_phone VARCHAR(20),
            source_wallet VARCHAR(255),
            source_user_id BIGINT,
            target_phone VARCHAR(20),
            target_wallet VARCHAR(255),
            target_user_id BIGINT,
            connection_type VARCHAR(50),  -- 'accomplice', 'victim', 'associated', 'suspicious'
            confidence FLOAT DEFAULT 0.5,
            evidence_count INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_source_phone ON fraud_network_connections(source_phone),
            INDEX idx_target_phone ON fraud_network_connections(target_phone),
            INDEX idx_source_user ON fraud_network_connections(source_user_id),
            INDEX idx_target_user ON fraud_network_connections(target_user_id)
        );
    """)

async def init_threat_tables():
    """Call from main.py startup"""
    if _pool:
        async with _pool.acquire() as conn:
            await _ensure_threat_tables(conn)

# ============================================================
# ARKHAM MOCK/REAL INTEGRATION
# ============================================================

class ArkhamClient:
    """Mock Arkham Intelligence client — swap for real API when credentials available"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ARKHAM_API_KEY")
        self.use_mock = not self.api_key
        self.base_url = "https://intel.arkm.com/api/v1"

    async def check_wallet_threat(self, wallet_address: str) -> Dict:
        """Query threat level for a wallet address"""

        if self.use_mock:
            # Mock implementation — returns realistic threat scores
            return self._mock_wallet_threat(wallet_address)
        else:
            # Real Arkham API call (when credentials available)
            return await self._real_wallet_threat(wallet_address)

    def _mock_wallet_threat(self, wallet: str) -> Dict:
        """Mock Arkham response"""
        # Simple deterministic mock based on wallet address hash
        hash_val = hash(wallet) % 100

        threat_score = (hash_val / 100) * 100  # 0-100

        threat_categories = {
            0: "clean",
            25: "suspicious",
            50: "high_risk",
            75: "sanctioned",
            100: "blacklisted"
        }

        entity_tags = []
        if threat_score > 50:
            entity_tags.append("fraud_associated")
        if threat_score > 70:
            entity_tags.append("sanctioned_region")
        if threat_score > 85:
            entity_tags.append("stolen_funds")

        return {
            "wallet_address": wallet,
            "threat_score": threat_score,
            "threat_category": threat_categories.get(int(threat_score / 25) * 25, "unknown"),
            "entity_tags": entity_tags,
            "last_checked": datetime.utcnow().isoformat(),
            "source": "mock"  # Indicates this is mock data
        }

    async def _real_wallet_threat(self, wallet: str) -> Dict:
        """Real Arkham API (placeholder — implement when credentials available)"""
        # TODO: Implement real Arkham API call
        # import aiohttp
        # async with aiohttp.ClientSession() as session:
        #     headers = {"Authorization": f"Bearer {self.api_key}"}
        #     url = f"{self.base_url}/entity/{wallet}"
        #     async with session.get(url, headers=headers) as resp:
        #         return await resp.json()
        return self._mock_wallet_threat(wallet)

arkham = ArkhamClient()

# ============================================================
# API ENDPOINTS
# ============================================================

@router.get("/check-score")
async def check_threat_score(request: Request, x_admin_key: Optional[str] = Header(None)):
    """
    Check threat level for wallet/phone/user
    Returns: combined threat score (Arkham + community reports)
    """
    if not _pool:
        raise HTTPException(status_code=500, detail="Database not initialized")

    query = request.query_params
    wallet = query.get("wallet")
    phone = query.get("phone")
    user_id = query.get("user_id")

    if not (wallet or phone or user_id):
        raise HTTPException(status_code=400, detail="Provide wallet, phone, or user_id")

    try:
        async with _pool.acquire() as conn:
            # Check if already cached
            if wallet:
                row = await conn.fetchrow(
                    "SELECT * FROM threat_intel_arkham WHERE wallet_address = $1 LIMIT 1",
                    wallet
                )
            elif phone:
                row = await conn.fetchrow(
                    "SELECT * FROM threat_intel_arkham WHERE phone_number = $1 LIMIT 1",
                    phone
                )
            else:
                row = await conn.fetchrow(
                    "SELECT * FROM threat_intel_arkham WHERE user_id = $1 LIMIT 1",
                    int(user_id)
                )

            if row:
                return {
                    "id": row["id"],
                    "wallet_address": row["wallet_address"],
                    "phone_number": row["phone_number"],
                    "user_id": row["user_id"],
                    "arkham_threat_score": row["threat_score"],
                    "community_reports": row["community_reports_count"],
                    "verified_reports": row["community_verified_count"],
                    "combined_threat_score": row["combined_threat_score"],
                    "is_flagged": row["is_flagged"],
                    "flag_reason": row["flag_reason"],
                    "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None
                }

            # Not cached — check Arkham
            arkham_result = await arkham.check_wallet_threat(wallet or "unknown")

            # Create new record
            threat_score = arkham_result.get("threat_score", 0)
            new_row = await conn.fetchrow(
                """
                INSERT INTO threat_intel_arkham (wallet_address, phone_number, user_id,
                    threat_score, threat_category, arkham_entity_tags, combined_threat_score)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING *
                """,
                wallet,
                phone,
                int(user_id) if user_id else None,
                threat_score,
                arkham_result.get("threat_category"),
                arkham_result.get("entity_tags"),
                threat_score
            )

            return {
                "id": new_row["id"],
                "wallet_address": new_row["wallet_address"],
                "phone_number": new_row["phone_number"],
                "user_id": new_row["user_id"],
                "arkham_threat_score": new_row["threat_score"],
                "community_reports": 0,
                "verified_reports": 0,
                "combined_threat_score": new_row["combined_threat_score"],
                "is_flagged": False,
                "updated_at": new_row["updated_at"].isoformat()
            }

    except Exception as e:
        logger.error(f"Error checking threat score: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/report-fraud")
async def submit_fraud_report(req: FraudReportRequest, x_admin_key: Optional[str] = Header(None)):
    """
    Community member submits fraud report
    Creates entry in fraud_reports_community for verification
    """
    if not _pool:
        raise HTTPException(status_code=500, detail="Database not initialized")

    try:
        async with _pool.acquire() as conn:
            # Insert report
            report = await conn.fetchrow(
                """
                INSERT INTO fraud_reports_community
                (reporter_user_id, target_phone, target_wallet, target_user_id,
                 fraud_type, severity, evidence_description, evidence_url, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'submitted')
                RETURNING *
                """,
                req.reporter_user_id,
                req.target_phone,
                req.target_wallet,
                req.target_user_id,
                req.fraud_type,
                req.severity,
                req.evidence_description,
                req.evidence_url
            )

            # Initialize reporter reputation if needed
            await conn.execute(
                """
                INSERT INTO fraud_community_reputation (user_id, total_reports, accuracy_score)
                VALUES ($1, 1, 0.5)
                ON CONFLICT (user_id) DO UPDATE SET total_reports = total_reports + 1
                """,
                req.reporter_user_id
            )

            # Log audit
            await conn.execute(
                """
                INSERT INTO integration_audit_log
                (system, action, action_type, target_id, target_type, user_id, details, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                "threat_intel",
                "Submit fraud report",
                "create",
                report["id"],
                "fraud_report",
                req.reporter_user_id,
                json.dumps({
                    "fraud_type": req.fraud_type,
                    "severity": req.severity,
                    "target_phone": req.target_phone,
                    "target_wallet": req.target_wallet
                }),
                "success"
            )

            return {
                "status": "success",
                "report_id": report["id"],
                "message": "Report submitted for community verification",
                "created_at": report["created_at"].isoformat()
            }

    except Exception as e:
        logger.error(f"Error submitting fraud report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify-report")
async def verify_fraud_report(req: FraudVerificationRequest, x_admin_key: Optional[str] = Header(None)):
    """
    Admin verifies a fraud report
    Updates report status and reporter reputation
    """
    if not _pool:
        raise HTTPException(status_code=500, detail="Database not initialized")

    try:
        async with _pool.acquire() as conn:
            # Get original report
            report = await conn.fetchrow(
                "SELECT * FROM fraud_reports_community WHERE id = $1",
                req.report_id
            )

            if not report:
                raise HTTPException(status_code=404, detail="Report not found")

            # Update verification
            verification = await conn.fetchrow(
                """
                INSERT INTO fraud_verification_queue
                (report_id, verified, verification_notes, verified_at)
                VALUES ($1, $2, $3, NOW())
                RETURNING *
                """,
                req.report_id,
                req.verified,
                req.verification_notes
            )

            # Update report status
            new_status = "confirmed" if req.verified else "dismissed"
            await conn.execute(
                """
                UPDATE fraud_reports_community
                SET status = $1, verification_count = verification_count + 1, updated_at = NOW()
                WHERE id = $2
                """,
                new_status,
                req.report_id
            )

            # Update reporter reputation
            if req.verified:
                await conn.execute(
                    """
                    UPDATE fraud_community_reputation
                    SET accurate_reports = accurate_reports + 1,
                        accuracy_score = (accurate_reports::float + 1) / total_reports,
                        rep_tokens_earned = rep_tokens_earned + 5.0
                    WHERE user_id = $1
                    """,
                    report["reporter_user_id"]
                )

            return {
                "status": "success",
                "report_id": req.report_id,
                "verified": req.verified,
                "new_status": new_status,
                "message": f"Report {'confirmed' if req.verified else 'dismissed'}"
            }

    except Exception as e:
        logger.error(f"Error verifying report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leaderboard")
async def get_fraud_detective_leaderboard(limit: int = 10, x_admin_key: Optional[str] = Header(None)):
    """
    Get leaderboard of best fraud detectives
    Ranked by accuracy score and verified reports
    """
    if not _pool:
        raise HTTPException(status_code=500, detail="Database not initialized")

    try:
        async with _pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT u.id, u.username, r.accurate_reports, r.total_reports,
                       r.accuracy_score, r.reputation_level, r.rep_tokens_earned
                FROM fraud_community_reputation r
                JOIN users u ON r.user_id = u.id
                WHERE r.total_reports > 0
                ORDER BY r.accuracy_score DESC, r.accurate_reports DESC
                LIMIT $1
                """,
                limit
            )

            return {
                "status": "success",
                "count": len(rows),
                "leaderboard": [
                    {
                        "rank": i + 1,
                        "user_id": row["id"],
                        "username": row["username"],
                        "accurate_reports": row["accurate_reports"],
                        "total_reports": row["total_reports"],
                        "accuracy_score": row["accuracy_score"],
                        "reputation_level": row["reputation_level"],
                        "rep_tokens_earned": row["rep_tokens_earned"]
                    }
                    for i, row in enumerate(rows)
                ]
            }

    except Exception as e:
        logger.error(f"Error fetching leaderboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/network")
async def get_fraud_network(phone: Optional[str] = None, wallet: Optional[str] = None,
                           user_id: Optional[int] = None, x_admin_key: Optional[str] = Header(None)):
    """
    Get network graph of fraud connections
    Shows relationships between suspicious entities
    """
    if not _pool:
        raise HTTPException(status_code=500, detail="Database not initialized")

    if not (phone or wallet or user_id):
        raise HTTPException(status_code=400, detail="Provide phone, wallet, or user_id")

    try:
        async with _pool.acquire() as conn:
            # Find direct connections
            if phone:
                rows = await conn.fetch(
                    """
                    SELECT * FROM fraud_network_connections
                    WHERE source_phone = $1 OR target_phone = $1
                    ORDER BY confidence DESC
                    """,
                    phone
                )
            elif wallet:
                rows = await conn.fetch(
                    """
                    SELECT * FROM fraud_network_connections
                    WHERE source_wallet = $1 OR target_wallet = $1
                    ORDER BY confidence DESC
                    """,
                    wallet
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT * FROM fraud_network_connections
                    WHERE source_user_id = $1 OR target_user_id = $1
                    ORDER BY confidence DESC
                    """,
                    user_id
                )

            return {
                "status": "success",
                "query": {"phone": phone, "wallet": wallet, "user_id": user_id},
                "connections_count": len(rows),
                "connections": [
                    {
                        "id": row["id"],
                        "source_phone": row["source_phone"],
                        "target_phone": row["target_phone"],
                        "source_wallet": row["source_wallet"],
                        "target_wallet": row["target_wallet"],
                        "connection_type": row["connection_type"],
                        "confidence": row["confidence"],
                        "evidence_count": row["evidence_count"]
                    }
                    for row in rows
                ]
            }

    except Exception as e:
        logger.error(f"Error fetching network: {e}")
        raise HTTPException(status_code=500, detail=str(e))
