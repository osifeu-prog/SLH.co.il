from pathlib import Path
import re
import shutil

path = Path(r"D:\SLH_PROJECT_V2\bot_full.py")
backup = Path(r"D:\SLH_PROJECT_V2\bot_full.py.bak_ascii_fix")

if not path.exists():
    raise SystemExit("bot_full.py not found")

shutil.copy2(path, backup)
text = path.read_text(encoding="utf-8")

# -----------------------------
# 1) Inject ASCII-safe Hebrew block
# -----------------------------
ascii_block = r'''
def H(s: str) -> str:
    return s.encode("ascii").decode("unicode_escape")


WELCOME_UNPAID = H(
    "\u05d1\u05e8\u05d5\u05da \u05d4\u05d1\u05d0.\n\n"
    "\u05db\u05d3\u05d9 \u05dc\u05e7\u05d1\u05dc \u05d2\u05d9\u05e9\u05d4 \u05de\u05dc\u05d0\u05d4 "
    "\u05d9\u05e9 \u05dc\u05d4\u05e9\u05dc\u05d9\u05dd \u05ea\u05e9\u05dc\u05d5\u05dd \u05e9\u05dc "
    f"{PRICE_ILS} "
    "\u05e9\"\u05d7.\n\n"
    "\u05dc\u05d0\u05d7\u05e8 \u05d4\u05ea\u05e9\u05dc\u05d5\u05dd \u05e9\u05dc\u05d7 "
    "\u05e6\u05d9\u05dc\u05d5\u05dd \u05de\u05e1\u05da / hash / \u05d0\u05e1\u05de\u05db\u05ea\u05d0.\n"
    "\u05e8\u05e7 \u05d0\u05d7\u05e8\u05d9 \u05d1\u05d3\u05d9\u05e7\u05ea \u05d0\u05d3\u05de\u05d9\u05df "
    "\u05d4\u05d2\u05d9\u05e9\u05d4 \u05ea\u05d0\u05d5\u05e9\u05e8."
)

WELCOME_PAID = H(
    "\u05d4\u05ea\u05e9\u05dc\u05d5\u05dd \u05e9\u05dc\u05da \u05d0\u05d5\u05e9\u05e8.\n\n"
    "\u05d4\u05d2\u05d9\u05e9\u05d4 \u05e9\u05dc\u05da \u05e4\u05e2\u05d9\u05dc\u05d4 \u05db\u05e2\u05ea."
)

PAYMENT_TEXT = H(
    "\u05d1\u05e7\u05e9\u05ea \u05ea\u05e9\u05dc\u05d5\u05dd \u05e0\u05e4\u05ea\u05d7\u05d4.\n\n"
    "\u05e1\u05db\u05d5\u05dd \u05dc\u05ea\u05e9\u05dc\u05d5\u05dd:\n"
    f"{PRICE_ILS} "
    "\u05e9\"\u05d7\n\n"
    "\u05e8\u05e9\u05ea:\n"
    f"{PAYMENT_NETWORK}\n\n"
    "\u05db\u05ea\u05d5\u05d1\u05ea \u05d4\u05d0\u05e8\u05e0\u05e7 \u05dc\u05ea\u05e9\u05dc\u05d5\u05dd:\n"
    f"{PAYMENT_WALLET_ADDRESS}\n\n"
    "\u05d7\u05e9\u05d5\u05d1:\n"
    "- \u05d4\u05d2\u05d9\u05e9\u05d4 \u05ea\u05d0\u05d5\u05e9\u05e8 \u05e8\u05e7 \u05dc\u05d0\u05d7\u05e8 "
    "\u05ea\u05e9\u05dc\u05d5\u05dd \u05d1\u05e4\u05d5\u05e2\u05dc \u05dc\u05db\u05ea\u05d5\u05d1\u05ea "
    "\u05d4\u05d6\u05d0\u05ea\n"
    "- \u05dc\u05d0\u05d7\u05e8 \u05d4\u05ea\u05e9\u05dc\u05d5\u05dd \u05e9\u05dc\u05d7 "
    "\u05e6\u05d9\u05dc\u05d5\u05dd \u05de\u05e1\u05da / hash / \u05d0\u05e1\u05de\u05db\u05ea\u05d0\n"
    "- \u05e8\u05e7 \u05d0\u05d7\u05e8\u05d9 \u05d1\u05d3\u05d9\u05e7\u05ea \u05d0\u05d3\u05de\u05d9\u05df "
    "\u05ea\u05e7\u05d1\u05dc \u05d2\u05d9\u05e9\u05d4\n\n"
    "\u05dc\u05d0\u05d7\u05e8 \u05e9\u05dc\u05d9\u05d7\u05ea \u05d4\u05ea\u05e9\u05dc\u05d5\u05dd "
    "\u05d0\u05e4\u05e9\u05e8 \u05dc\u05e9\u05dc\u05d5\u05d7 \u05e9\u05d5\u05d1 BUY "
    "\u05d0\u05d5 \u05dc\u05e9\u05dc\u05d5\u05d7 \u05d0\u05ea \u05d4\u05d0\u05e1\u05de\u05db\u05ea\u05d0 "
    "\u05db\u05d0\u05df \u05d1\u05e6'\u05d0\u05d8."
)

PENDING_TEXT = H(
    "\u05db\u05d1\u05e8 \u05e7\u05d9\u05d9\u05de\u05ea \u05d0\u05e6\u05dc\u05da "
    "\u05d1\u05e7\u05e9\u05ea \u05ea\u05e9\u05dc\u05d5\u05dd \u05e4\u05ea\u05d5\u05d7\u05d4.\n\n"
    "\u05d9\u05e9 \u05dc\u05d4\u05e9\u05dc\u05d9\u05dd \u05d0\u05ea \u05d4\u05ea\u05e9\u05dc\u05d5\u05dd "
    "\u05d4\u05e7\u05d9\u05d9\u05dd \u05d5\u05dc\u05e9\u05dc\u05d5\u05d7 \u05d0\u05e1\u05de\u05db\u05ea\u05d0 "
    "\u05db\u05d0\u05df \u05d1\u05e6'\u05d0\u05d8.\n"
    "\u05d0\u05d9\u05df \u05e6\u05d5\u05e8\u05da \u05dc\u05e4\u05ea\u05d5\u05d7 "
    "\u05d1\u05e7\u05e9\u05d4 \u05e0\u05d5\u05e1\u05e4\u05ea \u05db\u05e8\u05d2\u05e2."
)

ACCESS_LINK_LABEL = H(
    "\u05dc\u05d9\u05e0\u05e7 \u05d4\u05d2\u05d9\u05e9\u05d4 \u05e9\u05dc\u05da:"
)

ALREADY_ACTIVE = H(
    "\u05d4\u05d2\u05d9\u05e9\u05d4 \u05e9\u05dc\u05da \u05db\u05d1\u05e8 \u05e4\u05e2\u05d9\u05dc\u05d4."
)

NO_PERMISSION = H(
    "\u05d0\u05d9\u05df \u05d4\u05e8\u05e9\u05d0\u05d4."
)

USAGE_APPROVE = "Usage: /approve <user_id>"
USAGE_REJECT = "Usage: /reject <user_id>"
USAGE_STATUS = "Usage: /status <user_id>"
NO_AUDIT_YET = H("\u05d0\u05d9\u05df \u05dc\u05d5\u05d2\u05d9\u05dd \u05e2\u05d3\u05d9\u05d9\u05df.")
SEND_BUY_HINT = H(
    "\u05db\u05d3\u05d9 \u05dc\u05e4\u05ea\u05d5\u05d7 \u05d1\u05e7\u05e9\u05ea \u05ea\u05e9\u05dc\u05d5\u05dd "
    "\u05e9\u05dc\u05d7 BUY."
)
PAYMENT_OPENED = H(
    "\u05d1\u05e7\u05e9\u05ea \u05ea\u05e9\u05dc\u05d5\u05dd \u05e0\u05e4\u05ea\u05d7\u05d4"
)
REJECTED_USER_TEXT = H(
    "\u05d1\u05e7\u05e9\u05ea \u05d4\u05ea\u05e9\u05dc\u05d5\u05dd \u05e0\u05d3\u05d7\u05ea\u05d4. "
    "\u05d0\u05e4\u05e9\u05e8 \u05dc\u05e9\u05dc\u05d5\u05d7 BUY \u05de\u05d7\u05d3\u05e9 "
    "\u05d5\u05dc\u05e4\u05ea\u05d5\u05d7 \u05d1\u05e7\u05e9\u05d4 \u05d7\u05d3\u05e9\u05d4."
)
BUY_BUTTON_TEXT = H(
    "\u05e8\u05db\u05d5\u05e9 \u05d2\u05d9\u05e9\u05d4 \u05d1-"
) + f"{PRICE_ILS} " + H("\u05e9\"\u05d7")
'''

text, n = re.subn(
    r'WELCOME_UNPAID\s*=.*?PENDING_TEXT\s*=\s*""".*?"""',
    ascii_block.strip(),
    text,
    count=1,
    flags=re.DOTALL,
)
print(f"replaced text block: {n}")

# -----------------------------
# 2) Fix /start handler
# -----------------------------
start_handler = r'''@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    upsert_user(message.from_user.id, message.from_user.username)

    if is_paid(message.from_user.id):
        text = WELCOME_PAID
        if VIP_GROUP_LINK:
            text += f"\n\n{ACCESS_LINK_LABEL}\n{VIP_GROUP_LINK}"
        await message.answer(text)
    else:
        kb = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text=BUY_BUTTON_TEXT, callback_data="buy_now")]
            ]
        )
        await message.answer(WELCOME_UNPAID, reply_markup=kb)
'''

text, n = re.subn(
    r'@dp\.message\(Command\("start"\)\)\s+async def start_cmd\(message: types\.Message\):.*?(?=@dp\.callback_query\(F\.data == "buy_now"\))',
    start_handler + "\n\n",
    text,
    count=1,
    flags=re.DOTALL,
)
print(f"replaced /start handler: {n}")

# -----------------------------
# 3) Fix buy_now handler
# -----------------------------
buy_now_handler = r'''@dp.callback_query(F.data == "buy_now")
async def buy_now(callback: types.CallbackQuery):
    upsert_user(callback.from_user.id, callback.from_user.username)

    if is_paid(callback.from_user.id):
        text = ALREADY_ACTIVE
        if VIP_GROUP_LINK:
            text += f"\n\n{ACCESS_LINK_LABEL}\n{VIP_GROUP_LINK}"
        await callback.message.answer(text)
        await callback.answer()
        return

    if has_pending_request(callback.from_user.id):
        await callback.message.answer(PENDING_TEXT)

        log_admin_event(
            "payment.request.duplicate_blocked",
            actor_user_id=callback.from_user.id,
            actor_username=callback.from_user.username,
            target_user_id=callback.from_user.id,
            target_username=callback.from_user.username,
            entity_type="payment_request",
            success=True,
            reason="buy_now blocked because pending request already exists",
            metadata={"source": "callback", "button": "buy_now", "bot_username": BOT_USERNAME},
        )

        await callback.answer()
        return

    req_id = create_payment_request(callback.from_user.id, "BUY")

    log_admin_event(
        "payment.request.created",
        actor_user_id=callback.from_user.id,
        actor_username=callback.from_user.username,
        target_user_id=callback.from_user.id,
        target_username=callback.from_user.username,
        entity_type="payment_request",
        entity_id=str(req_id),
        success=True,
        reason="user opened payment request from callback",
        new_state={"status": "pending", "note": "BUY"},
        metadata={
            "source": "callback",
            "button": "buy_now",
            "network": PAYMENT_NETWORK,
            "wallet": PAYMENT_WALLET_ADDRESS,
            "bot_username": BOT_USERNAME,
        },
    )

    await callback.message.answer(PAYMENT_TEXT)
    await bot.send_message(
        ADMIN_ID,
        f"Payment request\nuser_id={callback.from_user.id}\nusername=@{callback.from_user.username or 'unknown'}\nrequest_id={req_id}\nnote=BUY\nnetwork={PAYMENT_NETWORK}\nwallet={PAYMENT_WALLET_ADDRESS}"
    )
    await callback.answer(PAYMENT_OPENED)
'''

text, n = re.subn(
    r'@dp\.callback_query\(F\.data == "buy_now"\)\s+async def buy_now\(callback: types\.CallbackQuery\):.*?(?=@dp\.message\(F\.text == "BUY"\))',
    buy_now_handler + "\n\n",
    text,
    count=1,
    flags=re.DOTALL,
)
print(f"replaced buy_now handler: {n}")

# -----------------------------
# 4) Fix BUY text handler
# -----------------------------
buy_text_handler = r'''@dp.message(F.text == "BUY")
async def buy_text(message: types.Message):
    upsert_user(message.from_user.id, message.from_user.username)

    if is_paid(message.from_user.id):
        text = ALREADY_ACTIVE
        if VIP_GROUP_LINK:
            text += f"\n\n{ACCESS_LINK_LABEL}\n{VIP_GROUP_LINK}"
        await message.answer(text)
        return

    if has_pending_request(message.from_user.id):
        await message.answer(PENDING_TEXT)

        log_admin_event(
            "payment.request.duplicate_blocked",
            actor_user_id=message.from_user.id,
            actor_username=message.from_user.username,
            target_user_id=message.from_user.id,
            target_username=message.from_user.username,
            entity_type="payment_request",
            success=True,
            reason="BUY blocked because pending request already exists",
            metadata={"source": "text", "text": "BUY", "bot_username": BOT_USERNAME},
        )
        return

    req_id = create_payment_request(message.from_user.id, "BUY")

    log_admin_event(
        "payment.request.created",
        actor_user_id=message.from_user.id,
        actor_username=message.from_user.username,
        target_user_id=message.from_user.id,
        target_username=message.from_user.username,
        entity_type="payment_request",
        entity_id=str(req_id),
        success=True,
        reason="user opened payment request from BUY message",
        new_state={"status": "pending", "note": "BUY"},
        metadata={
            "source": "text",
            "text": "BUY",
            "network": PAYMENT_NETWORK,
            "wallet": PAYMENT_WALLET_ADDRESS,
            "bot_username": BOT_USERNAME,
        },
    )

    await message.answer(PAYMENT_TEXT)
    await bot.send_message(
        ADMIN_ID,
        f"Payment request\nuser_id={message.from_user.id}\nusername=@{message.from_user.username or 'unknown'}\nrequest_id={req_id}\nnote=BUY\nnetwork={PAYMENT_NETWORK}\nwallet={PAYMENT_WALLET_ADDRESS}"
    )
'''

text, n = re.subn(
    r'@dp\.message\(F\.text == "BUY"\)\s+async def buy_text\(message: types\.Message\):.*?(?=@dp\.message\(Command\("approve"\)\))',
    buy_text_handler + "\n\n",
    text,
    count=1,
    flags=re.DOTALL,
)
print(f"replaced BUY handler: {n}")

# -----------------------------
# 5) Targeted string repairs
# -----------------------------
replacements = {
    'await message.answer("×گ××ں ××××گ×.")': 'await message.answer(NO_PERMISSION)',
    'await message.answer("×××\u200d×× ×\u200c× ×××ں: /approve <user_id>")': 'await message.answer(USAGE_APPROVE)',
    'await message.answer("×××\u200d×× ×\u200c× ×××ں: /reject <user_id>")': 'await message.answer(USAGE_REJECT)',
    'await message.answer("×××\u200d×× ×\u200c× ×××ں: /status <user_id>")': 'await message.answer(USAGE_STATUS)',
    'await message.answer("×گ××ں ×œ××××\u200c ×××××ں.")': 'await message.answer(NO_AUDIT_YET)',
    'await message.answer("××× ×œ××ھ×× ××××ھ ×ھ××œ××\u200c ××œ× BUY.")': 'await message.answer(SEND_BUY_HINT)',
    'await callback.answer("××××ھ ×ھ××œ××\u200c ×\u200c××ھ××")': 'await callback.answer(PAYMENT_OPENED)',
    'await message.answer("××××× ××œ×ڑ ××××œ×.")': 'await message.answer(ALREADY_ACTIVE)',
    'user_text = "××ھ××œ××\u200c ××œ×ڑ ×گ×××.\\n\\n××××× ××œ×ڑ ××××œ× ×××ھ."': 'user_text = WELCOME_PAID',
    'await bot.send_message(\n                target_id,\n                "××××ھ ××ھ××œ××\u200c ×\u200c×××ھ×. ×گ××× ×œ××œ×× BUY ×\u200d××× ××œ××ھ×× ×××× ××××.\"\n            )': 'await bot.send_message(target_id, REJECTED_USER_TEXT)',
}

for old, new in replacements.items():
    text = text.replace(old, new)

# Safer generic cleanups
text = text.replace('await message.answer("×گ××ں ××××گ×.")', 'await message.answer(NO_PERMISSION)')
text = text.replace('await message.answer("×گ××ں ×œ×××× ×××××ں.")', 'await message.answer(NO_AUDIT_YET)')
text = text.replace('await message.answer("××× ×œ××ھ×× ××××ھ ×ھ××œ×× ××œ× BUY.")', 'await message.answer(SEND_BUY_HINT)')

# Normalize approval message block
text = re.sub(
    r'user_text\s*=\s*WELCOME_PAID\s*if VIP_GROUP_LINK:\s*user_text \+= f".*?\{VIP_GROUP_LINK\}"',
    'user_text = WELCOME_PAID\n        if VIP_GROUP_LINK:\n            user_text += f"\\n\\n{ACCESS_LINK_LABEL}\\n{VIP_GROUP_LINK}"',
    text,
    count=1,
    flags=re.DOTALL,
)

# Normalize catch_all branch
text = re.sub(
    r'if is_paid\(message\.from_user\.id\):\s*await message\.answer\(.*?\)\s*elif has_pending_request\(message\.from_user\.id\):',
    'if is_paid(message.from_user.id):\n        await message.answer(ALREADY_ACTIVE)\n    elif has_pending_request(message.from_user.id):',
    text,
    count=1,
    flags=re.DOTALL,
)

path.write_text(text, encoding="utf-8", newline="\n")
print("OK: bot_full.py patched")
print(f"Backup: {backup}")