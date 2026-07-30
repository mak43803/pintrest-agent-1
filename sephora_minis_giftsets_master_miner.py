"""
Sephora Ultimate Minis, Gift Sets, Sephora Favorites & Deals Master Subcategory Miner
Scrapes 100% of Sephora Mini Size, Value & Gift Sets ($15/25/35 Under), Sephora Favorites, Luxe Minis & Sale Offers
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

SEPHORA_MINIS_GIFTS_VECTORS = [
    # --- ALL MINI SIZE ---
    ("Sephora Mini Size", "Sephora mini size travel makeup lip oil blush mascara"),
    ("Sephora Mini Size", "Sephora mini size travel skincare serum moisturizer toner"),
    ("Sephora Mini Size", "Sephora mini size travel hair oil spray dry shampoo"),
    ("Sephora Mini Size", "Sephora mini size travel fragrance perfume mist spray"),
    ("Sephora Mini Size", "Sephora mini size travel bath body wash lotion set"),

    # --- VALUE & GIFT SETS BY PRICE ---
    ("Sephora Gift Sets", "Sephora beauty gift set 15 dollars and under"),
    ("Sephora Gift Sets", "Sephora beauty gift set 25 dollars and under"),
    ("Sephora Gift Sets", "Sephora beauty gift set 35 dollars and under"),
    
    # --- SEPHORA FAVORITES & LUXE MINIS ---
    ("Sephora Favorites", "Sephora favorites holiday must haves beauty box"),
    ("Sephora Favorites", "Sephora favorites perfect lip pout 6 piece set"),
    ("Sephora Favorites", "Sephora favorites luxe minis travel discovery set"),
    ("Sephora Favorites", "Sephora favorites see whats new beauty sampler kit"),

    # --- SALE & OFFERS / DISCOUNTS ---
    ("Sephora Sale & Offers", "Sephora sale beauty makeup deal discount 2026"),
    ("Sephora Sale & Offers", "Sephora sale skincare deal discount 2026"),
    ("Sephora Sale & Offers", "Sephora sale fragrance gift set deal discount"),
    ("Sephora Sale & Offers", "Sephora luxury beauty brand deal value set")
]

def seed_single_batch(products):
    if not products:
        return 0

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

        seo_title = f"{p['title']} | Sephora {p['category']} Essential 2026"
        desc = f"Discover {p['title']}. Sephora viral mini size & value gift set find!"

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
    return inserted_count

async def mine_sephora_minis_gifts_master():
    print("🚀 Starting Sephora Ultimate Minis, Gift Sets & Sephora Favorites Master Miner...")
    total_seeded = 0
    seen_urls = set()

    bm = BrowserManager()
    await bm.initialize()

    for idx, (cat_label, vector_query) in enumerate(SEPHORA_MINIS_GIFTS_VECTORS, start=1):
        print(f"\n[{idx:02d}/{len(SEPHORA_MINIS_GIFTS_VECTORS)}] 📦 Minis & Gifts Subcategory: {cat_label} | Vector: '{vector_query}'")
        
        batch = []
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

                    batch.append({
                        "title": raw_title,
                        "category": cat_label,
                        "board_name": f"{cat_label} Finds 2026",
                        "source_url": full_url,
                        "affiliate_url": affiliate_url,
                        "image_url": img_src
                    })

            except Exception as e:
                print(f"   ⚠️ Page {page_num} Error: {e}")
            finally:
                await page.close()
                await asyncio.sleep(1)

        # Real-time seeding per vector
        seeded = seed_single_batch(batch)
        total_seeded += seeded
        print(f"   ✅ Vector Finished: Extracted {len(batch)} items, Seeded {seeded} NEW items to DB! (Total Seeded: {total_seeded})")

    await bm.close()
    print("═════════════════════════════════════════════════════════════════")
    print(f" 🎉 TOTAL NEW SEPHORA MINIS & GIFT SETS SEEDED INTO DB: {total_seeded}")
    print("═════════════════════════════════════════════════════════════════")

def main():
    asyncio.run(mine_sephora_minis_gifts_master())

if __name__ == "__main__":
    main()
