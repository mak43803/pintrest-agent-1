import asyncio
import logging
import sys
from browser.browser_manager import BrowserManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s │ %(levelname)-8s │ %(message)s")
logger = logging.getLogger("debug_collections")

async def main():
    manager = BrowserManager()
    await manager.initialize()
    page = await manager.new_page()
    
    try:
        logger.info("Navigating to Linktree Shop page...")
        await page.goto("https://linktr.ee/admin/shop", wait_until="domcontentloaded", timeout=60000)
        
        # Wait for page to load
        logger.info("Waiting for page load...")
        await page.wait_for_timeout(5000)
        
        # Switch to Manage tab
        manage_tab = page.locator('button:has-text("Manage")').first
        if await manage_tab.is_visible():
            logger.info("Clicking Manage tab...")
            await manage_tab.click(force=True)
            await page.wait_for_timeout(3000)
        
        # Save screenshot of Manage tab
        await page.screenshot(path="scratch/manage_tab.png")
        logger.info("Saved screenshot to scratch/manage_tab.png")
        
        # Print all visible buttons and text
        buttons = await page.locator("button").all()
        logger.info("--- Visible buttons on Manage tab: ---")
        for i, btn in enumerate(buttons):
            if await btn.is_visible():
                txt = await btn.inner_text()
                logger.info(f"Button [{i}]: '{txt.strip()}'")
                
        # Save page HTML
        content = await page.content()
        with open("scratch/manage_tab.html", "w", encoding="utf-8") as f:
            f.write(content)
        logger.info("Saved page HTML to scratch/manage_tab.html")
        
    except Exception as e:
        logger.error(f"Error occurred: {e}")
    finally:
        await page.close()
        await manager._context.close()
        await manager._playwright.stop()

if __name__ == "__main__":
    asyncio.run(main())
