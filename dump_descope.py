import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print("Navigating...")
        await page.goto("https://linktr.ee/login")
        print("Waiting 5s for descope to load...")
        await asyncio.sleep(5)
        
        try:
            # Try to get the descope-wc inner html
            wc = page.locator("descope-wc").first
            html = await wc.evaluate("el => el.shadowRoot.innerHTML")
            with open("descope_dump.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("Successfully dumped descope shadow root to descope_dump.html")
        except Exception as e:
            print(f"Failed to dump descope: {e}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
