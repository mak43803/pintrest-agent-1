import asyncio
import logging
import sys
import os

PROJECT_ROOT = r"c:\Users\mazzu\OneDrive\Desktop\pintrest ai agent"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from agent.pinterest_agent import PinterestAgent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("test_pipeline_single_run")

async def test_run():
    agent = PinterestAgent()
    try:
        await agent.initialize()
        logger.info("Running single affiliate pipeline cycle...")
        success = await agent.run_affiliate_pipeline(niche="Korean Sunscreens Zero White Cast")
        logger.info("Pipeline Execution Result: %s", success)
    finally:
        await agent.shutdown()

if __name__ == "__main__":
    asyncio.run(test_run())
