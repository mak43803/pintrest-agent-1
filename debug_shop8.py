import asyncio
from browser.browser_manager import BrowserManager

async def main():
    m = BrowserManager()
    await m.initialize()
    page = await m.context.new_page()
    await page.goto('https://linktr.ee/admin/shop', wait_until='domcontentloaded')
    
    await page.wait_for_timeout(5000)
    
    add_btn = page.get_by_role('button', name='Add', exact=True).first
    if not await add_btn.is_visible():
        add_btn = page.get_by_role('button', name='+ Add').first
    await add_btn.click(force=True)
    await page.wait_for_timeout(3000)
    
    linked = page.locator('button:has-text("Linked product")').first
    if await linked.is_visible():
        await linked.click(force=True)
        await page.wait_for_timeout(2000)
        
    search = page.locator('input[placeholder*="Search products"]').first
    await search.fill('https://www.amazon.com/dp/B0BGN816K8')
    await page.wait_for_timeout(5000)
    
    for btn in await page.locator('button').all():
        try:
            txt = (await btn.inner_text()).strip()
            if 'amazon' in txt.lower() and len(txt) > 20:
                await btn.click(force=True)
                break
        except Exception:
            pass
            
    await page.wait_for_timeout(4000)
    
    print('Finding final save button...')
    for btn in await page.locator('button').all():
        txt = (await btn.inner_text()).strip()
        if 'add' in txt.lower() or 'save' in txt.lower():
            vis = await btn.is_visible()
            dis = await btn.is_disabled()
            print(f"Potential final button: '{txt}' (Visible: {vis}, Disabled: {dis})")
            
    await m.close()
    
asyncio.run(main())
