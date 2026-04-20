"""
Blockchain Verification Helpers — REAL public-API clients
==========================================================
Shared module used by routes/arkham_bridge.py (and any other router that needs
verified on-chain data) to replace the previous mock "Arkham Intelligence"
integration with actual queries against free, keyless public APIs.

Clients provided:
  - BscScanClient    -> BSC balances (native BNB + BEP-20 tokens)
  - GoPlusClient     -> GoPlus Security address risk screen (real "Arkham" replacement)
  - ChainabuseClient -> Community fraud reports
  - TonCenterClient  -> TON wallet verification

All clients are async (aiohttp), have a 10s default timeout, and degrade
gracefully on rate-limit / network / parse failure rather than raising into the
caller — on failure they return a dict with ``source`` set to a marker like
``"rate_limited"`` or ``"network_error"`` so the calling router can record that
"we tried, here's why we have no data" instead of returning fake numbers.

No API keys are required for baseline usage. BSCSCAN_API_KEY is optional and
only needed if the BSC public RPC rate limits become a problem.
"""
from __future__ import annotations

import os
import logging
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any

try:
    import aiohttp
except ImportError:  # aiohttp is expected in requirements.txt; guard anyway
    aiohttp = None  # type: ignore

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------
# Constants
# ---------------------------------------------------------------

DEFAULT_TIMEOUT_SECS = 10
DEFAULT_UA = "SLH-Spark/1.0 (+https://slh-nft.com) blockchain-verify"

# GoPlus chain IDs
GOPLUS_CHAIN_IDS = {
    "eth": "1",
    "ethereum": "1",
    "bsc": "56",
    "bnb": "56",
    "polygon": "137",
    "matic": "137",
    "arbitrum": "42161",
    "optimism": "10",
    "avalanche": "43114",
    "fantom": "250",
}

# SLH token (context for default balance probes on BSC)
SLH_CONTRACT_BSC = "0xACb0A09414CEA1C879c67bB7A877E4e19480f022"
SLH_DECIMALS = 15  # Non-standard — SLH uses 15, not the ERC-20 default 18


# ---------------------------------------------------------------
# Shared helper
# ---------------------------------------------------------------

async def _http_get_json(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout_secs: int = DEFAULT_TIMEOUT_SECS,
) -> Dict[str, Any]:
    """
    Perform a single GET request and return parsed JSON.

    On any failure returns a dict with a ``source`` key describing the reason:
      - rate_limited   (HTTP 429)
      - http_error     (non-2xx)
      - network_error  (ClientError / timeout)
      - parse_error    (body not JSON)
      - aiohttp_missing

    Never raises — callers can always safely inspect the returned dict.
    """
    if aiohttp is None:
        logger.error("aiohttp not available — cannot reach %s", url)
        return {"source": "aiohttp_missing", "data": None, "error": "aiohttp not installed"}

    merged_headers = {"User-Agent": DEFAULT_UA, "Accept": "application/json"}
    if headers:
        merged_headers.update(headers)

    timeout = aiohttp.ClientTimeout(total=timeout_secs)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params=params, headers=merged_headers) as resp:
                status = resp.status
                if status == 429:
                    logger.warning("Rate limited by %s", url)
                    return {"source": "rate_limited", "data": None, "http_status": 429}
                if status >= 400:
                    body = ""
                    try:
                        body = (await resp.text())[:200]
                    except Exception:
                        pass
                    logger.warning("HTTP %s from %s: %s", status, url, body)
                    return {"source": "http_error", "data": None, "http_status": status, "body": body}
                try:
                    return await resp.json(content_type=None)
                except Exception as e:  # noqa: BLE001 — JSON parse failure
                    logger.warning("Failed to parse JSON from %s: %s", url, e)
                    return {"source": "parse_error", "data": None, "error": str(e)}
    except asyncio.TimeoutError:
        logger.warning("Timeout calling %s", url)
        return {"source": "network_error", "data": None, "error": "timeout"}
    except Exception as e:  # noqa: BLE001
        logger.warning("Network error calling %s: %s", url, e)
        return {"source": "network_error", "data": None, "error": str(e)}


# ---------------------------------------------------------------
# BscScan (real balance lookups on BSC)
# ---------------------------------------------------------------

class BscScanClient:
    """
    Keyless BscScan client. The free module=account endpoints work without a
    key at about 5 req/sec; a key raises the ceiling and is read from the
    BSCSCAN_API_KEY env var if present.
    """

    BASE_URL = "https://api.bscscan.com/api"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("BSCSCAN_API_KEY")

    def _params(self, extra: Dict[str, Any]) -> Dict[str, Any]:
        params = dict(extra)
        if self.api_key:
            params["apikey"] = self.api_key
        return params

    async def get_native_balance(self, wallet: str) -> Dict[str, Any]:
        """Returns dict with bnb_wei (str) and bnb (float)."""
        params = self._params({
            "module": "account",
            "action": "balance",
            "address": wallet,
            "tag": "latest",
        })
        data = await _http_get_json(self.BASE_URL, params=params)
        if data.get("source") in {"rate_limited", "http_error", "network_error", "parse_error", "aiohttp_missing"}:
            return {"wallet_address": wallet, "chain": "bsc", "source": data.get("source"), "data": None}
        # BscScan wraps result in {status, message, result}
        if not isinstance(data, dict) or data.get("status") != "1":
            return {
                "wallet_address": wallet,
                "chain": "bsc",
                "source": "bscscan_error",
                "data": None,
                "error": str(data.get("message") or data.get("result"))[:200],
            }
        wei_str = str(data.get("result", "0"))
        try:
            bnb = int(wei_str) / 1e18
        except (ValueError, TypeError):
            bnb = 0.0
        return {
            "wallet_address": wallet,
            "chain": "bsc",
            "source": "bscscan",
            "bnb_wei": wei_str,
            "bnb": bnb,
            "checked_at": datetime.utcnow().isoformat(),
        }

    async def get_token_balance(self, wallet: str, contract: str, decimals: int = 18) -> Dict[str, Any]:
        """Returns raw and human-readable token balance for a BEP-20."""
        params = self._params({
            "module": "account",
            "action": "tokenbalance",
            "contractaddress": contract,
            "address": wallet,
            "tag": "latest",
        })
        data = await _http_get_json(self.BASE_URL, params=params)
        if data.get("source") in {"rate_limited", "http_error", "network_error", "parse_error", "aiohttp_missing"}:
            return {
                "wallet_address": wallet,
                "contract": contract,
                "chain": "bsc",
                "source": data.get("source"),
                "data": None,
            }
        if not isinstance(data, dict) or data.get("status") != "1":
            return {
                "wallet_address": wallet,
                "contract": contract,
                "chain": "bsc",
                "source": "bscscan_error",
                "data": None,
                "error": str(data.get("message") or data.get("result"))[:200],
            }
        raw = str(data.get("result", "0"))
        try:
            human = int(raw) / (10 ** decimals)
        except (ValueError, TypeError):
            human = 0.0
        return {
            "wallet_address": wallet,
            "contract": contract,
            "chain": "bsc",
            "source": "bscscan",
            "balance_raw": raw,
            "balance": human,
            "decimals": decimals,
            "checked_at": datetime.utcnow().isoformat(),
        }


# ---------------------------------------------------------------
# GoPlus Security (real threat intelligence)
# ---------------------------------------------------------------

class GoPlusClient:
    """
    Free, keyless GoPlus Security address-risk API.

    Doc: https://docs.gopluslabs.io/reference/address-security-api
    Returns a rich dict of boolean-ish risk flags like:
      cybercrime, money_laundering, financial_crime, phishing_activities,
      blacklist_doubt, sanctioned, honeypot_related_address, fake_kyc, ...
    We combine these into a 0..100 threat_score + human category.
    """

    BASE_URL = "https://api.gopluslabs.io/api/v1/address_security"

    # Field -> weight in the composite threat score (sum ~=100 when everything is set)
    RISK_WEIGHTS = {
        "cybercrime": 25,
        "money_laundering": 20,
        "financial_crime": 15,
        "sanctioned": 20,
        "stealing_attack": 15,
        "phishing_activities": 15,
        "honeypot_related_address": 10,
        "blacklist_doubt": 10,
        "fake_kyc": 8,
        "malicious_mining_activities": 8,
        "darkweb_transactions": 10,
        "mixer": 5,
        "number_of_malicious_contracts_created": 0,  # numeric, handled separately
    }

    def __init__(self):
        self._base = self.BASE_URL

    @staticmethod
    def _resolve_chain_id(chain: str) -> str:
        if not chain:
            return "56"
        return GOPLUS_CHAIN_IDS.get(chain.lower(), chain)

    @staticmethod
    def _truthy(val: Any) -> bool:
        """GoPlus returns '1'/'0' strings, bools, ints — normalize."""
        if val is None:
            return False
        if isinstance(val, bool):
            return val
        if isinstance(val, (int, float)):
            return val != 0
        s = str(val).strip().lower()
        return s in {"1", "true", "yes"}

    async def check_address(self, wallet: str, chain: str = "bsc") -> Dict[str, Any]:
        """Query GoPlus for real address risk data on the given chain."""
        chain_id = self._resolve_chain_id(chain)
        url = f"{self._base}/{chain_id}"
        raw = await _http_get_json(url, params={"address": wallet})

        if raw.get("source") in {"rate_limited", "http_error", "network_error", "parse_error", "aiohttp_missing"}:
            return {
                "wallet_address": wallet,
                "chain": chain,
                "chain_id": chain_id,
                "source": raw.get("source"),
                "threat_score": 0.0,
                "threat_category": "unknown",
                "entity_tags": [],
                "raw_flags": {},
                "checked_at": datetime.utcnow().isoformat(),
                "error": raw.get("error") or raw.get("body"),
            }

        # GoPlus top-level: {"code":1, "message":"OK", "result":{...flags...}}
        result = raw.get("result") if isinstance(raw, dict) else None
        if raw.get("code") != 1 or not isinstance(result, dict):
            return {
                "wallet_address": wallet,
                "chain": chain,
                "chain_id": chain_id,
                "source": "goplus_error",
                "threat_score": 0.0,
                "threat_category": "unknown",
                "entity_tags": [],
                "raw_flags": {},
                "checked_at": datetime.utcnow().isoformat(),
                "error": str(raw.get("message"))[:200],
            }

        # Compute composite score
        score = 0.0
        tags: List[str] = []
        flags: Dict[str, Any] = {}
        for key, weight in self.RISK_WEIGHTS.items():
            val = result.get(key)
            flags[key] = val
            if key == "number_of_malicious_contracts_created":
                try:
                    n = int(val or 0)
                except (ValueError, TypeError):
                    n = 0
                if n > 0:
                    score += min(20.0, n * 2.0)
                    tags.append(f"malicious_contracts:{n}")
                continue
            if self._truthy(val):
                score += weight
                tags.append(key)

        score = max(0.0, min(100.0, score))

        if score >= 75:
            category = "blacklisted"
        elif score >= 50:
            category = "high_risk"
        elif score >= 25:
            category = "suspicious"
        elif score > 0:
            category = "low_risk"
        else:
            category = "clean"

        return {
            "wallet_address": wallet,
            "chain": chain,
            "chain_id": chain_id,
            "source": "goplus",
            "threat_score": round(score, 2),
            "threat_category": category,
            "entity_tags": tags,
            "raw_flags": flags,
            "data_source_url": f"{self._base}/{chain_id}?address={wallet}",
            "checked_at": datetime.utcnow().isoformat(),
        }


# ---------------------------------------------------------------
# Chainabuse (community fraud reports)
# ---------------------------------------------------------------

class ChainabuseClient:
    """
    Community-sourced scam / fraud reports.

    Chainabuse exposes a public reports endpoint; if it's unavailable or
    shape-shifts, we fail soft and return an empty list with an explanatory
    source marker rather than blowing up the caller.
    """

    BASE_URL = "https://api.chainabuse.com/v0/reports"

    async def get_reports(self, wallet: str, limit: int = 20) -> Dict[str, Any]:
        params = {"address": wallet, "limit": limit}
        raw = await _http_get_json(self.BASE_URL, params=params)

        if raw.get("source") in {"rate_limited", "http_error", "network_error", "parse_error", "aiohttp_missing"}:
            return {
                "wallet_address": wallet,
                "source": raw.get("source"),
                "reports": [],
                "count": 0,
                "checked_at": datetime.utcnow().isoformat(),
                "error": raw.get("error") or raw.get("body"),
            }

        # Response shape varies; handle both list-root and {"reports":[...]} variants.
        if isinstance(raw, list):
            items = raw
        elif isinstance(raw, dict) and isinstance(raw.get("reports"), list):
            items = raw["reports"]
        elif isinstance(raw, dict) and isinstance(raw.get("data"), list):
            items = raw["data"]
        else:
            items = []

        normalized = []
        for it in items[:limit]:
            if not isinstance(it, dict):
                continue
            normalized.append({
                "category": it.get("category") or it.get("scamCategory") or it.get("type"),
                "description": (it.get("description") or it.get("body") or "")[:500],
                "reported_at": it.get("createdAt") or it.get("reported_at"),
                "source": it.get("source") or "chainabuse",
            })

        return {
            "wallet_address": wallet,
            "source": "chainabuse",
            "reports": normalized,
            "count": len(normalized),
            "checked_at": datetime.utcnow().isoformat(),
        }


# ---------------------------------------------------------------
# TON Center
# ---------------------------------------------------------------

class TonCenterClient:
    """Free TON wallet info — used for TON address verification."""

    BASE_URL = "https://toncenter.com/api/v2/getAddressInformation"

    async def get_address_info(self, wallet: str) -> Dict[str, Any]:
        raw = await _http_get_json(self.BASE_URL, params={"address": wallet})
        if raw.get("source") in {"rate_limited", "http_error", "network_error", "parse_error", "aiohttp_missing"}:
            return {
                "wallet_address": wallet,
                "chain": "ton",
                "source": raw.get("source"),
                "data": None,
                "checked_at": datetime.utcnow().isoformat(),
            }
        if not isinstance(raw, dict) or not raw.get("ok"):
            return {
                "wallet_address": wallet,
                "chain": "ton",
                "source": "toncenter_error",
                "data": None,
                "checked_at": datetime.utcnow().isoformat(),
                "error": str(raw.get("error"))[:200] if isinstance(raw, dict) else None,
            }
        result = raw.get("result") or {}
        balance_nano = result.get("balance")
        try:
            balance_ton = int(balance_nano) / 1e9 if balance_nano is not None else None
        except (ValueError, TypeError):
            balance_ton = None
        return {
            "wallet_address": wallet,
            "chain": "ton",
            "source": "toncenter",
            "balance_nano": balance_nano,
            "balance_ton": balance_ton,
            "state": result.get("state"),
            "checked_at": datetime.utcnow().isoformat(),
        }


# ---------------------------------------------------------------
# Aggregate facade used by routers
# ---------------------------------------------------------------

class BlockchainThreatClient:
    """
    Thin façade that combines GoPlus + BscScan + Chainabuse into the shape the
    existing arkham_bridge router expects. Replaces the old mock ArkhamClient.
    """

    def __init__(self, bscscan_api_key: Optional[str] = None):
        self.bscscan = BscScanClient(api_key=bscscan_api_key)
        self.goplus = GoPlusClient()
        self.chainabuse = ChainabuseClient()
        self.ton = TonCenterClient()

    async def check_address(self, wallet: str, chain: str = "bsc") -> Dict[str, Any]:
        """
        Real threat data for a wallet. Keys returned match the previous mock
        contract (``wallet_address``, ``threat_score``, ``threat_category``,
        ``entity_tags``, ``last_checked``, ``source``) plus extras:
        ``chain``, ``chain_id``, ``raw_flags``, ``data_source_url``.
        """
        if not wallet or wallet == "unknown":
            return {
                "wallet_address": wallet,
                "chain": chain,
                "source": "no_wallet",
                "threat_score": 0.0,
                "threat_category": "unknown",
                "entity_tags": [],
                "last_checked": datetime.utcnow().isoformat(),
            }

        goplus_result = await self.goplus.check_address(wallet, chain=chain)
        # Preserve legacy key name `last_checked` for backward compat with the router.
        goplus_result["last_checked"] = goplus_result.get("checked_at")
        # Promote source to "goplus+bscscan" only when we also have balance data; for now
        # the router handles the balance fetch separately, so keep the source accurate.
        return goplus_result

    async def get_balance(
        self,
        wallet: str,
        chain: str = "bsc",
        token_contract: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Real balance lookup. On BSC, optionally includes SLH (default) or any BEP-20."""
        chain_norm = (chain or "bsc").lower()
        if chain_norm in {"ton"}:
            return await self.ton.get_address_info(wallet)
        if chain_norm in {"bsc", "bnb"}:
            native = await self.bscscan.get_native_balance(wallet)
            if token_contract:
                decimals = SLH_DECIMALS if token_contract.lower() == SLH_CONTRACT_BSC.lower() else 18
                token = await self.bscscan.get_token_balance(wallet, token_contract, decimals=decimals)
                native["token_balance"] = token
            return native
        return {
            "wallet_address": wallet,
            "chain": chain_norm,
            "source": "unsupported_chain",
            "data": None,
            "checked_at": datetime.utcnow().isoformat(),
        }

    async def get_community_reports(self, wallet: str) -> List[Dict[str, Any]]:
        """Flat list of community fraud reports for a wallet (Chainabuse)."""
        if not wallet:
            return []
        result = await self.chainabuse.get_reports(wallet)
        return result.get("reports") or []
