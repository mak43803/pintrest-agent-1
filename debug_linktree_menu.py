import asyncio
from browser.browser_manager import BrowserManager

async def debug_menu():
    manager = BrowserManager()
    await manager.initialize()
    page = await manager.context.new_page()
    try:
        print("Navigating to shop...")
        await page.goto("https://linktr.ee/admin/shop", wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)

        print("Clicking Add...")
        add_btn = page.locator('button:has-text("Add")').first
        await add_btn.click(force=True)
        await page.wait_for_timeout(3000)
        
        print("Dumping all role=menuitem or button texts...")
        items = await page.locator('[role="menuitem"], button').all()
        for i in items:
            try:
                if await i.is_visible():
                    print(await i.inner_text())
            except:
                pass
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await manager.close()

if __name__ == "__main__":
    asyncio.run(debug_menu())
