import asyncio, sys
sys.path.insert(0, ".")
from browser.browser_manager import BrowserManager
from browser.amazon_client import AmazonClient

async def test():
    bm = BrowserManager()
    await bm.initialize()
    ac = AmazonClient(bm, "savvyshop0965-20")
    try:
        details = await ac.fetch_product_details("https://www.amazon.com/dp/B0GL9L8PF5")
        print("TITLE:", details.title)
        print("PRICE:", repr(details.price))
        print("RATING:", details.rating)
        print("REVIEWS:", details.review_count)
    finally:
        await bm.close()

asyncio.run(test())
