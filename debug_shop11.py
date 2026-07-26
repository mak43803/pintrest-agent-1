import asyncio
from browser.browser_manager import BrowserManager

async def main():
    m = BrowserManager()
    await m.initialize()
    page = await m.context.new_page()
    await page.goto('https://linktr.ee/admin/shop', wait_until='domcontentloaded')
    
    await page.wait_for_timeout(10000)
    
    print("Clicking main Add button...")
    try:
        await page.locator('button').filter(has_text="Add").first.click(force=True)
    except Exception as e:
        print("Fallback to Add product button...")
        await page.locator('button:has-text("Add product")').first.click(force=True)
            
    await page.wait_for_timeout(3000)
    await page.wait_for_timeout(3000)
    
    print("Clicking Linked product...")
    linked = page.locator('button:has-text("Linked product")').first
    if await linked.is_visible():
        await linked.click(force=True)
        await page.wait_for_timeout(2000)
        
    print("Pasting amazon link...")
    search = page.locator('input[placeholder*="Search products"], input[placeholder*="Paste URL"], input[type="url"]').first
    await search.fill('https://www.amazon.com/dp/B0BGN816K8')
    await page.wait_for_timeout(5000)
    
    print("Clicking Amazon result...")
    for btn in await page.locator('button').all():
        try:
            txt = (await btn.inner_text()).strip()
            if 'amazon' in txt.lower() and len(txt) > 20:
                await btn.click(force=True)
                break
        except Exception:
            pass
            
    await page.wait_for_timeout(5000)
    
    print("Saving dialog html...")
    try:
        dialog_html = await page.locator('div[role="dialog"]').first.inner_html()
        with open('dialog.html', 'w', encoding='utf-8') as f:
            f.write(dialog_html)
    except Exception as e:
        print("Could not get dialog HTML:", e)
        
    print("Taking screenshot...")
    await page.screenshot(path="modal_final.png", full_page=True)
    
    await m.close()
    
asyncio.run(main())
