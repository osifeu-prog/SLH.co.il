from pathlib import Path

path = Path(r"D:\SLH_PROJECT_V2\bot_full.py")
text = path.read_text(encoding="utf-8")

def u(s):
    return s.encode("utf-8").decode("unicode_escape")

pairs = [
    (
        'WELCOME_UNPAID = f"""???? ???.\n\n??? ???? ???? ???? ?? ?????? ????? ?? {PRICE_ILS} ?"?.\n\n???? ?????? ??? ????? ??? / hash / ??????.\n?? ???? ????? ????? ????? ?????.\n"""',
        'WELCOME_UNPAID = f"""\\u05d1\\u05e8\\u05d5\\u05da \\u05d4\\u05d1\\u05d0.\n\n\\u05db\\u05d3\\u05d9 \\u05dc\\u05e7\\u05d1\\u05dc \\u05d2\\u05d9\\u05e9\\u05d4 \\u05de\\u05dc\\u05d0\\u05d4 \\u05d9\\u05e9 \\u05dc\\u05d4\\u05e9\\u05dc\\u05d9\\u05dd \\u05ea\\u05e9\\u05dc\\u05d5\\u05dd \\u05e9\\u05dc {PRICE_ILS} \\u05e9\\"\\u05d7.\n\n\\u05dc\\u05d0\\u05d7\\u05e8 \\u05d4\\u05ea\\u05e9\\u05dc\\u05d5\\u05dd \\u05e9\\u05dc\\u05d7 \\u05e6\\u05d9\\u05dc\\u05d5\\u05dd \\u05de\\u05e1\\u05da / hash / \\u05d0\\u05e1\\u05de\\u05db\\u05ea\\u05d0.\n\\u05e8\\u05e7 \\u05d0\\u05d7\\u05e8\\u05d9 \\u05d1\\u05d3\\u05d9\\u05e7\\u05ea \\u05d0\\u05d3\\u05de\\u05d9\\u05df \\u05d4\\u05d2\\u05d9\\u05e9\\u05d4 \\u05ea\\u05d0\\u05d5\\u05e9\\u05e8.\n"""'
    ),
    (
        'WELCOME_PAID = """?????? ??? ????.\n\n????? ??? ????? ???.\n"""',
        'WELCOME_PAID = """\\u05d4\\u05ea\\u05e9\\u05dc\\u05d5\\u05dd \\u05e9\\u05dc\\u05da \\u05d0\\u05d5\\u05e9\\u05e8.\n\n\\u05d4\\u05d2\\u05d9\\u05e9\\u05d4 \\u05e9\\u05dc\\u05da \\u05e4\\u05e2\\u05d9\\u05dc\\u05d4 \\u05db\\u05e2\\u05ea.\n"""'
    ),
    (
        'PAYMENT_TEXT = f"""???? ????? ?????.\n\n???? ??????:\n{PRICE_ILS} ?"?\n\n???:\n{PAYMENT_NETWORK}\n\n????? ????? ??????:\n{PAYMENT_WALLET_ADDRESS}\n\n????:\n- ????? ????? ?? ???? ????? ????? ?????? ????\n- ???? ?????? ??? ????? ??? / hash / ??????\n- ?? ???? ????? ????? ???? ????\n\n???? ????? ?????? ???? ????? ??? BUY ?? ????? ?? ??????? ??? ??\'??.\n"""',
        'PAYMENT_TEXT = f"""\\u05d1\\u05e7\\u05e9\\u05ea \\u05ea\\u05e9\\u05dc\\u05d5\\u05dd \\u05e0\\u05e4\\u05ea\\u05d7\\u05d4.\n\n\\u05e1\\u05db\\u05d5\\u05dd \\u05dc\\u05ea\\u05e9\\u05dc\\u05d5\\u05dd:\n{PRICE_ILS} \\u05e9\\"\\u05d7\n\n\\u05e8\\u05e9\\u05ea:\n{PAYMENT_NETWORK}\n\n\\u05db\\u05ea\\u05d5\\u05d1\\u05ea \\u05d4\\u05d0\\u05e8\\u05e0\\u05e7 \\u05dc\\u05ea\\u05e9\\u05dc\\u05d5\\u05dd:\n{PAYMENT_WALLET_ADDRESS}\n\n\\u05d7\\u05e9\\u05d5\\u05d1:\n- \\u05d4\\u05d2\\u05d9\\u05e9\\u05d4 \\u05ea\\u05d0\\u05d5\\u05e9\\u05e8 \\u05e8\\u05e7 \\u05dc\\u05d0\\u05d7\\u05e8 \\u05ea\\u05e9\\u05dc\\u05d5\\u05dd \\u05d1\\u05e4\\u05d5\\u05e2\\u05dc \\u05dc\\u05db\\u05ea\\u05d5\\u05d1\\u05ea \\u05d4\\u05d6\\u05d0\\u05ea\n- \\u05dc\\u05d0\\u05d7\\u05e8 \\u05d4\\u05ea\\u05e9\\u05dc\\u05d5\\u05dd \\u05e9\\u05dc\\u05d7 \\u05e6\\u05d9\\u05dc\\u05d5\\u05dd \\u05de\\u05e1\\u05da / hash / \\u05d0\\u05e1\\u05de\\u05db\\u05ea\\u05d0\n- \\u05e8\\u05e7 \\u05d0\\u05d7\\u05e8\\u05d9 \\u05d1\\u05d3\\u05d9\\u05e7\\u05ea \\u05d0\\u05d3\\u05de\\u05d9\\u05df \\u05ea\\u05e7\\u05d1\\u05dc \\u05d2\\u05d9\\u05e9\\u05d4\n\n\\u05dc\\u05d0\\u05d7\\u05e8 \\u05e9\\u05dc\\u05d9\\u05d7\\u05ea \\u05d4\\u05ea\\u05e9\\u05dc\\u05d5\\u05dd \\u05d0\\u05e4\\u05e9\\u05e8 \\u05dc\\u05e9\\u05dc\\u05d5\\u05d7 \\u05e9\\u05d5\\u05d1 BUY \\u05d0\\u05d5 \\u05dc\\u05e9\\u05dc\\u05d5\\u05d7 \\u05d0\\u05ea \\u05d4\\u05d0\\u05e1\\u05de\\u05db\\u05ea\\u05d0 \\u05db\\u05d0\\u05df \\u05d1\\u05e6\'\\u05d0\\u05d8.\n"""'
    ),
    (
        'PENDING_TEXT = """??? ????? ???? ???? ????? ?????.\n\n?? ?????? ?? ?????? ????? ?????? ?????? ??? ??\'??.\n??? ???? ????? ???? ????? ????.\n"""',
        'PENDING_TEXT = """\\u05db\\u05d1\\u05e8 \\u05e7\\u05d9\\u05d9\\u05de\\u05ea \\u05d0\\u05e6\\u05dc\\u05da \\u05d1\\u05e7\\u05e9\\u05ea \\u05ea\\u05e9\\u05dc\\u05d5\\u05dd \\u05e4\\u05ea\\u05d5\\u05d7\\u05d4.\n\n\\u05d9\\u05e9 \\u05dc\\u05d4\\u05e9\\u05dc\\u05d9\\u05dd \\u05d0\\u05ea \\u05d4\\u05ea\\u05e9\\u05dc\\u05d5\\u05dd \\u05d4\\u05e7\\u05d9\\u05d9\\u05dd \\u05d5\\u05dc\\u05e9\\u05dc\\u05d5\\u05d7 \\u05d0\\u05e1\\u05de\\u05db\\u05ea\\u05d0 \\u05db\\u05d0\\u05df \\u05d1\\u05e6\'\\u05d0\\u05d8.\n\\u05d0\\u05d9\\u05df \\u05e6\\u05d5\\u05e8\\u05da \\u05dc\\u05e4\\u05ea\\u05d5\\u05d7 \\u05d1\\u05e7\\u05e9\\u05d4 \\u05e0\\u05d5\\u05e1\\u05e4\\u05ea \\u05db\\u05e8\\u05d2\\u05e2.\n"""'
    ),
    ('text = "????? ??? ??? ?????."', 'text = "\\u05d4\\u05d2\\u05d9\\u05e9\\u05d4 \\u05e9\\u05dc\\u05da \\u05db\\u05d1\\u05e8 \\u05e4\\u05e2\\u05d9\\u05dc\\u05d4."'),
    ('await callback.answer("???? ????? ?????")', 'await callback.answer("\\u05d1\\u05e7\\u05e9\\u05ea \\u05ea\\u05e9\\u05dc\\u05d5\\u05dd \\u05e0\\u05e4\\u05ea\\u05d7\\u05d4")'),
    ('await message.answer("??? ?????.")', 'await message.answer("\\u05d0\\u05d9\\u05df \\u05d4\\u05e8\\u05e9\\u05d0\\u05d4.")'),
    ('await message.answer("????? ????: /approve <user_id>")', 'await message.answer("\\u05e9\\u05d9\\u05de\\u05d5\\u05e9 \\u05e0\\u05db\\u05d5\\u05df: /approve <user_id>")'),
    ('await message.answer("????? ????: /reject <user_id>")', 'await message.answer("\\u05e9\\u05d9\\u05de\\u05d5\\u05e9 \\u05e0\\u05db\\u05d5\\u05df: /reject <user_id>")'),
    ('await message.answer("????? ????: /status <user_id>")', 'await message.answer("\\u05e9\\u05d9\\u05de\\u05d5\\u05e9 \\u05e0\\u05db\\u05d5\\u05df: /status <user_id>")'),
    ('await message.answer("??? ????? ?????.")', 'await message.answer("\\u05d0\\u05d9\\u05df \\u05dc\\u05d5\\u05d2\\u05d9\\u05dd \\u05e2\\u05d3\\u05d9\\u05d9\\u05df.")'),
    ('await message.answer("??? ????? ???? ????? ??? BUY.")', 'await message.answer("\\u05db\\u05d3\\u05d9 \\u05dc\\u05e4\\u05ea\\u05d5\\u05d7 \\u05d1\\u05e7\\u05e9\\u05ea \\u05ea\\u05e9\\u05dc\\u05d5\\u05dd \\u05e9\\u05dc\\u05d7 BUY.")'),
    ('user_text = "?????? ??? ????.\\n\\n????? ??? ????? ???."', 'user_text = "\\u05d4\\u05ea\\u05e9\\u05dc\\u05d5\\u05dd \\u05e9\\u05dc\\u05da \\u05d0\\u05d5\\u05e9\\u05e8.\\n\\n\\u05d4\\u05d2\\u05d9\\u05e9\\u05d4 \\u05e9\\u05dc\\u05da \\u05e4\\u05e2\\u05d9\\u05dc\\u05d4 \\u05db\\u05e2\\u05ea."'),
    ('await message.answer(f"?? ???? ??? ????? ????? ??????: {e}")', 'await message.answer(f"\\u05dc\\u05d0 \\u05e0\\u05d9\\u05ea\\u05df \\u05d4\\u05d9\\u05d4 \\u05dc\\u05e9\\u05dc\\u05d5\\u05d7 \\u05d4\\u05d5\\u05d3\\u05e2\\u05d4 \\u05dc\\u05de\\u05e9\\u05ea\\u05de\\u05e9: {e}")'),
    ('"???? ?????? ?????. ???? ????? BUY ???? ?????? ???? ????.")', '"\\u05d1\\u05e7\\u05e9\\u05ea \\u05d4\\u05ea\\u05e9\\u05dc\\u05d5\\u05dd \\u05e0\\u05d3\\u05d7\\u05ea\\u05d4. \\u05d0\\u05e4\\u05e9\\u05e8 \\u05dc\\u05e9\\u05dc\\u05d5\\u05d7 BUY \\u05de\\u05d7\\u05d3\\u05e9 \\u05d5\\u05dc\\u05e4\\u05ea\\u05d5\\u05d7 \\u05d1\\u05e7\\u05e9\\u05d4 \\u05d7\\u05d3\\u05e9\\u05d4.")'),
]

changed = 0
for old, new in pairs:
    old_dec = u(old)
    new_dec = u(new)
    if old_dec in text:
        text = text.replace(old_dec, new_dec)
        changed += 1

path.write_text(text, encoding="utf-8", newline="\n")
print(f"OK: replacements applied = {changed}")