import asyncio
import logging
import sqlite3
import os
import sys

# Add project root to sys.path
PROJECT_ROOT = r"c:\Users\mazzu\OneDrive\Desktop\pintrest ai agent"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from browser.browser_manager import BrowserManager
from browser.amazon_client import AmazonClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("fix_search_links_in_db")

async def clean_database_search_links():
    db_path = os.path.join(PROJECT_ROOT, "database", "pinterest_ai_agent.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # Select products where affiliate_link is a search link (/s?k=...) or missing /dp/
    rows = conn.execute("SELECT id, product_name, title, affiliate_link FROM products WHERE status = 'Pending_Pin' AND (affiliate_link LIKE '%/s?k=%' OR affiliate_link NOT LIKE '%/dp/%')").fetchall()
    
    logger.info("Found %d products in Pending_Pin with search links needing direct ASIN resolution.", len(rows))
    if not rows:
        conn.close()
        return

    manager = BrowserManager()
    await manager.initialize()
    amazon = AmazonClient(manager)

    fixed_count = 0
    deleted_count = 0

    try:
        for r in rows:
            prod_id = r["id"]
            p_name = r["product_name"]
            aff_link = r["affiliate_link"] or ""
            
            logger.info("Processing Product #%d: '%s' (Current Link: %s)", prod_id, p_name[:40], aff_link[:60])
            
            clean_url = await amazon.ensure_direct_product_url(aff_link)
            
            if clean_url and "/dp/" in clean_url:
                conn.execute("UPDATE products SET affiliate_link = ? WHERE id = ?", (clean_url, prod_id))
                conn.commit()
                fixed_count += 1
                logger.info("✅ Fixed Product #%d -> %s", prod_id, clean_url)
            else:
                # If cannot resolve to a direct ASIN product page, remove unresolvable row to avoid bad pins
                conn.execute("DELETE FROM products WHERE id = ?", (prod_id,))
                conn.commit()
                deleted_count += 1
                logger.warning("⚠️ Deleted unresolvable Product #%d: '%s'", prod_id, p_name[:40])
    finally:
        await manager.close()
        conn.close()
        logger.info("🎉 Database Search Link Cleanup Complete: %d resolved to direct ASINs, %d unresolvable deleted.", fixed_count, deleted_count)

if __name__ == "__main__":
    asyncio.run(clean_database_search_links())
