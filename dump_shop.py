import asyncio
from playwright.async_api import async_playwright

async def dump_shop():
    async with async_playwright() as p:
        # Connect to existing user data dir
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=r"c:\Users\mazzu\AppData\Local\Google\Chrome\User Data",
            channel="chrome",
            headless=True
        )
        page = await browser.new_page()
        await page.goto("https://linktr.ee/admin/shop", wait_until="domcontentloaded")
        await page.wait_for_timeout(8000)
        
        await page.screenshot(path="debug_shop.png")
        
        # Dump all buttons
        buttons = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('button')).map(b => ({
                text: b.innerText,
                className: b.className,
                id: b.id,
                ariaLabel: b.getAttribute('aria-label')
            }));
        }''')
        
        print(f"Found {len(buttons)} buttons.")
        for idx, b in enumerate(buttons):
            text = b.get('text', '').strip().replace('\n', ' ')
            if text or b.get('ariaLabel'):
                print(f"Button {idx}: text='{text}', ariaLabel='{b.get('ariaLabel')}', class='{b.get('className')}'")
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(dump_shop())
