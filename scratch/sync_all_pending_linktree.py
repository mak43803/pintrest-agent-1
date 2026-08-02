import asyncio
import sys
import logging

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, ".")

from agent.pinterest_agent import PinterestAgent

logging.basicConfig(level=logging.INFO, format="%(asctime)s │ %(levelname)-8s │ %(message)s")
logger = logging.getLogger("sync_pending_linktree")

async def main():
    logger.info("=== STARTING PENDING LINKTREE SYNC ===")
    agent = PinterestAgent()
    await agent.initialize()
    await agent.browser_manager.initialize()
    
    synced_count = 0
    pending_item = agent.get_pending_linktree_product()
    
    while pending_item:
        logger.info(f"⏳ Syncing pending Linktree item [ID #{pending_item['id']}]: '{pending_item.get('title') or pending_item.get('product_name')}'...")
        try:
            success = await agent.sync_pending_linktree_product(pending_item)
            if success:
                synced_count += 1
                logger.info(f"✅ Successfully synced item [ID #{pending_item['id']}] to Linktree!")
            else:
                logger.error(f"❌ Failed to sync item [ID #{pending_item['id']}]")
                break
        except Exception as e:
            logger.error(f"❌ Exception syncing item [ID #{pending_item['id']}]: {e}")
            break
            
        pending_item = agent.get_pending_linktree_product()
        await asyncio.sleep(2)
        
    logger.info(f"=== LINKTREE SYNC COMPLETE: Synced {synced_count} items ===")
    await agent.browser_manager.close()
    await agent.db.close()

if __name__ == "__main__":
    asyncio.run(main())
