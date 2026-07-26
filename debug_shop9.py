import asyncio
from browser.browser_manager import BrowserManager

async def main():
    m = BrowserManager()
    await m.initialize()
    page = await m.context.new_page()
    await page.goto('https://linktr.ee/admin/shop', wait_until='domcontentloaded')
    
    await page.wait_for_timeout(5000)
    
    print("Clicking Affiliate Products tab...")
    await page.locator('text="Affiliate Products"').first.click(force=True)
    await page.wait_for_timeout(3000)
    
    print("Clicking exact Add button...")
    add_btn = page.get_by_role('button', name='Add', exact=True).first
    if await add_btn.is_visible():
        await add_btn.click(force=True)
        
    await page.wait_for_timeout(3000)
    
    print("Clicking Linked product...")
    linked = page.locator('button:has-text("Linked product")').first
    if await linked.is_visible():
        await linked.click(force=True)
        await page.wait_for_timeout(2000)
        
    search = page.locator('input[placeholder*="Search products"]').first
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
            
    await page.wait_for_timeout(4000)
    
    print('Trying has-text("Add product")...')
    final_btn = page.locator('button:has-text("Add product")').first
    if await final_btn.is_visible():
        print('Found Add product with has-text!')
        await final_btn.click(force=True)
    else:
        print('Not found with has-text. Trying get_by_role...')
        final_btn = page.get_by_role('button', name='Add product').first
        if await final_btn.is_visible():
            print('Found with get_by_role!')
        else:
            print('Could not find Add product at all. Buttons are:')
            btns = await page.locator('button').all_inner_texts()
            print([b for b in btns if b.strip()])
            
    await m.close()
    
asyncio.run(main())
