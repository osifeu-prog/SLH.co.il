from pathlib import Path
import re

path = Path(r"D:\SLH_PROJECT_V2\bot_full.py")
text = path.read_text(encoding="utf-8")

# 1) Fix VIP link label in /start paid flow
text = re.sub(
    r'text \+= f"\\n\\n.*?\{VIP_GROUP_LINK\}"',
    'text += f"\\n\\nלינק הגישה שלך:\\n{VIP_GROUP_LINK}"',
    text,
    count=1
)

# 2) Fix VIP link label in buy_now when already paid
text = re.sub(
    r'text \+= f"\\n\\n.*?\{VIP_GROUP_LINK\}"',
    'text += f"\\n\\nלינק הגישה שלך:\\n{VIP_GROUP_LINK}"',
    text,
    count=1
)

# 3) Fix buy button text
text = re.sub(
    r'InlineKeyboardButton\(text=f".*?\{PRICE_ILS\}.*?", callback_data="buy_now"\)',
    'InlineKeyboardButton(text=f"רכוש גישה ב-{PRICE_ILS} ש\\"ח", callback_data="buy_now")',
    text,
    count=1
)

# 4) Fix already-paid short text in buy_now
text = re.sub(
    r'text = ".*?"',
    'text = "הגישה שלך כבר פעילה."',
    text,
    count=1
)

path.write_text(text, encoding="utf-8", newline="\n")
print("DONE: targeted VIP/button fixes applied")