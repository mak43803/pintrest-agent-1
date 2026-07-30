"""
Sephora Multi-Page & Multi-Tab Mass Category Miner v5.0
Opens clean tab per query vector, crawls pages 1-3 for max product extraction.
"""
import asyncio
import datetime
import sqlite3
import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(".").resolve()))
from browser.browser_manager import BrowserManager

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

AFFILIATE_TAG = "savvyshop0965-20"
DB_PATH = Path("database/pinterest_ai_agent.db")

SEPHORA_VECTORS = [
    # New & Trending
    ("Sephora New", "Sephora new beauty releases 2026"),
    ("Sephora New", "Sephora new makeup launches"),
    ("Sephora New", "Sephora new lip oil tint"),
    # Back To School
    ("Sephora Back To School", "Back to school makeup essentials"),
    ("Sephora Back To School", "Back to school 5 minute skincare routine"),
    ("Sephora Back To School", "Dior lip oil $8 amazon dupe"),
    # Makeup
    ("Sephora Makeup", "Sephora liquid blush soft pinch"),
    ("Sephora Makeup", "Sephora dewy skin tint foundation"),
    ("Sephora Makeup", "ONE/SIZE Patrick Starrr setting spray"),
    ("Sephora Makeup", "Saie glowy super gel highlighter"),
    ("Sephora Makeup", "Charlotte Tilbury Hollywood flawless filter"),
    ("Sephora Makeup", "Summer Fridays lip butter balm"),
    ("Sephora Makeup", "Rare Beauty soft pinch matte blush"),
    ("Sephora Makeup", "e.l.f. Glow Reviver Lip Oil"),
    # Skincare
    ("Sephora Skincare", "Biodance bio collagen real deep mask"),
    ("Sephora Skincare", "Beauty of Joseon relief sun SPF 50"),
    ("Sephora Skincare", "Medicube zero pore pad 2.0"),
    ("Sephora Skincare", "Torriden dive in hyaluronic acid serum"),
    ("Sephora Skincare", "d'Alba white truffle spray serum"),
    ("Sephora Skincare", "Hero Cosmetics mighty acne patch"),
    ("Sephora Skincare", "Caudalie vinoperfect dark spot serum"),
    ("Sephora Skincare", "The Ordinary glycolic acid 7 toner"),
    # Fragrance
    ("Sephora Fragrance", "Sol de Janeiro perfume mists cheirosa 68 62 59"),
    ("Sephora Fragrance", "Kayali vanilla 28 perfume spray"),
    ("Sephora Fragrance", "Glossier You eau de parfum"),
    ("Sephora Fragrance", "Phlur missing person perfume"),
    ("Sephora Fragrance", "Maison Francis Kurkdjian Baccarat Rouge 540"),
    # Hair
    ("Sephora Hair", "Color Wow dream coat anti frizz spray"),
    ("Sephora Hair", "K18 leave in molecular repair hair mask"),
    ("Sephora Hair", "Kérastase elixir ultime hair oil"),
    ("Sephora Hair", "Moroccanoil treatment original hair oil"),
    ("Sephora Hair", "Dyson airwrap multi styler"),
    # Bath & Body
    ("Sephora Bath & Body", "Sol de Janeiro brazilian bum bum body cream"),
    ("Sephora Bath & Body", "Tree hut shea sugar scrub vanilla"),
    ("Sephora Bath & Body", "Salt & Stone natural deodorant"),
    ("Sephora Bath & Body", "Nécessaire the body wash eucalyptus"),
    # Mini Size
    ("Sephora Mini Size", "Sephora mini lip oil travel size"),
    ("Sephora Mini Size", "Sephora travel size mini skincare set"),
    ("Sephora Mini Size", "Laneige lip sleeping mask mini"),
    # Gifts & Value Sets
    ("Sephora Gifts", "Sephora beauty gift set value 2026"),
    ("Sephora Gifts", "Sephora lip care gift set holiday"),
    ("Sephora Gifts", "Sephora skincare value set kit")
]

async def mine_sephora_v5():
    print("🚀 Starting Sephora Multi-Page & Multi-Tab Mass Category Miner v5.0...")
    extracted_products = []
    seen_urls = set()

    bm = BrowserManager()
    await bm.initialize()

    for idx, (cat_label, vector_query) in enumerate(SEPHORA_VECTORS, start=1):
        print(f"\n[{idx:02d}/{len(SEPHORA_VECTORS)}] 📦 Category: {cat_label} | Vector: '{vector_query}'")
        
        # Scrape 2 pages per vector
        for page_num in range(1, 3):
            page = await bm.context.new_page()
            url = f"https://www.amazon.com/s?k={vector_query.replace(' ', '+')}&page={page_num}"
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(2000)

                for _ in range(4):
                    await page.mouse.wheel(0, 800)
                    await page.wait_for_timeout(350)

                result_cards = page.locator('div[data-component-type="s-search-result"]')
                card_count = await result_cards.count()

                yield_count = 0
                for c_idx in range(min(card_count, 18)):
                    card = result_cards.nth(c_idx)
                    link_loc = card.locator('a[href*="/dp/"]').first
                    if await link_loc.count() == 0:
                        continue

                    href = await link_loc.get_attribute("href") or ""
                    if not href or "/dp/" not in href:
                        continue

                    title_loc = card.locator('h2, span.a-text-normal, a.a-text-normal').first
                    raw_title = ""
                    if await title_loc.count() > 0:
                        raw_title = (await title_loc.inner_text()).strip().replace("\n", " ")

                    if not raw_title:
                        raw_title = (await card.inner_text()).split("\n")[0].strip()

                    if len(raw_title) < 5 or any(b in raw_title.lower() for b in ["book", "paperback", "kindle", "manual"]):
                        continue

                    full_url = href if href.startswith("http") else f"https://www.amazon.com{href}"
                    if full_url in seen_urls:
                        continue
                    seen_urls.add(full_url)

                    affiliate_url = f"{full_url}&tag={AFFILIATE_TAG}" if "tag=" not in full_url else full_url

                    img_loc = card.locator("img").first
                    img_src = ""
                    if await img_loc.count() > 0:
                        img_src = await img_loc.get_attribute("src") or ""

                    extracted_products.append({
                        "title": raw_title,
                        "category": cat_label,
                        "board_name": f"{cat_label} Finds 2026",
                        "source_url": full_url,
                        "affiliate_url": affiliate_url,
                        "image_url": img_src
                    })
                    yield_count += 1

                print(f"   📄 Page {page_num}: Extracted {yield_count} items (Total Unique: {len(extracted_products)})")

            except Exception as e:
                print(f"   ⚠️ Page {page_num} Error: {e}")
            finally:
                await page.close()
                await asyncio.sleep(1)

    await bm.close()
    print(f"\n🎉 Total Unique Sephora Category Products Extracted: {len(extracted_products)}")
    return extracted_products

def seed_to_db(products):
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

        seo_title = f"{p['title']} | Sephora {p['category']} Find 2026"
        desc = f"Discover {p['title']}. Sephora viral beauty essential & luxury find!"

        cursor.execute(
            """
            INSERT INTO products (
                product_name, category, board_name, status, source_url, 
                title, description, affiliate_link, image_path, retry_count, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
            """,
            (
                p_name,
                p["category"],
                p["board_name"],
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
    print(f" 🎉 MASS SEEDED {inserted_count} NEW SEPHORA CATEGORY PRODUCTS INTO AGENT DB!")
    print("═════════════════════════════════════════════════════════════════")

def main():
    products = asyncio.run(mine_sephora_v5())
    seed_to_db(products)

if __name__ == "__main__":
    main()
