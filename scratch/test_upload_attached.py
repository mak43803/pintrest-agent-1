import sys
sys.path.insert(0, ".")
import asyncio
import os
from browser.browser_manager import BrowserManager

async def test():
    driver = BrowserManager()
    await driver.initialize()
    page = await driver.new_page()
    
    print("Navigating to https://www.pinterest.com/pin-creation-tool/...")
    await page.goto("https://www.pinterest.com/pin-creation-tool/", wait_until="domcontentloaded", timeout=60000)
    await page.wait_for_timeout(3000)
    
    img_path = os.path.abspath("images/c390924f.jpg")
    print(f"Uploading image: {img_path}")
    
    uploaded = False
    
    # Check attached file inputs
    try:
        print("Waiting for input[type='file'] attached...")
        await page.wait_for_selector('input[type="file"]', state="attached", timeout=10000)
        file_inputs = await page.locator('input[type="file"]').all()
        print(f"Found {len(file_inputs)} attached file inputs.")
        for inp in file_inputs:
            try:
                await inp.set_input_files(img_path)
                await page.wait_for_timeout(3000)
                uploaded = True
                print("SUCCESS setting files on attached input!")
                break
            except Exception as e:
                print(f"Input file set error: {e}")
    except Exception as e:
        print(f"Wait for attached failed: {e}")
        
    title_box = page.locator('textarea[placeholder*="title" i], [data-test-id="pin-draft-title"]').first
    print(f"Title box count after upload: {await title_box.count()}")
    
    await page.screenshot(path="scratch/attached_upload_test.png")
    print("Saved screenshot to scratch/attached_upload_test.png")
    await driver.close()

if __name__ == "__main__":
    asyncio.run(test())
