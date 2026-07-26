"""
Debug: Find the correct main Add button on shop page and check what options appear.
"""
import asyncio, sys, logging
from pathlib import Path
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s │ %(levelname)-8s │ %(message)s")
PROJECT_ROOT = Path(__file__).parent
USER_DATA_DIR = str(PROJECT_ROOT / "browser_session")

async def wait_for_shop(page):
    for attempt in range(8):
        await page.wait_for_timeout(3000)
        body = await page.locator("body").inner_text()
        if "Something went wrong" in body:
            await page.reload(wait_until="domcontentloaded")
            continue
        try:
            await page.locator('button:has-text("Edit")').first.wait_for(state="visible", timeout=5000)
            return True
        except:
            pass
    return False

async def main():
    print("🔍 Finding correct main Add button...")
    pw = await async_playwright().start()
    context = await pw.chromium.launch_persistent_context(
        USER_DATA_DIR, headless=False, viewport={"width": 1280, "height": 800}, slow_mo=100,
        args=["--disable-blink-features=AutomationControlled", "--no-first-run", "--no-default-browser-check"]
    )
    page = await context.new_page()
    await page.goto("https://linktr.ee/admin/shop", wait_until="domcontentloaded")
    if not await wait_for_shop(page):
        print("❌ Shop failed to load")
        await context.close(); await pw.stop(); return

    # Find ALL elements with exact text "Add" that are visible
    print("\n--- All visible 'Add' elements ---")
    add_elements = page.locator(':text-is("Add")')
    for i in range(await add_elements.count()):
        el = add_elements.nth(i)
        try:
            vis = await el.is_visible()
            if vis:
                tag = await el.evaluate("e => e.tagName")
                cls = (await el.evaluate("e => e.className"))[:80]
                rect = await el.bounding_box()
                print(f"  [{i}] {tag} | class='{cls}' | pos=({rect['x']:.0f},{rect['y']:.0f}) | size={rect['width']:.0f}x{rect['height']:.0f}")
        except:
            pass

    # Try clicking each visible Add element and check what appears
    print("\n--- Trying button with exact text 'Add' ---")
    add_btns = page.locator('button').filter(has_text="Add")
    for i in range(await add_btns.count()):
        btn = add_btns.nth(i)
        try:
            txt = (await btn.inner_text()).strip()
            vis = await btn.is_visible()
            if txt == "Add" and vis:
                rect = await btn.bounding_box()
                print(f"  Found: button[{i}] at ({rect['x']:.0f},{rect['y']:.0f})")
                # Click it
                await btn.click(force=True)
                await page.wait_for_timeout(2000)
                
                # Check what appeared
                linked_product = page.locator('button:has-text("Linked product")')
                lp_count = await linked_product.count()
                print(f"  After click: found {lp_count} 'Linked product' buttons")
                
                for j in range(lp_count):
                    lp = linked_product.nth(j)
                    lp_txt = (await lp.inner_text()).strip().replace('\n', ' ')
                    lp_vis = await lp.is_visible()
                    print(f"    [{j}] text='{lp_txt}' visible={lp_vis}")
                
                if lp_count > 0:
                    print("✅ Found the correct Add button!")
                    break
                else:
                    # Close by pressing Escape
                    await page.keyboard.press("Escape")
                    await page.wait_for_timeout(1000)
                    print("  ❌ No Linked product option, trying next...")
        except Exception as ex:
            print(f"  Error: {ex}")

    await context.close()
    await pw.stop()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
