import re

with open("bot.py", "r", encoding="utf-8") as f:
    content = f.read()

# הסרת BOM
content = content.replace('\ufeff', '')

# מחליף את כל הבלוק השבורה של upgrade בנקי לחלוטין
clean_block = """@dp.message(Command("upgrade"))
async def cmd_upgrade(msg: Message):
    await msg.answer("<b>💎 Premium Tiers</b>\n\nPro (9.9 TON/mo) - x1.5 multiplier\nBusiness (29 TON/mo) - x2.0 multiplier", parse_mode="HTML")
"""

# החלפה חזקה
content = re.sub(r'@dp\.message\(Command\("upgrade"\)\)[\s\S]*?@dp\.message\(Command\("donate"\)', clean_block + "\n\n@dp.message(Command(\"donate\"))", content, flags=re.DOTALL)

# ניקוי שורות כפולות מיותרות אחרי הפונקציה
content = re.sub(r'Pro \(9\.9 TON/mo\) - x1\.5 multiplier[\s\S]*?Business \(29 TON/mo\) - x2\.0 multiplier", parse_mode="HTML"\)', '', content, flags=re.DOTALL)

with open("bot.py", "w", encoding="utf-8") as f:
    f.write(content)

print("✅ Strong final fix applied")
