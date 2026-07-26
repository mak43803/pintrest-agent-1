import asyncio
import sys
import logging
from browser.browser_manager import BrowserManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s │ %(levelname)-8s │ %(message)s")

async def main():
    manager = BrowserManager()
    await manager.initialize()
    page = await manager.new_page()
    
    try:
        print("Navigating to Linktree Shop...")
        await page.goto("https://linktr.ee/admin/shop", wait_until="domcontentloaded")
        await page.wait_for_timeout(10000)
        
        # Take a screenshot BEFORE clicking
        artifact_path_before = r"C:\Users\mazzu\.gemini\antigravity-ide\brain\44c35f6a-34ae-492b-a2ea-0e6f40144efe\linktree_before_click.png"
        await page.screenshot(path=artifact_path_before, full_page=True)
        
        # Click + Add on main page
        print("Trying to click + Add...")
        add_btns = await page.locator(':has-text("Add")').all()
        for idx, btn in enumerate(add_btns):
            try:
                if await btn.is_visible():
                    tag_name = await btn.evaluate("el => el.tagName")
                    classes = await btn.evaluate("el => el.className")
                    text = await btn.inner_text()
                    if "Add" in text and len(text) < 10:
                        print(f"Clicking Visible + Add candidate {idx}: tag={tag_name}, class={classes}, text='{text}'")
                        await btn.click(force=True)
                        await page.wait_for_timeout(3000)
                        
                        # Screenshot AFTER clicking this button
                        artifact_path_after = rf"C:\Users\mazzu\.gemini\antigravity-ide\brain\44c35f6a-34ae-492b-a2ea-0e6f40144efe\linktree_after_click_{idx}.png"
                        await page.screenshot(path=artifact_path_after, full_page=True)
                        print(f"Saved after click screenshot to {artifact_path_after}")
                        break
            except Exception as e:
                pass
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await manager.close()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
