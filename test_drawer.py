import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from browser.browser_manager import BrowserManager
from browser.linktree_client import LinktreeClient

async def main():
    manager = BrowserManager()
    await manager.initialize()
    client = LinktreeClient(manager)
    page = await client._get_page()

    await page.goto("https://linktr.ee/admin/shop", wait_until="domcontentloaded")
    await page.wait_for_timeout(5000)

    print("--- VISIBLE BUTTONS ON PAGE ---")
    btns = await page.locator('button, a').all()
    for b in btns:
        try:
            if await b.is_visible():
                txt = (await b.inner_text()).strip().replace('\n', ' ')
                aria = await b.get_attribute("aria-label") or ""
                tid = await b.get_attribute("data-testid") or ""
                print(f"BUTTON -> text: '{txt[:40]}', aria: '{aria}', testid: '{tid}'")
        except:
            pass

    logout = page.locator('*:has-text("Log out")').filter(visible=True)
    print(f"\nLog out visible count: {await logout.count()}")

    await page.screenshot(path="logs/drawer_authenticated.png")
    print("Saved logs/drawer_authenticated.png")

    await manager.close()

if __name__ == "__main__":
    asyncio.run(main())
