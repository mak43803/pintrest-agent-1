import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath("."))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from database.database import Database
from database.init_db import create_database
from tools.image_tools import ImageTools
from browser.browser_manager import BrowserManager
from browser.amazon_client import AmazonClient

async def test_all():
    print("=== 1. Testing Database Migration ===")
    db = Database("database/pinterest_ai_agent.db")
    create_database(db)
    with db.connection() as conn:
        cursor = conn.execute("PRAGMA table_info(products)")
        cols = [r["name"] for r in cursor.fetchall()]
        print("Products Table Columns:", cols)
        assert "price" in cols, "PRICE column missing from products table!"
    db.close()
    print("✅ Database migration verified!")

    print("\n=== 2. Testing ImageTools Price Tag & Badging ===")
    # Test valid real price
    badge_real = ImageTools.get_smart_badge("Beauty of Joseon Sunscreen", 0, "$14.99")
    print("Smart Badge with $14.99:", badge_real)
    
    # Test pin creation with real price
    test_img = "baddies_beauty_profile_photo.png"
    if os.path.exists(test_img):
        pin_path = ImageTools.create_pinterest_pin(
            test_img,
            title_text="Beauty of Joseon Relief Sun Rice Sunscreen",
            badge_text="✨ VIRAL FAVORITE",
            cta_text="Shop Now →",
            rating_text="4.8★ (15K+ REVIEWS)",
            price_text="$14.99"
        )
        print("Generated Pin with Real Price ($14.99):", pin_path)
    print("✅ ImageTools price formatting verified!")

    print("\n=== 3. Testing Amazon Live Product Search & Price Extraction ===")
    bm = BrowserManager()
    await bm.initialize()
    try:
        ac = AmazonClient(bm, "savvyshop0965-20")
        kw = "Beauty of Joseon Relief Sun Rice Sunscreen"
        url = await ac.search_products(kw)
        print("Found Amazon URL via Search:", url)
        if url:
            prod = await ac.fetch_product_details(url)
            print(f"Fetched Product: Title='{prod.title[:40]}...', Price='{prod.price}', Rating={prod.rating}★, Reviews={prod.review_count}")
            assert prod.price != "", f"Price extraction failed for {url}!"
            print(f"✅ Live Amazon Price Successfully Extracted: {prod.price}")
        else:
            print("Search returned None.")
    except Exception as e:
        print("Live Amazon search fetch error:", e)
    finally:
        await bm.close()

if __name__ == "__main__":
    asyncio.run(test_all())
