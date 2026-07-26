import asyncio
from browser.browser_manager import BrowserManager

async def create_collection_test():
    manager = BrowserManager()
    await manager.initialize()
    page = await manager.context.new_page()
    try:
        print("Navigating to shop...")
        await page.goto("https://linktr.ee/admin/shop", wait_until="domcontentloaded")
        
        print("Waiting for shop to load...")
        # Wait for 'Edit' button which means collections are loaded
        for attempt in range(10):
            await page.wait_for_timeout(3000)
            try:
                await page.locator('button:has-text("Edit")').first.wait_for(state="visible", timeout=5000)
                print("Shop fully loaded!")
                break
            except:
                pass
                
        print("Clicking Add...")
        add_btn = None
        for btn in await page.locator("button").all():
            try:
                txt = (await btn.inner_text()).strip()
                if txt == "Add" and await btn.is_visible():
                    add_btn = btn
                    break
            except Exception:
                pass
        
        if add_btn:
            await add_btn.click(force=True)
            await page.wait_for_timeout(2000)
            
            print("Looking for 'collection' in menu...")
            items = await page.locator('[role="menuitem"], button').all()
            found_coll = None
            for i in items:
                try:
                    if await i.is_visible():
                        txt = await i.inner_text()
                        print("Menu item:", txt)
                        if "collection" in txt.lower():
                            found_coll = i
                except:
                    pass
            
            if found_coll:
                print("Clicking collection menu item...")
                await found_coll.click(force=True)
                await page.wait_for_timeout(3000)
                await page.screenshot(path="linktree_coll_modal.png")
            else:
                print("No collection text found in menu.")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await manager.close()

if __name__ == "__main__":
    asyncio.run(create_collection_test())
