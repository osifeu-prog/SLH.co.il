import re
with open('bot.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Correct the broken multi-line string for cmd_upgrade - replace with a clean one-liner
old = 'await msg.answer("<b>🌎 Premium Tiers</b>\\n\\nPro (9.9 TON/mo) – x1.5 multiplier\\nBusiness (29 TON/mo) – x2.0 multiplier", parse_mode="HTML")'
new = 'await msg.answer("<b>🏌 Premium Tiers</b>\n\nPro (9.9 TON/mo) – x1.5 multiplier\nBusiness (29 TON/mo) – x2.0 multiplier", parse_mode="HTML")'
content = content.replace(old, new)

with open('bot.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed')
