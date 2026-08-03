import sys
sys.path.insert(0, ".")
import asyncio
from browser.browser_manager import BrowserManager

async def test():
    driver = BrowserManager()
    await driver.initialize()
    page = await driver.new_page()
    
    urls = [
        "https://www.pinterest.com/pin-creation-tool/",
        "https://www.pinterest.com/pin-builder/",
        "https://www.pinterest.com/business/hub/"
    ]
    
    for url in urls:
        print(f"\n==================================================")
        print(f"Testing URL: {url}")
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(4000)
            print(f"Actual Page URL after nav: {page.url}")
            
            inputs = await page.locator('input[type="file"]').all()
            print(f"Attached input[type='file'] count: {len(inputs)}")
            
            dz = await page.locator('[data-test-id="media-empty-view"], [aria-label*="file" i], [data-test-id*="upload" i]').all()
            print(f"Dropzone candidates count: {len(dz)}")
            
            buttons = await page.locator('button, a[href*="pin"], div[role="button"]').all()
            print(f"Buttons/Links count: {len(buttons)}")
            
            # Print page title & body text snippet
            title = await page.title()
            body = (await page.inner_text("body"))[:150].replace("\n", " ")
            print(f"Title: '{title}' | Body snippet: '{body}'")
            
        except Exception as e:
            print(f"Error on {url}: {e}")
            
    await driver.close()

if __name__ == "__main__":
    asyncio.run(test())
