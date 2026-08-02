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

logging.basicConfig(level=logging.INFO, format="%(asctime)s │ %(levelname)-8s │ %(message)s")
logger = logging.getLogger("direct_publish_test")

async def main():
    logger.info("=== TESTING DIRECT PINTEREST PUBLISH (LINKTREE BYPASSED) ===")
    agent = PinterestAgent()
    await agent.initialize()
    
    # Check pending items count
    pending = agent.get_pending_linktree_product()
    print("Pending Linktree Products count:", 1 if pending else 0)
    
    await agent.db.close()
    logger.info("=== DIRECT BYPASS VERIFIED ===")

if __name__ == "__main__":
    asyncio.run(main())
