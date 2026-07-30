import asyncio
import sys
from browser.browser_manager import BrowserManager

async def main():
    manager = BrowserManager()
    await manager.initialize()
    page = manager.context.pages[0]
    
    await page.goto("https://linktr.ee/admin/shop", wait_until="domcontentloaded")
    await page.wait_for_timeout(4000)
    
    drawer_loc = page.locator('*:has-text("Create new Linktree"), *:has-text("Share feedback")').filter(visible=True)
    count = await drawer_loc.count()
    print(f"DEBUG: visible drawer_loc count = {count}")
    
    for i in range(count):
        el = drawer_loc.nth(i)
        tag = await el.evaluate("el => el.tagName")
        txt = (await el.inner_text()).strip()[:100].replace('\n', ' ')
        bbox = await el.bounding_box()
        print(f"  [{i}] tag={tag}, bbox={bbox}, text='{txt}'")
        
    await manager.close()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
