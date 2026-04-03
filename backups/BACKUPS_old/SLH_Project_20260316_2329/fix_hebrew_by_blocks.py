from pathlib import Path
import re

path = Path(r"D:\SLH_PROJECT_V2\bot_full.py")
text = path.read_text(encoding="utf-8")

WELCOME_UNPAID = """ברוך הבא.

כדי לקבל גישה מלאה יש להשלים תשלום של {PRICE_ILS} ש"ח.

לאחר התשלום שלח צילום מסך / hash / אסמכתא.
רק אחרי בדיקת אדמין הגישה תאושר.
"""

WELCOME_PAID = """התשלום שלך אושר.

הגישה שלך פעילה כעת.
"""

PAYMENT_TEXT = """בקשת תשלום נפתחה.

סכום לתשלום:
{PRICE_ILS} ש"ח

רשת:
{PAYMENT_NETWORK}

כתובת הארנק לתשלום:
{PAYMENT_WALLET_ADDRESS}

חשוב:
- הגישה תאושר רק לאחר תשלום בפועל לכתובת הזאת
- לאחר התשלום שלח צילום מסך / hash / אסמכתא
- רק אחרי בדיקת אדמין תקבל גישה

לאחר שליחת התשלום אפשר לשלוח שוב BUY או לשלוח את האסמכתא כאן בצ'אט.
"""

PENDING_TEXT = """כבר קיימת אצלך בקשת תשלום פתוחה.

יש להשלים את התשלום הקיים ולשלוח אסמכתא כאן בצ'אט.
אין צורך לפתוח בקשה נוספת כרגע.
"""

patterns = [
    (
        r'WELCOME_UNPAID\s*=\s*f?""".*?"""',
        'WELCOME_UNPAID = f"""' + WELCOME_UNPAID + '"""'
    ),
    (
        r'WELCOME_PAID\s*=\s*""".*?"""',
        'WELCOME_PAID = """' + WELCOME_PAID + '"""'
    ),
    (
        r'PAYMENT_TEXT\s*=\s*f""".*?"""',
        'PAYMENT_TEXT = f"""' + PAYMENT_TEXT + '"""'
    ),
    (
        r'PENDING_TEXT\s*=\s*""".*?"""',
        'PENDING_TEXT = """' + PENDING_TEXT + '"""'
    ),
]

for pattern, replacement in patterns:
    text, n = re.subn(pattern, replacement, text, count=1, flags=re.DOTALL)
    print(f"{pattern} -> {n}")

literal_replacements = {
    'text = "أâأâأâأآأâ أآأإأع أâأâکأآ أآأآأâأإأâ."':
        'text = "הגישה שלך כבר פעילה."',

    'await callback.answer("أâکأآأآأع أعأآأإأâأâŒ أآ أآأعأâأâ")':
        'await callback.answer("בקשת תשלום נפתחה")',
}

for old, new in literal_replacements.items():
    if old in text:
        text = text.replace(old, new)
        print(f"literal replaced: {old[:40]}...")

text = text.replace(
    'await message.answer("??? ?????.")',
    'await message.answer("אין הרשאה.")'
)
text = text.replace(
    'await message.answer("????? ????: /approve <user_id>")',
    'await message.answer("שימוש נכון: /approve <user_id>")'
)
text = text.replace(
    'await message.answer("????? ????: /reject <user_id>")',
    'await message.answer("שימוש נכון: /reject <user_id>")'
)
text = text.replace(
    'await message.answer("????? ????: /status <user_id>")',
    'await message.answer("שימוש נכון: /status <user_id>")'
)
text = text.replace(
    'await message.answer("??? ????? ?????.")',
    'await message.answer("אין לוגים עדיין.")'
)
text = text.replace(
    'await message.answer("??? ????? ???? ????? ??? BUY.")',
    'await message.answer("כדי לפתוח בקשת תשלום שלח BUY.")'
)

path.write_text(text, encoding="utf-8", newline="\n")
print("DONE")