import asyncio
import sys
import logging
from browser.browser_manager import BrowserManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s │ %(levelname)-8s │ %(message)s")

async def main():
    manager = BrowserManager()
    await manager.initialize()
    page = await manager.context.new_page()
    
    try:
        print("Navigating to Linktree Shop...")
        await page.goto("https://linktr.ee/admin/shop", wait_until="networkidle")
        await page.wait_for_timeout(10000)
        
        # Click + Add on main page
        add_btn = page.locator('button:has-text("Add")').first
        if await add_btn.is_visible():
            await add_btn.click(force=True)
            await page.wait_for_timeout(2000)
            
            # Click Collection
            coll_btn = page.locator('button:has-text("collection"), button:has-text("Collection")').first
            if await coll_btn.is_visible():
                await coll_btn.click(force=True)
                await page.wait_for_timeout(4000)
                
                artifact_path = r"C:\Users\mazzu\.gemini\antigravity-ide\brain\44c35f6a-34ae-492b-a2ea-0e6f40144efe\linktree_step3_title.png"
                await page.screenshot(path=artifact_path, full_page=True)
                print(f"Saved title input screenshot to {artifact_path}")
                
                # Check what inputs exist
                inputs = await page.locator("input").all()
                for idx, inp in enumerate(inputs):
                    if await inp.is_visible():
                        ph = await inp.get_attribute("placeholder")
                        name = await inp.get_attribute("name")
                        typ = await inp.get_attribute("type")
                        print(f"Visible Input {idx}: placeholder={ph}, name={name}, type={typ}")
            else:
                print("Could not find Collection button in Add menu.")
        else:
            print("Could not find main Add button.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await manager.close()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
