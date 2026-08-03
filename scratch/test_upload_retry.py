import sys
sys.path.insert(0, ".")
import asyncio
import os
from browser.browser_manager import BrowserManager

async def upload_image_resilient(page, image_path: str) -> bool:
    print(f"Uploading image resilience test for file: {image_path}")
    
    # 1. First check if input[type="file"] is attached
    for attempt in range(1, 4):
        print(f"--- Upload Attempt {attempt} ---")
        try:
            # Check attached input file
            file_inputs = await page.locator('input[type="file"], [data-test-id="media-upload-input"]').all()
            print(f"Found {len(file_inputs)} file inputs.")
            if len(file_inputs) > 0:
                for inp in file_inputs:
                    try:
                        await inp.set_input_files(image_path)
                        await page.wait_for_timeout(3000)
                        print("SUCCESS: Image attached via set_input_files!")
                        return True
                    except Exception as e:
                        print(f"set_input_files error on element: {e}")
        except Exception as e:
            print(f"Error finding input files: {e}")
            
        # Try dropzone file chooser click
        try:
            dropzone = page.locator('[data-test-id="media-empty-view"], [aria-label*="Choose a file" i], div:has-text("Choose a file"), [data-test-id="pin-draft-media-slot"]').first
            if await dropzone.count() > 0:
                print("Found dropzone element! Attempting expect_file_chooser click...")
                async with page.expect_file_chooser(timeout=5000) as fc_info:
                    await dropzone.click(force=True)
                file_chooser = await fc_info.value
                await file_chooser.set_files(image_path)
                await page.wait_for_timeout(3000)
                print("SUCCESS: Image attached via expect_file_chooser!")
                return True
        except Exception as drop_e:
            print(f"Dropzone click error: {drop_e}")
            
        await page.wait_for_timeout(2000)
        
    return False

async def test():
    driver = BrowserManager()
    await driver.initialize()
    page = await driver.new_page()
    
    print("Navigating to https://www.pinterest.com/pin-builder/...")
    await page.goto("https://www.pinterest.com/pin-builder/", wait_until="domcontentloaded", timeout=60000)
    await page.wait_for_timeout(4000)
    print(f"Page URL: {page.url}")
    
    img_path = os.path.abspath("images/c390924f.jpg")
    success = await upload_image_resilient(page, img_path)
    print(f"Upload Resilient Result: {success}")
    
    await page.screenshot(path="scratch/resilient_upload_result.png")
    print("Saved screenshot to scratch/resilient_upload_result.png")
    await driver.close()

if __name__ == "__main__":
    asyncio.run(test())
