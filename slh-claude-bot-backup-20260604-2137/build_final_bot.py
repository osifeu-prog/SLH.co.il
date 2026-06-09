import re

with open("bot.py", "r", encoding="utf-8") as f:
    code = f.read()

# --- A) תיקון SQL (גרשיים) ---
code = code.replace("tier TEXT DEFAULT ''free''", "tier TEXT DEFAULT 'free'")

# --- B) החלף /status בגרסה דואלית (משתמש + מנהל) ---
old_status = r"@dp\.message\(Command\(\"status\"\)\)\s*async def cmd_status.*?\n\s*else:\s*\n\s*await msg\.answer\(\"משתמש לא נמצא\. הקלד /start\"\)"
new_status = '''@dp.message(Command("status"))
async def cmd_status(msg: types.Message):
    if msg.from_user.id in ADMIN_IDS:
        import datetime as dt, glob
        db_ok = pool is not None
        site = "\\U0001f534 DOWN"
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get("https://slh-nft.com/investor-landing/")
                site = f"\\U0001f7e2 {resp.status_code}"
        except:
            pass
        backups = len(glob.glob("backups/*.zip"))
        text = (
            "\\U0001f4ca <b>\\u05d3\\u05d5\\u05d7 \\u05de\\u05e2\\u05e8\\u05db\\u05ea SLH v4.5</b>\\n"
            f"\\U0001f539 \\u05d1\\u05e1\\u05d9\\u05e1 \\u05e0\\u05ea\\u05d5\\u05e0\\u05d9\\u05dd: {'\\u2705' if db_ok else '\\u274c'}\\n"
            f"\\U0001f539 \\u05d0\\u05ea\\u05e8 \\u05de\\u05e9\\u05e7\\u05d9\\u05e2\\u05d9\\u05dd: {site}\\n"
            f"\\U0001f539 \\u05d2\\u05d9\\u05d1\\u05d5\\u05d9\\u05d9\\u05dd: {backups} \\u05e7\\u05d1\\u05e6\\u05d9\\u05dd\\n"
            f"\\U0001f539 \\u05d6\\u05de\\u05df: {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        await msg.answer(text)
    else:
        uid = msg.from_user.id
        async with pool.acquire() as conn:
            user = await conn.fetchrow("SELECT points, energy, tier FROM users WHERE telegram_id=$1", uid)
            if user:
                await msg.answer(f"\\U0001f4ca <b>\\u05e1\\u05d8\\u05d8\\u05d5\\u05e1</b>\\n\\u2b50 \\u05e0\\u05e7\\u05d5\\u05d3\\u05d5\\u05ea: {user['points']}\\n\\u26a1 \\u05d0\\u05e0\\u05e8\\u05d2\\u05d9\\u05d4: {user['energy']}\\n\\U0001f3c5 \\u05e8\\u05de\\u05d4: {user['tier']}")
            else:
                await msg.answer("\\u05de\\u05e9\\u05ea\\u05de\\u05e9 \\u05dc\\u05d0 \\u05e0\\u05de\\u05e6\\u05d0. \\u05d4\\u05e7\\u05dc\\u05d3 /start")'''
code = re.sub(old_status, new_status, code, flags=re.DOTALL)

# --- C) החלף /backup ---
old_backup = r"@dp\.message\(Command\(\"backup\"\)\).*?await msg\.answer\(\"\\U0001f4be \\u05d2\\u05d9\\u05d1\\u05d5\\u05d9 \\(\\u05d1\\u05e7\\u05e8\\u05d5\\u05d1\\)\"\)"
new_backup = '''@dp.message(Command("backup"))
async def cmd_backup_system(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("\\u26d4 \\u05d2\\u05d9\\u05e9\\u05ea \\u05de\\u05e0\\u05d4\\u05dc \\u05d1\\u05dc\\u05d1\\u05d3.")
    import datetime as dt, zipfile, glob
    await msg.answer("\\U0001f4be \\u05d9\\u05d5\\u05e6\\u05e8 \\u05d2\\u05d9\\u05d1\\u05d5\\u05d9...")
    try:
        ts = dt.datetime.now().strftime("%Y%m%d-%H%M")
        zip_name = f"backups/full_backup_{ts}.zip"
        with zipfile.ZipFile(zip_name, 'w') as zf:
            zf.write('bot.py')
            for f in glob.glob('backups/*.zip'):
                zf.write(f)
        await msg.answer(f"\\u2705 \\u05d2\\u05d9\\u05d1\\u05d5\\u05d9 \\u05e0\\u05e9\\u05de\\u05e8: {zip_name}")
    except Exception as e:
        await msg.answer(f"\\u274c \\u05e9\\u05d2\\u05d9\\u05d0\\u05d4: {str(e)[:200]}")'''
code = re.sub(old_backup, new_backup, code, flags=re.DOTALL)

# --- D) הוסף /deploy ---
if "@dp.message(Command(\"deploy\"))" not in code:
    new_deploy = """
@dp.message(Command("deploy"))
async def cmd_deploy_system(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("\\u26d4 \\u05d2\\u05d9\\u05e9\\u05ea \\u05de\\u05e0\\u05d4\\u05dc \\u05d1\\u05dc\\u05d1\\u05d3.")
    await msg.answer("\\U0001f680 Deploy \\u05d6\\u05de\\u05d9\\u05df \\u05e8\\u05e7 \\u05d3\\u05e8\\u05da Git. \\u05d4\\u05d0\\u05ea\\u05e8 \\u05de\\u05ea\\u05e2\\u05d3\\u05db\\u05df \\u05d0\\u05d5\\u05d8\\u05d5\\u05de\\u05d8\\u05d9\\u05ea.")"""
    code = code.replace("# ====================== AI Fallback ======================", new_deploy + "\n# ====================== AI Fallback ======================")

# --- E) הוסף Marketplace, Archive, CSV ---
marketplace_code = '''
# ====================== Marketplace ======================
class ProductForm(StatesGroup):
    waiting_name = State()
    waiting_desc = State()
    waiting_price = State()
    waiting_stock = State()

class EditProductForm(StatesGroup):
    waiting_name = State()
    waiting_desc = State()
    waiting_price = State()
    waiting_stock = State()

def store_menu(products):
    kb = [[types.InlineKeyboardButton(text=f"{p['name']} - {p['price']} \\u05e0\\u05e7'", callback_data=f"buy_{p['id']}")] for p in products]
    kb.append([types.InlineKeyboardButton(text="\\U0001f519 \\u05d7\\u05d6\\u05e8\\u05d4", callback_data="main_menu")])
    return types.InlineKeyboardMarkup(inline_keyboard=kb)

def admin_product_menu(products):
    kb = []
    for p in products:
        row = [
            types.InlineKeyboardButton(text=f"\\u270f\\ufe0f {p['name']}", callback_data=f"edit_{p['id']}"),
            types.InlineKeyboardButton(text="\\U0001f5d1\\ufe0f", callback_data=f"ask_delete_{p['id']}")
        ]
        kb.append(row)
    kb.append([types.InlineKeyboardButton(text="\\u2795 \\u05d4\\u05d5\\u05e1\\u05e3 \\u05de\\u05d5\\u05e6\\u05e8", callback_data="add_product_menu")])
    kb.append([types.InlineKeyboardButton(text="\\U0001f4e6 \\u05d0\\u05e8\\u05db\\u05d9\\u05d5\\u05df", callback_data="archive")])
    kb.append([types.InlineKeyboardButton(text="\\U0001f519 \\u05d7\\u05d6\\u05e8\\u05d4", callback_data="admin")])
    return types.InlineKeyboardMarkup(inline_keyboard=kb)

def confirm_delete_keyboard(product_id):
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="\\u2705 \\u05db\\u05df, \\u05de\\u05d7\\u05e7", callback_data=f"delete_{product_id}"),
         types.InlineKeyboardButton(text="\\u274c \\u05dc\\u05d0", callback_data="admin_products")]
    ])

def confirm_buy_keyboard(product_id):
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="\\u2705 \\u05db\\u05df, \\u05e7\\u05e0\\u05d4!", callback_data=f"confirm_buy_{product_id}"),
         types.InlineKeyboardButton(text="\\u274c \\u05dc\\u05d0", callback_data="main_menu")]
    ])

def archive_menu(products):
    kb = [[types.InlineKeyboardButton(text=f"\\U0001f504 {p['name']}", callback_data=f"restore_{p['id']}")] for p in products]
    kb.append([types.InlineKeyboardButton(text="\\U0001f519 \\u05d7\\u05d6\\u05e8\\u05d4", callback_data="admin_products")])
    return types.InlineKeyboardMarkup(inline_keyboard=kb)

@dp.message(Command("store"))
async def cmd_store(msg: types.Message):
    async with pool.acquire() as conn:
        products = await conn.fetch("SELECT id, name, price FROM products WHERE stock > 0 AND deleted_at IS NULL ORDER BY id")
        if not products:
            return await msg.answer("\\U0001f6d2 \\u05d4\\u05d7\\u05e0\\u05d5\\u05ea \\u05e8\\u05d9\\u05e7\\u05d4 \\u05db\\u05e8\\u05d2\\u05e2.")
        await msg.answer("\\U0001f6d2 <b>\\u05d7\\u05e0\\u05d5\\u05ea SLH</b>\\n\\u05d1\\u05d7\\u05e8 \\u05de\\u05d5\\u05e6\\u05e8 \\u05dc\\u05e8\\u05db\\u05d9\\u05e9\\u05d4:", reply_markup=store_menu(products))

@dp.message(Command("add_product"))
async def cmd_add_product(msg: types.Message, state: FSMContext):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("\\u26d4 \\u05d2\\u05d9\\u05e9\\u05ea \\u05de\\u05e0\\u05d4\\u05dc \\u05d1\\u05dc\\u05d1\\u05d3.")
    await state.set_state(ProductForm.waiting_name)
    await msg.answer("\\u05e9\\u05dd \\u05d4\\u05de\\u05d5\\u05e6\\u05e8:")

@dp.message(ProductForm.waiting_name)
async def product_name(msg: types.Message, state: FSMContext):
    await state.update_data(name=msg.text)
    await state.set_state(ProductForm.waiting_desc)
    await msg.answer("\\u05ea\\u05d9\\u05d0\\u05d5\\u05e8 \\u05d4\\u05de\\u05d5\\u05e6\\u05e8:")

@dp.message(ProductForm.waiting_desc)
async def product_desc(msg: types.Message, state: FSMContext):
    await state.update_data(description=msg.text)
    await state.set_state(ProductForm.waiting_price)
    await msg.answer("\\u05de\\u05d7\\u05d9\\u05e8 (\\u05d1\\u05e0\\u05e7\\u05d5\\u05d3\\u05d5\\u05ea):")

@dp.message(ProductForm.waiting_price)
async def product_price(msg: types.Message, state: FSMContext):
    try:
        price = int(msg.text)
    except ValueError:
        return await msg.answer("\\u05de\\u05d7\\u05d9\\u05e8 \\u05d7\\u05d9\\u05d9\\u05d1 \\u05dc\\u05d4\\u05d9\\u05d5\\u05ea \\u05de\\u05e1\\u05e4\\u05e8. \\u05e0\\u05e1\\u05d4 \\u05e9\\u05d5\\u05d1.")
    await state.update_data(price=price)
    await state.set_state(ProductForm.waiting_stock)
    await msg.answer("\\u05db\\u05de\\u05d5\\u05ea \\u05d1\\u05de\\u05dc\\u05d0\\u05d9:")

@dp.message(ProductForm.waiting_stock)
async def product_stock(msg: types.Message, state: FSMContext):
    try:
        stock = int(msg.text)
    except ValueError:
        return await msg.answer("\\u05db\\u05de\\u05d5\\u05ea \\u05d7\\u05d9\\u05d9\\u05d1\\u05ea \\u05dc\\u05d4\\u05d9\\u05d5\\u05ea \\u05de\\u05e1\\u05e4\\u05e8. \\u05e0\\u05e1\\u05d4 \\u05e9\\u05d5\\u05d1.")
    data = await state.get_data()
    async with pool.acquire() as conn:
        await conn.execute("INSERT INTO products (name, description, price, stock) VALUES ($1, $2, $3, $4)",
                           data['name'], data['description'], data['price'], stock)
    await state.clear()
    await msg.answer(f"\\u2705 \\u05de\\u05d5\\u05e6\\u05e8 '{data['name']}' \\u05e0\\u05d5\\u05e1\\u05e3 \\u05d1\\u05d4\\u05e6\\u05dc\\u05d7\\u05d4!")

@dp.message(Command("products"))
async def cmd_products(msg: types.Message):
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, name, price, stock FROM products WHERE deleted_at IS NULL ORDER BY id")
        if not rows:
            return await msg.answer("\\U0001f4e6 \\u05d0\\u05d9\\u05df \\u05de\\u05d5\\u05e6\\u05e8\\u05d9\\u05dd \\u05d1\\u05de\\u05e2\\u05e8\\u05db\\u05ea.")
        text = "\\n".join(f"{r['id']}: {r['name']} - {r['price']} \\u05e0\\u05e7' ({r['stock']} \\u05d1\\u05de\\u05dc\\u05d0\\u05d9)" for r in rows)
        await msg.answer(f"\\U0001f4e6 <b>\\u05de\\u05d5\\u05e6\\u05e8\\u05d9\\u05dd</b>:\\n{text}")

@dp.message(Command("buy"))
async def cmd_buy(msg: types.Message):
    parts = msg.text.split()
    if len(parts) < 2:
        return await msg.answer("\\u05e9\\u05d9\\u05de\\u05d5\\u05e9: /buy [\\u05de\\u05d6\\u05d4\\u05d4 \\u05de\\u05d5\\u05e6\\u05e8]")
    try:
        product_id = int(parts[1])
    except ValueError:
        return await msg.answer("\\u05de\\u05d6\\u05d4\\u05d4 \\u05de\\u05d5\\u05e6\\u05e8 \\u05d7\\u05d9\\u05d9\\u05d1 \\u05dc\\u05d4\\u05d9\\u05d5\\u05ea \\u05de\\u05e1\\u05e4\\u05e8.")
    uid = msg.from_user.id
    async with pool.acquire() as conn:
        product = await conn.fetchrow("SELECT id, name, price, stock FROM products WHERE id = $1 AND deleted_at IS NULL", product_id)
        if not product or product['stock'] <= 0:
            return await msg.answer("\\u05d4\\u05de\\u05d5\\u05e6\\u05e8 \\u05dc\\u05d0 \\u05d6\\u05de\\u05d9\\u05df.")
        user = await conn.fetchrow("SELECT points FROM users WHERE telegram_id = $1", uid)
        if not user or user['points'] < product['price']:
            return await msg.answer("\\u05d0\\u05d9\\u05df \\u05de\\u05e1\\u05e4\\u05d9\\u05e7 \\u05e0\\u05e7\\u05d5\\u05d3\\u05d5\\u05ea.")
        await msg.answer(f"\\u05d4\\u05d0\\u05dd \\u05dc\\u05e8\\u05db\\u05d5\\u05e9 <b>{product['name']}</b> \\u05d1-<b>{product['price']}</b> \\u05e0\\u05e7\\u05d5\\u05d3\\u05d5\\u05ea?",
                         reply_markup=confirm_buy_keyboard(product_id))

@dp.message(Command("my_purchases"))
async def cmd_my_purchases(msg: types.Message):
    uid = msg.from_user.id
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT p.name, pu.points_spent, pu.created_at 
            FROM purchases pu JOIN products p ON pu.product_id = p.id 
            WHERE pu.user_id = $1 ORDER BY pu.created_at DESC LIMIT 20
        """, uid)
        if not rows:
            return await msg.answer("\\u05d0\\u05d9\\u05df \\u05e8\\u05db\\u05d9\\u05e9\\u05d5\\u05ea.")
        text = "\\n".join(f"{r['name']} - {r['points_spent']} \\u05e0\\u05e7' ({r['created_at'].strftime('%d/%m/%Y')})" for r in rows)
        await msg.answer(f"\\U0001f4dc <b>\\u05d4\\u05e8\\u05db\\u05d9\\u05e9\\u05d5\\u05ea \\u05e9\\u05dc\\u05d9</b>:\\n{text}")

@dp.message(Command("admin_products"))
async def cmd_admin_products(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("\\u26d4 \\u05d2\\u05d9\\u05e9\\u05ea \\u05de\\u05e0\\u05d4\\u05dc \\u05d1\\u05dc\\u05d1\\u05d3.")
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, name, price, stock, deleted_at FROM products ORDER BY id")
        if not rows:
            return await msg.answer("\\u05d0\\u05d9\\u05df \\u05de\\u05d5\\u05e6\\u05e8\\u05d9\\u05dd.")
        text = "\\n".join(f"{r['id']}: {r['name']} - {r['price']} \\u05e0\\u05e7' ({r['stock']} \\u05d1\\u05de\\u05dc\\u05d0\\u05d9)" + (" \\U0001f5c4\\ufe0f" if r['deleted_at'] else "") for r in rows)
        await msg.answer(f"\\U0001f4e6 <b>\\u05e0\\u05d9\\u05d4\\u05d5\\u05dc \\u05de\\u05d5\\u05e6\\u05e8\\u05d9\\u05dd</b>:\\n{text}\\n\\n\\u05d1\\u05d7\\u05e8 \\u05de\\u05d5\\u05e6\\u05e8 \\u05dc\\u05e2\\u05e8\\u05d9\\u05db\\u05d4/\\u05de\\u05d7\\u05d9\\u05e7\\u05d4:", reply_markup=admin_product_menu(rows))

@dp.message(Command("archive"))
async def cmd_archive(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("\\u26d4 \\u05d2\\u05d9\\u05e9\\u05ea \\u05de\\u05e0\\u05d4\\u05dc \\u05d1\\u05dc\\u05d1\\u05d3.")
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, name, price, stock FROM products WHERE deleted_at IS NOT NULL ORDER BY deleted_at DESC")
        if not rows:
            return await msg.answer("\\U0001f4e6 \\u05d4\\u05d0\\u05e8\\u05db\\u05d9\\u05d5\\u05df \\u05e8\\u05d9\\u05e7.")
        await msg.answer("\\U0001f5c4\\ufe0f <b>\\u05de\\u05d5\\u05e6\\u05e8\\u05d9\\u05dd \\u05d1\\u05d0\\u05e8\\u05db\\u05d9\\u05d5\\u05df</b>\\n\\u05dc\\u05d7\\u05e5 \\u05dc\\u05e9\\u05d9\\u05d7\\u05d6\\u05d5\\u05e8:", reply_markup=archive_menu(rows))

@dp.message(Command("restore_product"))
async def cmd_restore_product(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("\\u26d4 \\u05d2\\u05d9\\u05e9\\u05ea \\u05de\\u05e0\\u05d4\\u05dc \\u05d1\\u05dc\\u05d1\\u05d3.")
    parts = msg.text.split()
    if len(parts) < 2:
        return await msg.answer("\\u05e9\\u05d9\\u05de\\u05d5\\u05e9: /restore_product [\\u05de\\u05d6\\u05d4\\u05d4 \\u05de\\u05d5\\u05e6\\u05e8]")
    try:
        product_id = int(parts[1])
    except ValueError:
        return await msg.answer("\\u05de\\u05d6\\u05d4\\u05d4 \\u05de\\u05d5\\u05e6\\u05e8 \\u05d7\\u05d9\\u05d9\\u05d1 \\u05dc\\u05d4\\u05d9\\u05d5\\u05ea \\u05de\\u05e1\\u05e4\\u05e8.")
    async with pool.acquire() as conn:
        product = await conn.fetchrow("SELECT name FROM products WHERE id = $1 AND deleted_at IS NOT NULL", product_id)
        if not product:
            return await msg.answer("\\u05d4\\u05de\\u05d5\\u05e6\\u05e8 \\u05dc\\u05d0 \\u05e0\\u05de\\u05e6\\u05d0 \\u05d1\\u05d0\\u05e8\\u05db\\u05d9\\u05d5\\u05df.")
        await conn.execute("UPDATE products SET deleted_at = NULL WHERE id = $1", product_id)
        await msg.answer(f"\\U0001f504 \\u05d4\\u05de\\u05d5\\u05e6\\u05e8 '{product['name']}' \\u05e9\\u05d5\\u05d7\\u05d6\\u05e8 \\u05dc\\u05d7\\u05e0\\u05d5\\u05ea.")

@dp.message(Command("export_products"))
async def cmd_export_products(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("\\u26d4 \\u05d2\\u05d9\\u05e9\\u05ea \\u05de\\u05e0\\u05d4\\u05dc \\u05d1\\u05dc\\u05d1\\u05d3.")
    import csv, io
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, name, description, price, stock, deleted_at, created_at FROM products ORDER BY id")
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Name", "Description", "Price", "Stock", "Deleted", "Created"])
    for r in rows:
        writer.writerow([r['id'], r['name'], r['description'], r['price'], r['stock'], r['deleted_at'], r['created_at']])
    output.seek(0)
    await msg.answer_document(types.BufferedInputFile(output.getvalue().encode('utf-8-sig'), filename=f"products_{datetime.date.today()}.csv"))

@dp.message(Command("export_sales"))
async def cmd_export_sales(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("\\u26d4 \\u05d2\\u05d9\\u05e9\\u05ea \\u05de\\u05e0\\u05d4\\u05dc \\u05d1\\u05dc\\u05d1\\u05d3.")
    import csv, io
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT pu.id, u.username, p.name, pu.points_spent, pu.created_at 
            FROM purchases pu 
            JOIN users u ON pu.user_id = u.telegram_id 
            JOIN products p ON pu.product_id = p.id 
            ORDER BY pu.created_at DESC
        """)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "User", "Product", "Points", "Date"])
    for r in rows:
        writer.writerow([r['id'], r['username'], r['name'], r['points_spent'], r['created_at']])
    output.seek(0)
    await msg.answer_document(types.BufferedInputFile(output.getvalue().encode('utf-8-sig'), filename=f"sales_{datetime.date.today()}.csv"))

@dp.message(Command("sales"))
async def cmd_sales(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("\\u26d4 \\u05d2\\u05d9\\u05e9\\u05ea \\u05de\\u05e0\\u05d4\\u05dc \\u05d1\\u05dc\\u05d1\\u05d3.")
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT u.username, p.name, pu.points_spent, pu.created_at 
            FROM purchases pu 
            JOIN users u ON pu.user_id = u.telegram_id 
            JOIN products p ON pu.product_id = p.id 
            ORDER BY pu.created_at DESC LIMIT 50
        """)
        if not rows:
            return await msg.answer("\\u05d0\\u05d9\\u05df \\u05de\\u05db\\u05d9\\u05e8\\u05d5\\u05ea.")
        text = "\\n".join(f"{r['username']} \\u05e7\\u05e0\\u05d4 {r['name']} \\u05d1-{r['points_spent']} \\u05e0\\u05e7' ({r['created_at'].strftime('%d/%m/%Y %H:%M')})" for r in rows)
        await msg.answer(f"\\U0001f4b0 <b>\\u05de\\u05db\\u05d9\\u05e8\\u05d5\\u05ea</b>:\\n{text}")
'''
code = code.replace("# ====================== AI Fallback ======================", marketplace_code + "\n# ====================== AI Fallback ======================")

# --- F) callback handler מורחב ---
old_callback = r"@dp\.callback_query\(\).*?async def main_callback.*?\n\s*else:\s*\n\s*await msg\.answer\(\"\\u2728 Feature coming soon\"\)"
new_callback = '''@dp.callback_query()
async def main_callback(call: types.CallbackQuery):
    await call.answer()
    data = call.data
    msg = call.message
    uid = call.from_user.id
    if data.startswith("confirm_buy_"):
        product_id = int(data.split("_")[2])
        async with pool.acquire() as conn:
            product = await conn.fetchrow("SELECT id, name, price, stock FROM products WHERE id = $1 AND deleted_at IS NULL", product_id)
            if not product or product['stock'] <= 0:
                return await msg.answer("\\u05d4\\u05de\\u05d5\\u05e6\\u05e8 \\u05dc\\u05d0 \\u05d6\\u05de\\u05d9\\u05df \\u05e2\\u05d5\\u05d3.")
            user = await conn.fetchrow("SELECT points FROM users WHERE telegram_id = $1", uid)
            if not user or user['points'] < product['price']:
                return await msg.answer("\\u05d0\\u05d9\\u05df \\u05de\\u05e1\\u05e4\\u05d9\\u05e7 \\u05e0\\u05e7\\u05d5\\u05d3\\u05d5\\u05ea.")
            await conn.execute("UPDATE users SET points = points - $1 WHERE telegram_id = $2", product['price'], uid)
            await conn.execute("UPDATE products SET stock = stock - 1 WHERE id = $1", product_id)
            await conn.execute("INSERT INTO purchases (user_id, product_id, points_spent) VALUES ($1, $2, $3)", uid, product_id, product['price'])
            new_points = user['points'] - product['price']
            await msg.answer(f"\\U0001f389 \\u05e8\\u05db\\u05e9\\u05ea {product['name']} \\u05d1-{product['price']} \\u05e0\\u05e7\\u05d5\\u05d3\\u05d5\\u05ea!\\n\\u05d9\\u05ea\\u05e8\\u05d4: {new_points}")
        return
    if data.startswith("buy_"):
        product_id = int(data.split("_")[1])
        async with pool.acquire() as conn:
            product = await conn.fetchrow("SELECT id, name, price, stock FROM products WHERE id = $1 AND deleted_at IS NULL", product_id)
            if not product or product['stock'] <= 0:
                return await msg.answer("\\u05d4\\u05de\\u05d5\\u05e6\\u05e8 \\u05dc\\u05d0 \\u05d6\\u05de\\u05d9\\u05df.")
            await msg.answer(f"\\u05d4\\u05d0\\u05dd \\u05dc\\u05e8\\u05db\\u05d5\\u05e9 <b>{product['name']}</b> \\u05d1-<b>{product['price']}</b> \\u05e0\\u05e7\\u05d5\\u05d3\\u05d5\\u05ea?", reply_markup=confirm_buy_keyboard(product_id))
        return
    if data.startswith("restore_"):
        product_id = int(data.split("_")[1])
        if uid not in ADMIN_IDS:
            return await msg.answer("\\u26d4 \\u05d2\\u05d9\\u05e9\\u05ea \\u05de\\u05e0\\u05d4\\u05dc \\u05d1\\u05dc\\u05d1\\u05d3.")
        async with pool.acquire() as conn:
            product = await conn.fetchrow("SELECT name FROM products WHERE id = $1 AND deleted_at IS NOT NULL", product_id)
            if not product:
                return await msg.answer("\\u05d4\\u05de\\u05d5\\u05e6\\u05e8 \\u05dc\\u05d0 \\u05e0\\u05de\\u05e6\\u05d0 \\u05d1\\u05d0\\u05e8\\u05db\\u05d9\\u05d5\\u05df.")
            await conn.execute("UPDATE products SET deleted_at = NULL WHERE id = $1", product_id)
            await msg.answer(f"\\U0001f504 \\u05d4\\u05de\\u05d5\\u05e6\\u05e8 '{product['name']}' \\u05e9\\u05d5\\u05d7\\u05d6\\u05e8 \\u05dc\\u05d7\\u05e0\\u05d5\\u05ea.")
        return
    if data == "archive":
        await cmd_archive(msg)
        return
    if data.startswith("ask_delete_"):
        product_id = int(data.split("_")[2])
        if uid not in ADMIN_IDS:
            return await msg.answer("\\u26d4 \\u05d2\\u05d9\\u05e9\\u05ea \\u05de\\u05e0\\u05d4\\u05dc \\u05d1\\u05dc\\u05d1\\u05d3.")
        await msg.answer(f"\\u05d1\\u05d8\\u05d5\\u05d7 \\u05dc\\u05de\\u05d7\\u05d5\\u05e7 \\u05d0\\u05ea \\u05de\\u05d5\\u05e6\\u05e8 #{product_id}? \\u05d4\\u05d5\\u05d0 \\u05d9\\u05d5\\u05e2\\u05d1\\u05e8 \\u05dc\\u05d0\\u05e8\\u05db\\u05d9\\u05d5\\u05df.", reply_markup=confirm_delete_keyboard(product_id))
        return
    if data.startswith("delete_"):
        product_id = int(data.split("_")[1])
        if uid not in ADMIN_IDS:
            return await msg.answer("\\u26d4 \\u05d2\\u05d9\\u05e9\\u05ea \\u05de\\u05e0\\u05d4\\u05dc \\u05d1\\u05dc\\u05d1\\u05d3.")
        async with pool.acquire() as conn:
            product = await conn.fetchrow("SELECT name FROM products WHERE id = $1", product_id)
            if not product:
                return await msg.answer("\\u05de\\u05d5\\u05e6\\u05e8 \\u05dc\\u05d0 \\u05e0\\u05de\\u05e6\\u05d0.")
            await conn.execute("UPDATE products SET deleted_at = NOW() WHERE id = $1", product_id)
            await msg.answer(f"\\U0001f5c4\\ufe0f \\u05d4\\u05de\\u05d5\\u05e6\\u05e8 '{product['name']}' \\u05d4\\u05d5\\u05e2\\u05d1\\u05e8 \\u05dc\\u05d0\\u05e8\\u05db\\u05d9\\u05d5\\u05df.")
        return
    if data.startswith("edit_"):
        product_id = int(data.split("_")[1])
        if uid not in ADMIN_IDS:
            return await msg.answer("\\u26d4 \\u05d2\\u05d9\\u05e9\\u05ea \\u05de\\u05e0\\u05d4\\u05dc \\u05d1\\u05dc\\u05d1\\u05d3.")
        state = dp.fsm.resolve_context(bot, msg.chat.id, call.from_user.id)
        await state.update_data(product_id=product_id)
        await state.set_state(EditProductForm.waiting_name)
        async with pool.acquire() as conn:
            product = await conn.fetchrow("SELECT * FROM products WHERE id = $1", product_id)
            if not product:
                return await msg.answer("\\u05de\\u05d5\\u05e6\\u05e8 \\u05dc\\u05d0 \\u05e0\\u05de\\u05e6\\u05d0.")
        await msg.answer(f"\\u05e2\\u05e8\\u05d9\\u05db\\u05ea \\u05de\\u05d5\\u05e6\\u05e8 #{product_id}\\n\\u05e9\\u05dd \\u05e0\\u05d5\\u05db\\u05d7\\u05d9: {product['name']}\\n\\u05e9\\u05dd \\u05d7\\u05d3\\u05e9 (\\u05d0\\u05d5 '-' \\u05dc\\u05d4\\u05e9\\u05d0\\u05d9\\u05e8):")
        return
    if data == "add_product_menu":
        if uid not in ADMIN_IDS:
            return await msg.answer("\\u26d4 \\u05d2\\u05d9\\u05e9\\u05ea \\u05de\\u05e0\\u05d4\\u05dc \\u05d1\\u05dc\\u05d1\\u05d3.")
        state = dp.fsm.resolve_context(bot, msg.chat.id, call.from_user.id)
        await state.set_state(ProductForm.waiting_name)
        await msg.answer("\\u05e9\\u05dd \\u05d4\\u05de\\u05d5\\u05e6\\u05e8:")
        return
    if data == "store":
        await cmd_store(msg)
        return
    if data == "main_menu":
        await msg.answer("\\U0001f9e0 <b>SLH Spark AI v4.5</b>\\n\\n\\u05ea\\u05e4\\u05e8\\u05d9\\u05d8 \\u05e8\\u05d0\\u05e9\\u05d9", reply_markup=main_menu())
        return
    if data == "admin":
        await cmd_admin(msg)
        return
    if data == "admin_products":
        await cmd_admin_products(msg)
        return
    mapping = {
        "status": cmd_status, "points": cmd_points, "checkin": cmd_checkin,
        "tap": cmd_tap, "crypto": cmd_crypto, "donate": cmd_donate,
        "upgrade": cmd_upgrade, "tasks": cmd_tasks, "oracle": cmd_oracle,
        "peace": cmd_peace, "wallet": cmd_wallet, "referral": cmd_referral,
        "dashboard": cmd_dashboard, "help": cmd_help
    }
    handler = mapping.get(data)
    if handler:
        await handler(msg)
    else:
        await msg.answer("\\u2728 Feature coming soon")'''
code = re.sub(old_callback, new_callback, code, flags=re.DOTALL)

with open("bot.py", "w", encoding="utf-8") as f:
    f.write(code)
print("✅ bot.py updated with Marketplace, Archive, CSV, System")
