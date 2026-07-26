import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://linktr.ee/login")
        await asyncio.sleep(5)
        
        # Dump page text
        text = await page.evaluate("document.body.innerText")
        with open("page_text.txt", "w", encoding="utf-8") as f:
            f.write(text)
            
        print("Dumped page text.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
