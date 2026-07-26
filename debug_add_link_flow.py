import asyncio
import sys
from browser.browser_manager import BrowserManager
from browser.linktree_client import LinktreeClient

async def main():
    manager = BrowserManager()
    await manager.initialize()
    
    try:
        page = manager.context.pages[0]
        await page.goto("https://linktr.ee/admin", wait_until="networkidle")
        await page.wait_for_timeout(5000)
        
        # Take full page screenshot of main admin page
        await page.screenshot(path=r"C:\Users\mazzu\.gemini\antigravity-ide\brain\44c35f6a-34ae-492b-a2ea-0e6f40144efe\linktree_admin_page.png", full_page=True)
        print("Took screenshot of admin page")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await manager.close()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
