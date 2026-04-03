from pathlib import Path
import re
import shutil

path = Path(r"D:\SLH_PROJECT_V2\bot_full.py")
backup = Path(r"D:\SLH_PROJECT_V2\bot_full.py.bak_before_text_fix")

shutil.copy2(path, backup)
text = path.read_text(encoding="utf-8")

def sub_once(pattern: str, replacement: str, src: str):
    new_text, n = re.subn(pattern, lambda m: replacement, src, count=1, flags=re.DOTALL)
    return new_text, n

helper = '''
def H(s: str) -> str:
    return s.encode("ascii").decode("unicode_escape")
'''

if 'def H(s: str) -> str:' not in text:
    text = text.replace('dp = Dispatcher()', 'dp = Dispatcher()\n\n' + helper)

const_block = '''
WELCOME_UNPAID = H(
    "\\u05d1\\u05e8\\u05d5\\u05da \\u05d4\\u05d1\\u05d0.\\n\\n"
    "\\u05db\\u05d3\\u05d9 \\u05dc\\u05e7\\u05d1\\u05dc \\u05d2\\u05d9\\u05e9\\u05d4 \\u05de\\u05dc\\u05d0\\u05d4 \\u05d9\\u05e9 \\u05dc\\u05d4\\u05e9\\u05dc\\u05d9\\u05dd \\u05ea\\u05e9\\u05dc\\u05d5\\u05dd \\u05e9\\u05dc "
) + f"{PRICE_ILS} " + H(
    "\\u05e9\\\"\\u05d7.\\n\\n"
    "\\u05dc\\u05d0\\u05d7\\u05e8 \\u05d4\\u05ea\\u05e9\\u05dc\\u05d5\\u05dd \\u05e9\\u05dc\\u05d7 \\u05e6\\u05d9\\u05dc\\u05d5\\u05dd \\u05de\\u05e1\\u05da / hash / \\u05d0\\u05e1\\u05de\\u05db\\u05ea\\u05d0.\\n"
    "\\u05e8\\u05e7 \\u05d0\\u05d7\\u05e8\\u05d9 \\u05d1\\u05d3\\u05d9\\u05e7\\u05ea \\u05d0\\u05d3\\u05de\\u05d9\\u05df \\u05d4\\u05d2\\u05d9\\u05e9\\u05d4 \\u05ea\\u05d0\\u05d5\\u05e9\\u05e8."
)

WELCOME_PAID = H(
    "\\u05d4\\u05ea\\u05e9\\u05dc\\u05d5\\u05dd \\u05e9\\u05dc\\u05da \\u05d0\\u05d5\\u05e9\\u05e8.\\n\\n"
    "\\u05d4\\u05d2\\u05d9\\u05e9\\u05d4 \\u05e9\\u05dc\\u05da \\u05e4\\u05e2\\u05d9\\u05dc\\u05d4 \\u05db\\u05e2\\u05ea."
)

PAYMENT_TEXT = H(
    "\\u05d1\\u05e7\\u05e9\\u05ea \\u05ea\\u05e9\\u05dc\\u05d5\\u05dd \\u05e0\\u05e4\\u05ea\\u05d7\\u05d4.\\n\\n"
    "\\u05e1\\u05db\\u05d5\\u05dd \\u05dc\\u05ea\\u05e9\\u05dc\\u05d5\\u05dd:\\n"
) + f"{PRICE_ILS} " + H(
    "\\u05e9\\\"\\u05d7\\n\\n"
    "\\u05e8\\u05e9\\u05ea:\\n"
) + f"{PAYMENT_NETWORK}\\n\\n" + H(
    "\\u05db\\u05ea\\u05d5\\u05d1\\u05ea \\u05d4\\u05d0\\u05e8\\u05e0\\u05e7 \\u05dc\\u05ea\\u05e9\\u05dc\\u05d5\\u05dd:\\n"
) + f"{PAYMENT_WALLET_ADDRESS}\\n\\n" + H(
    "\\u05d7\\u05e9\\u05d5\\u05d1:\\n"
    "- \\u05dc\\u05d0\\u05d7\\u05e8 \\u05d4\\u05ea\\u05e9\\u05dc\\u05d5\\u05dd \\u05e9\\u05dc\\u05d7 \\u05e6\\u05d9\\u05dc\\u05d5\\u05dd \\u05de\\u05e1\\u05da / hash / \\u05d0\\u05e1\\u05de\\u05db\\u05ea\\u05d0\\n"
    "- \\u05e8\\u05e7 \\u05d0\\u05d7\\u05e8\\u05d9 \\u05d1\\u05d3\\u05d9\\u05e7\\u05ea \\u05d0\\u05d3\\u05de\\u05d9\\u05df \\u05ea\\u05e7\\u05d1\\u05dc \\u05d2\\u05d9\\u05e9\\u05d4\\n\\n"
    "\\u05dc\\u05d0\\u05d7\\u05e8 \\u05e9\\u05dc\\u05d9\\u05d7\\u05ea \\u05d4\\u05ea\\u05e9\\u05dc\\u05d5\\u05dd \\u05d0\\u05e4\\u05e9\\u05e8 \\u05dc\\u05e9\\u05dc\\u05d5\\u05d7 \\u05e9\\u05d5\\u05d1 BUY \\u05d0\\u05d5 \\u05dc\\u05e9\\u05dc\\u05d5\\u05d7 \\u05d0\\u05ea \\u05d4\\u05d0\\u05e1\\u05de\\u05db\\u05ea\\u05d0 \\u05db\\u05d0\\u05df \\u05d1\\u05e6\\'\\u05d0\\u05d8."
)

PENDING_TEXT = H(
    "\\u05db\\u05d1\\u05e8 \\u05e7\\u05d9\\u05d9\\u05de\\u05ea \\u05d0\\u05e6\\u05dc\\u05da \\u05d1\\u05e7\\u05e9\\u05ea \\u05ea\\u05e9\\u05dc\\u05d5\\u05dd \\u05e4\\u05ea\\u05d5\\u05d7\\u05d4.\\n\\n"
    "\\u05d9\\u05e9 \\u05dc\\u05d4\\u05e9\\u05dc\\u05d9\\u05dd \\u05d0\\u05ea \\u05d4\\u05ea\\u05e9\\u05dc\\u05d5\\u05dd \\u05d4\\u05e7\\u05d9\\u05d9\\u05dd \\u05d5\\u05dc\\u05e9\\u05dc\\u05d5\\u05d7 \\u05d0\\u05e1\\u05de\\u05db\\u05ea\\u05d0 \\u05db\\u05d0\\u05df \\u05d1\\u05e6\\'\\u05d0\\u05d8.\\n"
    "\\u05d0\\u05d9\\u05df \\u05e6\\u05d5\\u05e8\\u05da \\u05dc\\u05e4\\u05ea\\u05d5\\u05d7 \\u05d1\\u05e7\\u05e9\\u05d4 \\u05e0\\u05d5\\u05e1\\u05e4\\u05ea \\u05db\\u05e8\\u05d2\\u05e2."
)

ACCESS_LINK_LABEL = H("\\u05dc\\u05d9\\u05e0\\u05e7 \\u05d4\\u05d2\\u05d9\\u05e9\\u05d4 \\u05e9\\u05dc\\u05da:")
ALREADY_ACTIVE = H("\\u05d4\\u05d2\\u05d9\\u05e9\\u05d4 \\u05e9\\u05dc\\u05da \\u05db\\u05d1\\u05e8 \\u05e4\\u05e2\\u05d9\\u05dc\\u05d4.")
REDEEM_OK = H("\\u05e7\\u05d5\\u05d3 \\u05d4\\u05e0\\u05d9\\u05e1\\u05d5\\u05d9 \\u05d4\\u05d5\\u05e4\\u05e2\\u05dc \\u05d1\\u05d4\\u05e6\\u05dc\\u05d7\\u05d4.\\n\\n\\u05d4\\u05d2\\u05d9\\u05e9\\u05d4 \\u05e9\\u05dc\\u05da \\u05e4\\u05e2\\u05d9\\u05dc\\u05d4 \\u05db\\u05e2\\u05ea.")
REDEEM_PENDING = H("\\u05e7\\u05d5\\u05d3 \\u05d4\\u05e0\\u05d9\\u05e1\\u05d5\\u05d9 \\u05d4\\u05d5\\u05e4\\u05e2\\u05dc. \\u05e0\\u05d5\\u05e6\\u05e8\\u05d4 \\u05e2\\u05d1\\u05d5\\u05e8\\u05da \\u05d1\\u05e7\\u05e9\\u05d4 \\u05d1\\u05de\\u05e6\\u05d1 pending.")
REDEEM_REJECT = H("\\u05e7\\u05d5\\u05d3 \\u05d4\\u05e0\\u05d9\\u05e1\\u05d5\\u05d9 \\u05d4\\u05d5\\u05e4\\u05e2\\u05dc. \\u05d4\\u05de\\u05e9\\u05ea\\u05de\\u05e9 \\u05d4\\u05d5\\u05d7\\u05d6\\u05e8 \\u05dc\\u05de\\u05e6\\u05d1 \\u05dc\\u05dc\\u05d0 \\u05d2\\u05d9\\u05e9\\u05d4.")
REDEEM_BAD = H("\\u05d4\\u05e7\\u05d5\\u05d3 \\u05dc\\u05d0 \\u05ea\\u05e7\\u05d9\\u05df, \\u05dc\\u05d0 \\u05e4\\u05e2\\u05d9\\u05dc, \\u05e4\\u05d2 \\u05ea\\u05d5\\u05e7\\u05e3 \\u05d0\\u05d5 \\u05de\\u05d9\\u05e6\\u05d4 \\u05e9\\u05d9\\u05de\\u05d5\\u05e9\\u05d9\\u05dd.")
'''

text, n_const = sub_once(
    r'WELCOME_UNPAID\s*=.*?PENDING_TEXT\s*=.*?(?=@dp\.message\(Command\("start"\)\))',
    const_block + "\n\n",
    text
)

redeem_block = r'''
@dp.message(Command("redeem"))
async def redeem_code_cmd(message: types.Message):
    upsert_user(message.from_user.id, message.from_user.username)

    parts = (message.text or "").strip().split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await message.answer("Usage: /redeem <code>")
        return

    code = parts[1].strip().upper()

    row = tc_get_code(DB_NAME, DB_USER, DB_PASS, DB_HOST, DB_PORT, code)
    if not tc_code_is_usable(row):
        tc_mark_redemption(DB_NAME, DB_USER, DB_PASS, DB_HOST, DB_PORT, code, message.from_user.id, message.from_user.username, "invalid_or_inactive")
        await message.answer(REDEEM_BAD)
        return

    grant_type = str(row["grant_type"] or "").strip().lower()

    if grant_type == "full_access":
        approve_user(message.from_user.id)
        tc_increment_use(DB_NAME, DB_USER, DB_PASS, DB_HOST, DB_PORT, code)
        tc_mark_redemption(DB_NAME, DB_USER, DB_PASS, DB_HOST, DB_PORT, code, message.from_user.id, message.from_user.username, "granted_full_access")

        text = REDEEM_OK
        if VIP_GROUP_LINK:
            text += f"\n\n{ACCESS_LINK_LABEL}\n{VIP_GROUP_LINK}"
        await message.answer(text)
        return

    if grant_type == "pending_only":
        create_payment_request(message.from_user.id, "TEST_PENDING")
        tc_increment_use(DB_NAME, DB_USER, DB_PASS, DB_HOST, DB_PORT, code)
        tc_mark_redemption(DB_NAME, DB_USER, DB_PASS, DB_HOST, DB_PORT, code, message.from_user.id, message.from_user.username, "created_pending")
        await message.answer(REDEEM_PENDING)
        return

    if grant_type == "reject_only":
        reject_user(message.from_user.id)
        tc_increment_use(DB_NAME, DB_USER, DB_PASS, DB_HOST, DB_PORT, code)
        tc_mark_redemption(DB_NAME, DB_USER, DB_PASS, DB_HOST, DB_PORT, code, message.from_user.id, message.from_user.username, "rejected_access")
        await message.answer(REDEEM_REJECT)
        return

    tc_mark_redemption(DB_NAME, DB_USER, DB_PASS, DB_HOST, DB_PORT, code, message.from_user.id, message.from_user.username, "unknown_grant_type")
    await message.answer("Unsupported code grant type.")
'''

text, n_redeem = sub_once(
    r'@dp\.message\(Command\("redeem"\)\)\s+async def redeem_code_cmd\(message: types\.Message\):.*?(?=\nasync def main\(\):)',
    redeem_block + "\n",
    text
)

text = text.replace('await message.answer("שימוש נכון: /approve <user_id>")', 'await message.answer("Usage: /approve <user_id>")')
text = text.replace('await message.answer("שימוש נכון: /reject <user_id>")', 'await message.answer("Usage: /reject <user_id>")')
text = text.replace('await message.answer("שימוש נכון: /status <user_id>")', 'await message.answer("Usage: /status <user_id>")')

text = text.replace('text += f"\\n\\nלינק הגישה שלך:\\n{VIP_GROUP_LINK}"', 'text += f"\\n\\n{ACCESS_LINK_LABEL}\\n{VIP_GROUP_LINK}"')
text = text.replace('text += f"\\n\\nAccess link:\\n{VIP_GROUP_LINK}"', 'text += f"\\n\\n{ACCESS_LINK_LABEL}\\n{VIP_GROUP_LINK}"')
text = text.replace('text = "הגישה שלך כבר פעילה."', 'text = ALREADY_ACTIVE')

path.write_text(text, encoding="utf-8", newline="\n")

print("backup:", backup)
print("constants replaced:", n_const)
print("redeem replaced:", n_redeem)
print("DONE")