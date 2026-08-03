import sys
sys.path.insert(0, ".")
import asyncio
from browser.browser_manager import BrowserManager

async def test():
    driver = BrowserManager()
    await driver.initialize()
    page = await driver.new_page()
    
    print("Navigating to https://www.pinterest.com/pin-creation-tool/ with logged in session...")
    try:
        await page.goto("https://www.pinterest.com/pin-creation-tool/", wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print(f"Nav error: {e}")
        
    await page.wait_for_timeout(5000)
    print(f"URL after nav: {page.url}")
    
    # Take screenshot
    await page.screenshot(path="scratch/logged_in_builder.png")
    print("Saved screenshot to scratch/logged_in_builder.png")
    
    # Inspect inputs
    file_inputs = await page.locator('input[type="file"]').all()
    print(f"Found {len(file_inputs)} file inputs.")
    for i, inp in enumerate(file_inputs):
        print(f" Input #{i}: tag={await inp.evaluate('el => el.tagName')} | visible={await inp.is_visible()}")
        
    # Inspect buttons / dropzones
    dzs = await page.locator('[data-test-id], [aria-label], [role="button"], button').all()
    print(f"Found {len(dzs)} candidate elements.")
    for i, dz in enumerate(dzs[:30]):
        try:
            tid = await dz.get_attribute("data-test-id") or ""
            label = await dz.get_attribute("aria-label") or ""
            text = (await dz.inner_text())[:40].replace("\n", " ")
            print(f" [{i}] tid='{tid}' | label='{label}' | text='{text}' | visible={await dz.is_visible()}")
        except Exception:
            pass

    await driver.close()

if __name__ == "__main__":
    asyncio.run(test())
