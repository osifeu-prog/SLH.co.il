[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$ErrorActionPreference = "Stop"

# =========================
# CONFIG
# =========================
$Root = "D:\SLH_ECOSYSTEM"
$BotDir = Join-Path $Root "nfty-bot"
$DockerfilesDir = Join-Path $Root "dockerfiles"
$ComposePath = Join-Path $Root "docker-compose.yml"
$EnvPath = Join-Path $Root ".env"
$DockerfilePath = Join-Path $DockerfilesDir "Dockerfile.nfty"
$MainPyPath = Join-Path $BotDir "main.py"
$Ts = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupDir = Join-Path $Root "backups\$Ts"

# Ã—â€Ã—â€ºÃ—Â Ã—Â¡ Ã—â€ºÃ—ÂÃ—Å¸ Ã—ËœÃ—â€¢Ã—Â§Ã—Å¸ Ã—â€”Ã—â€œÃ—Â© Ã—Å¾Ã—â€˜Ã—â€¢Ã—ËœÃ—Â¤Ã—ÂÃ—â€œÃ—Â¨ Ã—Å“Ã—Â¤Ã—Â Ã—â„¢ Ã—â€Ã—Â¨Ã—Â¦Ã—â€
$FreshToken = "8478252455:AAHDZAYvVbuHxyfNyLQ1XIMO6DrQi6zohMA"

function Info($m) { Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Ok($m)   { Write-Host "[ OK ] $m" -ForegroundColor Green }
function Warn($m) { Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Err($m)  { Write-Host "[ERR ] $m" -ForegroundColor Red }

function Ensure-Dir([string]$Path) {
    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Force -Path $Path | Out-Null
        Ok "Created directory: $Path"
    } else {
        Info "Directory exists: $Path"
    }
}

function Write-Utf8NoBom {
    param(
        [Parameter(Mandatory=$true)][string]$Path,
        [Parameter(Mandatory=$true)][string]$Content
    )
    $enc = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $enc)
    Ok "Wrote file: $Path"
}

function Backup-File([string]$Path) {
    if (Test-Path $Path) {
        Ensure-Dir $BackupDir
        Copy-Item $Path (Join-Path $BackupDir ([System.IO.Path]::GetFileName($Path))) -Force
        Ok "Backed up: $Path"
    }
}

function Set-Or-Add-EnvVar {
    param(
        [string]$Path,
        [string]$Key,
        [string]$Value
    )

    if (-not (Test-Path $Path)) {
        New-Item -ItemType File -Force -Path $Path | Out-Null
    }

    $raw = Get-Content $Path -Raw -ErrorAction SilentlyContinue
    $pattern = "(?m)^$([regex]::Escape($Key))=.*$"

    if ($raw -match $pattern) {
        $raw = [regex]::Replace($raw, $pattern, "$Key=$Value")
    } else {
        if (-not [string]::IsNullOrWhiteSpace($raw) -and -not $raw.EndsWith("`n")) {
            $raw += "`r`n"
        }
        $raw += "$Key=$Value`r`n"
    }

    Write-Utf8NoBom -Path $Path -Content $raw
}

function Require-Command([string]$Name) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command not found: $Name"
    }
}

function Replace-Or-Append-NftyService {
    param(
        [string]$ComposeFile,
        [string]$ServiceYaml
    )

    if (-not (Test-Path $ComposeFile)) {
        throw "docker-compose.yml not found: $ComposeFile"
    }

    $raw = Get-Content $ComposeFile -Raw

    # Ã—Å¾Ã—Â Ã—Â¡Ã—â€ Ã—Å“Ã—â€Ã—â€”Ã—Å“Ã—â„¢Ã—Â£ service Ã—Â§Ã—â„¢Ã—â„¢Ã—Â Ã—â€˜Ã—Â©Ã—Â nfty-bot
    $pattern = '(?ms)^  nfty-bot:\r?\n(?:^(?:    |\S).*\r?\n?)*?(?=^  [A-Za-z0-9_-]+:|\Z)'
    if ($raw -match $pattern) {
        $updated = [regex]::Replace($raw, $pattern, $ServiceYaml + "`r`n")
        Write-Utf8NoBom -Path $ComposeFile -Content $updated
        Ok "Replaced existing nfty-bot service"
        return
    }

    # Ã—ÂÃ—Â Ã—ÂÃ—â„¢Ã—Å¸ service Ã—â€ºÃ—â€“Ã—â€, Ã—Å¾Ã—â€¢Ã—Â¡Ã—â„¢Ã—Â£ Ã—â€˜Ã—Â¡Ã—â€¢Ã—Â£
    $updated = $raw.TrimEnd() + "`r`n`r`n" + $ServiceYaml + "`r`n"
    Write-Utf8NoBom -Path $ComposeFile -Content $updated
    Ok "Appended nfty-bot service"
}

# =========================
# PRECHECKS
# =========================
Require-Command docker

if ($FreshToken -eq "PASTE_FRESH_TOKEN_HERE") {
    throw "Set a fresh bot token in `$FreshToken before running. The previous token is not valid."
}

Ensure-Dir $Root
Ensure-Dir $BotDir
Ensure-Dir $DockerfilesDir

if (-not (Test-Path $ComposePath)) {
    throw "Missing docker-compose.yml at $ComposePath"
}

Backup-File $ComposePath
Backup-File $EnvPath
Backup-File $MainPyPath
Backup-File $DockerfilePath

# =========================
# main.py (Marketplace + Companion)
# =========================
$MainPy = @'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

import aiohttp
import asyncpg
from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, Message, ReplyKeyboardMarkup

from slh_payments.ledger import transfer, get_balance, ensure_balance
from slh_payments.config import ADMIN_USER_ID, TON_WALLET

APP_NAME = "SLH NFT Marketplace | SPARK IND"
TAGLINE = "From Bits to Infinity"
ACTIVATION_FEE_ILS = Decimal("22.221")
ACTIVATION_FEE_TON = Decimal("1.5")
COINGECKO_BASE = os.getenv("COINGECKO_BASE_URL", "https://api.coingecko.com/api/v3")
BSC_TOKEN_CONTRACT = os.getenv("SLH_BSC_CONTRACT", "0xACb0A09414CEA1C879c67bB7A877E4e19480f022")
BOT_TOKEN = os.getenv("BOT_TOKEN") or os.getenv("NFTY_MADNESS_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:slh_secure_2026@postgres:5432/slh_main")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
log = logging.getLogger("nfty-bot")
router = Router()

class SellStates(StatesGroup):
    waiting_name = State()
    waiting_category = State()
    waiting_price = State()
    waiting_currency = State()
    waiting_description = State()
    waiting_media_url = State()

@dataclass
class AppContext:
    pool: asyncpg.Pool
    session: aiohttp.ClientSession

def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Ã°Å¸â€ºÂÃ¯Â¸Â Ã—Â¢Ã—â„¢Ã—â€¢Ã—Å¸ Ã—â€˜Ã—Å¾Ã—Â¨Ã—Â§Ã—Ëœ"), KeyboardButton(text="Ã°Å¸â€™Â¼ Ã—â€Ã—ÂÃ—Â¨Ã—Â Ã—Â§ Ã—Â©Ã—Å“Ã—â„¢")],
            [KeyboardButton(text="Ã°Å¸â€œÂ¦ Ã—â€Ã—Â¤Ã—Â¨Ã—â„¢Ã—ËœÃ—â„¢Ã—Â Ã—Â©Ã—Å“Ã—â„¢"), KeyboardButton(text="Ã°Å¸ÂÂ·Ã¯Â¸Â Ã—â€Ã—Å¾Ã—â€ºÃ—â„¢Ã—Â¨Ã—â€¢Ã—Âª Ã—Â©Ã—Å“Ã—â„¢")],
            [KeyboardButton(text="Ã¢Å¾â€¢ Ã—Å“Ã—Å¾Ã—â€ºÃ—â„¢Ã—Â¨Ã—â€"), KeyboardButton(text="Ã°Å¸ÂÂ£ Ã—â€Ã—â€”Ã—â€˜Ã—Â¨ Ã—Â©Ã—Å“Ã—â„¢")],
            [KeyboardButton(text="Ã°Å¸ÂÅ½ Ã—â€Ã—ÂÃ—â€ºÃ—Å“"), KeyboardButton(text="Ã°Å¸Å½Â® Ã—Â©Ã—â€”Ã—Â§")],
            [KeyboardButton(text="Ã°Å¸â€œÅ¡ Ã—Å“Ã—Å¾Ã—â€œ"), KeyboardButton(text="Ã°Å¸ËœÂ´ Ã—Â Ã—â€¢Ã—â€”")],
            [KeyboardButton(text="Ã°Å¸â€œÂ£ Ã—Â©Ã—â„¢Ã—ÂªÃ—â€¢Ã—Â£"), KeyboardButton(text="Ã¢Ââ€œ Ã—Â¢Ã—â€“Ã—Â¨Ã—â€")],
            [KeyboardButton(text="Ã¢â€žÂ¹Ã¯Â¸Â Ã—Â©Ã—ÂÃ—Å“Ã—â€¢Ã—Âª Ã—Â Ã—Â¤Ã—â€¢Ã—Â¦Ã—â€¢Ã—Âª")],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )

def admin_listing_actions(listing_id: int, owner_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="Ã¢Å“â€¦ Ã—ÂÃ—Â©Ã—Â¨", callback_data=f"admin:approve:{listing_id}:{owner_id}"),
            InlineKeyboardButton(text="Ã¢ÂÅ’ Ã—â€œÃ—â€”Ã—â€", callback_data=f"admin:reject:{listing_id}:{owner_id}")
        ]]
    )

def activation_actions(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="Ã¢Å“â€¦ Ã—ÂÃ—Â©Ã—Â¨ Ã—â€Ã—Â¤Ã—Â¢Ã—Å“Ã—â€", callback_data=f"admin:activate:{user_id}"),
            InlineKeyboardButton(text="Ã¢ÂÅ’ Ã—â€œÃ—â€”Ã—â€ Ã—â€Ã—Â¤Ã—Â¢Ã—Å“Ã—â€", callback_data=f"admin:activate_reject:{user_id}")
        ]]
    )

async def create_http_session() -> aiohttp.ClientSession:
    return aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15))

async def create_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(dsn=DATABASE_URL, min_size=1, max_size=10, command_timeout=30)

async def bootstrap_db(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS nfty_users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                is_activated BOOLEAN NOT NULL DEFAULT FALSE,
                activated_at TIMESTAMPTZ,
                referred_by BIGINT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS nfty_activation_requests (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                ton_amount NUMERIC(18,8) NOT NULL DEFAULT 1.5,
                ils_amount NUMERIC(18,3) NOT NULL DEFAULT 22.221,
                tx_ref TEXT,
                note TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                reviewed_at TIMESTAMPTZ
            );

            CREATE TABLE IF NOT EXISTS nfty_items (
                id BIGSERIAL PRIMARY KEY,
                owner_id BIGINT NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                media_url TEXT,
                metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS nfty_listings (
                id BIGSERIAL PRIMARY KEY,
                item_id BIGINT NOT NULL REFERENCES nfty_items(id) ON DELETE CASCADE,
                seller_id BIGINT NOT NULL,
                price NUMERIC(18,8) NOT NULL,
                currency_symbol TEXT NOT NULL DEFAULT 'SLH',
                status TEXT NOT NULL DEFAULT 'pending_approval',
                admin_note TEXT,
                approved_by BIGINT,
                approved_at TIMESTAMPTZ,
                sold_to BIGINT,
                sold_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS virtual_pets (
                user_id BIGINT PRIMARY KEY,
                pet_name TEXT NOT NULL DEFAULT 'Sparky',
                pet_type TEXT NOT NULL DEFAULT 'spark',
                level INT NOT NULL DEFAULT 1,
                xp INT NOT NULL DEFAULT 0,
                mood INT NOT NULL DEFAULT 80,
                energy INT NOT NULL DEFAULT 80,
                hunger INT NOT NULL DEFAULT 20,
                curiosity INT NOT NULL DEFAULT 50,
                creativity INT NOT NULL DEFAULT 50,
                evolution_stage INT NOT NULL DEFAULT 1,
                last_action_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS pet_action_log (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                action_type TEXT NOT NULL,
                delta JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS system_events (
                id BIGSERIAL PRIMARY KEY,
                event_type TEXT NOT NULL,
                actor_id BIGINT,
                entity_type TEXT,
                entity_id TEXT,
                payload JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """)

async def log_event(pool: asyncpg.Pool, event_type: str, actor_id: Optional[int]=None, entity_type: Optional[str]=None, entity_id: Optional[str]=None, payload: Optional[dict[str, Any]]=None) -> None:
    payload = payload or {}
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO system_events (event_type, actor_id, entity_type, entity_id, payload)
            VALUES ($1, $2, $3, $4, $5::jsonb)
            """,
            event_type, actor_id, entity_type, entity_id, json.dumps(payload, ensure_ascii=False)
        )

async def upsert_user(pool: asyncpg.Pool, message: Message, referred_by: Optional[int]=None) -> None:
    full_name = " ".join([x for x in [message.from_user.first_name, message.from_user.last_name] if x]).strip()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO nfty_users (user_id, username, full_name, referred_by)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id)
            DO UPDATE SET username = EXCLUDED.username, full_name = EXCLUDED.full_name, updated_at = NOW()
            """,
            message.from_user.id, message.from_user.username, full_name, referred_by
        )
        await conn.execute(
            """
            INSERT INTO virtual_pets (user_id)
            VALUES ($1)
            ON CONFLICT (user_id) DO NOTHING
            """,
            message.from_user.id
        )

async def is_activated(pool: asyncpg.Pool, user_id: int) -> bool:
    async with pool.acquire() as conn:
        val = await conn.fetchval("SELECT is_activated FROM nfty_users WHERE user_id = $1", user_id)
        return bool(val)

async def require_activation(message: Message, pool: asyncpg.Pool) -> bool:
    if await is_activated(pool, message.from_user.id):
        return True
    await message.answer(
        "Ã°Å¸â€Â <b>Ã—Â Ã—â€œÃ—Â¨Ã—Â©Ã—Âª Ã—â€Ã—Â¤Ã—Â¢Ã—Å“Ã—Âª Ã—â€”Ã—Â©Ã—â€˜Ã—â€¢Ã—Å¸</b>\n\n"
        "Ã—â€ºÃ—â€œÃ—â„¢ Ã—Å“Ã—â€Ã—Â©Ã—ÂªÃ—Å¾Ã—Â© Ã—â€˜Ã—Å¾Ã—Â¨Ã—Â§Ã—Ëœ Ã—â„¢Ã—Â© Ã—Å“Ã—â€˜Ã—Â¦Ã—Â¢ Ã—â€Ã—Â¤Ã—Â¢Ã—Å“Ã—â€ Ã—â€”Ã—â€œ-Ã—Â¤Ã—Â¢Ã—Å¾Ã—â„¢Ã—Âª.\n"
        f"Ã—Â¢Ã—Å“Ã—â€¢Ã—Âª Ã—â€Ã—â€Ã—Â¤Ã—Â¢Ã—Å“Ã—â€: <b>{ACTIVATION_FEE_ILS}Ã¢â€šÂª</b> (~{ACTIVATION_FEE_TON} TON)\n"
        f"Ã—â€ºÃ—ÂªÃ—â€¢Ã—â€˜Ã—Âª TON Ã—Å“Ã—ÂªÃ—Â©Ã—Å“Ã—â€¢Ã—Â:\n<code>{TON_WALLET}</code>\n\n"
        "Ã—ÂÃ—â€”Ã—Â¨Ã—â„¢ Ã—â€Ã—ÂªÃ—Â©Ã—Å“Ã—â€¢Ã—Â Ã—Â©Ã—Å“Ã—â€”:\n<code>/activate TX123456</code>",
        reply_markup=main_menu()
    )
    return False

async def fetch_prices(session: aiohttp.ClientSession) -> dict[str, Any]:
    out = {"bitcoin": None, "toncoin": None, "bsc_token": None}
    try:
        async with session.get(f"{COINGECKO_BASE}/simple/price", params={"ids":"bitcoin,toncoin","vs_currencies":"usd,ils"}) as resp:
            if resp.status == 200:
                data = await resp.json()
                out["bitcoin"] = data.get("bitcoin")
                out["toncoin"] = data.get("toncoin")
        async with session.get(f"{COINGECKO_BASE}/simple/token_price/binance-smart-chain", params={"contract_addresses":BSC_TOKEN_CONTRACT,"vs_currencies":"usd,ils"}) as resp:
            if resp.status == 200:
                data = await resp.json()
                out["bsc_token"] = data.get(BSC_TOKEN_CONTRACT.lower()) or data.get(BSC_TOKEN_CONTRACT)
    except Exception:
        log.exception("price fetch failed")
    return out

def fmt_prices(prices: dict[str, Any]) -> str:
    lines = ["Ã°Å¸â€œË† <b>Ã—Å¾Ã—â€”Ã—â„¢Ã—Â¨Ã—â„¢ Ã—Â©Ã—â€¢Ã—Â§</b>"]
    if prices.get("bitcoin"):
        lines.append(f"Ã¢â‚¬Â¢ BTC: ${prices['bitcoin'].get('usd','?')} | Ã¢â€šÂª{prices['bitcoin'].get('ils','?')}")
    if prices.get("toncoin"):
        lines.append(f"Ã¢â‚¬Â¢ TON: ${prices['toncoin'].get('usd','?')} | Ã¢â€šÂª{prices['toncoin'].get('ils','?')}")
    if prices.get("bsc_token"):
        lines.append(f"Ã¢â‚¬Â¢ SLH/BSC: ${prices['bsc_token'].get('usd','?')} | Ã¢â€šÂª{prices['bsc_token'].get('ils','?')}")
    if len(lines) == 1:
        lines.append("Ã¢â‚¬Â¢ Ã—â€ºÃ—Â¨Ã—â€™Ã—Â¢ Ã—Å“Ã—Â Ã—â€“Ã—Å¾Ã—â„¢Ã—Å¸")
    return "\n".join(lines)

async def get_ctx(bot: Bot) -> AppContext:
    return bot["ctx"]

async def get_pet(pool: asyncpg.Pool, user_id: int):
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM virtual_pets WHERE user_id = $1", user_id)

def pet_face(stage: int, mood: int, energy: int) -> str:
    if energy < 25:
        return "Ã°Å¸ËœÂ´"
    if mood < 35:
        return "Ã°Å¸Â¥Âº"
    if stage >= 4:
        return "Ã°Å¸Å’Å’"
    if stage == 3:
        return "Ã¢Å“Â¨"
    if stage == 2:
        return "Ã°Å¸ÂÂ¾"
    return "Ã°Å¸ÂÂ£"

def pet_stage_name(stage: int) -> str:
    return {
        1: "Spark Seed",
        2: "Pixel Friend",
        3: "Neo Companion",
        4: "Infinity Spirit",
    }.get(stage, "Unknown")

async def apply_pet_action(pool: asyncpg.Pool, user_id: int, action_type: str):
    deltas = {
        "feed":  {"mood": 6, "energy": 4, "hunger": -12, "xp": 4, "curiosity": 0, "creativity": 0},
        "play":  {"mood": 10, "energy": -8, "hunger": 5, "xp": 6, "curiosity": 2, "creativity": 1},
        "learn": {"mood": 3, "energy": -6, "hunger": 3, "xp": 10, "curiosity": 8, "creativity": 2},
        "sleep": {"mood": 2, "energy": 14, "hunger": 4, "xp": 2, "curiosity": 0, "creativity": 0},
    }
    delta = deltas[action_type]

    async with pool.acquire() as conn:
        pet = await conn.fetchrow("SELECT * FROM virtual_pets WHERE user_id = $1", user_id)
        if not pet:
            await conn.execute("INSERT INTO virtual_pets (user_id) VALUES ($1) ON CONFLICT (user_id) DO NOTHING", user_id)
            pet = await conn.fetchrow("SELECT * FROM virtual_pets WHERE user_id = $1", user_id)

        level = int(pet["level"])
        xp = int(pet["xp"]) + delta["xp"]
        mood = max(0, min(100, int(pet["mood"]) + delta["mood"]))
        energy = max(0, min(100, int(pet["energy"]) + delta["energy"]))
        hunger = max(0, min(100, int(pet["hunger"]) + delta["hunger"]))
        curiosity = max(0, min(100, int(pet["curiosity"]) + delta["curiosity"]))
        creativity = max(0, min(100, int(pet["creativity"]) + delta["creativity"]))
        evolution_stage = int(pet["evolution_stage"])

        while xp >= level * 25:
            xp -= level * 25
            level += 1

        if level >= 15:
            evolution_stage = 4
        elif level >= 9:
            evolution_stage = 3
        elif level >= 4:
            evolution_stage = 2

        await conn.execute(
            """
            UPDATE virtual_pets
            SET level = $2,
                xp = $3,
                mood = $4,
                energy = $5,
                hunger = $6,
                curiosity = $7,
                creativity = $8,
                evolution_stage = $9,
                last_action_at = NOW(),
                updated_at = NOW()
            WHERE user_id = $1
            """,
            user_id, level, xp, mood, energy, hunger, curiosity, creativity, evolution_stage
        )
        await conn.execute(
            "INSERT INTO pet_action_log (user_id, action_type, delta) VALUES ($1, $2, $3::jsonb)",
            user_id, action_type, json.dumps(delta, ensure_ascii=False)
        )

    return await get_pet(pool, user_id)

def pet_status_text(pet) -> str:
    face = pet_face(int(pet["evolution_stage"]), int(pet["mood"]), int(pet["energy"]))
    return (
        f"{face} <b>{pet['pet_name']}</b>\n"
        f"Ã—Â©Ã—Å“Ã—â€˜: <b>{pet_stage_name(int(pet['evolution_stage']))}</b>\n"
        f"Ã—Â¨Ã—Å¾Ã—â€: <b>{pet['level']}</b>\n"
        f"XP: <b>{pet['xp']}</b>\n"
        f"Ã—Å¾Ã—Â¦Ã—â€˜ Ã—Â¨Ã—â€¢Ã—â€”: <b>{pet['mood']}</b>/100\n"
        f"Ã—ÂÃ—Â Ã—Â¨Ã—â€™Ã—â„¢Ã—â€: <b>{pet['energy']}</b>/100\n"
        f"Ã—Â¨Ã—Â¢Ã—â€˜: <b>{pet['hunger']}</b>/100\n"
        f"Ã—Â¡Ã—Â§Ã—Â¨Ã—Â Ã—â€¢Ã—Âª: <b>{pet['curiosity']}</b>/100\n"
        f"Ã—â„¢Ã—Â¦Ã—â„¢Ã—Â¨Ã—ÂªÃ—â„¢Ã—â€¢Ã—Âª: <b>{pet['creativity']}</b>/100"
    )

@router.message(Command("start"))
async def cmd_start(message: Message, command: CommandObject, bot: Bot):
    ctx = await get_ctx(bot)
    referred_by = None
    if command.args and command.args.startswith("ref_"):
        try:
            referred_by = int(command.args.replace("ref_", "").strip())
        except Exception:
            referred_by = None

    await upsert_user(ctx.pool, message, referred_by)
    prices = await fetch_prices(ctx.session)
    pet = await get_pet(ctx.pool, message.from_user.id)

    await message.answer(
        f"Ã°Å¸Å½Â¨ <b>{APP_NAME}</b>\n"
        f"<i>{TAGLINE}</i>\n\n"
        "Ã—â€˜Ã—Â¨Ã—â€¢Ã—Å¡ Ã—â€Ã—â€˜Ã—Â Ã—Å“Ã—Å¾Ã—Â¨Ã—Â§Ã—Ëœ Ã—â€Ã—â€œÃ—â„¢Ã—â€™Ã—â„¢Ã—ËœÃ—Å“Ã—â„¢ Ã—Â©Ã—Å“ SLH.\n"
        "Ã—â€ºÃ—ÂÃ—Å¸ Ã—ÂÃ—Â¤Ã—Â©Ã—Â¨ Ã—Å“Ã—Â§Ã—Â Ã—â€¢Ã—Âª, Ã—Å“Ã—Å¾Ã—â€ºÃ—â€¢Ã—Â¨ Ã—â€¢Ã—Å“Ã—Â Ã—â€Ã—Å“ Ã—Â Ã—â€ºÃ—Â¡Ã—â„¢Ã—Â Ã—â€œÃ—â„¢Ã—â€™Ã—â„¢Ã—ËœÃ—Å“Ã—â„¢Ã—â„¢Ã—Â Ã¢â‚¬â€ Ã—â€¢Ã—â€™Ã—Â Ã—Å“Ã—Â¤Ã—ÂªÃ—â€” Ã—â€”Ã—â€˜Ã—Â¨ Ã—â€¢Ã—â„¢Ã—Â¨Ã—ËœÃ—â€¢Ã—ÂÃ—Å“Ã—â„¢ Ã—Å¾Ã—Â©Ã—Å“Ã—Å¡.\n\n"
        f"{fmt_prices(prices)}\n\n"
        f"Ã°Å¸ÂÂ£ Ã—â€Ã—â€”Ã—â€˜Ã—Â¨ Ã—Â©Ã—Å“Ã—Å¡ Ã—Å¾Ã—â€¢Ã—â€ºÃ—Å¸:\n{pet_status_text(pet)}\n\n"
        f"Ã°Å¸â€Â Ã—â€Ã—Â¤Ã—Â¢Ã—Å“Ã—Âª Ã—â€”Ã—Â©Ã—â€˜Ã—â€¢Ã—Å¸: <b>{ACTIVATION_FEE_ILS}Ã¢â€šÂª</b> (~{ACTIVATION_FEE_TON} TON)",
        reply_markup=main_menu()
    )
    await log_event(ctx.pool, "user_start", actor_id=message.from_user.id, payload={"referred_by": referred_by})

@router.message(Command("help"))
@router.message(F.text == "Ã¢Ââ€œ Ã—Â¢Ã—â€“Ã—Â¨Ã—â€")
async def cmd_help(message: Message, bot: Bot):
    ctx = await get_ctx(bot)
    await log_event(ctx.pool, "view_help", actor_id=message.from_user.id)
    await message.answer(
        "Ã°Å¸â€ Ëœ <b>Ã—Å¾Ã—â€œÃ—Â¨Ã—â„¢Ã—Å¡ Ã—Â©Ã—â„¢Ã—Å¾Ã—â€¢Ã—Â©</b>\n\n"
        "/start Ã¢â‚¬â€œ Ã—Â¤Ã—ÂªÃ—â„¢Ã—â€”Ã—â€\n"
        "/activate TXREF Ã¢â‚¬â€œ Ã—â€˜Ã—Â§Ã—Â©Ã—Âª Ã—â€Ã—Â¤Ã—Â¢Ã—Å“Ã—â€\n"
        "/browse Ã¢â‚¬â€œ Ã—Â¢Ã—â„¢Ã—â€¢Ã—Å¸ Ã—â€˜Ã—Â¤Ã—Â¨Ã—â„¢Ã—ËœÃ—â„¢Ã—Â\n"
        "/sell Ã¢â‚¬â€œ Ã—â„¢Ã—Â¦Ã—â„¢Ã—Â¨Ã—Âª Ã—Â¤Ã—Â¨Ã—â„¢Ã—Ëœ Ã—Å“Ã—Å¾Ã—â€ºÃ—â„¢Ã—Â¨Ã—â€\n"
        "/buy 123 Ã¢â‚¬â€œ Ã—Â§Ã—Â Ã—â„¢Ã—â„¢Ã—Âª Ã—Â¤Ã—Â¨Ã—â„¢Ã—Ëœ\n"
        "/my_items Ã¢â‚¬â€œ Ã—â€Ã—Â Ã—â€ºÃ—Â¡Ã—â„¢Ã—Â Ã—Â©Ã—Å“Ã—â„¢\n"
        "/my_listings Ã¢â‚¬â€œ Ã—â€Ã—Å¾Ã—â€ºÃ—â„¢Ã—Â¨Ã—â€¢Ã—Âª Ã—Â©Ã—Å“Ã—â„¢\n"
        "/wallet Ã¢â‚¬â€œ Ã—â„¢Ã—ÂªÃ—Â¨Ã—â€¢Ã—Âª SLH/ZVK\n"
        "/pet Ã¢â‚¬â€œ Ã—Å¾Ã—Â¦Ã—â€˜ Ã—â€Ã—â€”Ã—â€˜Ã—Â¨ Ã—â€Ã—â€¢Ã—â€¢Ã—â„¢Ã—Â¨Ã—ËœÃ—â€¢Ã—ÂÃ—Å“Ã—â„¢\n"
        "/feed | /play | /learn | /sleep Ã¢â‚¬â€œ Ã—Â¤Ã—Â¢Ã—â€¢Ã—Å“Ã—â€¢Ã—Âª Ã—Å“Ã—â€”Ã—â€˜Ã—Â¨\n"
        "/share Ã¢â‚¬â€œ Ã—Â§Ã—â„¢Ã—Â©Ã—â€¢Ã—Â¨ Ã—Â©Ã—â„¢Ã—ÂªÃ—â€¢Ã—Â£",
        reply_markup=main_menu()
    )

@router.message(Command("faq"))
@router.message(F.text == "Ã¢â€žÂ¹Ã¯Â¸Â Ã—Â©Ã—ÂÃ—Å“Ã—â€¢Ã—Âª Ã—Â Ã—Â¤Ã—â€¢Ã—Â¦Ã—â€¢Ã—Âª")
async def cmd_faq(message: Message, bot: Bot):
    await message.answer(
        "Ã¢â€žÂ¹Ã¯Â¸Â <b>Ã—Â©Ã—ÂÃ—Å“Ã—â€¢Ã—Âª Ã—Â Ã—Â¤Ã—â€¢Ã—Â¦Ã—â€¢Ã—Âª</b>\n\n"
        "Ã¢â‚¬Â¢ Ã—â€Ã—Â¤Ã—Â¢Ã—Å“Ã—â€: Ã—Å¾Ã—Â©Ã—Å“Ã—Å¾Ã—â„¢Ã—Â Ã—â€¢Ã—Â©Ã—â€¢Ã—Å“Ã—â€”Ã—â„¢Ã—Â /activate Ã—Â¢Ã—Â Ã—ÂÃ—Â¡Ã—Å¾Ã—â€ºÃ—ÂªÃ—Â\n"
        "Ã¢â‚¬Â¢ Ã—Å¾Ã—ËœÃ—â€˜Ã—Â¢Ã—â€¢Ã—Âª: SLH Ã—ÂÃ—â€¢ ZVK\n"
        "Ã¢â‚¬Â¢ Ã—â€ºÃ—Å“ Ã—Â¤Ã—Â¨Ã—â„¢Ã—Ëœ Ã—â€”Ã—â€œÃ—Â© Ã—â€œÃ—â€¢Ã—Â¨Ã—Â© Ã—ÂÃ—â„¢Ã—Â©Ã—â€¢Ã—Â¨ Ã—Å¾Ã—Â Ã—â€Ã—Å“\n"
        "Ã¢â‚¬Â¢ Ã—â€Ã—â€”Ã—â€˜Ã—Â¨ Ã—â€Ã—â€¢Ã—â€¢Ã—â„¢Ã—Â¨Ã—ËœÃ—â€¢Ã—ÂÃ—Å“Ã—â„¢ Ã—Å¾Ã—ÂªÃ—Â¤Ã—ÂªÃ—â€” Ã—â€œÃ—Â¨Ã—Å¡ Ã—Â¤Ã—Â¢Ã—â„¢Ã—Å“Ã—â€¢Ã—Âª, Ã—Å¾Ã—Â©Ã—â€”Ã—Â§ Ã—â€¢Ã—Å“Ã—Å¾Ã—â„¢Ã—â€œÃ—â€",
        reply_markup=main_menu()
    )

@router.message(Command("share"))
@router.message(F.text == "Ã°Å¸â€œÂ£ Ã—Â©Ã—â„¢Ã—ÂªÃ—â€¢Ã—Â£")
async def cmd_share(message: Message, bot: Bot):
    me = await bot.get_me()
    text = f"Ã¢Å“Â¨ {APP_NAME}\nÃ°Å¸ÂªÂ {TAGLINE}\nhttps://t.me/{me.username}?start=ref_{message.from_user.id}"
    await message.answer("Ã°Å¸â€œÂ£ <b>Ã—ËœÃ—Â§Ã—Â¡Ã—Ëœ Ã—Â©Ã—â„¢Ã—ÂªÃ—â€¢Ã—Â£</b>\n\n" + f"<code>{text}</code>", reply_markup=main_menu())

@router.message(Command("wallet"))
@router.message(F.text == "Ã°Å¸â€™Â¼ Ã—â€Ã—ÂÃ—Â¨Ã—Â Ã—Â§ Ã—Â©Ã—Å“Ã—â„¢")
async def cmd_wallet(message: Message, bot: Bot):
    ctx = await get_ctx(bot)
    await upsert_user(ctx.pool, message)

    balances = []
    for symbol in ("SLH", "ZVK"):
        try:
            try:
                bal = await get_balance(message.from_user.id, symbol)
            except TypeError:
                bal = await get_balance(user_id=message.from_user.id, symbol=symbol)
        except Exception:
            bal = "?"
        balances.append(f"Ã¢â‚¬Â¢ {symbol}: <b>{bal}</b>")

    await message.answer("Ã°Å¸â€™Â¼ <b>Ã—â€Ã—ÂÃ—Â¨Ã—Â Ã—Â§ Ã—Â©Ã—Å“Ã—Å¡</b>\n\n" + "\n".join(balances), reply_markup=main_menu())

@router.message(Command("browse"))
@router.message(F.text == "Ã°Å¸â€ºÂÃ¯Â¸Â Ã—Â¢Ã—â„¢Ã—â€¢Ã—Å¸ Ã—â€˜Ã—Å¾Ã—Â¨Ã—Â§Ã—Ëœ")
async def cmd_browse(message: Message, bot: Bot):
    ctx = await get_ctx(bot)
    await upsert_user(ctx.pool, message)
    if not await require_activation(message, ctx.pool):
        return

    async with ctx.pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT l.id, i.title, i.category, i.description, l.price, l.currency_symbol
            FROM nfty_listings l
            JOIN nfty_items i ON i.id = l.item_id
            WHERE l.status = 'active'
            ORDER BY l.created_at DESC
            LIMIT 15
        """)

    if not rows:
        await message.answer("Ã—â€ºÃ—Â¨Ã—â€™Ã—Â¢ Ã—ÂÃ—â„¢Ã—Å¸ Ã—Â¤Ã—Â¨Ã—â„¢Ã—ËœÃ—â„¢Ã—Â Ã—Â¤Ã—Â¢Ã—â„¢Ã—Å“Ã—â„¢Ã—Â Ã—â€˜Ã—Å¾Ã—Â¨Ã—Â§Ã—Ëœ.", reply_markup=main_menu())
        return

    parts = ["Ã°Å¸â€ºÂÃ¯Â¸Â <b>Ã—Â¤Ã—Â¨Ã—â„¢Ã—ËœÃ—â„¢Ã—Â Ã—â€“Ã—Å¾Ã—â„¢Ã—Â Ã—â„¢Ã—Â</b>\n"]
    for row in rows:
        parts.append(
            f"#{row['id']} | <b>{row['title']}</b>\n"
            f"Ã—Â§Ã—ËœÃ—â€™Ã—â€¢Ã—Â¨Ã—â„¢Ã—â€: {row['category']}\n"
            f"Ã—Å¾Ã—â€”Ã—â„¢Ã—Â¨: <b>{row['price']} {row['currency_symbol']}</b>\n"
            f"Ã—ÂªÃ—â„¢Ã—ÂÃ—â€¢Ã—Â¨: {row['description'][:120]}\n"
            f"Ã—Å“Ã—Â§Ã—Â Ã—â„¢Ã—â„¢Ã—â€: <code>/buy {row['id']}</code>\n"
        )
    await message.answer("\n".join(parts), reply_markup=main_menu())

@router.message(Command("my_items"))
@router.message(F.text == "Ã°Å¸â€œÂ¦ Ã—â€Ã—Â¤Ã—Â¨Ã—â„¢Ã—ËœÃ—â„¢Ã—Â Ã—Â©Ã—Å“Ã—â„¢")
async def cmd_my_items(message: Message, bot: Bot):
    ctx = await get_ctx(bot)
    await upsert_user(ctx.pool, message)
    if not await require_activation(message, ctx.pool):
        return

    async with ctx.pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, title, category, description
            FROM nfty_items
            WHERE owner_id = $1
            ORDER BY created_at DESC
            LIMIT 30
        """, message.from_user.id)

    if not rows:
        await message.answer("Ã—Â¢Ã—â€œÃ—â„¢Ã—â„¢Ã—Å¸ Ã—ÂÃ—â„¢Ã—Å¸ Ã—Å“Ã—Å¡ Ã—Â Ã—â€ºÃ—Â¡Ã—â„¢Ã—Â Ã—â€œÃ—â„¢Ã—â€™Ã—â„¢Ã—ËœÃ—Å“Ã—â„¢Ã—â„¢Ã—Â.", reply_markup=main_menu())
        return

    out = ["Ã°Å¸â€œÂ¦ <b>Ã—â€Ã—Â Ã—â€ºÃ—Â¡Ã—â„¢Ã—Â Ã—Â©Ã—Å“Ã—â„¢</b>\n"]
    for row in rows:
        out.append(f"Ã¢â‚¬Â¢ #{row['id']} | <b>{row['title']}</b> | {row['category']}\n  {row['description'][:100]}")
    await message.answer("\n".join(out), reply_markup=main_menu())

@router.message(Command("my_listings"))
@router.message(F.text == "Ã°Å¸ÂÂ·Ã¯Â¸Â Ã—â€Ã—Å¾Ã—â€ºÃ—â„¢Ã—Â¨Ã—â€¢Ã—Âª Ã—Â©Ã—Å“Ã—â„¢")
async def cmd_my_listings(message: Message, bot: Bot):
    ctx = await get_ctx(bot)
    await upsert_user(ctx.pool, message)
    if not await require_activation(message, ctx.pool):
        return

    async with ctx.pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT l.id, i.title, l.price, l.currency_symbol, l.status
            FROM nfty_listings l
            JOIN nfty_items i ON i.id = l.item_id
            WHERE l.seller_id = $1
            ORDER BY l.created_at DESC
            LIMIT 30
        """, message.from_user.id)

    if not rows:
        await message.answer("Ã—ÂÃ—â„¢Ã—Å¸ Ã—Å“Ã—Å¡ Ã—â€ºÃ—Â¨Ã—â€™Ã—Â¢ Ã—Å¾Ã—â€ºÃ—â„¢Ã—Â¨Ã—â€¢Ã—Âª Ã—Â¤Ã—Â¢Ã—â„¢Ã—Å“Ã—â€¢Ã—Âª.", reply_markup=main_menu())
        return

    out = ["Ã°Å¸ÂÂ·Ã¯Â¸Â <b>Ã—â€Ã—Å¾Ã—â€ºÃ—â„¢Ã—Â¨Ã—â€¢Ã—Âª Ã—Â©Ã—Å“Ã—â„¢</b>\n"]
    for row in rows:
        out.append(f"Ã¢â‚¬Â¢ #{row['id']} | <b>{row['title']}</b>\n  Ã—Å¾Ã—â€”Ã—â„¢Ã—Â¨: {row['price']} {row['currency_symbol']} | Ã—Å¾Ã—Â¦Ã—â€˜: <b>{row['status']}</b>")
    await message.answer("\n".join(out), reply_markup=main_menu())

@router.message(Command("activate"))
async def cmd_activate(message: Message, command: CommandObject, bot: Bot):
    ctx = await get_ctx(bot)
    await upsert_user(ctx.pool, message)
    tx_ref = (command.args or "").strip()
    if not tx_ref:
        await message.answer("Ã—Â©Ã—Å“Ã—â€” Ã—â€ºÃ—Å¡:\n<code>/activate TX123456</code>", reply_markup=main_menu())
        return

    async with ctx.pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO nfty_activation_requests (user_id, tx_ref, status)
            VALUES ($1, $2, 'pending')
        """, message.from_user.id, tx_ref)

    await message.answer("Ã¢Å“â€¦ Ã—â€˜Ã—Â§Ã—Â©Ã—Âª Ã—â€Ã—â€Ã—Â¤Ã—Â¢Ã—Å“Ã—â€ Ã—Â Ã—Â§Ã—Å“Ã—ËœÃ—â€ Ã—â€¢Ã—Â Ã—Â©Ã—Å“Ã—â€”Ã—â€ Ã—Å“Ã—ÂÃ—â„¢Ã—Â©Ã—â€¢Ã—Â¨ Ã—Å¾Ã—Â Ã—â€Ã—Å“.", reply_markup=main_menu())

    try:
        await bot.send_message(
            ADMIN_USER_ID,
            "Ã°Å¸â€â€ <b>Ã—â€˜Ã—Â§Ã—Â©Ã—Âª Ã—â€Ã—Â¤Ã—Â¢Ã—Å“Ã—â€ Ã—â€”Ã—â€œÃ—Â©Ã—â€</b>\n\n"
            f"Ã—Å¾Ã—Â©Ã—ÂªÃ—Å¾Ã—Â©: <code>{message.from_user.id}</code>\n"
            f"Ã—ÂÃ—Â¡Ã—Å¾Ã—â€ºÃ—ÂªÃ—Â: <code>{tx_ref}</code>",
            reply_markup=activation_actions(message.from_user.id)
        )
    except Exception:
        log.exception("failed to notify admin")

@router.callback_query(F.data.startswith("admin:activate:"))
async def cb_admin_activate(callback, bot: Bot):
    ctx = await get_ctx(bot)
    if callback.from_user.id != ADMIN_USER_ID:
        await callback.answer("Ã—ÂÃ—â„¢Ã—Å¸ Ã—â€Ã—Â¨Ã—Â©Ã—ÂÃ—â€", show_alert=True)
        return

    user_id = int(callback.data.split(":")[2])
    async with ctx.pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO nfty_users (user_id, is_activated, activated_at)
            VALUES ($1, TRUE, NOW())
            ON CONFLICT (user_id)
            DO UPDATE SET is_activated = TRUE, activated_at = NOW(), updated_at = NOW()
        """, user_id)
        await conn.execute("""
            UPDATE nfty_activation_requests
            SET status='approved', reviewed_at=NOW()
            WHERE user_id=$1 AND status='pending'
        """, user_id)

    await callback.answer("Ã—â€Ã—â€”Ã—Â©Ã—â€˜Ã—â€¢Ã—Å¸ Ã—â€Ã—â€¢Ã—Â¤Ã—Â¢Ã—Å“")
    await callback.message.edit_reply_markup(reply_markup=None)
    await bot.send_message(user_id, "Ã°Å¸Å½â€° Ã—â€Ã—â€”Ã—Â©Ã—â€˜Ã—â€¢Ã—Å¸ Ã—Â©Ã—Å“Ã—Å¡ Ã—â€Ã—â€¢Ã—Â¤Ã—Â¢Ã—Å“.", reply_markup=main_menu())

@router.callback_query(F.data.startswith("admin:activate_reject:"))
async def cb_admin_activate_reject(callback, bot: Bot):
    ctx = await get_ctx(bot)
    if callback.from_user.id != ADMIN_USER_ID:
        await callback.answer("Ã—ÂÃ—â„¢Ã—Å¸ Ã—â€Ã—Â¨Ã—Â©Ã—ÂÃ—â€", show_alert=True)
        return

    user_id = int(callback.data.split(":")[2])
    async with ctx.pool.acquire() as conn:
        await conn.execute("""
            UPDATE nfty_activation_requests
            SET status='rejected', reviewed_at=NOW()
            WHERE user_id=$1 AND status='pending'
        """, user_id)

    await callback.answer("Ã—â€˜Ã—Â§Ã—Â©Ã—Âª Ã—â€Ã—â€Ã—Â¤Ã—Â¢Ã—Å“Ã—â€ Ã—Â Ã—â€œÃ—â€”Ã—ÂªÃ—â€")
    await callback.message.edit_reply_markup(reply_markup=None)
    await bot.send_message(user_id, "Ã¢ÂÅ’ Ã—â€˜Ã—Â§Ã—Â©Ã—Âª Ã—â€Ã—â€Ã—Â¤Ã—Â¢Ã—Å“Ã—â€ Ã—Â Ã—â€œÃ—â€”Ã—ÂªÃ—â€.", reply_markup=main_menu())

@router.message(Command("sell"))
@router.message(F.text == "Ã¢Å¾â€¢ Ã—Å“Ã—Å¾Ã—â€ºÃ—â„¢Ã—Â¨Ã—â€")
async def cmd_sell(message: Message, state: FSMContext, bot: Bot):
    ctx = await get_ctx(bot)
    await upsert_user(ctx.pool, message)
    if not await require_activation(message, ctx.pool):
        return

    await state.set_state(SellStates.waiting_name)
    await message.answer("Ã°Å¸â€œÂ <b>Ã—â„¢Ã—Â¦Ã—â„¢Ã—Â¨Ã—Âª Ã—Â¤Ã—Â¨Ã—â„¢Ã—Ëœ Ã—â€”Ã—â€œÃ—Â©</b>\n\nÃ—Â©Ã—Å“Ã—â€˜ 1/6\nÃ—â€ºÃ—ÂªÃ—â€¢Ã—â€˜ Ã—Â©Ã—Â Ã—Å“Ã—Â¤Ã—Â¨Ã—â„¢Ã—Ëœ:", reply_markup=main_menu())

@router.message(SellStates.waiting_name)
async def sell_name(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(SellStates.waiting_category)
    await message.answer("Ã—Â©Ã—Å“Ã—â€˜ 2/6\nÃ—â€ºÃ—ÂªÃ—â€¢Ã—â€˜ Ã—Â§Ã—ËœÃ—â€™Ã—â€¢Ã—Â¨Ã—â„¢Ã—â€ Ã—Å“Ã—Â¤Ã—Â¨Ã—â„¢Ã—Ëœ:")

@router.message(SellStates.waiting_category)
async def sell_category(message: Message, state: FSMContext):
    await state.update_data(category=message.text.strip())
    await state.set_state(SellStates.waiting_price)
    await message.answer("Ã—Â©Ã—Å“Ã—â€˜ 3/6\nÃ—â€ºÃ—ÂªÃ—â€¢Ã—â€˜ Ã—Å¾Ã—â€”Ã—â„¢Ã—Â¨ Ã—Å¾Ã—Â¡Ã—Â¤Ã—Â¨Ã—â„¢. Ã—Å“Ã—â€œÃ—â€¢Ã—â€™Ã—Å¾Ã—â€: 150")

@router.message(SellStates.waiting_price)
async def sell_price(message: Message, state: FSMContext):
    try:
        price = Decimal(message.text.strip())
        if price <= 0:
            raise ValueError()
    except (InvalidOperation, ValueError):
        await message.answer("Ã—Â¦Ã—Â¨Ã—â„¢Ã—Å¡ Ã—Å¾Ã—â€”Ã—â„¢Ã—Â¨ Ã—Å¾Ã—Â¡Ã—Â¤Ã—Â¨Ã—â„¢ Ã—â€”Ã—â„¢Ã—â€¢Ã—â€˜Ã—â„¢.")
        return
    await state.update_data(price=str(price))
    await state.set_state(SellStates.waiting_currency)
    await message.answer("Ã—Â©Ã—Å“Ã—â€˜ 4/6\nÃ—â€˜Ã—â€”Ã—Â¨ Ã—Å¾Ã—ËœÃ—â€˜Ã—Â¢: SLH Ã—ÂÃ—â€¢ ZVK")

@router.message(SellStates.waiting_currency)
async def sell_currency(message: Message, state: FSMContext):
    symbol = message.text.strip().upper()
    if symbol not in {"SLH", "ZVK"}:
        await message.answer("Ã—â€ºÃ—Â¨Ã—â€™Ã—Â¢ Ã—Â Ã—ÂªÃ—Å¾Ã—â€ºÃ—â„¢Ã—Â Ã—Â¨Ã—Â§ SLH Ã—ÂÃ—â€¢ ZVK.")
        return
    await state.update_data(currency_symbol=symbol)
    await state.set_state(SellStates.waiting_description)
    await message.answer("Ã—Â©Ã—Å“Ã—â€˜ 5/6\nÃ—â€ºÃ—ÂªÃ—â€¢Ã—â€˜ Ã—ÂªÃ—â„¢Ã—ÂÃ—â€¢Ã—Â¨ Ã—Â§Ã—Â¦Ã—Â¨ Ã—Å“Ã—Â¤Ã—Â¨Ã—â„¢Ã—Ëœ:")

@router.message(SellStates.waiting_description)
async def sell_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    await state.set_state(SellStates.waiting_media_url)
    await message.answer("Ã—Â©Ã—Å“Ã—â€˜ 6/6\nÃ—Â©Ã—Å“Ã—â€” Ã—Â§Ã—â„¢Ã—Â©Ã—â€¢Ã—Â¨ Ã—Å“Ã—Å¾Ã—â€œÃ—â„¢Ã—â€/Ã—ÂªÃ—Å¾Ã—â€¢Ã—Â Ã—â€, Ã—ÂÃ—â€¢ Ã—â€ºÃ—ÂªÃ—â€¢Ã—â€˜ - Ã—Å“Ã—â€œÃ—â„¢Ã—Å“Ã—â€¢Ã—â€™.")

@router.message(SellStates.waiting_media_url)
async def sell_media_url(message: Message, state: FSMContext, bot: Bot):
    ctx = await get_ctx(bot)
    data = await state.get_data()
    media_url = None if message.text.strip() == "-" else message.text.strip()
    await state.clear()

    async with ctx.pool.acquire() as conn:
        async with conn.transaction():
            item_id = await conn.fetchval("""
                INSERT INTO nfty_items (owner_id, title, category, description, media_url)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """, message.from_user.id, data["title"], data["category"], data["description"], media_url)

            listing_id = await conn.fetchval("""
                INSERT INTO nfty_listings (item_id, seller_id, price, currency_symbol, status)
                VALUES ($1, $2, $3, $4, 'pending_approval')
                RETURNING id
            """, item_id, message.from_user.id, Decimal(data["price"]), data["currency_symbol"])

    await message.answer(f"Ã¢Å“â€¦ Ã—â€Ã—Â¤Ã—Â¨Ã—â„¢Ã—Ëœ Ã—Â Ã—Â©Ã—Å“Ã—â€” Ã—Å“Ã—ÂÃ—â„¢Ã—Â©Ã—â€¢Ã—Â¨ Ã—Å¾Ã—Â Ã—â€Ã—Å“.\nÃ—Å¾Ã—â€“Ã—â€Ã—â€ Ã—Å¾Ã—â€ºÃ—â„¢Ã—Â¨Ã—â€: <b>{listing_id}</b>", reply_markup=main_menu())

    try:
        await bot.send_message(
            ADMIN_USER_ID,
            "Ã°Å¸â€ â€¢ <b>Ã—Â¤Ã—Â¨Ã—â„¢Ã—Ëœ Ã—â€”Ã—â€œÃ—Â© Ã—Å“Ã—ÂÃ—â„¢Ã—Â©Ã—â€¢Ã—Â¨</b>\n\n"
            f"Ã—Å¾Ã—â€“Ã—â€Ã—â€ Ã—Å¾Ã—â€ºÃ—â„¢Ã—Â¨Ã—â€: <b>{listing_id}</b>\n"
            f"Ã—Å¾Ã—â€¢Ã—â€ºÃ—Â¨: <code>{message.from_user.id}</code>\n"
            f"Ã—Â©Ã—Â: <b>{data['title']}</b>\n"
            f"Ã—Â§Ã—ËœÃ—â€™Ã—â€¢Ã—Â¨Ã—â„¢Ã—â€: {data['category']}\n"
            f"Ã—Å¾Ã—â€”Ã—â„¢Ã—Â¨: {data['price']} {data['currency_symbol']}\n"
            f"Ã—ÂªÃ—â„¢Ã—ÂÃ—â€¢Ã—Â¨: {data['description']}",
            reply_markup=admin_listing_actions(listing_id, message.from_user.id)
        )
    except Exception:
        log.exception("failed sending admin approval")

@router.callback_query(F.data.startswith("admin:approve:"))
async def cb_admin_approve(callback, bot: Bot):
    ctx = await get_ctx(bot)
    if callback.from_user.id != ADMIN_USER_ID:
        await callback.answer("Ã—ÂÃ—â„¢Ã—Å¸ Ã—â€Ã—Â¨Ã—Â©Ã—ÂÃ—â€", show_alert=True)
        return

    _, _, listing_id, owner_id = callback.data.split(":")
    async with ctx.pool.acquire() as conn:
        await conn.execute("""
            UPDATE nfty_listings
            SET status='active', approved_by=$1, approved_at=NOW()
            WHERE id=$2
        """, callback.from_user.id, int(listing_id))

    await callback.answer("Ã—â€Ã—Â¤Ã—Â¨Ã—â„¢Ã—Ëœ Ã—ÂÃ—â€¢Ã—Â©Ã—Â¨")
    await callback.message.edit_reply_markup(reply_markup=None)
    await bot.send_message(int(owner_id), f"Ã°Å¸Å½â€° Ã—â€Ã—Â¤Ã—Â¨Ã—â„¢Ã—Ëœ #{listing_id} Ã—ÂÃ—â€¢Ã—Â©Ã—Â¨ Ã—â€¢Ã—Â¢Ã—Å“Ã—â€ Ã—Å“Ã—Å¾Ã—Â¨Ã—Â§Ã—Ëœ.", reply_markup=main_menu())

@router.callback_query(F.data.startswith("admin:reject:"))
async def cb_admin_reject(callback, bot: Bot):
    ctx = await get_ctx(bot)
    if callback.from_user.id != ADMIN_USER_ID:
        await callback.answer("Ã—ÂÃ—â„¢Ã—Å¸ Ã—â€Ã—Â¨Ã—Â©Ã—ÂÃ—â€", show_alert=True)
        return

    _, _, listing_id, owner_id = callback.data.split(":")
    async with ctx.pool.acquire() as conn:
        await conn.execute("""
            UPDATE nfty_listings
            SET status='rejected', approved_by=$1, approved_at=NOW()
            WHERE id=$2
        """, callback.from_user.id, int(listing_id))

    await callback.answer("Ã—â€Ã—Â¤Ã—Â¨Ã—â„¢Ã—Ëœ Ã—Â Ã—â€œÃ—â€”Ã—â€")
    await callback.message.edit_reply_markup(reply_markup=None)
    await bot.send_message(int(owner_id), f"Ã¢ÂÅ’ Ã—â€Ã—Â¤Ã—Â¨Ã—â„¢Ã—Ëœ #{listing_id} Ã—Â Ã—â€œÃ—â€”Ã—â€.", reply_markup=main_menu())

@router.message(Command("buy"))
async def cmd_buy(message: Message, command: CommandObject, bot: Bot):
    ctx = await get_ctx(bot)
    await upsert_user(ctx.pool, message)
    if not await require_activation(message, ctx.pool):
        return

    if not command.args:
        await message.answer("Ã—â„¢Ã—Â© Ã—Å“Ã—Â©Ã—Å“Ã—â€¢Ã—â€” Ã—â€ºÃ—Å¡: <code>/buy 123</code>", reply_markup=main_menu())
        return

    try:
        listing_id = int(command.args.strip())
    except Exception:
        await message.answer("Ã—Å¾Ã—â€“Ã—â€Ã—â€ Ã—â€Ã—Â¤Ã—Â¨Ã—â„¢Ã—Ëœ Ã—â€”Ã—â„¢Ã—â„¢Ã—â€˜ Ã—Å“Ã—â€Ã—â„¢Ã—â€¢Ã—Âª Ã—Å¾Ã—Â¡Ã—Â¤Ã—Â¨.", reply_markup=main_menu())
        return

    async with ctx.pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT l.id, l.item_id, l.price, l.currency_symbol, l.status, l.seller_id, i.title
            FROM nfty_listings l
            JOIN nfty_items i ON i.id = l.item_id
            WHERE l.id = $1
        """, listing_id)

    if not row:
        await message.answer("Ã—â€Ã—Â¤Ã—Â¨Ã—â„¢Ã—Ëœ Ã—Å“Ã—Â Ã—Â Ã—Å¾Ã—Â¦Ã—Â.", reply_markup=main_menu())
        return
    if row["status"] != "active":
        await message.answer("Ã—â€Ã—Â¤Ã—Â¨Ã—â„¢Ã—Ëœ Ã—ÂÃ—â„¢Ã—Â Ã—â€¢ Ã—â€“Ã—Å¾Ã—â„¢Ã—Å¸ Ã—â€ºÃ—Â¨Ã—â€™Ã—Â¢.", reply_markup=main_menu())
        return
    if row["seller_id"] == message.from_user.id:
        await message.answer("Ã—ÂÃ—â„¢ Ã—ÂÃ—Â¤Ã—Â©Ã—Â¨ Ã—Å“Ã—Â§Ã—Â Ã—â€¢Ã—Âª Ã—ÂÃ—Âª Ã—â€Ã—Â¤Ã—Â¨Ã—â„¢Ã—Ëœ Ã—Â©Ã—Å“ Ã—Â¢Ã—Â¦Ã—Å¾Ã—Å¡.", reply_markup=main_menu())
        return

    price = Decimal(str(row["price"]))
    symbol = row["currency_symbol"]

    try:
        try:
            enough = await ensure_balance(message.from_user.id, symbol, price)
        except TypeError:
            enough = await ensure_balance(user_id=message.from_user.id, symbol=symbol, amount=price)
    except Exception:
        await message.answer("Ã—Å“Ã—Â Ã—â€Ã—Â¦Ã—Å“Ã—â€”Ã—ÂªÃ—â„¢ Ã—Å“Ã—â€˜Ã—â€œÃ—â€¢Ã—Â§ Ã—â„¢Ã—ÂªÃ—Â¨Ã—â€ Ã—â€ºÃ—Â¨Ã—â€™Ã—Â¢.", reply_markup=main_menu())
        return

    if not enough:
        await message.answer(f"Ã¢ÂÅ’ Ã—ÂÃ—â„¢Ã—Å¸ Ã—Å¾Ã—Â¡Ã—Â¤Ã—â„¢Ã—Â§ {symbol}. Ã—Â Ã—â€œÃ—Â¨Ã—Â©: <b>{price} {symbol}</b>", reply_markup=main_menu())
        return

    try:
        try:
            await transfer(message.from_user.id, row["seller_id"], symbol, price, f"NFT purchase #{listing_id}")
        except TypeError:
            await transfer(from_user_id=message.from_user.id, to_user_id=row["seller_id"], symbol=symbol, amount=price, note=f"NFT purchase #{listing_id}")
    except Exception:
        await message.answer("Ã—â€Ã—Â¢Ã—â€˜Ã—Â¨Ã—Âª Ã—â€Ã—ÂªÃ—Â©Ã—Å“Ã—â€¢Ã—Â Ã—Â Ã—â€ºÃ—Â©Ã—Å“Ã—â€.", reply_markup=main_menu())
        return

    async with ctx.pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("UPDATE nfty_items SET owner_id = $1 WHERE id = $2", message.from_user.id, row["item_id"])
            await conn.execute("UPDATE nfty_listings SET status='sold', sold_to=$1, sold_at=NOW() WHERE id=$2", message.from_user.id, listing_id)

    # Ã—â€˜Ã—â€¢Ã—Â Ã—â€¢Ã—Â¡ Ã—Å“Ã—â€”Ã—â€˜Ã—Â¨ Ã—â€Ã—â€¢Ã—â€¢Ã—â„¢Ã—Â¨Ã—ËœÃ—â€¢Ã—ÂÃ—Å“Ã—â„¢ Ã—Â¢Ã—Å“ Ã—Â¨Ã—â€ºÃ—â„¢Ã—Â©Ã—â€
    await apply_pet_action(ctx.pool, message.from_user.id, "play")

    await message.answer(
        f"Ã¢Å“â€¦ Ã—â€Ã—Â¢Ã—Â¡Ã—Â§Ã—â€ Ã—â€Ã—â€¢Ã—Â©Ã—Å“Ã—Å¾Ã—â€\nÃ—Â§Ã—Â Ã—â„¢Ã—Âª Ã—ÂÃ—Âª <b>{row['title']}</b>\nÃ—Â¡Ã—â€ºÃ—â€¢Ã—Â: <b>{price} {symbol}</b>\n\n"
        "Ã°Å¸ÂÂ£ Ã—â€Ã—â€”Ã—â€˜Ã—Â¨ Ã—Â©Ã—Å“Ã—Å¡ Ã—Â§Ã—â„¢Ã—â€˜Ã—Å“ Ã—â€˜Ã—â€¢Ã—Â Ã—â€¢Ã—Â¡ Ã—Å¾Ã—Â¦Ã—â€˜ Ã—Â¨Ã—â€¢Ã—â€” Ã—Â¢Ã—Å“ Ã—â€Ã—Â¤Ã—Â¢Ã—â„¢Ã—Å“Ã—â€¢Ã—Âª Ã—â€˜Ã—Å¾Ã—Â¨Ã—Â§Ã—Ëœ.",
        reply_markup=main_menu()
    )
    try:
        await bot.send_message(row["seller_id"], f"Ã°Å¸â€™Â¸ Ã—â€Ã—Â¤Ã—Â¨Ã—â„¢Ã—Ëœ Ã—Â©Ã—Å“Ã—Å¡ <b>{row['title']}</b> Ã—Â Ã—Å¾Ã—â€ºÃ—Â¨.", reply_markup=main_menu())
    except Exception:
        pass

@router.message(Command("pet"))
@router.message(F.text == "Ã°Å¸ÂÂ£ Ã—â€Ã—â€”Ã—â€˜Ã—Â¨ Ã—Â©Ã—Å“Ã—â„¢")
async def cmd_pet(message: Message, bot: Bot):
    ctx = await get_ctx(bot)
    await upsert_user(ctx.pool, message)
    pet = await get_pet(ctx.pool, message.from_user.id)
    await message.answer("Ã°Å¸ÂÂ£ <b>Ã—â€Ã—â€”Ã—â€˜Ã—Â¨ Ã—â€Ã—â€¢Ã—â€¢Ã—â„¢Ã—Â¨Ã—ËœÃ—â€¢Ã—ÂÃ—Å“Ã—â„¢ Ã—Â©Ã—Å“Ã—Å¡</b>\n\n" + pet_status_text(pet), reply_markup=main_menu())

@router.message(Command("feed"))
@router.message(F.text == "Ã°Å¸ÂÅ½ Ã—â€Ã—ÂÃ—â€ºÃ—Å“")
async def cmd_feed(message: Message, bot: Bot):
    ctx = await get_ctx(bot)
    await upsert_user(ctx.pool, message)
    pet = await apply_pet_action(ctx.pool, message.from_user.id, "feed")
    await message.answer("Ã°Å¸ÂÅ½ Ã—â€Ã—â€”Ã—â€˜Ã—Â¨ Ã—Â©Ã—Å“Ã—Å¡ Ã—ÂÃ—â€ºÃ—Å“.\n\n" + pet_status_text(pet), reply_markup=main_menu())

@router.message(Command("play"))
@router.message(F.text == "Ã°Å¸Å½Â® Ã—Â©Ã—â€”Ã—Â§")
async def cmd_play(message: Message, bot: Bot):
    ctx = await get_ctx(bot)
    await upsert_user(ctx.pool, message)
    pet = await apply_pet_action(ctx.pool, message.from_user.id, "play")
    await message.answer("Ã°Å¸Å½Â® Ã—Â©Ã—â„¢Ã—â€”Ã—Â§Ã—Âª Ã—Â¢Ã—Â Ã—â€Ã—â€”Ã—â€˜Ã—Â¨ Ã—Â©Ã—Å“Ã—Å¡.\n\n" + pet_status_text(pet), reply_markup=main_menu())

@router.message(Command("learn"))
@router.message(F.text == "Ã°Å¸â€œÅ¡ Ã—Å“Ã—Å¾Ã—â€œ")
async def cmd_learn(message: Message, bot: Bot):
    ctx = await get_ctx(bot)
    await upsert_user(ctx.pool, message)
    pet = await apply_pet_action(ctx.pool, message.from_user.id, "learn")
    await message.answer("Ã°Å¸â€œÅ¡ Ã—â€Ã—â€”Ã—â€˜Ã—Â¨ Ã—Â©Ã—Å“Ã—Å¡ Ã—Å“Ã—Å¾Ã—â€œ Ã—Å¾Ã—Â©Ã—â€Ã—â€¢ Ã—â€”Ã—â€œÃ—Â©.\n\n" + pet_status_text(pet), reply_markup=main_menu())

@router.message(Command("sleep"))
@router.message(F.text == "Ã°Å¸ËœÂ´ Ã—Â Ã—â€¢Ã—â€”")
async def cmd_sleep(message: Message, bot: Bot):
    ctx = await get_ctx(bot)
    await upsert_user(ctx.pool, message)
    pet = await apply_pet_action(ctx.pool, message.from_user.id, "sleep")
    await message.answer("Ã°Å¸ËœÂ´ Ã—â€Ã—â€”Ã—â€˜Ã—Â¨ Ã—Â©Ã—Å“Ã—Å¡ Ã—Â Ã—â€” Ã—â€¢Ã—â€Ã—ÂªÃ—ÂÃ—â€¢Ã—Â©Ã—Â©.\n\n" + pet_status_text(pet), reply_markup=main_menu())

@router.message()
async def fallback(message: Message):
    await message.answer(
        "Ã—Å“Ã—Â Ã—â€“Ã—â„¢Ã—â€Ã—â„¢Ã—ÂªÃ—â„¢ Ã—ÂÃ—Âª Ã—â€Ã—Â¤Ã—Â¢Ã—â€¢Ã—Å“Ã—â€.\n\n"
        "Ã—ÂÃ—Â¤Ã—Â©Ã—Â¨ Ã—Å“Ã—â€Ã—Â©Ã—ÂªÃ—Å¾Ã—Â© Ã—â€˜Ã—ÂªÃ—Â¤Ã—Â¨Ã—â„¢Ã—Ëœ Ã—ÂÃ—â€¢ Ã—â€˜Ã—Â¤Ã—Â§Ã—â€¢Ã—â€œÃ—â€¢Ã—Âª:\n"
        "/start | /browse | /sell | /buy <id> | /my_items | /my_listings | /wallet | /pet | /feed | /play | /learn | /sleep | /help | /faq | /share",
        reply_markup=main_menu()
    )

async def on_startup(bot: Bot):
    ctx = await get_ctx(bot)
    await bootstrap_db(ctx.pool)
    log.info("startup complete")

async def on_shutdown(bot: Bot):
    ctx = await get_ctx(bot)
    await ctx.session.close()
    await ctx.pool.close()
    log.info("shutdown complete")

async def main():
    if not BOT_TOKEN:
        raise RuntimeError("Missing BOT_TOKEN or NFTY_MADNESS_TOKEN")

    pool = await create_pool()
    session = await create_http_session()
    ctx = AppContext(pool=pool, session=session)

    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    bot["ctx"] = ctx

    storage = RedisStorage.from_url(REDIS_URL)
    dp = Dispatcher(storage=storage)
    dp.include_router(router)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())
'@

Write-Utf8NoBom -Path $MainPyPath -Content $MainPy

# =========================
# Dockerfile
# =========================
$Dockerfile = @'
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app:/app/shared

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY ./nfty-bot /app
COPY ./shared /app/shared

RUN pip install --no-cache-dir \
    aiogram==3.26.0 \
    aiohttp>=3.9.0 \
    asyncpg>=0.29.0 \
    redis>=5.0.0

CMD ["python", "/app/main.py"]
'@

Write-Utf8NoBom -Path $DockerfilePath -Content $Dockerfile

# =========================
# .env
# =========================
Set-Or-Add-EnvVar -Path $EnvPath -Key "NFTY_MADNESS_TOKEN" -Value $FreshToken
Set-Or-Add-EnvVar -Path $EnvPath -Key "BOT_TOKEN" -Value '${NFTY_MADNESS_TOKEN}'
Set-Or-Add-EnvVar -Path $EnvPath -Key "DATABASE_URL" -Value "postgresql://postgres:slh_secure_2026@postgres:5432/slh_main"
Set-Or-Add-EnvVar -Path $EnvPath -Key "REDIS_URL" -Value "redis://redis:6379/0"
Set-Or-Add-EnvVar -Path $EnvPath -Key "COINGECKO_BASE_URL" -Value "https://api.coingecko.com/api/v3"
Set-Or-Add-EnvVar -Path $EnvPath -Key "SLH_BSC_CONTRACT" -Value "0xACb0A09414CEA1C879c67bB7A877E4e19480f022"
Set-Or-Add-EnvVar -Path $EnvPath -Key "LOG_LEVEL" -Value "INFO"

# =========================
# docker-compose nfty-bot service
# =========================
$ServiceYaml = @'
  nfty-bot:
    container_name: slh-nfty
    build:
      context: .
      dockerfile: ./dockerfiles/Dockerfile.nfty
    restart: unless-stopped
    env_file:
      - .env
    environment:
      BOT_TOKEN: ${NFTY_MADNESS_TOKEN}
      DATABASE_URL: postgresql://postgres:slh_secure_2026@postgres:5432/slh_main
      REDIS_URL: redis://redis:6379/0
      COINGECKO_BASE_URL: https://api.coingecko.com/api/v3
      SLH_BSC_CONTRACT: 0xACb0A09414CEA1C879c67bB7A877E4e19480f022
      PYTHONPATH: /app:/app/shared
    volumes:
      - ./nfty-bot:/app
      - ./shared:/app/shared
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    command: ["python", "/app/main.py"]
'@

Replace-Or-Append-NftyService -ComposeFile $ComposePath -ServiceYaml $ServiceYaml

# =========================
# STOP OLD / REBUILD / UP
# =========================
Set-Location $Root

Info "Stopping old nfty-bot service..."
docker compose stop nfty-bot 2>$null | Out-Null

Info "Removing old nfty-bot container..."
docker compose rm -f nfty-bot 2>$null | Out-Null

Info "Building nfty-bot..."
docker compose build --no-cache nfty-bot

Info "Starting nfty-bot..."
docker compose up -d nfty-bot

Start-Sleep -Seconds 5

Info "Container status:"
docker compose ps nfty-bot

Info "Last logs:"
docker compose logs --tail=120 nfty-bot

Ok "Repair + upgrade complete."
Warn "Backups saved under: $BackupDir"