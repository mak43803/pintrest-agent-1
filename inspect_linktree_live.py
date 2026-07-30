import asyncio
import sys
import json
from browser.browser_manager import BrowserManager

async def main():
    manager = BrowserManager()
    await manager.initialize()
    page = manager.context.pages[0]
    
    print("Navigating to https://linktr.ee/admin/shop...")
    await page.goto("https://linktr.ee/admin/shop", wait_until="domcontentloaded")
    await page.wait_for_timeout(6000)
    
    # Save full HTML
    html_content = await page.content()
    with open("shop_dom_dump.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("Saved shop_dom_dump.html")
    
    # Take screenshot
    await page.screenshot(path="shop_dom_screenshot.png", full_page=True)
    print("Saved shop_dom_screenshot.png")
    
    # Extract DOM structure of all interactive elements
    elements_info = await page.evaluate('''() => {
        const els = Array.from(document.querySelectorAll('button, a, input, [role="button"], h1, h2, h3, h4, span, p, div'));
        return els.map(el => {
            const r = el.getBoundingClientRect();
            const txt = (el.innerText || el.textContent || '').trim().replace(/\\s+/g, ' ');
            if (r.width > 0 && r.height > 0 && txt.length > 0 && txt.length < 100) {
                return {
                    tag: el.tagName,
                    text: txt,
                    role: el.getAttribute('role') || '',
                    aria: el.getAttribute('aria-label') || '',
                    href: el.getAttribute('href') || '',
                    x: Math.round(r.x),
                    y: Math.round(r.y),
                    w: Math.round(r.width),
                    h: Math.round(r.height)
                };
            }
            return null;
        }).filter(Boolean);
    }''')
    
    with open("shop_dom_elements.json", "w", encoding="utf-8") as f:
        json.dump(elements_info, f, indent=2)
    print(f"Saved {len(elements_info)} DOM elements to shop_dom_elements.json")
    
    # Print elements that contain 'Add' or 'Collection' or 'Shop' or 'Product'
    print("\n=== Key Interactive Elements Found ===")
    for item in elements_info:
        t = item['text'].lower()
        if any(k in t for k in ['add', 'collection', 'shop', 'product', 'organize', 'manage', 'affiliate']):
            print(f"[{item['tag']}] x={item['x']}, y={item['y']}, w={item['w']}, h={item['h']} | txt='{item['text']}' | aria='{item['aria']}'")
            
    await manager.close()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
