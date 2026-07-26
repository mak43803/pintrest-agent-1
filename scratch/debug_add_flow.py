import asyncio
import logging
from browser.browser_manager import BrowserManager
from browser.linktree_client import LinktreeClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    manager = BrowserManager()
    await manager.initialize()
    page = await manager.new_page()
    
    try:
        logger.info("Navigating to Shop page...")
        await page.goto("https://linktr.ee/admin/shop", wait_until="domcontentloaded")
        
        logger.info("Waiting for Edit button...")
        edit_btn = page.locator('button:has-text("Edit")').first
        await edit_btn.wait_for(state="visible", timeout=30000)
        logger.info("Shop page loaded successfully!")
        
        # Click the Add button
        add_btn = page.get_by_role("button", name="Add", exact=True)
        await add_btn.click()
        logger.info("Clicked Add button.")
        await page.wait_for_timeout(2000)
        
        # Click "Linked product"
        linked_btn = page.locator('button:has-text("Add a Linked product to your shop")').first
        await linked_btn.click()
        logger.info("Clicked Linked product button.")
        await page.wait_for_timeout(3000)
        
        # Paste raw link
        url = "https://www.amazon.com/dp/B0036BCWG0"
        search_input = page.locator('input[placeholder*="Search products"], input[placeholder*="Paste URL"], input[type="url"]').first
        await search_input.fill(url)
        logger.info("Pasted URL.")
        await page.wait_for_timeout(5000)
        
        # Locate search result and click
        dialog = page.locator('dialog:has-text("Add a Linked product")').first
        result_btn = dialog.locator('section button').first
        await result_btn.click(force=True)
        logger.info("Clicked search result. Waiting 5 seconds...")
        await page.wait_for_timeout(5000)
        
        # Save screenshot
        await page.screenshot(path="scratch/product_details_open.png")
        logger.info("Saved screenshot to scratch/product_details_open.png")
        
        # Print all visible buttons on page
        buttons = await page.locator("button").all()
        logger.info("Visible buttons with details modal open:")
        for i, btn in enumerate(buttons):
            if await btn.is_visible():
                txt = await btn.inner_text()
                logger.info(f"  [{i}]: '{txt.strip()}'")
                
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        await page.close()
        await manager._context.close()
        await manager._playwright.stop()

asyncio.run(main())
