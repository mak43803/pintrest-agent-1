import sys
import asyncio
import logging
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from browser.browser_manager import BrowserManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s │ %(levelname)-8s │ %(message)s")
logger = logging.getLogger("test_upload")

async def main():
    manager = BrowserManager()
    await manager.initialize()
    page = await manager.new_page()
    
    logger.info("Navigating to Pinterest Pin Builder...")
    await page.goto("https://www.pinterest.com/pin-builder/", wait_until="domcontentloaded")
    await page.wait_for_timeout(5000)
    
    # Save screenshot of initial pin builder page
    await page.screenshot(path="pinterest_pin_builder_initial.png", full_page=True)
    logger.info("Saved pinterest_pin_builder_initial.png")
    
    # Find all file inputs on page
    file_inputs = await page.locator('input[type="file"]').all()
    logger.info(f"Found {len(file_inputs)} input[type='file'] elements on page.")
    
    for i, fi in enumerate(file_inputs):
        is_vis = await fi.is_visible()
        accept = await fi.get_attribute("accept")
        id_attr = await fi.get_attribute("id")
        name_attr = await fi.get_attribute("name")
        data_test_id = await fi.get_attribute("data-test-id")
        logger.info(f"File Input #{i+1}: visible={is_vis}, id={id_attr}, name={name_attr}, accept={accept}, data-test-id={data_test_id}")
        
    # Check dropzone / media uploader buttons
    triggers = await page.locator('[data-test-id*="media"], [data-test-id*="upload"], [aria-label*="upload" i], [aria-label*="media" i], [role="button"]').all()
    logger.info(f"Found {len(triggers)} potential upload trigger elements.")
    for i, tr in enumerate(triggers[:10]):
        txt = await tr.inner_text()
        label = await tr.get_attribute("aria-label")
        data_tid = await tr.get_attribute("data-test-id")
        if await tr.is_visible():
            logger.info(f"Trigger #{i+1}: text='{txt.strip()[:30]}', aria-label='{label}', data-test-id='{data_tid}'")

    # Test uploading a sample image file if any image file exists in images/
    img_files = list(Path("images").glob("*.jpg")) + list(Path("images").glob("*.png"))
    if img_files:
        sample_img = str(img_files[0].resolve())
        logger.info(f"Testing upload with sample image: {sample_img}")
        
        # Try setting input files on the first file input
        if file_inputs:
            logger.info("Attempting set_input_files on file_inputs[0]...")
            await file_inputs[0].set_input_files(sample_img)
            await file_inputs[0].evaluate("el => { el.dispatchEvent(new Event('input', { bubbles: true })); el.dispatchEvent(new Event('change', { bubbles: true })); }")
            await page.wait_for_timeout(5000)
            
            await page.screenshot(path="pinterest_after_upload_attempt.png", full_page=True)
            logger.info("Saved pinterest_after_upload_attempt.png")
            
            # Check what images or previews exist after upload attempt
            imgs = await page.locator('img').all()
            logger.info(f"Total img tags on page after upload: {len(imgs)}")
            for j, img in enumerate(imgs):
                src = await img.get_attribute("src")
                if src and ("blob:" in src or "pinimg" in src or "data:" in src or "media" in src):
                    logger.info(f" Preview Image #{j+1}: src={src[:80]}")

    await manager.close()

if __name__ == "__main__":
    asyncio.run(main())
