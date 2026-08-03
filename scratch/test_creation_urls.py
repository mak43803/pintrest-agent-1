import sys
sys.path.insert(0, ".")
import asyncio
from browser.browser_manager import BrowserManager

async def test():
    driver = BrowserManager()
    await driver.initialize()
    page = await driver.new_page()
    
    test_urls = [
        "https://www.pinterest.com/pin-builder/",
        "https://www.pinterest.com/pin-creation-tool/",
        "https://www.pinterest.com/idea-pin-builder/",
        "https://www.pinterest.com/create/",
        "https://www.pinterest.com/business/hub/"
    ]
    
    for u in test_urls:
        print(f"\n--- Navigating to: {u} ---")
        try:
            await page.goto(u, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)
            print(f"Final URL: {page.url}")
            inputs = await page.locator('input[type="file"]').count()
            print(f"Input file count: {inputs}")
            if inputs > 0:
                print(f"🎉 FOUND WORKING PIN BUILDER URL: {u} (Final: {page.url})")
        except Exception as e:
            print(f"Error on {u}: {e}")
            
    # Also test clicking Create button on home page
    print("\n--- Testing Click 'Create' button on Home Page ---")
    await page.goto("https://www.pinterest.com/", wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(3000)
    print(f"Home URL: {page.url}")
    
    # Try finding Create button/link
    create_btn = page.locator('a[href*="pin-builder"], a[href*="creation"], button:has-text("Create"), div:has-text("Create"), [aria-label*="Create" i]').first
    if await create_btn.count() > 0:
        print(f"Found Create button! Text: '{await create_btn.inner_text()}' | Clicking...")
        await create_btn.click(force=True)
        await page.wait_for_timeout(3000)
        print(f"URL after click: {page.url}")
        print(f"Input file count after click: {await page.locator('input[type=\"file\"]').count()}")

    await driver.close()

if __name__ == "__main__":
    asyncio.run(test())
