from pathlib import Path
import re

path = Path(r"D:\SLH_PROJECT_V2\bot_full.py")
text = path.read_text(encoding="utf-8")

# 1) force the constant to a clean value if it exists
text = re.sub(
    r'ACCESS_LINK_LABEL\s*=.*',
    'ACCESS_LINK_LABEL = "לינק הגישה שלך:"',
    text
)

# 2) normalize common usages near VIP_GROUP_LINK
text = text.replace('text += f"\\n\\n{ACCESS_LINK_LABEL}\\n{VIP_GROUP_LINK}"', 'text += f"\\n\\nלינק הגישה שלך:\\n{VIP_GROUP_LINK}"')
text = text.replace('text += f"\\n\\nAccess link:\\n{VIP_GROUP_LINK}"', 'text += f"\\n\\nלינק הגישה שלך:\\n{VIP_GROUP_LINK}"')

# 3) if any broken literal line remains before the VIP link, replace it
text = re.sub(
    r'text \+= f"\\n\\n.*?\\n\{VIP_GROUP_LINK\}"',
    'text += f"\\n\\nלינק הגישה שלך:\\n{VIP_GROUP_LINK}"',
    text
)

# 4) same idea for direct await message blocks if present
text = re.sub(
    r'await message\.answer\(text\)',
    'await message.answer(text)',
    text
)

path.write_text(text, encoding="utf-8", newline="\n")
print("OK: patched link label")