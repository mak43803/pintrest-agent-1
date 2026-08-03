import sys
sys.path.insert(0, ".")
import asyncio
from browser.browser_manager import BrowserManager

async def test():
    driver = BrowserManager()
    await driver.initialize()
    page = await driver.new_page()
    
    print("Navigating to https://www.pinterest.com/pin-creation-tool/...")
    await page.goto("https://www.pinterest.com/pin-creation-tool/", wait_until="domcontentloaded", timeout=60000)
    await page.wait_for_timeout(4000)
    print(f"URL: {page.url}")
    
    # Try clicking Create Pin menu button
    print("\nLooking for 'Create Pin' header button...")
    create_pin_btn = page.locator('[data-test-id="mega-nav-header-name"]:has-text("Create Pin"), div:has-text("Create Pin"), button:has-text("Create Pin"), a[href*="pin-creation-tool"]').first
    if await create_pin_btn.count() > 0 and await create_pin_btn.is_visible():
        print("Found Create Pin button! Clicking...")
        await create_pin_btn.click()
        await page.wait_for_timeout(5000)
        print(f"URL after click: {page.url}")
        
    print("\n--- Inspecting page after click ---")
    file_inputs = await page.locator('input[type="file"]').all()
    print(f"Found {len(file_inputs)} file inputs.")
    
    elements = await page.locator('input, textarea, div[contenteditable="true"], button, [data-test-id]').all()
    print(f"Found {len(elements)} elements.")
    for i, el in enumerate(elements):
        try:
            if not await el.is_visible():
                continue
            tag = await el.evaluate("el => el.tagName")
            tid = await el.get_attribute("data-test-id") or ""
            ph = await el.get_attribute("placeholder") or await el.get_attribute("aria-label") or await el.inner_text() or ""
            print(f" [{i}] <{tag}> data-test-id='{tid}' | text/ph: '{ph[:50].strip()}'")
        except Exception:
            pass

    await page.screenshot(path="scratch/pinterest_creation_tool_click.png")
    print("\nSaved screenshot to scratch/pinterest_creation_tool_click.png")
    await driver.close()

if __name__ == "__main__":
    asyncio.run(test())
