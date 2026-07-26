import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from playwright.async_api import async_playwright
from config.settings import PROJECT_ROOT

async def main():
    print("==========================================================")
    print(" LINKTREE INTERACTIVE LOGIN HELPER")
    print("==========================================================")
    print("Opening Google Chrome window with persistent profile...")
    print("Please log in to your Linktree account in the opened Chrome window.")
    print("Take as much time as you need.")
    print("==========================================================")

    user_data_dir = str(PROJECT_ROOT / "browser_session")
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            channel="chrome",
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
            no_viewport=False,
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto("https://linktr.ee/login")
        
        print("\n--> Chrome is open. Please log in now.")
        print("--> Press ENTER in terminal when you are done logging in...")
        
        # Wait for user input or auto-detection
        loop = asyncio.get_running_loop()
        
        async def wait_for_enter():
            await loop.run_in_executor(None, input, "Press ENTER after logging in: ")

        async def check_admin_loop():
            while True:
                try:
                    if "admin" in page.url.lower() and "login" not in page.url.lower():
                        print("\n🎉 SUCCESS! Detected active Linktree admin session!")
                        break
                except Exception:
                    pass
                await asyncio.sleep(2)

        # Wait for either user pressing enter or auto-detecting admin URL
        enter_task = asyncio.create_task(wait_for_enter())
        admin_task = asyncio.create_task(check_admin_loop())
        
        done, pending = await asyncio.wait(
            [enter_task, admin_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        for task in pending:
            task.cancel()
            
        print("\n✅ Session cookies have been saved to browser_session successfully!")
        print("Closing browser window in 5 seconds...")
        await asyncio.sleep(5)
        await context.close()

if __name__ == "__main__":
    asyncio.run(main())
