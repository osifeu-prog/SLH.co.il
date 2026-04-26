"""
SPARK IND - Match & Friends Bot
================================
Friendship/dating bot by INTERESTS ONLY.
No age, no required photos. Just shared passions.

Bot: @G4meb0t_bot_bot
Framework: aiogram 3.x
Storage: In-memory (dict)
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Shared payment library for premium features
try:
    from slh_payments import payment_gate
    HAS_PAYMENTS = True
except ImportError:
    HAS_PAYMENTS = False

# ── Config ──────────────────────────────────────────────────────

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "224223270"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("match-bot")

# ── In-Memory Storage ───────────────────────────────────────────

profiles: dict[int, dict] = {}       # user_id -> profile
match_requests: dict[str, dict] = {} # "uid1:uid2" -> {from, to, status}
activities: list[dict] = []          # live activity posts
blocked: dict[int, set] = {}         # user_id -> set of blocked user_ids

# ── Interest Categories ─────────────────────────────────────────

INTERESTS = {
    "tech":      {"emoji": "\U0001f4bb", "label": "\u05d8\u05db\u05e0\u05d5\u05dc\u05d5\u05d2\u05d9\u05d4"},
    "sports":    {"emoji": "\u26bd",     "label": "\u05e1\u05e4\u05d5\u05e8\u05d8"},
    "cooking":   {"emoji": "\U0001f373", "label": "\u05d1\u05d9\u05e9\u05d5\u05dc"},
    "music":     {"emoji": "\U0001f3b5", "label": "\u05de\u05d5\u05d6\u05d9\u05e7\u05d4"},
    "art":       {"emoji": "\U0001f3a8", "label": "\u05d0\u05de\u05e0\u05d5\u05ea"},
    "gaming":    {"emoji": "\U0001f3ae", "label": "\u05d2\u05d9\u05d9\u05de\u05d9\u05e0\u05d2"},
    "family":    {"emoji": "\U0001f46a", "label": "\u05de\u05e9\u05e4\u05d7\u05d4"},
    "education": {"emoji": "\U0001f4da", "label": "\u05d7\u05d9\u05e0\u05d5\u05da"},
    "business":  {"emoji": "\U0001f4bc", "label": "\u05e2\u05e1\u05e7\u05d9\u05dd"},
    "crypto":    {"emoji": "\U0001f4b0", "label": "\u05e7\u05e8\u05d9\u05e4\u05d8\u05d5"},
    "fitness":   {"emoji": "\U0001f4aa", "label": "\u05db\u05d5\u05e9\u05e8"},
    "nature":    {"emoji": "\U0001f333", "label": "\u05d8\u05d1\u05e2"},
}

# ── FSM States ──────────────────────────────────────────────────

class ProfileSetup(StatesGroup):
    name = State()
    bio = State()
    interests = State()

class EditProfile(StatesGroup):
    choose = State()
    name = State()
    bio = State()
    interests = State()

class ActivityPost(StatesGroup):
    text = State()

# ── Router ──────────────────────────────────────────────────────

router = Router()

# ── Helpers ─────────────────────────────────────────────────────

BRAND = "\u2728 SPARK IND \u00b7 Match & Friends"

def profile_text(p: dict) -> str:
    ints = ", ".join(
        f"{INTERESTS[i]['emoji']} {INTERESTS[i]['label']}" for i in p.get("interests", [])
    )
    ints_display = ints or "\u05d0\u05d9\u05df"
    joined = p.get("joined", "-")
    name = p["name"]
    bio = p.get("bio", "-")
    return (
        f"\U0001f464 {name}\n"
        f"\U0001f4dd {bio}\n"
        f"\U0001f3af \u05ea\u05d7\u05d5\u05de\u05d9\u05dd: {ints_display}\n"
        f"\U0001f4c5 \u05d4\u05e6\u05d8\u05e8\u05e4/\u05d4: {joined}"
    )

def match_key(a: int, b: int) -> str:
    return f"{min(a,b)}:{max(a,b)}"

def interests_keyboard(selected: list[str]) -> InlineKeyboardMarkup:
    rows = []
    items = list(INTERESTS.items())
    for i in range(0, len(items), 3):
        row = []
        for key, val in items[i:i+3]:
            check = "\u2705 " if key in selected else ""
            row.append(InlineKeyboardButton(
                text=f"{check}{val['emoji']} {val['label']}",
                callback_data=f"int:{key}"
            ))
        rows.append(row)
    rows.append([InlineKeyboardButton(text="\u2705 \u05e1\u05d9\u05d9\u05de\u05ea\u05d9!", callback_data="int:done")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def score(uid: int) -> int:
    """Social score: accepted matches + activities posted."""
    accepted = sum(
        1 for mk, mv in match_requests.items()
        if mv["status"] == "accepted" and uid in (mv["from"], mv["to"])
    )
    posted = sum(1 for a in activities if a["user_id"] == uid)
    return accepted * 3 + posted

# ── /start ──────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    if uid in profiles:
        await msg.answer(
            f"\U0001f44b \u05d4\u05d9\u05d9, {profiles[uid]['name']}! \u05db\u05d1\u05e8 \u05d9\u05e9 \u05dc\u05da \u05e4\u05e8\u05d5\u05e4\u05d9\u05dc.\n"
            f"\u05e9\u05dc\u05d7/\u05d9 /find \u05db\u05d3\u05d9 \u05dc\u05de\u05e6\u05d5\u05d0 \u05d7\u05d1\u05e8\u05d9\u05dd \u05d7\u05d3\u05e9\u05d9\u05dd!\n\n{BRAND}",
            parse_mode="HTML"
        )
        return

    await msg.answer(
        f"\U0001f31f <b>\u05d1\u05e8\u05d5\u05da \u05d4\u05d1\u05d0 \u05dc-SPARK IND Match & Friends!</b>\n\n"
        f"\u05db\u05d0\u05df \u05de\u05d5\u05e6\u05d0\u05d9\u05dd \u05d7\u05d1\u05e8\u05d9\u05dd \u05dc\u05e4\u05d9 \u05ea\u05d7\u05d5\u05de\u05d9\u05dd \u05de\u05e9\u05d5\u05ea\u05e4\u05d9\u05dd \u05d1\u05dc\u05d1\u05d3.\n"
        f"\u05dc\u05dc\u05d0 \u05d2\u05d9\u05dc, \u05dc\u05dc\u05d0 \u05ea\u05de\u05d5\u05e0\u05d5\u05ea \u05d7\u05d5\u05d1\u05d4 \u2013 \u05e8\u05e7 \u05ea\u05e9\u05d5\u05e7\u05d4!\n\n"
        f"\u05d1\u05d5\u05d0/\u05d9 \u05e0\u05ea\u05d7\u05d9\u05dc \u05e2\u05dd \u05d4\u05e4\u05e8\u05d5\u05e4\u05d9\u05dc \u05e9\u05dc\u05da.\n"
        f"\U0001f4dd <b>\u05de\u05d4 \u05d4\u05e9\u05dd \u05e9\u05dc\u05da?</b> (\u05db\u05d9\u05e0\u05d5\u05d9 / \u05e9\u05dd \u05d0\u05de\u05d9\u05ea\u05d9)",
        parse_mode="HTML"
    )
    await state.set_state(ProfileSetup.name)

@router.message(ProfileSetup.name)
async def setup_name(msg: Message, state: FSMContext):
    await state.update_data(name=msg.text.strip())
    await msg.answer(
        "\U0001f4ac <b>\u05e1\u05e4\u05e8/\u05d9 \u05e7\u05e6\u05ea \u05e2\u05dc \u05e2\u05e6\u05de\u05da</b> (\u05de\u05e9\u05e4\u05d8 \u05d0\u05d7\u05d3 \u05d0\u05d5 \u05e9\u05e0\u05d9\u05d9\u05dd):",
        parse_mode="HTML"
    )
    await state.set_state(ProfileSetup.bio)

@router.message(ProfileSetup.bio)
async def setup_bio(msg: Message, state: FSMContext):
    await state.update_data(bio=msg.text.strip(), interests=[])
    await msg.answer(
        "\U0001f3af <b>\u05d1\u05d7\u05e8/\u05d9 \u05ea\u05d7\u05d5\u05de\u05d9\u05dd:</b>\n\u05dc\u05d7\u05e5/\u05d9 \u05dc\u05d1\u05d7\u05d9\u05e8\u05d4/\u05d4\u05e1\u05e8\u05d4, \u05d5\u05d0\u05d6 \"\u05e1\u05d9\u05d9\u05de\u05ea\u05d9\".",
        parse_mode="HTML",
        reply_markup=interests_keyboard([])
    )
    await state.set_state(ProfileSetup.interests)

@router.callback_query(ProfileSetup.interests, F.data.startswith("int:"))
async def setup_interests_cb(cb: CallbackQuery, state: FSMContext):
    choice = cb.data.split(":")[1]
    data = await state.get_data()
    selected = data.get("interests", [])

    if choice == "done":
        if not selected:
            await cb.answer("\u05d1\u05d7\u05e8/\u05d9 \u05dc\u05e4\u05d7\u05d5\u05ea \u05ea\u05d7\u05d5\u05dd \u05d0\u05d7\u05d3!", show_alert=True)
            return
        uid = cb.from_user.id
        profiles[uid] = {
            "name": data["name"],
            "bio": data["bio"],
            "interests": selected,
            "joined": datetime.now().strftime("%d/%m/%Y"),
            "user_id": uid,
        }
        await state.clear()
        await cb.message.edit_text(
            f"\U0001f389 <b>\u05d4\u05e4\u05e8\u05d5\u05e4\u05d9\u05dc \u05e0\u05d5\u05e6\u05e8!</b>\n\n"
            f"{profile_text(profiles[uid])}\n\n"
            f"\u05e9\u05dc\u05d7/\u05d9 /find \u05dc\u05de\u05e6\u05d5\u05d0 \u05d7\u05d1\u05e8\u05d9\u05dd \u05e2\u05dd \u05ea\u05d7\u05d5\u05de\u05d9\u05dd \u05de\u05e9\u05d5\u05ea\u05e4\u05d9\u05dd!\n\n{BRAND}",
            parse_mode="HTML"
        )
        return

    if choice in selected:
        selected.remove(choice)
    else:
        selected.append(choice)
    await state.update_data(interests=selected)
    await cb.message.edit_reply_markup(reply_markup=interests_keyboard(selected))
    await cb.answer()

# ── /profile ────────────────────────────────────────────────────

@router.message(Command("profile"))
async def cmd_profile(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    if uid not in profiles:
        await msg.answer("\u05d0\u05d9\u05df \u05dc\u05da \u05e4\u05e8\u05d5\u05e4\u05d9\u05dc \u05e2\u05d3\u05d9\u05d9\u05df. \u05e9\u05dc\u05d7/\u05d9 /start \u05dc\u05d9\u05e6\u05d9\u05e8\u05d4.")
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="\u270f\ufe0f \u05e2\u05e8\u05d9\u05db\u05ea \u05e9\u05dd", callback_data="edit:name"),
            InlineKeyboardButton(text="\u270f\ufe0f \u05e2\u05e8\u05d9\u05db\u05ea \u05d1\u05d9\u05d5", callback_data="edit:bio"),
        ],
        [InlineKeyboardButton(text="\U0001f3af \u05e2\u05e8\u05d9\u05db\u05ea \u05ea\u05d7\u05d5\u05de\u05d9\u05dd", callback_data="edit:interests")],
    ])
    await msg.answer(
        f"\U0001f464 <b>\u05d4\u05e4\u05e8\u05d5\u05e4\u05d9\u05dc \u05e9\u05dc\u05da:</b>\n\n{profile_text(profiles[uid])}\n\n{BRAND}",
        parse_mode="HTML",
        reply_markup=kb,
    )

@router.callback_query(F.data.startswith("edit:"))
async def edit_profile_start(cb: CallbackQuery, state: FSMContext):
    field = cb.data.split(":")[1]
    if field == "name":
        await cb.message.answer("\u270f\ufe0f \u05e9\u05dc\u05d7/\u05d9 \u05e9\u05dd \u05d7\u05d3\u05e9:")
        await state.set_state(EditProfile.name)
    elif field == "bio":
        await cb.message.answer("\u270f\ufe0f \u05e9\u05dc\u05d7/\u05d9 \u05d1\u05d9\u05d5 \u05d7\u05d3\u05e9:")
        await state.set_state(EditProfile.bio)
    elif field == "interests":
        current = profiles.get(cb.from_user.id, {}).get("interests", [])
        await state.update_data(interests=list(current))
        await cb.message.answer(
            "\U0001f3af \u05d1\u05d7\u05e8/\u05d9 \u05ea\u05d7\u05d5\u05de\u05d9\u05dd \u05d7\u05d3\u05e9\u05d9\u05dd:",
            reply_markup=interests_keyboard(current),
        )
        await state.set_state(EditProfile.interests)
    await cb.answer()

@router.message(EditProfile.name)
async def edit_name(msg: Message, state: FSMContext):
    profiles[msg.from_user.id]["name"] = msg.text.strip()
    await state.clear()
    await msg.answer("\u2705 \u05d4\u05e9\u05dd \u05e2\u05d5\u05d3\u05db\u05df!")

@router.message(EditProfile.bio)
async def edit_bio(msg: Message, state: FSMContext):
    profiles[msg.from_user.id]["bio"] = msg.text.strip()
    await state.clear()
    await msg.answer("\u2705 \u05d4\u05d1\u05d9\u05d5 \u05e2\u05d5\u05d3\u05db\u05df!")

@router.callback_query(EditProfile.interests, F.data.startswith("int:"))
async def edit_interests_cb(cb: CallbackQuery, state: FSMContext):
    choice = cb.data.split(":")[1]
    data = await state.get_data()
    selected = data.get("interests", [])

    if choice == "done":
        if not selected:
            await cb.answer("\u05d1\u05d7\u05e8/\u05d9 \u05dc\u05e4\u05d7\u05d5\u05ea \u05ea\u05d7\u05d5\u05dd \u05d0\u05d7\u05d3!", show_alert=True)
            return
        profiles[cb.from_user.id]["interests"] = selected
        await state.clear()
        await cb.message.edit_text("\u2705 \u05d4\u05ea\u05d7\u05d5\u05de\u05d9\u05dd \u05e2\u05d5\u05d3\u05db\u05e0\u05d5!")
        return

    if choice in selected:
        selected.remove(choice)
    else:
        selected.append(choice)
    await state.update_data(interests=selected)
    await cb.message.edit_reply_markup(reply_markup=interests_keyboard(selected))
    await cb.answer()

# ── /find ───────────────────────────────────────────────────────

@router.message(Command("find"))
async def cmd_find(msg: Message):
    uid = msg.from_user.id
    if uid not in profiles:
        await msg.answer("\u05e6\u05e8\u05d9\u05da \u05e4\u05e8\u05d5\u05e4\u05d9\u05dc \u05e7\u05d5\u05d3\u05dd! /start")
        return

    my_interests = set(profiles[uid]["interests"])
    my_blocked = blocked.get(uid, set())
    matches = []

    for oid, op in profiles.items():
        if oid == uid or oid in my_blocked:
            continue
        if uid in blocked.get(oid, set()):
            continue
        shared = my_interests & set(op["interests"])
        if shared:
            matches.append((oid, op, shared))

    matches.sort(key=lambda x: len(x[2]), reverse=True)

    if not matches:
        await msg.answer(
            "\U0001f614 \u05dc\u05d0 \u05e0\u05de\u05e6\u05d0\u05d5 \u05d4\u05ea\u05d0\u05de\u05d5\u05ea \u05e2\u05d3\u05d9\u05d9\u05df.\n\u05d4\u05d6\u05de\u05d9\u05e0/\u05d9 \u05d7\u05d1\u05e8\u05d9\u05dd \u05d5\u05e0\u05e1\u05d4 \u05e9\u05d5\u05d1!"
        )
        return

    text = f"\U0001f50d <b>\u05d4\u05ea\u05d0\u05de\u05d5\u05ea \u05e9\u05e0\u05de\u05e6\u05d0\u05d5 ({len(matches)}):</b>\n\n"
    buttons = []
    for oid, op, shared in matches[:10]:
        shared_labels = ", ".join(INTERESTS[s]["emoji"] + INTERESTS[s]["label"] for s in shared)
        mk = match_key(uid, oid)
        mr = match_requests.get(mk)
        status = ""
        if mr and mr["status"] == "accepted":
            status = " \u2705 \u05de\u05d7\u05d5\u05d1\u05e8\u05d9\u05dd!"
        elif mr and mr["from"] == uid:
            status = " \u23f3 \u05de\u05d7\u05db\u05d4 \u05dc\u05d0\u05d9\u05e9\u05d5\u05e8"
        elif mr and mr["to"] == uid:
            status = " \U0001f4e9 \u05d1\u05d9\u05e7\u05e9/\u05d4 \u05dc\u05d4\u05ea\u05d7\u05d1\u05e8!"

        text += f"\u2022 <b>{op['name']}</b> \u2013 {shared_labels}{status}\n"

        if not mr or (mr["status"] == "pending" and mr["to"] == uid):
            label = "\U0001f91d \u05d4\u05ea\u05d7\u05d1\u05e8" if (mr and mr["to"] == uid) else "\U0001f44b \u05e9\u05dc\u05d7 \u05d1\u05e7\u05e9\u05d4"
            buttons.append([InlineKeyboardButton(
                text=f"{label} \u2013 {op['name']}",
                callback_data=f"match:{oid}"
            )])

    text += f"\n{BRAND}"
    kb = InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None
    await msg.answer(text, parse_mode="HTML", reply_markup=kb)

# ── Match request / accept ──────────────────────────────────────

@router.callback_query(F.data.startswith("match:"))
async def handle_match(cb: CallbackQuery):
    uid = cb.from_user.id
    oid = int(cb.data.split(":")[1])
    mk = match_key(uid, oid)
    mr = match_requests.get(mk)

    if uid not in profiles:
        await cb.answer("\u05e6\u05e8\u05d9\u05da \u05e4\u05e8\u05d5\u05e4\u05d9\u05dc \u05e7\u05d5\u05d3\u05dd!", show_alert=True)
        return

    bot: Bot = cb.bot

    if mr and mr["status"] == "accepted":
        await cb.answer("\u05db\u05d1\u05e8 \u05de\u05d7\u05d5\u05d1\u05e8\u05d9\u05dd!", show_alert=True)
        return

    if mr and mr["status"] == "pending" and mr["to"] == uid:
        # Accept!
        mr["status"] = "accepted"
        my_name = profiles[uid]["name"]
        their_name = profiles[oid]["name"]

        await cb.message.answer(
            f"\U0001f389 <b>\u05d4\u05ea\u05d7\u05d1\u05e8\u05ea\u05dd!</b>\n\n"
            f"\u05d0\u05ea/\u05d4 \u05d5-{their_name} \u05e2\u05db\u05e9\u05d9\u05d5 \u05d7\u05d1\u05e8\u05d9\u05dd \u05d1-SPARK IND!\n"
            f"\u05d0\u05e4\u05e9\u05e8 \u05dc\u05e4\u05e0\u05d5\u05ea \u05d9\u05e9\u05d9\u05e8\u05d5\u05ea \u05d1\u05d8\u05dc\u05d2\u05e8\u05dd \U0001f449 tg://user?id={oid}",
            parse_mode="HTML"
        )
        try:
            await bot.send_message(
                oid,
                f"\U0001f389 <b>{my_name} \u05d0\u05d9\u05e9\u05e8/\u05d4 \u05d0\u05ea \u05d4\u05d7\u05d9\u05d1\u05d5\u05e8!</b>\n\n"
                f"\u05d0\u05ea\u05dd \u05e2\u05db\u05e9\u05d9\u05d5 \u05d7\u05d1\u05e8\u05d9\u05dd! \U0001f449 tg://user?id={uid}",
                parse_mode="HTML"
            )
        except Exception:
            pass
        await cb.answer("\u05de\u05d7\u05d5\u05d1\u05e8\u05d9\u05dd! \U0001f389")
        return

    if mr and mr["from"] == uid:
        await cb.answer("\u05db\u05d1\u05e8 \u05e9\u05dc\u05d7\u05ea \u05d1\u05e7\u05e9\u05d4, \u05de\u05d7\u05db\u05d4...", show_alert=True)
        return

    # New request
    match_requests[mk] = {"from": uid, "to": oid, "status": "pending"}
    their_name = profiles[oid]["name"]
    my_name = profiles[uid]["name"]

    await cb.answer(f"\U0001f4e8 \u05d1\u05e7\u05e9\u05d4 \u05e0\u05e9\u05dc\u05d7\u05d4 \u05dc-{their_name}!")

    try:
        shared = set(profiles[uid]["interests"]) & set(profiles[oid]["interests"])
        shared_labels = ", ".join(INTERESTS[s]["emoji"] + INTERESTS[s]["label"] for s in shared)
        await bot.send_message(
            oid,
            f"\U0001f44b <b>\u05de\u05d9\u05e9\u05d4\u05d5 \u05e8\u05d5\u05e6\u05d4 \u05dc\u05d4\u05ea\u05d7\u05d1\u05e8!</b>\n\n"
            f"\u05ea\u05d7\u05d5\u05de\u05d9\u05dd \u05de\u05e9\u05d5\u05ea\u05e4\u05d9\u05dd: {shared_labels}\n\n"
            f"\u05dc\u05d7\u05e5/\u05d9 \u05dc\u05d0\u05e9\u05e8 \u05d0\u05ea \u05d4\u05d7\u05d9\u05d1\u05d5\u05e8:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="\u2705 \u05dc\u05d0\u05e9\u05e8!", callback_data=f"match:{uid}")],
                [InlineKeyboardButton(text="\u274c \u05dc\u05d0 \u05ea\u05d5\u05d3\u05d4", callback_data=f"decline:{uid}")],
            ])
        )
    except Exception:
        pass

@router.callback_query(F.data.startswith("decline:"))
async def handle_decline(cb: CallbackQuery):
    uid = cb.from_user.id
    oid = int(cb.data.split(":")[1])
    mk = match_key(uid, oid)
    if mk in match_requests:
        match_requests[mk]["status"] = "declined"
    await cb.message.edit_text("\u05d3\u05d7\u05d9\u05ea \u05d0\u05ea \u05d4\u05d1\u05e7\u05e9\u05d4.")
    await cb.answer()

# ── /matches ────────────────────────────────────────────────────

@router.message(Command("matches"))
async def cmd_matches(msg: Message):
    uid = msg.from_user.id
    accepted = []
    pending_in = []
    pending_out = []

    for mk, mr in match_requests.items():
        if mr["status"] == "accepted" and uid in (mr["from"], mr["to"]):
            other = mr["to"] if mr["from"] == uid else mr["from"]
            if other in profiles:
                accepted.append(profiles[other])
        elif mr["status"] == "pending" and mr["to"] == uid:
            if mr["from"] in profiles:
                pending_in.append(profiles[mr["from"]])
        elif mr["status"] == "pending" and mr["from"] == uid:
            if mr["to"] in profiles:
                pending_out.append(profiles[mr["to"]])

    text = f"\U0001f91d <b>\u05d4\u05d7\u05d9\u05d1\u05d5\u05e8\u05d9\u05dd \u05e9\u05dc\u05da:</b>\n\n"

    if accepted:
        text += "<b>\u2705 \u05d7\u05d1\u05e8\u05d9\u05dd \u05de\u05d0\u05d5\u05e9\u05e8\u05d9\u05dd:</b>\n"
        for p in accepted:
            text += f"  \u2022 {p['name']} \u2013 tg://user?id={p['user_id']}\n"
    else:
        text += "\u05d0\u05d9\u05df \u05d7\u05d9\u05d1\u05d5\u05e8\u05d9\u05dd \u05de\u05d0\u05d5\u05e9\u05e8\u05d9\u05dd \u05e2\u05d3\u05d9\u05d9\u05df.\n"

    if pending_in:
        text += f"\n<b>\U0001f4e9 \u05d1\u05e7\u05e9\u05d5\u05ea \u05e9\u05d4\u05ea\u05e7\u05d1\u05dc\u05d5 ({len(pending_in)}):</b>\n"
        for p in pending_in:
            text += f"  \u2022 {p['name']}\n"
        text += "\u05e9\u05dc\u05d7/\u05d9 /find \u05dc\u05d0\u05e9\u05e8 \u05d0\u05d5\u05ea\u05dd!\n"

    if pending_out:
        text += f"\n<b>\u23f3 \u05d1\u05e7\u05e9\u05d5\u05ea \u05e9\u05e9\u05dc\u05d7\u05ea ({len(pending_out)}):</b>\n"
        for p in pending_out:
            text += f"  \u2022 {p['name']}\n"

    text += f"\n{BRAND}"
    await msg.answer(text, parse_mode="HTML")

# ── /activity ───────────────────────────────────────────────────

@router.message(Command("activity"))
async def cmd_activity(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    if uid not in profiles:
        await msg.answer("\u05e6\u05e8\u05d9\u05da \u05e4\u05e8\u05d5\u05e4\u05d9\u05dc \u05e7\u05d5\u05d3\u05dd! /start")
        return

    await msg.answer(
        "\U0001f3c3 <b>\u05de\u05d4 \u05d0\u05ea/\u05d4 \u05de\u05d7\u05e4\u05e9/\u05ea \u05e2\u05db\u05e9\u05d9\u05d5?</b>\n\n"
        "\u05db\u05ea\u05d1/\u05d9 \u05dc\u05de\u05e9\u05dc, \u05de\u05e9\u05d4\u05d5:\n"
        "\u2022 \"\u05de\u05d7\u05e4\u05e9 \u05e9\u05d5\u05ea\u05e3 \u05dc\u05e8\u05d9\u05e6\u05d4\"\n"
        "\u2022 \"\u05de\u05d9 \u05d1\u05d0 \u05dc\u05d1\u05e9\u05dc \u05d1\u05d9\u05d7\u05d3?\"\n"
        "\u2022 \"\u05e8\u05d5\u05e6\u05d4 \u05dc\u05e9\u05d7\u05e7 \u05de\u05e9\u05d7\u05e7 \u05dc\u05d5\u05d7\"",
        parse_mode="HTML"
    )
    await state.set_state(ActivityPost.text)

@router.message(ActivityPost.text)
async def post_activity(msg: Message, state: FSMContext):
    uid = msg.from_user.id
    p = profiles[uid]

    activity = {
        "user_id": uid,
        "name": p["name"],
        "text": msg.text.strip(),
        "interests": p["interests"],
        "time": datetime.now(),
    }
    activities.append(activity)
    await state.clear()

    await msg.answer(
        f"\u2705 <b>\u05e4\u05d5\u05e8\u05e1\u05dd!</b>\n\n"
        f"\U0001f4e2 {p['name']}: \"{msg.text.strip()}\"\n\n"
        f"\u05e0\u05e9\u05dc\u05d7 \u05d4\u05ea\u05e8\u05d0\u05d4 \u05dc\u05d7\u05d1\u05e8\u05d9\u05dd \u05e2\u05dd \u05ea\u05d7\u05d5\u05de\u05d9\u05dd \u05de\u05e9\u05d5\u05ea\u05e4\u05d9\u05dd!",
        parse_mode="HTML"
    )

    # Notify matched users with shared interests
    my_interests = set(p["interests"])
    bot: Bot = msg.bot
    notified = 0
    for oid, op in profiles.items():
        if oid == uid:
            continue
        if uid in blocked.get(oid, set()):
            continue
        shared = my_interests & set(op["interests"])
        if shared:
            try:
                await bot.send_message(
                    oid,
                    f"\U0001f514 <b>\u05e4\u05e2\u05d9\u05dc\u05d5\u05ea \u05d7\u05d3\u05e9\u05d4!</b>\n\n"
                    f"\u05de\u05d9\u05e9\u05d4\u05d5 \u05e2\u05dd \u05ea\u05d7\u05d5\u05de\u05d9\u05dd \u05de\u05e9\u05d5\u05ea\u05e4\u05d9\u05dd \u05de\u05d7\u05e4\u05e9:\n"
                    f"\U0001f4ac \"{msg.text.strip()}\"\n\n"
                    f"\u05e9\u05dc\u05d7/\u05d9 /find \u05dc\u05d4\u05ea\u05d7\u05d1\u05e8!",
                    parse_mode="HTML"
                )
                notified += 1
            except Exception:
                pass

    if notified:
        await msg.answer(f"\U0001f4e8 \u05e0\u05e9\u05dc\u05d7\u05d4 \u05d4\u05ea\u05e8\u05d0\u05d4 \u05dc-{notified} \u05d0\u05e0\u05e9\u05d9\u05dd \u05e2\u05dd \u05ea\u05d7\u05d5\u05de\u05d9\u05dd \u05d3\u05d5\u05de\u05d9\u05dd!")

# ── /active ─────────────────────────────────────────────────────

@router.message(Command("active"))
async def cmd_active(msg: Message):
    """Show recent activities (last 2 hours)."""
    cutoff = datetime.now() - timedelta(hours=2)
    recent = [a for a in activities if a["time"] > cutoff]
    recent.sort(key=lambda x: x["time"], reverse=True)

    if not recent:
        await msg.answer("\U0001f634 \u05d0\u05d9\u05df \u05e4\u05e2\u05d9\u05dc\u05d5\u05d9\u05d5\u05ea \u05d0\u05d7\u05e8\u05d5\u05e0\u05d5\u05ea. \u05e4\u05e8\u05e1\u05dd/\u05d9 \u05d0\u05d7\u05ea \u05e2\u05dd /activity!")
        return

    text = f"\U0001f525 <b>\u05de\u05d9 \u05e4\u05e2\u05d9\u05dc \u05e2\u05db\u05e9\u05d9\u05d5?</b>\n\n"
    for a in recent[:10]:
        mins_ago = int((datetime.now() - a["time"]).total_seconds() / 60)
        text += f"\u2022 <b>{a['name']}</b> ({mins_ago} \u05d3\u05e7\u05d5\u05ea): {a['text']}\n"

    text += f"\n\u05e9\u05dc\u05d7/\u05d9 /activity \u05dc\u05e4\u05e8\u05e1\u05dd \u05de\u05e9\u05d4\u05d5 \u05de\u05e9\u05dc\u05da!\n\n{BRAND}"
    await msg.answer(text, parse_mode="HTML")

# ── /leaderboard ────────────────────────────────────────────────

@router.message(Command("leaderboard"))
async def cmd_leaderboard(msg: Message):
    if not profiles:
        await msg.answer("\u05d0\u05d9\u05df \u05de\u05e9\u05ea\u05de\u05e9\u05d9\u05dd \u05e2\u05d3\u05d9\u05d9\u05df.")
        return

    scored = [(uid, p, score(uid)) for uid, p in profiles.items()]
    scored.sort(key=lambda x: x[2], reverse=True)

    medals = ["\U0001f947", "\U0001f948", "\U0001f949"]
    text = f"\U0001f3c6 <b>\u05dc\u05d5\u05d7 \u05de\u05dc\u05db\u05d9\u05dd \u2013 \u05d4\u05db\u05d9 \u05d7\u05d1\u05e8\u05ea\u05d9\u05d9\u05dd:</b>\n\n"
    for i, (uid, p, sc) in enumerate(scored[:10]):
        medal = medals[i] if i < 3 else f"{i+1}."
        text += f"{medal} <b>{p['name']}</b> \u2013 {sc} \u05e0\u05e7\u05d5\u05d3\u05d5\u05ea\n"

    text += f"\n\u05e0\u05e7\u05d5\u05d3\u05d5\u05ea = \u05d7\u05d9\u05d1\u05d5\u05e8\u05d9\u05dd (\u00d73) + \u05e4\u05e2\u05d9\u05dc\u05d5\u05d9\u05d5\u05ea\n\n{BRAND}"
    await msg.answer(text, parse_mode="HTML")

# ── /block ──────────────────────────────────────────────────────

@router.message(Command("block"))
async def cmd_block(msg: Message):
    """Block a user by replying to their forwarded message or by ID."""
    parts = msg.text.split()
    if len(parts) < 2:
        await msg.answer("\u05e9\u05d9\u05de\u05d5\u05e9: /block <user_id>")
        return
    try:
        target = int(parts[1])
    except ValueError:
        await msg.answer("\u05e0\u05d0 \u05dc\u05e9\u05dc\u05d5\u05d7 \u05de\u05d6\u05d4\u05d4 \u05de\u05e9\u05ea\u05de\u05e9 \u05ea\u05e7\u05d9\u05df.")
        return
    blocked.setdefault(msg.from_user.id, set()).add(target)
    await msg.answer("\u2705 \u05d4\u05de\u05e9\u05ea\u05de\u05e9 \u05e0\u05d7\u05e1\u05dd.")

# ── /help ───────────────────────────────────────────────────────

@router.message(Command("help"))
async def cmd_help(msg: Message):
    await msg.answer(
        f"\U0001f4d6 <b>\u05e4\u05e7\u05d5\u05d3\u05d5\u05ea \u2013 SPARK IND Match & Friends</b>\n\n"
        f"/start \u2013 \u05d4\u05e8\u05e9\u05de\u05d4 + \u05d9\u05e6\u05d9\u05e8\u05ea \u05e4\u05e8\u05d5\u05e4\u05d9\u05dc\n"
        f"/profile \u2013 \u05e6\u05e4\u05d9\u05d9\u05d4/\u05e2\u05e8\u05d9\u05db\u05ea \u05e4\u05e8\u05d5\u05e4\u05d9\u05dc\n"
        f"/find \u2013 \u05de\u05e6\u05d0 \u05d7\u05d1\u05e8\u05d9\u05dd \u05dc\u05e4\u05d9 \u05ea\u05d7\u05d5\u05de\u05d9\u05dd\n"
        f"/matches \u2013 \u05d4\u05d7\u05d9\u05d1\u05d5\u05e8\u05d9\u05dd \u05e9\u05dc\u05da\n"
        f"/activity \u2013 \u05e4\u05e8\u05e1\u05dd \"\u05d0\u05e0\u05d9 \u05de\u05d7\u05e4\u05e9 \u05e2\u05db\u05e9\u05d9\u05d5...\"\n"
        f"/active \u2013 \u05de\u05d9 \u05e4\u05e2\u05d9\u05dc \u05e2\u05db\u05e9\u05d9\u05d5?\n"
        f"/leaderboard \u2013 \u05d4\u05db\u05d9 \u05d7\u05d1\u05e8\u05ea\u05d9\u05d9\u05dd\n"
        f"/block <id> \u2013 \u05d7\u05e1\u05d9\u05de\u05ea \u05de\u05e9\u05ea\u05de\u05e9\n"
        f"/help \u2013 \u05d4\u05e2\u05d6\u05e8\u05d4 \u05d6\u05d5\n\n"
        f"\U0001f512 \u05d4\u05d6\u05d4\u05d5\u05d9\u05d5\u05ea \u05e0\u05d7\u05e9\u05e4\u05d5\u05ea \u05e8\u05e7 \u05d0\u05d7\u05e8\u05d9 \u05d4\u05e1\u05db\u05de\u05d4 \u05d4\u05d3\u05d3\u05d9\u05ea!\n\n{BRAND}",
        parse_mode="HTML"
    )

# ── Main ────────────────────────────────────────────────────────

async def main():
    if not BOT_TOKEN:
        log.error("BOT_TOKEN not set!")
        return

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    log.info(f"SPARK IND Match & Friends Bot starting...")
    log.info(f"Admin: {ADMIN_USER_ID}")
    log.info(f"Payments module: {'loaded' if HAS_PAYMENTS else 'not available'}")

    me = None
    try:
        me = await bot.get_me()
        log.info(f"Bot: @{me.username} ({me.id})")
    except Exception as e:
        log.error(f"Failed to get bot info: {e}")

    # Coordination: register inbound + post ready (no-op if env unset)
    try:
        from shared.coordination import init_coordination_for_bot
        await init_coordination_for_bot(
            bot, dp,
            name="game-bot",
            username=(me.username if me else None),
        )
    except Exception as e:
        log.warning(f"coordination init failed: {e}")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
