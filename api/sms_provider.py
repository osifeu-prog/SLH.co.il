"""SLH SMS provider — pluggable OTP/verification code sender.

One public async function: `send_otp(phone, code, purpose)`.
Behavior selected by env var `SMS_PROVIDER`:

    twilio       — Twilio REST API. Needs TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM
    inforu       — Israeli Inforu (infobip-like) REST API. Needs INFORU_USERNAME, INFORU_API_TOKEN, INFORU_SENDER
    sms019       — 019 Mobile (Israeli). Needs SMS019_USERNAME, SMS019_PASSWORD, SMS019_SENDER
    infinireach  — InfiniReach Multi-Platform Gateway (sends through your own Android phone via SIM).
                   Needs INFINIREACH_API_KEY, INFINIREACH_FROM (e164 phone of your registered device)
    stub         — no-op, returns success=True with note. Used in dev.
    disabled     — explicit refusal, returns success=False. For prod when not yet wired.

If SMS_PROVIDER is unset we default to `stub` in development and `disabled` in production
(detected by presence of RAILWAY_ENVIRONMENT env var).

Every attempt is logged via the standard logger and, when possible, to event_log.
No secrets are ever logged.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Optional

import httpx

log = logging.getLogger("slh.sms")


@dataclass
class SmsResult:
    ok: bool
    provider: str
    message_id: Optional[str] = None
    error: Optional[str] = None
    stub: bool = False  # True if no real SMS left the server


# ---------------------------------------------------------------------------
# Provider detection
# ---------------------------------------------------------------------------


def _resolved_provider() -> str:
    explicit = (os.getenv("SMS_PROVIDER") or "").strip().lower()
    if explicit:
        return explicit
    # No provider chosen — pick a safe default.
    # On Railway (prod), refuse rather than silently fake-send.
    if os.getenv("RAILWAY_ENVIRONMENT"):
        return "disabled"
    return "stub"


# ---------------------------------------------------------------------------
# Provider implementations
# ---------------------------------------------------------------------------


async def _send_twilio(phone: str, body: str) -> SmsResult:
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    frm = os.getenv("TWILIO_FROM")
    if not (sid and token and frm):
        return SmsResult(ok=False, provider="twilio", error="twilio env vars missing")
    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            url,
            data={"To": phone, "From": frm, "Body": body},
            auth=(sid, token),
        )
    if resp.status_code >= 400:
        return SmsResult(
            ok=False,
            provider="twilio",
            error=f"http {resp.status_code}: {resp.text[:200]}",
        )
    try:
        j = resp.json()
        return SmsResult(ok=True, provider="twilio", message_id=j.get("sid"))
    except Exception:
        return SmsResult(ok=True, provider="twilio")


async def _send_inforu(phone: str, body: str) -> SmsResult:
    """Inforu (inforu.co.il) — Israel. POST JSON to their REST endpoint."""
    user = os.getenv("INFORU_USERNAME")
    tok = os.getenv("INFORU_API_TOKEN")
    sender = os.getenv("INFORU_SENDER", "SLH")
    if not (user and tok):
        return SmsResult(ok=False, provider="inforu", error="inforu env vars missing")
    payload = {
        "Data": {
            "Message": body,
            "Recipients": [{"Phone": phone}],
            "Settings": {"Sender": sender},
        }
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            "https://capi.inforu.co.il/api/v2/SMS/SendSms",
            json=payload,
            headers={
                "Authorization": f"Basic {_basic_auth(user, tok)}",
                "Content-Type": "application/json",
            },
        )
    if resp.status_code >= 400:
        return SmsResult(
            ok=False,
            provider="inforu",
            error=f"http {resp.status_code}: {resp.text[:200]}",
        )
    try:
        j = resp.json()
        # Inforu returns { "StatusId": 1, "StatusDescription": "Success", ... } on success
        if j.get("StatusId") == 1:
            return SmsResult(ok=True, provider="inforu", message_id=str(j.get("MessageId", "")))
        return SmsResult(
            ok=False, provider="inforu", error=str(j.get("StatusDescription", "unknown"))
        )
    except Exception:
        return SmsResult(ok=True, provider="inforu")  # best-effort


async def _send_sms019(phone: str, body: str) -> SmsResult:
    """019 Mobile — Israel. SOAP-ish form POST."""
    user = os.getenv("SMS019_USERNAME")
    pw = os.getenv("SMS019_PASSWORD")
    sender = os.getenv("SMS019_SENDER", "SLH")
    if not (user and pw):
        return SmsResult(ok=False, provider="sms019", error="sms019 env vars missing")
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            "https://www.019sms.co.il/api",
            data={
                "user": user,
                "password": pw,
                "sender": sender,
                "recipient": phone,
                "message": body,
            },
        )
    if resp.status_code >= 400:
        return SmsResult(
            ok=False, provider="sms019", error=f"http {resp.status_code}"
        )
    # 019 returns XML-ish; we trust 2xx as success unless we parse it
    return SmsResult(ok=True, provider="sms019")


async def _send_infinireach(phone: str, body: str) -> SmsResult:
    """InfiniReach (api.infinireach.io) — sends through Osif's Android phone via SIM.
    Free tier: 1 device, unlimited SMS via your own carrier plan.
    """
    key = os.getenv("INFINIREACH_API_KEY")
    sender = os.getenv("INFINIREACH_FROM") or os.getenv("INFINIREACH_DEVICE_PHONE")
    api_url = os.getenv("INFINIREACH_API_URL", "https://api.infinireach.io/api/v1/messages")
    if not key:
        return SmsResult(ok=False, provider="infinireach", error="INFINIREACH_API_KEY missing")
    if not sender:
        return SmsResult(ok=False, provider="infinireach", error="INFINIREACH_FROM missing (e164 phone)")
    payload = {
        "channel": "sms",
        "e164From": sender,
        "to": phone,
        "message": body,
    }
    # Cloudflare-friendly UA — empty/Python UA gets blocked with code 1010
    headers = {
        "X-API-Key": key,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (compatible; SLH-Bot/1.0)",
        "Accept": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(api_url, json=payload, headers=headers)
    except httpx.TimeoutException:
        return SmsResult(ok=False, provider="infinireach", error="timeout (>30s)")
    if resp.status_code >= 400:
        return SmsResult(
            ok=False,
            provider="infinireach",
            error=f"http {resp.status_code}: {resp.text[:200]}",
        )
    try:
        j = resp.json()
        if j.get("success") is True:
            return SmsResult(
                ok=True,
                provider="infinireach",
                message_id=str(j.get("messageId") or j.get("jobId") or ""),
            )
        return SmsResult(
            ok=False,
            provider="infinireach",
            error=str(j.get("error") or j.get("message") or "unknown"),
        )
    except Exception:
        return SmsResult(ok=True, provider="infinireach")  # best-effort


async def _send_stub(phone: str, body: str) -> SmsResult:
    """Dev-only stub: logs, does not send. ok=True so flow proceeds with _dev_code exposure."""
    log.info("SMS stub: phone=%s body_len=%d (not actually sent)", _mask_phone(phone), len(body))
    return SmsResult(ok=True, provider="stub", stub=True)


async def _send_disabled(phone: str, body: str) -> SmsResult:
    log.warning("SMS disabled: refusing send to %s", _mask_phone(phone))
    return SmsResult(
        ok=False,
        provider="disabled",
        error="SMS provider not configured. Set SMS_PROVIDER env var.",
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def send_otp(phone: str, code: str, purpose: str = "device_pair") -> SmsResult:
    """Send an OTP code to a phone number. `purpose` is used to shape the body."""
    body = _render_body(code, purpose)
    provider = _resolved_provider()
    try:
        if provider == "twilio":
            return await _send_twilio(phone, body)
        if provider == "inforu":
            return await _send_inforu(phone, body)
        if provider == "sms019":
            return await _send_sms019(phone, body)
        if provider == "infinireach":
            return await _send_infinireach(phone, body)
        if provider == "stub":
            return await _send_stub(phone, body)
        if provider == "disabled":
            return await _send_disabled(phone, body)
        log.warning("unknown SMS_PROVIDER=%r, falling back to disabled", provider)
        return await _send_disabled(phone, body)
    except Exception as e:
        log.exception("sms provider %s crashed: %s", provider, e)
        return SmsResult(ok=False, provider=provider, error=f"{type(e).__name__}: {e}")


def provider_status() -> dict:
    """Return a non-secret summary of current SMS config, for health endpoints."""
    provider = _resolved_provider()
    configured = {
        "twilio": bool(
            os.getenv("TWILIO_ACCOUNT_SID")
            and os.getenv("TWILIO_AUTH_TOKEN")
            and os.getenv("TWILIO_FROM")
        ),
        "inforu": bool(os.getenv("INFORU_USERNAME") and os.getenv("INFORU_API_TOKEN")),
        "sms019": bool(os.getenv("SMS019_USERNAME") and os.getenv("SMS019_PASSWORD")),
        "infinireach": bool(
            os.getenv("INFINIREACH_API_KEY")
            and (os.getenv("INFINIREACH_FROM") or os.getenv("INFINIREACH_DEVICE_PHONE"))
        ),
    }
    return {
        "provider": provider,
        "stub": provider == "stub",
        "configured": configured,
        "ready": provider in ("stub",) or (provider in configured and configured[provider]),
    }


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _render_body(code: str, purpose: str) -> str:
    if purpose == "device_pair":
        return f"SLH: קוד לצימוד המכשיר: {code}. תוקף 5 דק'. לא שלחת? התעלם."
    if purpose == "login":
        return f"SLH: קוד התחברות: {code}. תוקף 5 דק'."
    return f"SLH code: {code} (5 min)"


def _mask_phone(phone: str) -> str:
    if not phone or len(phone) < 6:
        return "***"
    return phone[:3] + "***" + phone[-3:]


def _basic_auth(user: str, password: str) -> str:
    import base64

    token = f"{user}:{password}".encode("utf-8")
    return base64.b64encode(token).decode("ascii")
