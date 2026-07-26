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
        await page.goto("https://linktr.ee/admin/shop")
        await page.wait_for_timeout(10000)
        
        print("Finding all elements with Add...")
        buttons = await page.locator("button, [role='button'], a").all()
        found_any = False
        for i, b in enumerate(buttons):
            try:
                text = await b.inner_text()
                if "add" in text.lower():
                    html = await b.evaluate("el => el.outerHTML")
                    print(f"\n--- MATCH {i} ---")
                    print(f"TEXT: {text.strip()}")
                    print(f"HTML: {html}")
                    found_any = True
            except:
                pass
        
        if not found_any:
            print("No elements with 'add' found.")
            
        await browser.close()

asyncio.run(main())
