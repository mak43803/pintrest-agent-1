import asyncio
from browser.browser_manager import BrowserManager

async def main():
    m = BrowserManager()
    await m.initialize()
    page = await m.context.new_page()
    await page.goto('https://linktr.ee/admin/shop', wait_until='domcontentloaded')
    
    await page.wait_for_timeout(10000)
    
    await page.screenshot(path="shop_page_initial.png", full_page=True)
    print("Screenshot saved to shop_page_initial.png")
    
    await m.close()
    
asyncio.run(main())
