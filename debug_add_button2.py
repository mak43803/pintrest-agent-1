import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    profile_dir = r"c:\Users\mazzu\OneDrive\Desktop\pintrest ai agent\browser_profiles\linktree_profile"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=False
        )
        page = browser.pages[0] if browser.pages else await browser.new_page()
        await page.goto("https://linktr.ee/admin/shop", wait_until="networkidle")
        await page.wait_for_timeout(5000)
        
        # Take screenshot to see where we are
        await page.screenshot(path="debug_add_btn.png")
        
        print("Finding all buttons...")
        buttons = await page.locator("button").all()
        for i, b in enumerate(buttons):
            try:
                text = await b.inner_text()
                if "add" in text.lower():
                    html = await b.evaluate("el => el.outerHTML")
                    print(f"[{i}] {text.strip()} -> {html[:300]}")
            except:
                pass
                
        await browser.close()

asyncio.run(main())
