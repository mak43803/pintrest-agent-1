"""
Test Ulta Beauty Scraper using Playwright / Crawl4AI
"""
import asyncio
import sys
from playwright.async_api import async_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def main():
    url = "https://www.ulta.com/shop/all?minAmount=0&maxAmount=20"
    print(f"🌐 Opening Ulta Beauty: {url}...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(5000)
            
            # Scroll down slightly to load lazy images & product cards
            for _ in range(4):
                await page.mouse.wheel(0, 800)
                await page.wait_for_timeout(1000)
                
            title = await page.title()
            print(f"📄 Page Title: {title}")
            
            cards = page.locator("div.ProductCard, li.ProductListingResults__productCard, div[class*='ProductCard']")
            count = await cards.count()
            print(f"📦 Found Product Cards: {count}")
            
            if count == 0:
                # Try locating product links or general product selectors
                links = page.locator("a[href*='/p/']")
                link_count = await links.count()
                print(f"🔗 Product links found: {link_count}")
                for i in range(min(link_count, 10)):
                    l_text = await links.nth(i).inner_text()
                    l_href = await links.nth(i).get_attribute("href")
                    print(f"   Candidate #{i+1}: {l_text[:40]} | {l_href[:60]}")
            else:
                for i in range(min(count, 5)):
                    c_text = await cards.nth(i).inner_text()
                    c_text_clean = " ".join(c_text.split())
                    print(f"   Product #{i+1}: {c_text_clean[:100]}")
                    
        except Exception as e:
            print(f"❌ Error scraping Ulta: {e}")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
