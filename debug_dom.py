import asyncio
from browser.browser_manager import BrowserManager

async def main():
    print("Initializing BrowserManager...")
    manager = BrowserManager()
    await manager.initialize()
    page = await manager.new_page()
    
    print("Navigating to admin/shop...")
    await page.goto("https://linktr.ee/admin/shop")
    await page.wait_for_timeout(8000)
    
    print("Finding 'Test Collection'...")
    collection_card = None
    for sel in [":text-is('Test Collection')", "button:has-text('Test Collection')", "h3:has-text('Test Collection')", "div[role='button']:has-text('Test Collection')"]:
        try:
            await page.wait_for_selector(sel, state="visible", timeout=3000)
            collection_card = page.locator(sel).first
            break
        except Exception:
            continue
            
    if collection_card:
        print("Clicking Test Collection...")
        await collection_card.click(force=True)
        await page.wait_for_timeout(3000)
        await page.screenshot(path="debug_01_collection_opened.png")
        
        print("Finding '+ Add' button...")
        add_product_btn = None
        for selector in ['button:has-text("+ Add")', 'button:has-text("Add")', '//button[.//span[text()="Add"]]']:
            loc = page.locator(selector).locator('visible=true').first
            if await loc.count() > 0:
                add_product_btn = loc
                break
                
        if add_product_btn:
            print("Clicking + Add...")
            await add_product_btn.click(force=True)
            await page.wait_for_timeout(3000)
            print("Dumping DOM...")
            html = await page.content()
            with open("search_modal_dom.html", "w", encoding="utf-8") as f:
                f.write(html)
            
            print("Pasting URL...")
            search_input = page.locator('input[placeholder="Search products or paste a link"], #Search\\ products\\ or\\ paste\\ a\\ link-search').first
            await search_input.fill("https://www.amazon.com/dp/B081FGTPSS")
            await page.wait_for_timeout(6000)
            await page.screenshot(path="debug_03_search_results.png")
            
            print("Finding blue '+' button...")
            result_add_btn = None
            for selector in ['button[aria-label="Select product"]', 'button.bg-component-button-accent-bg:has(svg)', 'button.rounded-full:has(svg)']:
                try:
                    await page.wait_for_selector(selector, state="visible", timeout=3000)
                    result_add_btn = page.locator(selector).first
                    break
                except Exception:
                    continue
            
            if not result_add_btn:
                print("Fallback blue + button search...")
                result_add_btn = page.locator('button:has(svg)').locator('visible=true').last
                
            print("Clicking blue '+' button...")
            await result_add_btn.click(force=True)
            await page.wait_for_timeout(3000)
            await page.screenshot(path="debug_04_after_blue_plus.png")
            
            print("Clicking Continue...")
            continue_btn = page.locator('button:has-text("Continue"), button:has-text("Save")').locator('visible=true').first
            await continue_btn.click(force=True)
            await page.wait_for_timeout(3000)
            await page.screenshot(path="debug_05_after_continue.png")
            
            print("Checking if another Save is needed...")
            save_btn = page.locator('button:has-text("Save")').locator('visible=true').first
            if await save_btn.count() > 0:
                print("Clicking Save...")
                await save_btn.click(force=True)
                await page.wait_for_timeout(3000)
                await page.screenshot(path="debug_06_after_save.png")
                
            print("Done!")
        else:
            print("Could not find + Add button")
    else:
        print("Could not find Test Collection")
        
    await manager.close()

if __name__ == "__main__":
    asyncio.run(main())
