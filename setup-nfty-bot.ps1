[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$ErrorActionPreference = "Stop"

# =========================
# CONFIG
# =========================
$Root = "D:\SLH_ECOSYSTEM"
$BotDir = Join-Path $Root "nfty-bot"
$DockerfilesDir = Join-Path $Root "dockerfiles"
$ComposeFile = Join-Path $Root "docker-compose.yml"
$DockerfileNfty = Join-Path $DockerfilesDir "Dockerfile.nfty"
$MainPy = Join-Path $BotDir "main.py"
$EnvFile = Join-Path $Root ".env"

function Write-Info($msg)  { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Ok($msg)    { Write-Host "[ OK ] $msg" -ForegroundColor Green }
function Write-Warn($msg)  { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg)   { Write-Host "[ERR ] $msg" -ForegroundColor Red }

function Ensure-Dir {
    param([Parameter(Mandatory=$true)][string]$Path)
    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Force -Path $Path | Out-Null
        Write-Ok "Created directory: $Path"
    } else {
        Write-Info "Directory exists: $Path"
    }
}

function Write-Utf8NoBom {
    param(
        [Parameter(Mandatory=$true)][string]$Path,
        [Parameter(Mandatory=$true)][string]$Content
    )
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $utf8NoBom)
    Write-Ok "Wrote file: $Path"
}

function Ensure-LineInFile {
    param(
        [Parameter(Mandatory=$true)][string]$Path,
        [Parameter(Mandatory=$true)][string]$Line
    )
    if (-not (Test-Path $Path)) {
        New-Item -ItemType File -Path $Path -Force | Out-Null
    }

    $content = Get-Content $Path -Raw -ErrorAction SilentlyContinue
    if ($content -notmatch [regex]::Escape($Line)) {
        Add-Content -Path $Path -Value $Line
        Write-Ok "Added line to $Path : $Line"
    } else {
        Write-Info "Line already exists in $Path : $Line"
    }
}

function Ensure-EnvVar {
    param(
        [Parameter(Mandatory=$true)][string]$Path,
        [Parameter(Mandatory=$true)][string]$Key,
        [Parameter(Mandatory=$true)][string]$Value
    )

    if (-not (Test-Path $Path)) {
        New-Item -ItemType File -Path $Path -Force | Out-Null
    }

    $raw = Get-Content $Path -Raw -ErrorAction SilentlyContinue
    if ($raw -match "(?m)^$([regex]::Escape($Key))=") {
        $updated = [regex]::Replace($raw, "(?m)^$([regex]::Escape($Key))=.*$", "$Key=$Value")
        Write-Utf8NoBom -Path $Path -Content $updated
        Write-Ok "Updated env var: $Key"
    } else {
        $append = if ([string]::IsNullOrWhiteSpace($raw)) { "$Key=$Value`r`n" } else { $raw.TrimEnd() + "`r`n$Key=$Value`r`n" }
        Write-Utf8NoBom -Path $Path -Content $append
        Write-Ok "Added env var: $Key"
    }
}

function Ensure-ComposeService {
    param(
        [Parameter(Mandatory=$true)][string]$ComposePath,
        [Parameter(Mandatory=$true)][string]$ServiceBlock
    )

    if (-not (Test-Path $ComposePath)) {
        throw "docker-compose.yml not found at: $ComposePath"
    }

    $raw = Get-Content $ComposePath -Raw
    if ($raw -match "(?m)^\s{2}nfty-bot:") {
        Write-Warn "nfty-bot service already exists in docker-compose.yml. Skipping block append."
        return
    }

    $updated = $raw.TrimEnd() + "`r`n`r`n" + $ServiceBlock + "`r`n"
    Write-Utf8NoBom -Path $ComposePath -Content $updated
    Write-Ok "Appended nfty-bot service to docker-compose.yml"
}

function Require-Command {
    param([Parameter(Mandatory=$true)][string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command not found: $Name"
    }
}

# =========================
# PRECHECK
# =========================
Write-Info "Starting NFTY bot setup..."

Require-Command docker

Ensure-Dir $Root
Ensure-Dir $BotDir
Ensure-Dir $DockerfilesDir

if (-not (Test-Path $ComposeFile)) {
    throw "Missing docker-compose.yml at $ComposeFile"
}

# =========================
# FILE: main.py
# =========================
$mainPyContent = @'
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
            [KeyboardButton(text="🛍️ עיון במרקט"), KeyboardButton(text="💼 הארנק שלי")],
            [KeyboardButton(text="📦 הפריטים שלי"), KeyboardButton(text="🏷️ המכירות שלי")],
            [KeyboardButton(text="➕ למכירה"), KeyboardButton(text="📣 שיתוף")],
            [KeyboardButton(text="❓ עזרה"), KeyboardButton(text="ℹ️ שאלות נפוצות")],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )

def admin_listing_actions(listing_id: int, owner_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="✅ אשר", callback_data=f"admin:approve:{listing_id}:{owner_id}"),
            InlineKeyboardButton(text="❌ דחה", callback_data=f"admin:reject:{listing_id}:{owner_id}")
        ]]
    )

def activation_actions(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="✅ אשר הפעלה", callback_data=f"admin:activate:{user_id}"),
            InlineKeyboardButton(text="❌ דחה הפעלה", callback_data=f"admin:activate_reject:{user_id}")
        ]]
    )

async def create_http_session() -> aiohttp.ClientSession:
    timeout = aiohttp.ClientTimeout(total=15)
    return aiohttp.ClientSession(timeout=timeout)

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

async def is_activated(pool: asyncpg.Pool, user_id: int) -> bool:
    async with pool.acquire() as conn:
        val = await conn.fetchval("SELECT is_activated FROM nfty_users WHERE user_id = $1", user_id)
        return bool(val)

async def require_activation(message: Message, pool: asyncpg.Pool) -> bool:
    if await is_activated(pool, message.from_user.id):
        return True
    await message.answer(
        "🔐 <b>נדרשת הפעלת חשבון</b>\n\n"
        "כדי להשתמש במרקט יש לבצע הפעלה חד-פעמית.\n"
        f"עלות ההפעלה: <b>{ACTIVATION_FEE_ILS}₪</b> (~{ACTIVATION_FEE_TON} TON)\n"
        f"כתובת TON לתשלום:\n<code>{TON_WALLET}</code>\n\n"
        "אחרי התשלום שלח:\n<code>/activate TX123456</code>",
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
    lines = ["📈 <b>מחירי שוק</b>"]
    if prices.get("bitcoin"):
        lines.append(f"• BTC: ${prices['bitcoin'].get('usd','?')} | ₪{prices['bitcoin'].get('ils','?')}")
    if prices.get("toncoin"):
        lines.append(f"• TON: ${prices['toncoin'].get('usd','?')} | ₪{prices['toncoin'].get('ils','?')}")
    if prices.get("bsc_token"):
        lines.append(f"• SLH/BSC: ${prices['bsc_token'].get('usd','?')} | ₪{prices['bsc_token'].get('ils','?')}")
    if len(lines) == 1:
        lines.append("• כרגע לא זמין")
    return "\n".join(lines)

async def get_ctx(bot: Bot) -> AppContext:
    return bot["ctx"]

@router.message(Command("start"))
async def cmd_start(message: Message, command: CommandObject, bot: Bot):
    ctx = await get_ctx(bot)
    referred_by = None
    if command.args and command.args.startswith("ref_"):
        try:
            referred_by = int(command.args.replace("ref_", "").strip())
        except:
            referred_by = None

    await upsert_user(ctx.pool, message, referred_by)
    prices = await fetch_prices(ctx.session)
    await message.answer(
        f"🎨 <b>{APP_NAME}</b>\n"
        f"<i>{TAGLINE}</i>\n\n"
        "ברוך הבא למרקט הדיגיטלי של SLH.\n"
        "כאן אפשר לגלות, לקנות, למכור ולנהל נכסים דיגיטליים בעברית מלאה.\n\n"
        "🧩 סוגי נכסים:\n"
        "• אמנות דיגיטלית\n"
        "• פריטי אספנות\n"
        "• כרטיסי גישה\n"
        "• נכסים קהילתיים\n\n"
        f"{fmt_prices(prices)}\n\n"
        f"🔐 הפעלת חשבון: <b>{ACTIVATION_FEE_ILS}₪</b> (~{ACTIVATION_FEE_TON} TON)",
        reply_markup=main_menu()
    )
    await log_event(ctx.pool, "user_start", actor_id=message.from_user.id, payload={"referred_by": referred_by})

@router.message(Command("help"))
@router.message(F.text == "❓ עזרה")
async def cmd_help(message: Message, bot: Bot):
    ctx = await get_ctx(bot)
    await log_event(ctx.pool, "view_help", actor_id=message.from_user.id)
    await message.answer(
        "🆘 <b>מדריך שימוש</b>\n\n"
        "/start – פתיחה\n"
        "/activate TXREF – בקשת הפעלה\n"
        "/browse – עיון בפריטים\n"
        "/sell – יצירת פריט למכירה\n"
        "/buy 123 – קניית פריט\n"
        "/my_items – הנכסים שלי\n"
        "/my_listings – המכירות שלי\n"
        "/wallet – יתרות SLH/ZVK\n"
        "/share – קישור שיתוף",
        reply_markup=main_menu()
    )

@router.message(Command("faq"))
@router.message(F.text == "ℹ️ שאלות נפוצות")
async def cmd_faq(message: Message, bot: Bot):
    await message.answer(
        "ℹ️ <b>שאלות נפוצות</b>\n\n"
        "• הפעלה: משלמים ושולחים /activate עם אסמכתא\n"
        "• מטבעות: SLH או ZVK\n"
        "• כל פריט חדש דורש אישור מנהל\n"
        "• אפשר למכור אמנות, פריטי אספנות וכרטיסי גישה",
        reply_markup=main_menu()
    )

@router.message(Command("share"))
@router.message(F.text == "📣 שיתוף")
async def cmd_share(message: Message, bot: Bot):
    me = await bot.get_me()
    text = f"✨ {APP_NAME}\n🪐 {TAGLINE}\nhttps://t.me/{me.username}?start=ref_{message.from_user.id}"
    await message.answer("📣 <b>טקסט שיתוף</b>\n\n" + f"<code>{text}</code>", reply_markup=main_menu())

@router.message(Command("wallet"))
@router.message(F.text == "💼 הארנק שלי")
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
        balances.append(f"• {symbol}: <b>{bal}</b>")

    await message.answer("💼 <b>הארנק שלך</b>\n\n" + "\n".join(balances), reply_markup=main_menu())

@router.message(Command("browse"))
@router.message(F.text == "🛍️ עיון במרקט")
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
        await message.answer("כרגע אין פריטים פעילים במרקט.", reply_markup=main_menu())
        return

    parts = ["🛍️ <b>פריטים זמינים</b>\n"]
    for row in rows:
        parts.append(
            f"#{row['id']} | <b>{row['title']}</b>\n"
            f"קטגוריה: {row['category']}\n"
            f"מחיר: <b>{row['price']} {row['currency_symbol']}</b>\n"
            f"תיאור: {row['description'][:120]}\n"
            f"לקנייה: <code>/buy {row['id']}</code>\n"
        )
    await message.answer("\n".join(parts), reply_markup=main_menu())

@router.message(Command("my_items"))
@router.message(F.text == "📦 הפריטים שלי")
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
        await message.answer("עדיין אין לך נכסים דיגיטליים.", reply_markup=main_menu())
        return

    out = ["📦 <b>הנכסים שלי</b>\n"]
    for row in rows:
        out.append(f"• #{row['id']} | <b>{row['title']}</b> | {row['category']}\n  {row['description'][:100]}")
    await message.answer("\n".join(out), reply_markup=main_menu())

@router.message(Command("my_listings"))
@router.message(F.text == "🏷️ המכירות שלי")
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
        await message.answer("אין לך כרגע מכירות פעילות.", reply_markup=main_menu())
        return

    out = ["🏷️ <b>המכירות שלי</b>\n"]
    for row in rows:
        out.append(f"• #{row['id']} | <b>{row['title']}</b>\n  מחיר: {row['price']} {row['currency_symbol']} | מצב: <b>{row['status']}</b>")
    await message.answer("\n".join(out), reply_markup=main_menu())

@router.message(Command("activate"))
async def cmd_activate(message: Message, command: CommandObject, bot: Bot):
    ctx = await get_ctx(bot)
    await upsert_user(ctx.pool, message)
    tx_ref = (command.args or "").strip()
    if not tx_ref:
        await message.answer("שלח כך:\n<code>/activate TX123456</code>", reply_markup=main_menu())
        return

    async with ctx.pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO nfty_activation_requests (user_id, tx_ref, status)
            VALUES ($1, $2, 'pending')
        """, message.from_user.id, tx_ref)

    await message.answer("✅ בקשת ההפעלה נקלטה ונשלחה לאישור מנהל.", reply_markup=main_menu())

    try:
        await bot.send_message(
            ADMIN_USER_ID,
            "🔔 <b>בקשת הפעלה חדשה</b>\n\n"
            f"משתמש: <code>{message.from_user.id}</code>\n"
            f"אסמכתא: <code>{tx_ref}</code>",
            reply_markup=activation_actions(message.from_user.id)
        )
    except Exception:
        log.exception("failed to notify admin")

@router.callback_query(F.data.startswith("admin:activate:"))
async def cb_admin_activate(callback, bot: Bot):
    ctx = await get_ctx(bot)
    if callback.from_user.id != ADMIN_USER_ID:
        await callback.answer("אין הרשאה", show_alert=True)
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

    await callback.answer("החשבון הופעל")
    await callback.message.edit_reply_markup(reply_markup=None)
    await bot.send_message(user_id, "🎉 החשבון שלך הופעל.", reply_markup=main_menu())

@router.callback_query(F.data.startswith("admin:activate_reject:"))
async def cb_admin_activate_reject(callback, bot: Bot):
    ctx = await get_ctx(bot)
    if callback.from_user.id != ADMIN_USER_ID:
        await callback.answer("אין הרשאה", show_alert=True)
        return

    user_id = int(callback.data.split(":")[2])
    async with ctx.pool.acquire() as conn:
        await conn.execute("""
            UPDATE nfty_activation_requests
            SET status='rejected', reviewed_at=NOW()
            WHERE user_id=$1 AND status='pending'
        """, user_id)

    await callback.answer("בקשת ההפעלה נדחתה")
    await callback.message.edit_reply_markup(reply_markup=None)
    await bot.send_message(user_id, "❌ בקשת ההפעלה נדחתה.", reply_markup=main_menu())

@router.message(Command("sell"))
@router.message(F.text == "➕ למכירה")
async def cmd_sell(message: Message, state: FSMContext, bot: Bot):
    ctx = await get_ctx(bot)
    await upsert_user(ctx.pool, message)
    if not await require_activation(message, ctx.pool):
        return

    await state.set_state(SellStates.waiting_name)
    await message.answer("📝 <b>יצירת פריט חדש</b>\n\nשלב 1/6\nכתוב שם לפריט:", reply_markup=main_menu())

@router.message(SellStates.waiting_name)
async def sell_name(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(SellStates.waiting_category)
    await message.answer("שלב 2/6\nכתוב קטגוריה לפריט:")

@router.message(SellStates.waiting_category)
async def sell_category(message: Message, state: FSMContext):
    await state.update_data(category=message.text.strip())
    await state.set_state(SellStates.waiting_price)
    await message.answer("שלב 3/6\nכתוב מחיר מספרי. לדוגמה: 150")

@router.message(SellStates.waiting_price)
async def sell_price(message: Message, state: FSMContext):
    try:
        price = Decimal(message.text.strip())
        if price <= 0:
            raise ValueError()
    except (InvalidOperation, ValueError):
        await message.answer("צריך מחיר מספרי חיובי.")
        return
    await state.update_data(price=str(price))
    await state.set_state(SellStates.waiting_currency)
    await message.answer("שלב 4/6\nבחר מטבע: SLH או ZVK")

@router.message(SellStates.waiting_currency)
async def sell_currency(message: Message, state: FSMContext):
    symbol = message.text.strip().upper()
    if symbol not in @("SLH","ZVK"):
        pass
    if symbol not in {"SLH", "ZVK"}:
        await message.answer("כרגע נתמכים רק SLH או ZVK.")
        return
    await state.update_data(currency_symbol=symbol)
    await state.set_state(SellStates.waiting_description)
    await message.answer("שלב 5/6\nכתוב תיאור קצר לפריט:")

@router.message(SellStates.waiting_description)
async def sell_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    await state.set_state(SellStates.waiting_media_url)
    await message.answer("שלב 6/6\nשלח קישור למדיה/תמונה, או כתוב - לדילוג.")

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

    await message.answer(f"✅ הפריט נשלח לאישור מנהל.\nמזהה מכירה: <b>{listing_id}</b>", reply_markup=main_menu())

    try:
        await bot.send_message(
            ADMIN_USER_ID,
            "🆕 <b>פריט חדש לאישור</b>\n\n"
            f"מזהה מכירה: <b>{listing_id}</b>\n"
            f"מוכר: <code>{message.from_user.id}</code>\n"
            f"שם: <b>{data['title']}</b>\n"
            f"קטגוריה: {data['category']}\n"
            f"מחיר: {data['price']} {data['currency_symbol']}\n"
            f"תיאור: {data['description']}",
            reply_markup=admin_listing_actions(listing_id, message.from_user.id)
        )
    except Exception:
        log.exception("failed sending admin approval")

@router.callback_query(F.data.startswith("admin:approve:"))
async def cb_admin_approve(callback, bot: Bot):
    ctx = await get_ctx(bot)
    if callback.from_user.id != ADMIN_USER_ID:
        await callback.answer("אין הרשאה", show_alert=True)
        return

    _, _, listing_id, owner_id = callback.data.split(":")
    async with ctx.pool.acquire() as conn:
        await conn.execute("""
            UPDATE nfty_listings
            SET status='active', approved_by=$1, approved_at=NOW()
            WHERE id=$2
        """, callback.from_user.id, int(listing_id))

    await callback.answer("הפריט אושר")
    await callback.message.edit_reply_markup(reply_markup=None)
    await bot.send_message(int(owner_id), f"🎉 הפריט #{listing_id} אושר ועלה למרקט.", reply_markup=main_menu())

@router.callback_query(F.data.startswith("admin:reject:"))
async def cb_admin_reject(callback, bot: Bot):
    ctx = await get_ctx(bot)
    if callback.from_user.id != ADMIN_USER_ID:
        await callback.answer("אין הרשאה", show_alert=True)
        return

    _, _, listing_id, owner_id = callback.data.split(":")
    async with ctx.pool.acquire() as conn:
        await conn.execute("""
            UPDATE nfty_listings
            SET status='rejected', approved_by=$1, approved_at=NOW()
            WHERE id=$2
        """, callback.from_user.id, int(listing_id))

    await callback.answer("הפריט נדחה")
    await callback.message.edit_reply_markup(reply_markup=None)
    await bot.send_message(int(owner_id), f"❌ הפריט #{listing_id} נדחה.", reply_markup=main_menu())

@router.message(Command("buy"))
async def cmd_buy(message: Message, command: CommandObject, bot: Bot):
    ctx = await get_ctx(bot)
    await upsert_user(ctx.pool, message)
    if not await require_activation(message, ctx.pool):
        return

    if not command.args:
        await message.answer("יש לשלוח כך: <code>/buy 123</code>", reply_markup=main_menu())
        return

    try:
        listing_id = int(command.args.strip())
    except:
        await message.answer("מזהה הפריט חייב להיות מספר.", reply_markup=main_menu())
        return

    async with ctx.pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT l.id, l.item_id, l.price, l.currency_symbol, l.status, l.seller_id, i.title
            FROM nfty_listings l
            JOIN nfty_items i ON i.id = l.item_id
            WHERE l.id = $1
        """, listing_id)

    if not row:
        await message.answer("הפריט לא נמצא.", reply_markup=main_menu())
        return
    if row["status"] != "active":
        await message.answer("הפריט אינו זמין כרגע.", reply_markup=main_menu())
        return
    if row["seller_id"] == message.from_user.id:
        await message.answer("אי אפשר לקנות את הפריט של עצמך.", reply_markup=main_menu())
        return

    price = Decimal(str(row["price"]))
    symbol = row["currency_symbol"]

    try:
        try:
            enough = await ensure_balance(message.from_user.id, symbol, price)
        except TypeError:
            enough = await ensure_balance(user_id=message.from_user.id, symbol=symbol, amount=price)
    except Exception:
        await message.answer("לא הצלחתי לבדוק יתרה כרגע.", reply_markup=main_menu())
        return

    if not enough:
        await message.answer(f"❌ אין מספיק {symbol}. נדרש: <b>{price} {symbol}</b>", reply_markup=main_menu())
        return

    try:
        try:
            await transfer(message.from_user.id, row["seller_id"], symbol, price, f"NFT purchase #{listing_id}")
        except TypeError:
            await transfer(from_user_id=message.from_user.id, to_user_id=row["seller_id"], symbol=symbol, amount=price, note=f"NFT purchase #{listing_id}")
    except Exception:
        await message.answer("העברת התשלום נכשלה.", reply_markup=main_menu())
        return

    async with ctx.pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("UPDATE nfty_items SET owner_id = $1 WHERE id = $2", message.from_user.id, row["item_id"])
            await conn.execute("UPDATE nfty_listings SET status='sold', sold_to=$1, sold_at=NOW() WHERE id=$2", message.from_user.id, listing_id)

    await message.answer(
        f"✅ העסקה הושלמה\nקנית את <b>{row['title']}</b>\nסכום: <b>{price} {symbol}</b>",
        reply_markup=main_menu()
    )
    try:
        await bot.send_message(row["seller_id"], f"💸 הפריט שלך <b>{row['title']}</b> נמכר.", reply_markup=main_menu())
    except:
        pass

@router.message()
async def fallback(message: Message):
    await message.answer(
        "לא זיהיתי את הפעולה.\n\n"
        "אפשר להשתמש בתפריט או בפקודות:\n"
        "/start | /browse | /sell | /buy <id> | /my_items | /my_listings | /wallet | /help | /faq | /share",
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

Write-Utf8NoBom -Path $MainPy -Content $mainPyContent

# =========================
# FILE: Dockerfile.nfty
# =========================
$dockerfileContent = @'
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 `
    PYTHONDONTWRITEBYTECODE=1 `
    PYTHONPATH=/app:/app/shared

RUN apt-get update && apt-get install -y --no-install-recommends `
    build-essential `
    libpq-dev `
    && rm -rf /var/lib/apt/lists/*

COPY ./nfty-bot /app
COPY ./shared /app/shared

RUN pip install --no-cache-dir `
    aiogram>=3.20.0 `
    aiohttp>=3.9.0 `
    asyncpg>=0.29.0 `
    redis>=5.0.0

CMD ["python", "/app/main.py"]
'@

Write-Utf8NoBom -Path $DockerfileNfty -Content $dockerfileContent

# =========================
# ENV
# =========================
Ensure-EnvVar -Path $EnvFile -Key "NFTY_MADNESS_TOKEN" -Value "REPLACE_WITH_NEW_TOKEN"
Ensure-EnvVar -Path $EnvFile -Key "BOT_TOKEN" -Value '${NFTY_MADNESS_TOKEN}'
Ensure-EnvVar -Path $EnvFile -Key "DATABASE_URL" -Value "postgresql://postgres:slh_secure_2026@postgres:5432/slh_main"
Ensure-EnvVar -Path $EnvFile -Key "REDIS_URL" -Value "redis://redis:6379/0"
Ensure-EnvVar -Path $EnvFile -Key "COINGECKO_BASE_URL" -Value "https://api.coingecko.com/api/v3"
Ensure-EnvVar -Path $EnvFile -Key "SLH_BSC_CONTRACT" -Value "0xACb0A09414CEA1C879c67bB7A877E4e19480f022"

# =========================
# docker-compose service
# =========================
$serviceBlock = @'
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
    volumes:
      - ./nfty-bot:/app
      - ./shared:/app/shared
    depends_on:
      - postgres
      - redis
    command: ["python", "/app/main.py"]
'@

Ensure-ComposeService -ComposePath $ComposeFile -ServiceBlock $serviceBlock

# =========================
# BUILD + UP
# =========================
Set-Location $Root

Write-Info "Running docker compose build nfty-bot..."
docker compose build nfty-bot

Write-Info "Running docker compose up -d nfty-bot..."
docker compose up -d nfty-bot

Write-Info "Showing container status..."
docker compose ps nfty-bot

Write-Info "Showing last logs..."
docker compose logs --tail=80 nfty-bot

Write-Ok "NFTY bot setup completed."
Write-Warn "Before production: replace NFTY_MADNESS_TOKEN in .env with a fresh token from BotFather."