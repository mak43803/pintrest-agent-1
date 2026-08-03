import sys
sys.path.insert(0, ".")
import asyncio
from agent.pinterest_agent import PinterestAgent

async def test():
    agent = PinterestAgent()
    print("Executing 1 Full Pipeline Cycle for Product #932 (Color Wow Dream Coat)...")
    res = await agent.run_affiliate_pipeline(niche="Hair care & treatments")
    print(f"\nPipeline Cycle Result: {res}")

if __name__ == "__main__":
    asyncio.run(test())
