"""
Ulta Beauty Multi-Page Bulk Miner & Database Seeder v3.0
Mines 500+ to 1,000+ beauty products across multiple pages (Under $20 range) and populates Agent DB.
"""
import asyncio
import datetime
import sqlite3
import sys
import re
from pathlib import Path
from playwright.async_api import async_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

AFFILIATE_TAG = "savvyshop0965-20"
DB_PATH = Path("database/pinterest_ai_agent.db")

def format_amazon_search_affiliate(keyword: str) -> str:
    clean_kw = re.sub(r'[^\w\s]', '', keyword).replace(" ", "+")
    return f"https://www.amazon.com/s?k={clean_kw}&i=beauty&tag={AFFILIATE_TAG}"

async def mine_ulta_multipage(start_page: int = 1, end_page: int = 10):
    print(f"🚀 Starting Ulta Beauty Bulk Multi-Page Miner (Pages {start_page} to {end_page})...")

    extracted_products = []
    seen_urls = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            for page_num in range(start_page, end_page + 1):
                url = f"https://www.ulta.com/shop/all?minAmount=0&maxAmount=20&page={page_num}"
                print(f"📄 Scraping Page {page_num}/{end_page}: {url}...")

                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    await page.wait_for_timeout(3000)

                    for _ in range(8):
                        await page.mouse.wheel(0, 1000)
                        await page.wait_for_timeout(600)

                    product_links = page.locator("a[href*='/p/']")
                    count = await product_links.count()

                    page_count = 0
                    for i in range(count):
                        link = product_links.nth(i)
                        href = await link.get_attribute("href") or ""
                        if not href or href in seen_urls:
                            continue
                        seen_urls.add(href)

                        text = (await link.inner_text()).strip()
                        lines = [l.strip() for l in text.split("\n") if l.strip()]
                        if not lines:
                            continue

                        full_url = href if href.startswith("http") else f"https://www.ulta.com{href}"
                        full_title = " ".join(lines)
                        
                        # Cleaning title
                        full_title = re.sub(r'^\d+\s+sizes\s*', '', full_title, flags=re.I)
                        full_title = re.sub(r'quicklook|add to bag|shades', '', full_title, flags=re.I).strip()

                        if len(full_title) < 5:
                            continue

                        brand = lines[0] if len(lines) > 0 else "Ulta Beauty"
                        
                        img_src = ""
                        try:
                            parent = link.locator("xpath=..")
                            img_loc = parent.locator("img").first
                            if await img_loc.count() > 0:
                                img_src = await img_loc.get_attribute("src") or await img_loc.get_attribute("data-src") or ""
                        except Exception:
                            pass

                        amazon_affiliate_url = format_amazon_search_affiliate(full_title)

                        extracted_products.append({
                            "brand": brand,
                            "name": full_title,
                            "title": full_title,
                            "source_url": full_url,
                            "image_url": img_src,
                            "affiliate_url": amazon_affiliate_url
                        })
                        page_count += 1

                    print(f"   ✅ Page {page_num} Done: Extracted {page_count} items (Total so far: {len(extracted_products)})")

                except Exception as p_err:
                    print(f"   ⚠️ Error on Page {page_num}: {p_err}")

        except Exception as e:
            print(f"❌ Global Scraping Error: {e}")

        finally:
            await browser.close()

    print(f"🎉 Total Extracted Unique Ulta Products: {len(extracted_products)}")
    return extracted_products

def seed_products_to_db(products):
    if not products:
        print("⚠️ No products to seed.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT product_name, title, source_url FROM products")
    rows = cursor.fetchall()
    existing_set = set()
    for r in rows:
        if r[0]: existing_set.add(r[0].lower().strip())
        if r[1]: existing_set.add(r[1].lower().strip())
        if r[2]: existing_set.add(r[2].lower().strip())

    inserted_count = 0
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")

    for p in products:
        p_name = p["title"]
        if p_name.lower().strip() in existing_set or p["source_url"].lower().strip() in existing_set:
            continue

        seo_title = f"{p['title']} | Ulta Beauty Finds Under $20"
        desc = f"Discover {p['title']} on Ulta Beauty & Amazon. High-converting viral beauty find under $20!"
        category = "Ulta Beauty Under $20 Finds"
        board_name = "Ulta Beauty Finds Under $20"

        cursor.execute(
            """
            INSERT INTO products (
                product_name, category, board_name, status, source_url, 
                title, description, affiliate_link, image_path, retry_count, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
            """,
            (
                p_name,
                category,
                board_name,
                "Pending_Pin",
                p["source_url"],
                seo_title,
                desc,
                p["affiliate_url"],
                p["image_url"],
                now_iso,
                now_iso
            )
        )
        inserted_count += 1
        existing_set.add(p_name.lower().strip())

    conn.commit()
    conn.close()

    print("═════════════════════════════════════════════════════════════════")
    print(f" 🎉 MASS SEEDED {inserted_count} NEW ULTA BEAUTY PRODUCTS INTO AGENT DB!")
    print("═════════════════════════════════════════════════════════════════")

def main():
    # Mine 10 pages (~600+ products)
    products = asyncio.run(mine_ulta_multipage(start_page=1, end_page=10))
    seed_products_to_db(products)

if __name__ == "__main__":
    main()
