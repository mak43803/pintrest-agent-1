import asyncio
from browser.browser_manager import BrowserManager
from playwright.async_api import Page
import time

async def test_amazon_bestsellers():
    manager = BrowserManager()
    await manager.initialize()
    page = await manager.context.new_page()
    try:
        print("Navigating to Amazon Best Sellers Beauty (US)...")
        await page.goto("https://www.amazon.com/Best-Sellers-Beauty/zgbs/beauty", wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)
        
        print("Dumping all text...")
        # Typically the titles are in div[class*="p13n-sc-truncate"] or div._cDEzb_p13n-sc-css-line-clamp
        texts = await page.locator('div._cDEzb_p13n-sc-css-line-clamp-3_g3dy1, div.p13n-sc-truncate-desktop-type2, span._cDEzb_p13n-sc-css-line-clamp-2_EWgCb, div[class*="line-clamp"]').all_inner_texts()
        
        # If the specific classes aren't found, try a more generic approach
        if not texts:
            print("Fallback to generic a tag texts in the grid")
            texts = await page.locator('div#gridItemRoot a > span > div').all_inner_texts()
            
        valid_texts = set()
        for t in texts:
            t = t.strip()
            if t and len(t) > 5 and "Amazon" not in t:
                valid_texts.add(t)
                
        for t in list(valid_texts)[:30]:
            print(t)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await manager.close()

if __name__ == "__main__":
    asyncio.run(test_amazon_bestsellers())
