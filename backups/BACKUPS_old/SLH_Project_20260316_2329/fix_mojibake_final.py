from pathlib import Path
import re

path = Path(r"D:\SLH_PROJECT_V2\bot_full.py")
text = path.read_text(encoding="utf-8")

def replace_literal(src: str, old: str, new: str):
    if old in src:
        return src.replace(old, new), 1
    return src, 0

helper = '''
def H(s: str) -> str:
    return s.encode("ascii").decode("unicode_escape")
'''

if "def H(s: str) -> str:" not in text:
    text = text.replace("dp = Dispatcher()", "dp = Dispatcher()\n\n" + helper)

const_block = '''
WELCOME_UNPAID = H(
    "\\u05d1\\u05e8\\u05d5\\u05da \\u05d4\\u05d1\\u05d0.\\n\\n"
    "\\u05db\\u05d3\\u05d9 \\u05dc\\u05e7\\u05d1\\u05dc \\u05d2\\u05d9\\u05e9\\u05d4 \\u05de\\u05dc\\u05d0\\u05d4 \\u05d9\\u05e9 \\u05dc\\u05d4\\u05e9\\u05dc\\u05d9\\u05dd \\u05ea\\u05e9\\u05dc\\u05d5\\u05dd \\u05e9\\u05dc "
) + f"{PRICE_ILS} " + H(
    "\\u05e9\\"\\u05d7.\\n\\n"
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
) + f"{PRICE_ILS}\\n\\n" + H(
    "\\u05e8\\u05e9\\u05ea:\\n"
) + f"{PAYMENT_NETWORK}\\n\\n" + H(
    "\\u05db\\u05ea\\u05d5\\u05d1\\u05ea \\u05d4\\u05d0\\u05e8\\u05e0\\u05e7 \\u05dc\\u05ea\\u05e9\\u05dc\\u05d5\\u05dd:\\n"
) + f"{PAYMENT_WALLET_ADDRESS}\\n\\n" + H(
    "\\u05d7\\u05e9\\u05d5\\u05d1:\\n"
    "- \\u05d4\\u05d2\\u05d9\\u05e9\\u05d4 \\u05ea\\u05d0\\u05d5\\u05e9\\u05e8 \\u05e8\\u05e7 \\u05dc\\u05d0\\u05d7\\u05e8 \\u05d1\\u05d3\\u05d9\\u05e7\\u05ea \\u05d0\\u05d3\\u05de\\u05d9\\u05df\\n"
    "- \\u05dc\\u05d0\\u05d7\\u05e8 \\u05d4\\u05ea\\u05e9\\u05dc\\u05d5\\u05dd \\u05e9\\u05dc\\u05d7 \\u05e6\\u05d9\\u05dc\\u05d5\\u05dd \\u05de\\u05e1\\u05da / hash / \\u05d0\\u05e1\\u05de\\u05db\\u05ea\\u05d0\\n\\n"
    "\\u05dc\\u05d0\\u05d7\\u05e8 \\u05e9\\u05dc\\u05d9\\u05d7\\u05ea \\u05d4\\u05ea\\u05e9\\u05dc\\u05d5\\u05dd \\u05d0\\u05e4\\u05e9\\u05e8 \\u05dc\\u05e9\\u05dc\\u05d5\\u05d7 \\u05e9\\u05d5\\u05d1 BUY \\u05d0\\u05d5 \\u05dc\\u05e9\\u05dc\\u05d5\\u05d7 \\u05d0\\u05ea \\u05d4\\u05d0\\u05e1\\u05de\\u05db\\u05ea\\u05d0 \\u05db\\u05d0\\u05df \\u05d1\\u05e6'\\u05d0\\u05d8."
)

PENDING_TEXT = H(
    "\\u05db\\u05d1\\u05e8 \\u05e7\\u05d9\\u05d9\\u05de\\u05ea \\u05d0\\u05e6\\u05dc\\u05da \\u05d1\\u05e7\\u05e9\\u05ea \\u05ea\\u05e9\\u05dc\\u05d5\\u05dd \\u05e4\\u05ea\\u05d5\\u05d7\\u05d4.\\n\\n"
    "\\u05d9\\u05e9 \\u05dc\\u05d4\\u05e9\\u05dc\\u05d9\\u05dd \\u05d0\\u05ea \\u05d4\\u05ea\\u05e9\\u05dc\\u05d5\\u05dd \\u05d4\\u05e7\\u05d9\\u05d9\\u05dd \\u05d5\\u05dc\\u05e9\\u05dc\\u05d5\\u05d7 \\u05d0\\u05e1\\u05de\\u05db\\u05ea\\u05d0 \\u05db\\u05d0\\u05df \\u05d1\\u05e6'\\u05d0\\u05d8.\\n"
    "\\u05d0\\u05d9\\u05df \\u05e6\\u05d5\\u05e8\\u05da \\u05dc\\u05e4\\u05ea\\u05d5\\u05d7 \\u05d1\\u05e7\\u05e9\\u05d4 \\u05e0\\u05d5\\u05e1\\u05e4\\u05ea \\u05db\\u05e8\\u05d2\\u05e2."
)

ACCESS_LINK_LABEL = H("\\u05dc\\u05d9\\u05e0\\u05e7 \\u05d4\\u05d2\\u05d9\\u05e9\\u05d4 \\u05e9\\u05dc\\u05da:")
ALREADY_ACTIVE = H("\\u05d4\\u05d2\\u05d9\\u05e9\\u05d4 \\u05e9\\u05dc\\u05da \\u05db\\u05d1\\u05e8 \\u05e4\\u05e2\\u05d9\\u05dc\\u05d4.")
REDEEM_OK = H("\\u05e7\\u05d5\\u05d3 \\u05d4\\u05e0\\u05d9\\u05e1\\u05d5\\u05d9 \\u05d4\\u05d5\\u05e4\\u05e2\\u05dc \\u05d1\\u05d4\\u05e6\\u05dc\\u05d7\\u05d4.\\n\\n\\u05d4\\u05d2\\u05d9\\u05e9\\u05d4 \\u05e9\\u05dc\\u05da \\u05e4\\u05e2\\u05d9\\u05dc\\u05d4 \\u05db\\u05e2\\u05ea.")
REDEEM_PENDING = H("\\u05e7\\u05d5\\u05d3 \\u05d4\\u05e0\\u05d9\\u05e1\\u05d5\\u05d9 \\u05d4\\u05d5\\u05e4\\u05e2\\u05dc. \\u05e0\\u05d5\\u05e6\\u05e8\\u05d4 \\u05e2\\u05d1\\u05d5\\u05e8\\u05da \\u05d1\\u05e7\\u05e9\\u05d4 \\u05d1\\u05de\\u05e6\\u05d1 pending.")
REDEEM_REJECT = H("\\u05e7\\u05d5\\u05d3 \\u05d4\\u05e0\\u05d9\\u05e1\\u05d5\\u05d9 \\u05d4\\u05d5\\u05e4\\u05e2\\u05dc. \\u05d4\\u05de\\u05e9\\u05ea\\u05de\\u05e9 \\u05d4\\u05d5\\u05d7\\u05d6\\u05e8 \\u05dc\\u05de\\u05e6\\u05d1 \\u05dc\\u05dc\\u05d0 \\u05d2\\u05d9\\u05e9\\u05d4.")
REDEEM_BAD = H("\\u05d4\\u05e7\\u05d5\\u05d3 \\u05dc\\u05d0 \\u05ea\\u05e7\\u05d9\\u05df, \\u05dc\\u05d0 \\u05e4\\u05e2\\u05d9\\u05dc, \\u05e4\\u05d2 \\u05ea\\u05d5\\u05e7\\u05e3 \\u05d0\\u05d5 \\u05de\\u05d9\\u05e6\\u05d4 \\u05e9\\u05d9\\u05de\\u05d5\\u05e9\\u05d9\\u05dd.")
'''

text, n = re.subn(
    r'WELCOME_UNPAID\s*=.*?PENDING_TEXT\s*=.*?(?=@dp\.message\(Command\("start"\)\))',
    const_block + "\n\n",
    text,
    count=1,
    flags=re.DOTALL
)
print("constants replaced:", n)

text, n1 = replace_literal(text, 'text += f"\\n\\nלינק הגישה שלך:\\n{VIP_GROUP_LINK}"', 'text += f"\\n\\n{ACCESS_LINK_LABEL}\\n{VIP_GROUP_LINK}"')
text, n2 = replace_literal(text, 'text += f"\\n\\nAccess link:\\n{VIP_GROUP_LINK}"', 'text += f"\\n\\n{ACCESS_LINK_LABEL}\\n{VIP_GROUP_LINK}"')
text, n3 = replace_literal(text, 'text = "הגישה שלך כבר פעילה."', 'text = ALREADY_ACTIVE')
text, n4 = replace_literal(text, 'await message.answer("הקוד לא תקין, לא פעיל, פג תוקף או מיצה שימושים.")', 'await message.answer(REDEEM_BAD)')
text, n5 = replace_literal(text, 'text = "קוד הניסוי הופעל בהצלחה.\\n\\nהגישה שלך פעילה כעת."', 'text = REDEEM_OK')
text, n6 = replace_literal(text, 'await message.answer("קוד הניסוי הופעל. נוצרה עבורך בקשה במצב pending.")', 'await message.answer(REDEEM_PENDING)')
text, n7 = replace_literal(text, 'await message.answer("קוד הניסוי הופעל. המשתמש הוחזר למצב ללא גישה.")', 'await message.answer(REDEEM_REJECT)')

text = text.replace('await message.answer("Usage: /approve <user_id>")', 'await message.answer("Usage: /approve <user_id>")')
text = text.replace('await message.answer("Usage: /reject <user_id>")', 'await message.answer("Usage: /reject <user_id>")')
text = text.replace('await message.answer("Usage: /status <user_id>")', 'await message.answer("Usage: /status <user_id>")')

path.write_text(text, encoding="utf-8", newline="\\n")
print("DONE", n1, n2, n3, n4, n5, n6, n7)