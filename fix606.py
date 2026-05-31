import re

with open("bot.py", "r", encoding="utf-8") as f:
    content = f.read()

# תיקון השורה השבורה עם 💎
pattern = r'await msg\.answer\("<b>💎 Premium Tiers</b>.*?(?=\n\n|\n\s*async|\Z)' 
replacement = r'await msg.answer("<b>💎 Premium Tiers</b>\n\nPro (9.9 TON/mo) - x1.5 multiplier\nBusiness (29 TON/mo) - x2.0 multiplier", parse_mode="HTML")'

content = re.sub(pattern, replacement, content, flags=re.DOTALL | re.MULTILINE)

with open("bot.py", "w", encoding="utf-8") as f:
    f.write(content)

print("✅ Line 606 fixed successfully")
