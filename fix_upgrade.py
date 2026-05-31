import re
with open('bot.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('\ufeff', '')
clean = '''@dp.message(Command("upgrade"))
async def cmd_upgrade(msg: Message):
    await msg.answer("<b>🎌 Premium Tiers</b>\n\nPro (9.9 TON/mo) – x1.5 multiplier\nBusiness (29 TON/mo) – x2.0 multiplier", parse_mode="HTML")'''
content = re.sub(r'@dp\.message\(Command\("upgrade"\)\)[\s\S]*?(?=@dp\.message\(Command\("donate"\)\)|$)', clean, content, flags=re.DOTALL_CONTENT)
content = re.sub(r'Pro \(9\.9 TON/mo\) - x1\.5 multiplier[\s\S]*?Business \(29 TON/mo\) - x2\.0 multiplier", parse_mode="HTML"\)', '', content, flags=re.DOTALL_CONTENT)
with open('bot.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('✅ Fixed')
