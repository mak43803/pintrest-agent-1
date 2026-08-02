import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from browser.browser_manager import BrowserManager
from browser.amazon_client import AmazonClient

async def test():
    manager = BrowserManager()
    await manager.initialize()
    amazon = AmazonClient(manager, affiliate_tag="savvyshop0965-20")
    
    test_urls = [
        "https://www.amazon.com/dp/B07B4KQVK6",  # Mighty Patch
        "https://www.amazon.com/dp/B0B2RM68G2"   # Biodance Collagen Mask
    ]
    
    for url in test_urls:
        print(f"\n--- Testing Amazon Page: {url} ---")
        p = await amazon.fetch_product_details(url)
        print(f"  Title          : {p.title[:60]}")
        print(f"  Live Real Price: '{p.price}'")
        print(f"  Rating         : {p.rating}★ ({p.review_count} reviews)")
        print(f"  Clean ASIN Link: {p.affiliate_url}")
        
    await manager.close()

if __name__ == "__main__":
    asyncio.run(test())
