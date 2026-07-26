import asyncio
import logging
from browser.browser_manager import BrowserManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    manager = BrowserManager()
    await manager.initialize()
    page = await manager.new_page()
    
    try:
        logger.info("Navigating to Shop page...")
        await page.goto("https://linktr.ee/admin/shop", wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)
        
        # Close any open dialogs using our selectors
        closed_any = False
        for close_selector in [
            '[aria-label="Close"]',
            '[aria-label="Close dialog"]',
            'button:has-text("Close")',
            'button.close-button',
            '[data-testid="tips-dialog-done"]'
        ]:
            try:
                close_btns = await page.locator(close_selector).all()
                for btn in close_btns:
                    if await btn.is_visible():
                        logger.info(f"Clicking visible close button: {close_selector}")
                        await btn.click(force=True)
                        closed_any = True
                        await page.wait_for_timeout(1000)
            except Exception as e:
                logger.error(f"Error clicking {close_selector}: {e}")
                
        if not closed_any:
            logger.info("No visible close buttons found. Pressing Escape key...")
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(1000)
            
        await page.screenshot(path="scratch/after_cleanup.png")
        logger.info("Saved cleanup screenshot to scratch/after_cleanup.png")
        
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        await page.close()
        await manager._context.close()
        await manager._playwright.stop()

asyncio.run(main())
