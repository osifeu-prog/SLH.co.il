import re

with open("bot_v4.5_store_final.py", "r", encoding="utf-8") as f:
    code = f.read()

# פקודות ה-Marketplace (כולל add_product, store, products, buy, archive, export, sales, admin_products, edit, delete, restore, my_purchases)
pattern = r"(# --- Marketplace.*?)(?=\n# (?:--- (?!Marketplace)|\
))"  # לוכד את כל בלוק Marketplace
match = re.search(pattern, code, re.DOTALL)
if not match:
    print("❌ לא נמצא בלוק Marketplace")
    exit()

marketplace_code = match.group(0)

# עטוף ב-Router
final_code = """from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from core.database import pool

router = Router(name="marketplace")

# FSM
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

""" + marketplace_code

with open("modular_bot/handlers/marketplace.py", "w", encoding="utf-8") as f:
    f.write(final_code)

print("✅ handlers/marketplace.py נוצר")
