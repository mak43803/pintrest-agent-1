import asyncio
import sys
import logging
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, ".")

from agent.pinterest_agent import PinterestAgent
from baddies_watchdog import run_watchdog_audit

logging.basicConfig(level=logging.INFO, format="%(asctime)s │ %(levelname)-8s │ %(message)s")
logger = logging.getLogger("sync_and_generate")

async def main():
    logger.info("=== STARTING PRODUCT SYNC & VIRAL CREATION PIPELINE ===")
    
    # 1. Run audit
    run_watchdog_audit(auto_repair=True, verbose=True)
    
    agent = PinterestAgent()
    await agent.initialize()
    await agent.browser_manager.initialize()
    
    # 2. Check & sync pending linktree items
    pending_item = agent.get_pending_linktree_product()
    while pending_item:
        logger.info(f"⏳ Syncing pending Linktree item [ID #{pending_item['id']}]: '{pending_item.get('title') or pending_item.get('product_name')}'...")
        try:
            await agent.sync_pending_linktree_product(pending_item)
            logger.info(f"✅ Successfully synced item [ID #{pending_item['id']}] to Linktree!")
        except Exception as e:
            logger.error(f"❌ Error syncing item [ID #{pending_item['id']}]: {e}")
            break
        pending_item = agent.get_pending_linktree_product()
        
    # 3. Generate new Back-to-School viral product pin
    category = "Acne patches & pimple patches"
    product_keyword = "Hero Cosmetics Mighty Patch Original"
    logger.info(f"🚀 Generating NEW Viral Baddies Beauty Pin cycle for: '{product_keyword}' in Category: '{category}'...")
    
    try:
        success = await agent.run_affiliate_pipeline(niche=category, product_keyword=product_keyword)
        if success:
            logger.info(f"🎉 SUCCESSFULLY PUBLISHED & SYNCED NEW VIRAL PIN: '{product_keyword}'!")
        else:
            logger.warning(f"⚠️ Pipeline completed with status: {success}")
    except Exception as e:
        logger.error(f"❌ Error executing pipeline: {e}")
        
    await agent.browser_manager.close()
    await agent.db.close()
    logger.info("=== WORK COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(main())
