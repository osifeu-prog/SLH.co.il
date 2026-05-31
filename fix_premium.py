import re

with open("bot.py", "r", encoding="utf-8") as f:
    content = f.read()

# תיקון אגרסיבי של השורה השבורה
pattern = r'await msg\.answer\("<b>💎 Premium Tiers</b>.*?parse_mode=["\']HTML["\']?\s*\)?'
replacement = r'await msg.answer("<b>💎 Premium Tiers</b>\n\nPro (9.9 TON/mo) - x1.5 multiplier\nBusiness (29 TON/mo) - x2.0 multiplier", parse_mode="HTML")'

content = re.sub(pattern, replacement, content, flags=re.DOTALL | re.MULTILINE)

# ניקוי שאריות אם יש
content = re.sub(r'await msg\.answer\("<b>💎 Premium Tiers</b>[^"]*?$', replacement, content, flags=re.MULTILINE)

with open("bot.py", "w", encoding="utf-8") as f:
    f.write(content)

print("✅ Fixed Premium Tiers string")
