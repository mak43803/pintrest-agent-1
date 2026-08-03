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
    
    # Check for Create Pin button
    create_hdr_btn = page.locator('[data-test-id="mega-nav-header-name"]:has-text("Create Pin"), div:has-text("Create Pin"), button:has-text("Create Pin"), a[href*="pin-creation-tool"]').first
    if await create_hdr_btn.count() > 0 and await create_hdr_btn.is_visible():
        print("Clicking Create Pin header button...")
        await create_hdr_btn.click(force=True)
        await page.wait_for_timeout(3000)
        
    img_path = os.path.abspath("images/c390924f.jpg")
    print(f"Uploading image: {img_path}")
    
    # Strategy 1: Dropzone click + expect_file_chooser
    uploaded = False
    try:
        dropzone = page.locator('[data-test-id="media-empty-view"], [data-test-id="pin-draft-media-slot"]').first
        if await dropzone.count() > 0:
            print("Found dropzone! Clicking via expect_file_chooser...")
            async with page.expect_file_chooser(timeout=5000) as fc_info:
                await dropzone.click(force=True)
            fc = await fc_info.value
            await fc.set_files(img_path)
            await page.wait_for_timeout(4000)
            uploaded = True
            print("Successfully set files via expect_file_chooser!")
    except Exception as e:
        print(f"Strategy 1 failed: {e}")
        
    # Strategy 2: Direct set_input_files on hidden input
    if not uploaded:
        try:
            inp = page.locator('input[type="file"], [data-test-id="media-upload-input"]').first
            print("Setting input files on hidden file input...")
            await inp.set_input_files(img_path)
            await page.wait_for_timeout(4000)
            uploaded = True
            print("Successfully set files via direct hidden input!")
        except Exception as e:
            print(f"Strategy 2 failed: {e}")
            
    # Verification check: Check if title input appeared
    title_inp = page.locator('textarea[placeholder*="title" i], [data-test-id="pin-draft-title"]').first
    print(f"Title input count after upload: {await title_inp.count()}")
    
    await page.screenshot(path="scratch/after_upload_test.png")
    print("Saved screenshot to scratch/after_upload_test.png")
    await driver.close()

if __name__ == "__main__":
    asyncio.run(test())
