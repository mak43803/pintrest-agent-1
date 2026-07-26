import asyncio
import logging
import sqlite3
import sys
from browser.browser_manager import BrowserManager
from browser.linktree_client import LinktreeClient

# Force stdout/stderr to use UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(asctime)s │ %(levelname)-8s │ %(message)s")
logger = logging.getLogger("add_failed_to_linktree")

db_path = r"c:\Users\mazzu\OneDrive\Desktop\pintrest ai agent\database\pinterest_ai_agent.db"

async def main():
    # 1. Fetch failed products from SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, product_name, affiliate_link FROM products WHERE status = 'Pinterest_Published'"
    )
    products = cursor.fetchall()
    
    if not products:
        logger.info("No products found with status 'Pinterest_Published' to add.")
        conn.close()
        return
        
    logger.info(f"Found {len(products)} products with status 'Pinterest_Published' to add to Linktree.")
    
    # 2. Initialize Browser and LinktreeClient
    manager = BrowserManager()
    await manager.initialize()
    
    # Pass manager to LinktreeClient
    linktree = LinktreeClient(manager)
    
    # Authenticate Linktree if needed
    is_logged_in = await linktree.login()
    if not is_logged_in:
        logger.error("Failed to authenticate to Linktree. Exiting.")
        await manager._context.close()
        await manager._playwright.stop()
        conn.close()
        return

    success_count = 0
    failure_count = 0
    
    # 3. Add each product
    for prod_id, product_name, affiliate_link in products:
        logger.info(f"--- Adding [{success_count + failure_count + 1}/{len(products)}]: ID {prod_id} - '{product_name}' ---")
        try:
            # Add to Linktree (it will add directly to main shop feed)
            success = await linktree.add_link(title=product_name, url=affiliate_link)
            if success:
                logger.info(f"✅ Successfully added '{product_name}' to Linktree!")
                
                # Update status in DB
                cursor.execute(
                    "UPDATE products SET status = 'Published', updated_at = datetime('now') WHERE id = ?",
                    (prod_id,)
                )
                conn.commit()
                success_count += 1
            else:
                logger.error(f"❌ Failed to add '{product_name}' to Linktree.")
                failure_count += 1
        except Exception as e:
            logger.error(f"❌ Error adding '{product_name}': {e}")
            failure_count += 1
            
        # Cooldown between additions
        await asyncio.sleep(5)
        
    logger.info(f"=== Addition Summary ===")
    logger.info(f"Total processed: {len(products)}")
    logger.info(f"Successfully added & marked Published: {success_count}")
    logger.info(f"Failed to add: {failure_count}")
    
    # 4. Cleanup
    conn.close()
    # Close the context and playwright
    await manager._context.close()
    await manager._playwright.stop()

if __name__ == "__main__":
    asyncio.run(main())
