import asyncio
import sys
from browser.browser_manager import BrowserManager

async def main():
    manager = BrowserManager()
    await manager.initialize()
    
    try:
        page = manager.context.pages[0]
        await page.goto("https://linktr.ee/admin/shop", wait_until="networkidle")
        await page.wait_for_timeout(5000)
        
        # 1. Click main + Add button at the very top of the Shop page
        print("Clicking main + Add button...")
        add_btn = page.locator('button:has-text("Add"), span:has-text("+ Add"), button[aria-label*="Add" i]').first
        await add_btn.click()
        await page.wait_for_timeout(2000)
        
        # Take a screenshot to see what modal or dropdown it shows next!
        artifact_path = r"C:\Users\mazzu\.gemini\antigravity-ide\brain\44c35f6a-34ae-492b-a2ea-0e6f40144efe\linktree_after_add.png"
        await page.screenshot(path=artifact_path, full_page=True)
        print(f"Screenshot taken: {artifact_path}")
        
        # The screenshot is taken!
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await manager.close()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
