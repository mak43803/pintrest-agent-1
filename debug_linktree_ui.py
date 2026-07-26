import asyncio
import sys
import logging
from browser.browser_manager import BrowserManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s │ %(levelname)-8s │ %(message)s")

async def main():
    manager = BrowserManager()
    await manager.initialize()
    page = await manager.context.new_page()
    
    try:
        print("Navigating to Linktree Shop...")
        await page.goto("https://linktr.ee/admin/shop", wait_until="networkidle")
        await page.wait_for_timeout(10000)
        
        artifact_path = r"C:\Users\mazzu\.gemini\antigravity-ide\brain\44c35f6a-34ae-492b-a2ea-0e6f40144efe\linktree_step1_shop.png"
        await page.screenshot(path=artifact_path, full_page=True)
        print(f"Saved shop screenshot to {artifact_path}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await manager.close()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
