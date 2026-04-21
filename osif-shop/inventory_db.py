"""
OsifShop - Inventory Database Module
Shops, products, stock movements, reports.
"""
import os
import asyncpg
import logging
from datetime import datetime, timedelta

from shared_db_core import init_db_pool as _shared_init_db_pool

log = logging.getLogger("osifshop.db")

_pool = None

async def pool():
    global _pool
    if _pool is None:
        # Phase 0B (2026-04-21): unified fail-fast pool via shared_db_core.
        # max_size standardized 5→4 to fit Railway's 88-conn budget.
        _pool = await _shared_init_db_pool(
            os.getenv("DATABASE_URL", "postgresql://postgres:slh_secure_2026@postgres:5432/slh_main"),
        )
    return _pool


async def init_tables():
    """Create inventory tables if not exist."""
    p = await pool()
    async with p.acquire() as c:
        await c.execute("""
            CREATE TABLE IF NOT EXISTS shops (
                id SERIAL PRIMARY KEY,
                owner_id BIGINT NOT NULL UNIQUE,
                shop_name TEXT NOT NULL,
                currency TEXT DEFAULT 'ILS',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await c.execute("""
            CREATE TABLE IF NOT EXISTS shop_products (
                id SERIAL PRIMARY KEY,
                shop_id INT REFERENCES shops(id),
                barcode TEXT,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT,
                price NUMERIC(12,2) DEFAULT 0,
                cost NUMERIC(12,2) DEFAULT 0,
                quantity INT DEFAULT 0,
                min_quantity INT DEFAULT 5,
                image_url TEXT,
                brand TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(shop_id, barcode)
            )
        """)
        await c.execute("""
            CREATE TABLE IF NOT EXISTS stock_movements (
                id SERIAL PRIMARY KEY,
                shop_id INT REFERENCES shops(id),
                product_id INT REFERENCES shop_products(id),
                movement_type TEXT NOT NULL,
                quantity INT NOT NULL,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await c.execute("CREATE INDEX IF NOT EXISTS idx_sp_shop ON shop_products(shop_id)")
        await c.execute("CREATE INDEX IF NOT EXISTS idx_sp_barcode ON shop_products(shop_id, barcode)")
        await c.execute("CREATE INDEX IF NOT EXISTS idx_sm_shop ON stock_movements(shop_id, created_at)")
    log.info("Inventory tables ready")


# ═══════════════════════════════════
# SHOPS
# ═══════════════════════════════════
async def get_shop(owner_id: int):
    p = await pool()
    async with p.acquire() as c:
        return await c.fetchrow("SELECT * FROM shops WHERE owner_id=$1", owner_id)


async def create_shop(owner_id: int, shop_name: str):
    p = await pool()
    async with p.acquire() as c:
        row = await c.fetchrow(
            "INSERT INTO shops (owner_id, shop_name) VALUES ($1, $2) "
            "ON CONFLICT (owner_id) DO UPDATE SET shop_name=$2 RETURNING *",
            owner_id, shop_name)
        return row


# ═══════════════════════════════════
# PRODUCTS
# ═══════════════════════════════════
async def get_product_by_barcode(shop_id: int, barcode: str):
    p = await pool()
    async with p.acquire() as c:
        return await c.fetchrow(
            "SELECT * FROM shop_products WHERE shop_id=$1 AND barcode=$2",
            shop_id, barcode)


async def get_product_by_id(product_id: int):
    p = await pool()
    async with p.acquire() as c:
        return await c.fetchrow("SELECT * FROM shop_products WHERE id=$1", product_id)


async def add_product(shop_id: int, barcode: str, name: str, brand: str = "",
                      category: str = "", image_url: str = "", price: float = 0, cost: float = 0):
    p = await pool()
    async with p.acquire() as c:
        return await c.fetchrow(
            """INSERT INTO shop_products (shop_id, barcode, name, brand, category, image_url, price, cost)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
               ON CONFLICT (shop_id, barcode) DO UPDATE SET
                   name=EXCLUDED.name, brand=EXCLUDED.brand, category=EXCLUDED.category,
                   image_url=EXCLUDED.image_url, updated_at=CURRENT_TIMESTAMP
               RETURNING *""",
            shop_id, barcode, name, brand, category, image_url, price, cost)


async def set_price(shop_id: int, barcode: str, price: float):
    p = await pool()
    async with p.acquire() as c:
        return await c.execute(
            "UPDATE shop_products SET price=$3, updated_at=CURRENT_TIMESTAMP WHERE shop_id=$1 AND barcode=$2",
            shop_id, barcode, price)


async def set_cost(shop_id: int, barcode: str, cost: float):
    p = await pool()
    async with p.acquire() as c:
        return await c.execute(
            "UPDATE shop_products SET cost=$3, updated_at=CURRENT_TIMESTAMP WHERE shop_id=$1 AND barcode=$2",
            shop_id, barcode, cost)


async def set_min_quantity(shop_id: int, barcode: str, min_qty: int):
    p = await pool()
    async with p.acquire() as c:
        return await c.execute(
            "UPDATE shop_products SET min_quantity=$3, updated_at=CURRENT_TIMESTAMP WHERE shop_id=$1 AND barcode=$2",
            shop_id, barcode, min_qty)


async def search_products(shop_id: int, query: str):
    p = await pool()
    async with p.acquire() as c:
        q = f"%{query}%"
        return await c.fetch(
            "SELECT * FROM shop_products WHERE shop_id=$1 AND (name ILIKE $2 OR barcode ILIKE $2 OR brand ILIKE $2) ORDER BY name LIMIT 20",
            shop_id, q)


async def get_all_products(shop_id: int, limit: int = 50):
    p = await pool()
    async with p.acquire() as c:
        return await c.fetch(
            "SELECT * FROM shop_products WHERE shop_id=$1 ORDER BY name LIMIT $2",
            shop_id, limit)


async def count_products(shop_id: int) -> int:
    p = await pool()
    async with p.acquire() as c:
        return await c.fetchval("SELECT COUNT(*) FROM shop_products WHERE shop_id=$1", shop_id)


# ═══════════════════════════════════
# STOCK MOVEMENTS
# ═══════════════════════════════════
async def add_stock(shop_id: int, barcode: str, qty: int, note: str = ""):
    """Add stock (incoming). Returns updated product."""
    p = await pool()
    async with p.acquire() as c:
        prod = await c.fetchrow("SELECT id, quantity FROM shop_products WHERE shop_id=$1 AND barcode=$2", shop_id, barcode)
        if not prod:
            return None
        async with c.transaction():
            new_qty = prod["quantity"] + qty
            await c.execute("UPDATE shop_products SET quantity=$2, updated_at=CURRENT_TIMESTAMP WHERE id=$1", prod["id"], new_qty)
            await c.execute(
                "INSERT INTO stock_movements (shop_id, product_id, movement_type, quantity, note) VALUES ($1,$2,'in',$3,$4)",
                shop_id, prod["id"], qty, note)
        return await c.fetchrow("SELECT * FROM shop_products WHERE id=$1", prod["id"])


async def remove_stock(shop_id: int, barcode: str, qty: int, movement_type: str = "sale", note: str = ""):
    """Remove stock (sale/adjustment). Returns updated product or None if insufficient."""
    p = await pool()
    async with p.acquire() as c:
        prod = await c.fetchrow("SELECT id, quantity FROM shop_products WHERE shop_id=$1 AND barcode=$2", shop_id, barcode)
        if not prod:
            return None, "not_found"
        if prod["quantity"] < qty:
            return None, "insufficient"
        async with c.transaction():
            new_qty = prod["quantity"] - qty
            await c.execute("UPDATE shop_products SET quantity=$2, updated_at=CURRENT_TIMESTAMP WHERE id=$1", prod["id"], new_qty)
            await c.execute(
                "INSERT INTO stock_movements (shop_id, product_id, movement_type, quantity, note) VALUES ($1,$2,$3,$4,$5)",
                shop_id, prod["id"], movement_type, qty, note)
        updated = await c.fetchrow("SELECT * FROM shop_products WHERE id=$1", prod["id"])
        return updated, "ok"


# ═══════════════════════════════════
# LOW STOCK ALERTS
# ═══════════════════════════════════
async def get_low_stock(shop_id: int):
    p = await pool()
    async with p.acquire() as c:
        return await c.fetch(
            "SELECT * FROM shop_products WHERE shop_id=$1 AND quantity <= min_quantity ORDER BY quantity ASC",
            shop_id)


# ═══════════════════════════════════
# REPORTS
# ═══════════════════════════════════
async def get_report(shop_id: int, days: int = 7):
    """Sales report for last N days."""
    p = await pool()
    since = datetime.now() - timedelta(days=days)
    async with p.acquire() as c:
        total_products = await c.fetchval("SELECT COUNT(*) FROM shop_products WHERE shop_id=$1", shop_id)
        total_stock = await c.fetchval("SELECT COALESCE(SUM(quantity), 0) FROM shop_products WHERE shop_id=$1", shop_id)
        stock_value = await c.fetchval("SELECT COALESCE(SUM(quantity * price), 0) FROM shop_products WHERE shop_id=$1", shop_id)
        cost_value = await c.fetchval("SELECT COALESCE(SUM(quantity * cost), 0) FROM shop_products WHERE shop_id=$1", shop_id)

        movements_in = await c.fetchval(
            "SELECT COALESCE(SUM(quantity), 0) FROM stock_movements WHERE shop_id=$1 AND movement_type='in' AND created_at>=$2",
            shop_id, since)
        movements_out = await c.fetchval(
            "SELECT COALESCE(SUM(quantity), 0) FROM stock_movements WHERE shop_id=$1 AND movement_type IN ('sale','out') AND created_at>=$2",
            shop_id, since)
        low_stock = await c.fetchval(
            "SELECT COUNT(*) FROM shop_products WHERE shop_id=$1 AND quantity <= min_quantity",
            shop_id)

        top_sold = await c.fetch(
            """SELECT sp.name, sp.barcode, SUM(sm.quantity) as sold
               FROM stock_movements sm JOIN shop_products sp ON sm.product_id=sp.id
               WHERE sm.shop_id=$1 AND sm.movement_type IN ('sale','out') AND sm.created_at>=$2
               GROUP BY sp.name, sp.barcode ORDER BY sold DESC LIMIT 5""",
            shop_id, since)

    return {
        "days": days,
        "total_products": total_products,
        "total_stock": total_stock,
        "stock_value": float(stock_value),
        "cost_value": float(cost_value),
        "movements_in": movements_in,
        "movements_out": movements_out,
        "low_stock": low_stock,
        "top_sold": [dict(r) for r in top_sold],
    }


async def export_csv(shop_id: int) -> str:
    """Export inventory as CSV string."""
    p = await pool()
    async with p.acquire() as c:
        rows = await c.fetch("SELECT barcode, name, brand, category, price, cost, quantity, min_quantity FROM shop_products WHERE shop_id=$1 ORDER BY name", shop_id)
    lines = ["\u05d1\u05e8\u05e7\u05d5\u05d3,\u05e9\u05dd,\u05de\u05d5\u05ea\u05d2,\u05e7\u05d8\u05d2\u05d5\u05e8\u05d9\u05d4,\u05de\u05d7\u05d9\u05e8,\u05e2\u05dc\u05d5\u05ea,\u05db\u05de\u05d5\u05ea,\u05de\u05d9\u05e0\u05d9\u05de\u05d5\u05dd"]
    for r in rows:
        lines.append(f"{r['barcode']},{r['name']},{r['brand']},{r['category']},{r['price']},{r['cost']},{r['quantity']},{r['min_quantity']}")
    return "\n".join(lines)
