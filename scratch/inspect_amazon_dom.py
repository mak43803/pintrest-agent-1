import asyncio, sys
sys.path.insert(0, ".")
from browser.browser_manager import BrowserManager

async def test():
    bm = BrowserManager()
    await bm.initialize()
    page = await bm.new_page()
    try:
        await page.goto("https://www.amazon.com/dp/B0GL9L8PF5", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(3000)
        
        # Check all possible title locators
        h1s = await page.locator("h1, #productTitle, #title, #titleSection h1").all_inner_texts()
        print("ALL H1s / TITLES:", h1s)
        
        # Check og:title meta tag
        meta_t = await page.locator("meta[property='og:title']").get_attribute("content")
        print("META OG TITLE:", meta_t)
        
        # Check price elements
        offscreen = await page.locator("span.a-price span.a-offscreen, .a-price .a-offscreen, #corePrice_feature_div span.a-offscreen, #corePriceDisplay_desktop_feature_div span.a-offscreen").all_inner_texts()
        print("OFFSCREEN PRICES:", offscreen)
        
        # Check body prices
        body_t = await page.locator("#dp-container, #centerCol, body").inner_text()
        import re
        prices = re.findall(r'\$\s*(\d{1,3}(?:\.\d{2})?)', body_t)
        print("FOUND PRICES IN BODY:", prices[:10])

    finally:
        await bm.close()

asyncio.run(test())
