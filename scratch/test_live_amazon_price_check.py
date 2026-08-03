import sys
sys.path.insert(0, ".")
import asyncio
from browser.amazon_client import AmazonClient
from browser.browser_manager import BrowserManager

async def test():
    driver = BrowserManager()
    await driver.initialize()
    client = AmazonClient(driver)
    
    # Pre-warm session on Amazon home page
    page = await driver.new_page()
    await page.goto("https://www.amazon.com", wait_until="domcontentloaded")
    await page.wait_for_timeout(2000)
    await page.close()
    
    urls = [
        "https://www.amazon.com/dp/B08AESTURA",
        "https://www.amazon.com/dp/B01CFL5A0G",
        "https://www.amazon.com/dp/B08C1KN9K9",
        "https://www.amazon.com/dp/B091B8756Y",
        "https://www.amazon.com/dp/B00V4L3J8U"
    ]
    
    for url in urls:
        print(f"\nTesting URL: {url}")
        try:
            prod = await client.fetch_product_details(url)
            print(f"  Title: {prod.title[:40]}")
            print(f"  Price: '{prod.price}'")
            print(f"  Rating: {prod.rating}★ ({prod.review_count} reviews)")
        except Exception as e:
            print(f"  Error: {e}")
            
    await driver.close()

if __name__ == "__main__":
    asyncio.run(test())
