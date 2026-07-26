import asyncio
from browser.browser_manager import BrowserManager

async def take_screenshot():
    manager = BrowserManager()
    await manager.initialize()
    page = await manager.context.new_page()
    try:
        print("Navigating to shop...")
        await page.goto("https://linktr.ee/admin/shop", wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)

        print("Taking screenshot of shop page...")
        await page.screenshot(path="linktree_shop_page.png")
        print("Done!")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await manager.close()

if __name__ == "__main__":
    asyncio.run(take_screenshot())
