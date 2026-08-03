import sys
sys.path.insert(0, ".")
import asyncio
from browser.browser_manager import BrowserManager

async def test():
    driver = BrowserManager()
    await driver.initialize()
    page = await driver.new_page()
    
    print("Navigating to https://www.pinterest.com/pin-builder/...")
    await page.goto("https://www.pinterest.com/pin-builder/", wait_until="domcontentloaded")
    await page.wait_for_timeout(5000)
    
    print("\n--- Current Page Title & URL ---")
    print(f"URL: {page.url}")
    print(f"Title: {await page.title()}")
    
    print("\n--- Inspecting Text Inputs & Textareas ---")
    inputs = await page.locator('input, textarea, div[contenteditable="true"], button').all()
    for i, el in enumerate(inputs):
        try:
            if not await el.is_visible():
                continue
            tag = await el.evaluate("el => el.tagName")
            ph = await el.get_attribute("placeholder") or await el.get_attribute("aria-label") or await el.get_attribute("data-test-id") or await el.inner_text() or ""
            print(f"[{i}] <{tag}> data-test-id/ph/text: '{ph[:60].strip()}'")
        except Exception:
            pass
            
    await page.screenshot(path="scratch/pinterest_builder_debug.png")
    print("\nScreenshot saved to scratch/pinterest_builder_debug.png")
    await driver.close()

if __name__ == "__main__":
    asyncio.run(test())
