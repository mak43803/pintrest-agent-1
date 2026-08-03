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
    
    create_hdr_btn = page.locator('[data-test-id="mega-nav-header-name"]:has-text("Create Pin"), div:has-text("Create Pin"), button:has-text("Create Pin")').first
    if await create_hdr_btn.count() > 0 and await create_hdr_btn.is_visible():
        print("Clicking Create Pin header button...")
        await create_hdr_btn.click(force=True)
        await page.wait_for_timeout(3000)
        
    img_path = os.path.abspath("images/c390924f.jpg")
    print(f"Uploading image: {img_path}")
    
    uploaded = False
    
    # Method 1: Dropzone div click
    dropzone = page.locator('[data-test-id="media-empty-view"], [aria-label*="Choose a file" i], div:has-text("Choose a file")').first
    if await dropzone.count() > 0 and await dropzone.is_visible():
        try:
            print("Trying Method 1: Dropzone click with expect_file_chooser...")
            async with page.expect_file_chooser(timeout=5000) as fc_info:
                await dropzone.click(force=True)
            fc = await fc_info.value
            await fc.set_files(img_path)
            await page.wait_for_timeout(3000)
            uploaded = True
            print("SUCCESS via Method 1 (Dropzone click)!")
        except Exception as e:
            print(f"Method 1 failed: {e}")
            
    # Method 2: Direct set_input_files on page level file locator
    if not uploaded:
        try:
            print("Trying Method 2: page.set_input_files('input[type=\"file\"]') ...")
            file_loc = page.locator('input[type="file"]').first
            await file_loc.set_input_files(img_path)
            await page.wait_for_timeout(3000)
            uploaded = True
            print("SUCCESS via Method 2 (page.set_input_files)!")
        except Exception as e:
            print(f"Method 2 failed: {e}")

    title_box = page.locator('textarea[placeholder*="title" i], [data-test-id="pin-draft-title"]').first
    print(f"Title box count after upload: {await title_box.count()}")
    
    await page.screenshot(path="scratch/perfect_upload_test.png")
    print("Saved screenshot to scratch/perfect_upload_test.png")
    await driver.close()

if __name__ == "__main__":
    asyncio.run(test())
