"""
Barcode Product Lookup - Open Food Facts API
Free, no API key needed. Returns product info from barcode.
"""
import logging
import aiohttp

log = logging.getLogger("osifshop.barcode")

OFF_API = "https://world.openfoodfacts.org/api/v2/product"


async def lookup_barcode(barcode: str) -> dict | None:
    """Lookup product by barcode from Open Food Facts.
    Returns dict with name, brand, category, image_url or None if not found.
    """
    url = f"{OFF_API}/{barcode}.json"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                if data.get("status") != 1:
                    return None
                p = data.get("product", {})
                return {
                    "barcode": barcode,
                    "name": p.get("product_name") or p.get("product_name_he") or p.get("product_name_en") or "",
                    "brand": p.get("brands") or "",
                    "category": p.get("categories") or p.get("categories_tags", [""])[0] if p.get("categories_tags") else "",
                    "image_url": p.get("image_front_small_url") or p.get("image_url") or "",
                    "quantity_text": p.get("quantity") or "",
                }
    except Exception as e:
        log.warning("Barcode lookup failed for %s: %s", barcode, e)
        return None
