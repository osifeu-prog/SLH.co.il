from pathlib import Path
import re

path = Path(r"D:\SLH_PROJECT_V2\bot_full.py")
text = path.read_text(encoding="utf-8")

helper = '''
def H(s: str) -> str:
    return s.encode("ascii").decode("unicode_escape")
'''

if "def H(s: str) -> str:" not in text:
    text = text.replace('dp = Dispatcher()', 'dp = Dispatcher()\n' + helper)

replacements = {
    r'WELCOME_UNPAID\s*=\s*f""".*?"""': '''WELCOME_UNPAID = H(
    "\\u05d1\\u05e8\\u05d5\\u05da \\u05d4\\u05d1\\u05d0.\\n\\n"
    "\\u05db\\u05d3\\u05d9 \\u05dc\\u05e7\\u05d1\\u05dc \\u05d2\\u05d9\\u05e9\\u05d4 \\u05de\\u05dc\\u05d0\\u05d4 \\u05d9\\u05e9 \\u05dc\\u05d4\\u05e9\\u05dc\\u05d9\\u05dd \\u05ea\\u05e9\\u05dc\\u05d5\\u05dd \\u05e9\\u05dc "
) + f"{PRICE_ILS} " + H(
    "\\u05e9\\"\\u05d7.\\n\\n"
    "\\u05dc\\u05d0\\u05d7\\u05e8 \\u05d4\\u05ea\\u05e9\\u05dc\\u05d5\\u05dd \\u05e9\\u05dc\\u05d7 \\u05e6\\u05d9\\u05dc\\u05d5\\u05dd \\u05de\\u05e1\\u05da / hash / \\u05d0\\u05e1\\u05de\\u05db\\u05ea\\u05d0.\\n"
    "\\u05e8\\u05e7 \\u05d0\\u05d7\\u05e8\\u05d9 \\u05d1\\u05d3\\u05d9\\u05e7\\u05ea \\u05d0\\u05d3\\u05de\\u05d9\\u05df \\u05d4\\u05d2\\u05d9\\u05e9\\u05d4 \\u05ea\\u05d0\\u05d5\\u05e9\\u05e8."
)''',

    r'WELCOME_PAID\s*=\s*""".*?"""': '''WELCOME_PAID = H(
    "\\u05d4\\u05ea\\u05e9\\u05dc\\u05d5\\u05dd \\u05e9\\u05dc\\u05da \\u05d0\\u05d5\\u05e9\\u05e8.\\n\\n"
    "\\u05d4\\u05d2\\u05d9\\u05e9\\u05d4 \\u05e9\\u05dc\\u05da \\u05e4\\u05e2\\u05d9\\u05dc\\u05d4 \\u05db\\u05e2\\u05ea."
)''',

    r'PAYMENT_TEXT\s*=\s*f""".*?"""': '''PAYMENT_TEXT = H(
    "\\u05d1\\u05e7\\u05e9\\u05ea \\u05ea\\u05e9\\u05dc\\u05d5\\u05dd \\u05e0\\u05e4\\u05ea\\u05d7\\u05d4.\\n\\n"
    "\\u05e1\\u05db\\u05d5\\u05dd \\u05dc\\u05ea\\u05e9\\u05dc\\u05d5\\u05dd:\\n"
) + f"{PRICE_ILS}\\n\\n" + H(
    "\\u05e8\\u05e9\\u05ea:\\n"
) + f"{PAYMENT_NETWORK}\\n\\n" + H(
    "\\u05db\\u05ea\\u05d5\\u05d1\\u05ea \\u05d4\\u05d0\\u05e8\\u05e0\\u05e7 \\u05dc\\u05ea\\u05e9\\u05dc\\u05d5\\u05dd:\\n"
) + f"{PAYMENT_WALLET_ADDRESS}\\n\\n" + H(
    "\\u05d7\\u05e9\\u05d5\\u05d1:\\n"
    "- \\u05dc\\u05d0\\u05d7\\u05e8 \\u05d4\\u05ea\\u05e9\\u05dc\\u05d5\\u05dd \\u05e9\\u05dc\\u05d7 \\u05e6\\u05d9\\u05dc\\u05d5\\u05dd \\u05de\\u05e1\\u05da / hash / \\u05d0\\u05e1\\u05de\\u05db\\u05ea\\u05d0\\n"
    "- \\u05e8\\u05e7 \\u05d0\\u05d7\\u05e8\\u05d9 \\u05d1\\u05d3\\u05d9\\u05e7\\u05ea \\u05d0\\u05d3\\u05de\\u05d9\\u05df \\u05ea\\u05e7\\u05d1\\u05dc \\u05d2\\u05d9\\u05e9\\u05d4\\n\\n"
    "\\u05dc\\u05d0\\u05d7\\u05e8 \\u05e9\\u05dc\\u05d9\\u05d7\\u05ea \\u05d4\\u05ea\\u05e9\\u05dc\\u05d5\\u05dd \\u05d0\\u05e4\\u05e9\\u05e8 \\u05dc\\u05e9\\u05dc\\u05d5\\u05d7 \\u05e9\\u05d5\\u05d1 BUY \\u05d0\\u05d5 \\u05dc\\u05e9\\u05dc\\u05d5\\u05d7 \\u05d0\\u05ea \\u05d4\\u05d0\\u05e1\\u05de\\u05db\\u05ea\\u05d0 \\u05db\\u05d0\\u05df \\u05d1\\u05e6'\\u05d0\\u05d8."
)''',

    r'PENDING_TEXT\s*=\s*""".*?"""': '''PENDING_TEXT = H(
    "\\u05db\\u05d1\\u05e8 \\u05e7\\u05d9\\u05d9\\u05de\\u05ea \\u05d0\\u05e6\\u05dc\\u05da \\u05d1\\u05e7\\u05e9\\u05ea \\u05ea\\u05e9\\u05dc\\u05d5\\u05dd \\u05e4\\u05ea\\u05d5\\u05d7\\u05d4.\\n\\n"
    "\\u05d9\\u05e9 \\u05dc\\u05d4\\u05e9\\u05dc\\u05d9\\u05dd \\u05d0\\u05ea \\u05d4\\u05ea\\u05e9\\u05dc\\u05d5\\u05dd \\u05d4\\u05e7\\u05d9\\u05d9\\u05dd \\u05d5\\u05dc\\u05e9\\u05dc\\u05d5\\u05d7 \\u05d0\\u05e1\\u05de\\u05db\\u05ea\\u05d0 \\u05db\\u05d0\\u05df \\u05d1\\u05e6'\\u05d0\\u05d8.\\n"
    "\\u05d0\\u05d9\\u05df \\u05e6\\u05d5\\u05e8\\u05da \\u05dc\\u05e4\\u05ea\\u05d5\\u05d7 \\u05d1\\u05e7\\u05e9\\u05d4 \\u05e0\\u05d5\\u05e1\\u05e4\\u05ea \\u05db\\u05e8\\u05d2\\u05e2."
)'''
}

for pattern, replacement in replacements.items():
    text, n = re.subn(pattern, replacement, text, count=1, flags=re.DOTALL)
    print(pattern, "=>", n)

text = text.replace('שימוש נכון: /approve <user_id>', 'Usage: /approve <user_id>')
text = text.replace('שימוש נכון: /reject <user_id>', 'Usage: /reject <user_id>')
text = text.replace('שימוש נכון: /status <user_id>', 'Usage: /status <user_id>')
text = text.replace('לינק הגישה שלך:', 'Access link:')

text = text.replace('await message.answer("הקוד לא תקין, לא פעיל, פג תוקף או מיצה שימושים.")',
                    'await message.answer(H("\\u05d4\\u05e7\\u05d5\\u05d3 \\u05dc\\u05d0 \\u05ea\\u05e7\\u05d9\\u05df, \\u05dc\\u05d0 \\u05e4\\u05e2\\u05d9\\u05dc, \\u05e4\\u05d2 \\u05ea\\u05d5\\u05e7\\u05e3 \\u05d0\\u05d5 \\u05de\\u05d9\\u05e6\\u05d4 \\u05e9\\u05d9\\u05de\\u05d5\\u05e9\\u05d9\\u05dd."))')

text = text.replace('await message.answer("קוד הניסוי הופעל בהצלחה.\\n\\nהגישה שלך פעילה כעת.")',
                    'await message.answer(H("\\u05e7\\u05d5\\u05d3 \\u05d4\\u05e0\\u05d9\\u05e1\\u05d5\\u05d9 \\u05d4\\u05d5\\u05e4\\u05e2\\u05dc \\u05d1\\u05d4\\u05e6\\u05dc\\u05d7\\u05d4.\\n\\n\\u05d4\\u05d2\\u05d9\\u05e9\\u05d4 \\u05e9\\u05dc\\u05da \\u05e4\\u05e2\\u05d9\\u05dc\\u05d4 \\u05db\\u05e2\\u05ea."))')

text = text.replace('await message.answer("קוד הניסוי הופעל. נוצרה עבורך בקשה במצב pending.")',
                    'await message.answer(H("\\u05e7\\u05d5\\u05d3 \\u05d4\\u05e0\\u05d9\\u05e1\\u05d5\\u05d9 \\u05d4\\u05d5\\u05e4\\u05e2\\u05dc. \\u05e0\\u05d5\\u05e6\\u05e8\\u05d4 \\u05e2\\u05d1\\u05d5\\u05e8\\u05da \\u05d1\\u05e7\\u05e9\\u05d4 \\u05d1\\u05de\\u05e6\\u05d1 pending."))')

text = text.replace('await message.answer("קוד הניסוי הופעל. המשתמש הוחזר למצב ללא גישה.")',
                    'await message.answer(H("\\u05e7\\u05d5\\u05d3 \\u05d4\\u05e0\\u05d9\\u05e1\\u05d5\\u05d9 \\u05d4\\u05d5\\u05e4\\u05e2\\u05dc. \\u05d4\\u05de\\u05e9\\u05ea\\u05de\\u05e9 \\u05d4\\u05d5\\u05d7\\u05d6\\u05e8 \\u05dc\\u05de\\u05e6\\u05d1 \\u05dc\\u05dc\\u05d0 \\u05d2\\u05d9\\u05e9\\u05d4."))')

path.write_text(text, encoding="utf-8", newline="\n")
print("DONE")