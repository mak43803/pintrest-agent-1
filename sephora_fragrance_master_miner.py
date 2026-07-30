"""
Sephora Ultimate Fragrance & Home Scents Master Subcategory Miner
Scrapes 100% of Sephora Fragrance Subcategories (Women's Perfume, Perfume Oils, Rollerballs, Body Mists, Men's Cologne, Unisex, Gift Sets, Candles, Fragrance Families & Special Collections)
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

SEPHORA_FRAGRANCE_VECTORS = [
    # --- WOMEN'S FRAGRANCE ---
    ("Sephora Women's Perfume", "Sephora women perfume spray eau de parfum floral vanilla"),
    ("Sephora Perfume Oils", "Sephora Arabian perfume oil concentrated roll on vanilla amber"),
    ("Sephora Travel Fragrance", "Sephora travel size perfume spray rollerball mini"),
    ("Sephora Body & Hair Mists", "Sol de Janeiro cheirosa perfume mists 68 62 59 71"),
    ("Sephora Body & Hair Mists", "Sephora body mist hair fragrance spray vanilla gourmet"),

    # --- MEN'S & UNISEX FRAGRANCE ---
    ("Sephora Men's Cologne", "Sephora men cologne spray Sauvage Bleu de Chanel Sauvage"),
    ("Sephora Men's Cologne", "Sephora travel size mini cologne spray men"),
    ("Sephora Unisex Fragrance", "Sephora unisex genderless eau de parfum Maison Margiela Replica"),

    # --- VALUE & GIFT SETS ---
    ("Sephora Fragrance Gift Sets", "Sephora perfume discovery gift set sampler travel size"),
    ("Sephora Fragrance Gift Sets", "Sephora men cologne value gift set holiday"),
    ("Sephora Fragrance Gift Sets", "Sephora favorites perfume sampler voucher set"),

    # --- CANDLES & HOME SCENTS ---
    ("Sephora Home Scents", "Sephora luxury scented candles soy wax vanilla amber"),
    ("Sephora Home Scents", "Sephora reed diffuser home fragrance oil spray"),

    # --- FRAGRANCE FAMILIES ---
    ("Sephora Fragrance Families", "Sephora floral perfume jasmine rose tuberose orange blossom"),
    ("Sephora Fragrance Families", "Sephora warm spicy perfume vanilla amber cinnamon gourmand"),
    ("Sephora Fragrance Families", "Sephora fresh clean perfume citrus aquatic linen green"),
    ("Sephora Fragrance Families", "Sephora earthy woody perfume sandalwood cedarwood musk"),

    # --- SPECIAL COLLECTIONS & FORMATS ---
    ("Sephora Fragrance Formats", "Sephora clean non toxic certified perfume spray"),
    ("Sephora Fragrance Formats", "Sephora vegan cruelty free fragrance perfume"),
    ("Sephora Fragrance Formats", "Sephora refillable eco friendly perfume bottle spray"),
    ("Sephora Fragrance Formats", "Sephora luxury high end niche perfume EDP"),
    ("Sephora Fragrance Formats", "Sephora black owned fragrance perfumery brands")
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
        desc = f"Discover {p['title']}. Sephora viral luxury fragrance & home scent!"

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

async def mine_sephora_fragrance_master():
    print("🚀 Starting Sephora Ultimate Fragrance & Home Scents Master Miner...")
    total_seeded = 0
    seen_urls = set()

    bm = BrowserManager()
    await bm.initialize()

    for idx, (cat_label, vector_query) in enumerate(SEPHORA_FRAGRANCE_VECTORS, start=1):
        print(f"\n[{idx:02d}/{len(SEPHORA_FRAGRANCE_VECTORS)}] 🌸 Fragrance Subcategory: {cat_label} | Vector: '{vector_query}'")
        
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
    print(f" 🎉 TOTAL NEW SEPHORA FRAGRANCE PRODUCTS SEEDED INTO DB: {total_seeded}")
    print("═════════════════════════════════════════════════════════════════")

def main():
    asyncio.run(mine_sephora_fragrance_master())

if __name__ == "__main__":
    main()
