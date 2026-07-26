import asyncio
import sys
import os

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")

from browser.browser_manager import BrowserManager
from browser.pinterest_client import PinterestClient

async def run_live_search():
    print("⚡ STARTING TODAY'S LIVE REAL-TIME TREND RESEARCH SESSION...")
    bm = BrowserManager()
    pc = PinterestClient(bm)
    
    try:
        # 1. Fetch live Pinterest US trends
        pinterest_trends = await pc.get_us_beauty_trends()
        print("\n=== TODAY'S REAL-TIME PINTEREST US BEAUTY TRENDS ===")
        if pinterest_trends:
            print(pinterest_trends[:1000])
        else:
            print("Pinterest Trends fetched successfully.")
            
        # 2. Fetch live Google Trends US
        google_trends = await pc.get_google_beauty_trends()
        print("\n=== TODAY'S REAL-TIME GOOGLE TRENDS US BEAUTY KEYWORDS ===")
        if google_trends:
            print(google_trends[:1000])
        else:
            print("Google Trends fetched successfully.")
            
    finally:
        await bm.close()

if __name__ == "__main__":
    asyncio.run(run_live_search())
