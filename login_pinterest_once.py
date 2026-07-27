import asyncio
import logging
from playwright.async_api import async_playwright
from pathlib import Path
from config.settings import PROJECT_ROOT

logging.basicConfig(level=logging.INFO, format="%(asctime)s │ %(levelname)-8s │ %(message)s")
logger = logging.getLogger("login_pinterest")

async def main():
    user_data_dir = str(PROJECT_ROOT / "browser_session")
    logger.info("Launching Chrome GUI mode to log in to Pinterest...")
    
    async with async_playwright() as p:
        # Launch persistent context in headful mode (headless=False)
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            channel="chrome",
            headless=False,
            viewport={"width": 1280, "height": 800},
            ignore_default_args=["--enable-automation"],
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        page = await context.new_page()
        
        logger.info("Opening Pinterest Login...")
        await page.goto("https://www.pinterest.com/login", wait_until="domcontentloaded")
        
        logger.info("=========================================================")
        logger.info("📌 PINTEREST MANUAL LOGIN WINDOW IS NOW OPEN!")
        logger.info("Please log in to your Pinterest Account in the opened Chrome window.")
        logger.info("Once you are logged in successfully and see your Pinterest Feed/Home,")
        logger.info("just wait here. The session cookies will save automatically.")
        logger.info("=========================================================")
        
        # Wait 120 seconds for user to log in
        for i in range(120, 0, -1):
            current_url = page.url.lower()
            if "login" not in current_url and ("pinterest.com" in current_url or "home" in current_url):
                logger.info(f"✅ Login Detected! (URL: {current_url})")
                await asyncio.sleep(5) # Let cookies settle
                break
                
            if i % 10 == 0:
                logger.info(f"⏳ {i} seconds remaining for manual login...")
            await asyncio.sleep(1)
            
        logger.info("Closing browser and saving persistent session cookies...")
        await context.close()
        logger.info("🎉 Pinterest Session Cookies successfully saved to browser_session!")

if __name__ == "__main__":
    asyncio.run(main())
