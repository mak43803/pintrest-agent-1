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
        
        # 1. Find Gamer Tech (Test) collection and click "Add products to collection +"
        coll_loc = page.get_by_text("Gamer Tech (Test)", exact=True).first
        add_products_btn = page.locator('button, div').filter(has_text="Add products to collection +").first
        
        if await add_products_btn.is_visible():
            await add_products_btn.click(force=True)
        else:
            await coll_loc.click(force=True)
            
        await page.wait_for_timeout(3000)
        
        # 2. Click small + Add
        for selector in ['button:has-text("Add")', 'text="+ Add"']:
            for btn in reversed(await page.locator(selector).all()):
                if await btn.is_visible():
                    await btn.click(force=True)
                    break
                
        await page.wait_for_timeout(3000)
        
        # 3. Paste URL
        url = "https://www.amazon.com/dp/B08HR4ZLYP"
        search_input = page.locator('input[placeholder*="Search"], input[placeholder*="paste"], input[type="url"]').first
        await search_input.click(force=True)
        await search_input.fill(url)
        
        await page.wait_for_timeout(15000)
        
        # 4. Check for Product Details form and close image modal
        await page.wait_for_timeout(5000)
        if await page.get_by_text("Select file to upload").first.is_visible():
            print("Upload modal is visible. Pressing Escape...")
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(3000)
        
        # 5. Take Screenshot!
        artifact_path = r"C:\Users\mazzu\.gemini\antigravity-ide\brain\44c35f6a-34ae-492b-a2ea-0e6f40144efe\linktree_after_escape.png"
        await page.screenshot(path=artifact_path, full_page=True)
        print(f"Screenshot taken: {artifact_path}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await manager.close()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
