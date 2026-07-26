import asyncio
import logging
from browser.browser_manager import BrowserManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s │ %(levelname)-8s │ %(message)s")
logger = logging.getLogger("find_publish_button")

async def main():
    manager = BrowserManager()
    await manager.initialize()
    page = await manager.new_page()
    
    try:
        logger.info("Navigating to Pinterest pin-builder...")
        await page.goto("https://www.pinterest.com/pin-builder/", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(5000)
        
        # Search for any element containing the text "Publish" or "Save"
        logger.info("--- Searching for any element containing 'Publish' or 'Save' ---")
        for word in ["Publish", "Save"]:
            elements = await page.locator(f'*:has-text("{word}")').all()
            logger.info(f"Found {len(elements)} elements containing '{word}':")
            for idx, el in enumerate(elements):
                try:
                    tag = await el.evaluate("el => el.tagName")
                    # We only care about buttons, inputs, links, or div/span that are visible
                    if await el.is_visible() and tag.lower() in ["button", "div", "span", "a", "input"]:
                        txt = await el.inner_text()
                        eid = await el.get_attribute("id") or ""
                        al = await el.get_attribute("aria-label") or ""
                        testid = await el.get_attribute("data-test-id") or ""
                        role = await el.get_attribute("role") or ""
                        logger.info(f"  [{idx}]: <{tag}> id='{eid}' role='{role}' data-test-id='{testid}' aria-label='{al}' text='{txt.strip()[:60]}'")
                except Exception:
                    pass
                    
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        await page.close()
        await manager._context.close()
        await manager._playwright.stop()

if __name__ == "__main__":
    asyncio.run(main())
