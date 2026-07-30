"""
Sephora Ultimate Skincare Master Subcategory Miner v2.0
Real-time vector seeding into Agent DB for all 100% Skincare Subcategories
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

SEPHORA_SKINCARE_SUBCATEGORY_VECTORS = [
    # --- MOISTURIZERS ---
    ("Sephora Skincare Moisturizers", "Sephora face creams hydrating gel moisturizer"),
    ("Sephora Skincare Moisturizers", "Sephora night creams barrier repair ceramides"),
    ("Sephora Skincare Moisturizers", "Sephora face oils squalane rosehip marula"),
    ("Sephora Skincare Moisturizers", "Sephora facial mists essences hydrating spray"),
    ("Sephora Skincare Moisturizers", "Sephora BB CC cream skin tint moisturizer"),

    # --- CLEANSERS & TONERS ---
    ("Sephora Skincare Cleansers", "Sephora face wash gentle foaming cleanser"),
    ("Sephora Skincare Cleansers", "Sephora exfoliator AHA BHA liquid scrub"),
    ("Sephora Skincare Cleansers", "Sephora cleansing balm oil makeup remover"),
    ("Sephora Skincare Cleansers", "Sephora face wipes micellar water travel"),
    ("Sephora Skincare Cleansers", "Sephora hydrating exfoliating face toner"),

    # --- TREATMENTS & SERUMS ---
    ("Sephora Skincare Treatments", "Sephora face serums hyaluronic niacinamide vitamin c"),
    ("Sephora Skincare Treatments", "Sephora acne blemish spot treatment salicylic acid"),
    ("Sephora Skincare Treatments", "Sephora facial peels glycolic acid resurfacing"),

    # --- MASKS ---
    ("Sephora Skincare Masks", "Sephora hydrating clay mud face masks"),
    ("Sephora Skincare Masks", "Sephora bio collagen real deep sheet masks"),
    ("Sephora Skincare Masks", "Sephora under eye hydrogel patches masks"),

    # --- EYE & LIP CARE ---
    ("Sephora Skincare Eye & Lip", "Sephora eye cream dark circles puffiness peptides"),
    ("Sephora Skincare Eye & Lip", "Sephora lip balm butter treatment mask sleeping"),

    # --- SUNSCREEN ---
    ("Sephora Skincare Sunscreen", "Sephora face sunscreen SPF 50 invisible zero white cast"),
    ("Sephora Skincare Sunscreen", "Sephora body sunscreen spray lotion mineral"),

    # --- HIGH TECH TOOLS & WELLNESS ---
    ("Sephora Skincare Tools", "Sephora LED face light therapy mask microcurrent"),
    ("Sephora Skincare Tools", "Sephora dermaroller gua sha facial roller tool"),
    ("Sephora Skincare Wellness", "Sephora skin supplements collagen gummies vitamins"),
    ("Sephora Skincare Wellness", "Sephora feminine care body wash hygiene"),

    # --- SHOP BY CONCERN ---
    ("Sephora Skincare Concerns", "Sephora acne blemishes pimple patches hydrocolloid"),
    ("Sephora Skincare Concerns", "Sephora anti aging retinol peptide serum cream"),
    ("Sephora Skincare Concerns", "Sephora dark spots hyperpigmentation vitamin c corrector"),
    ("Sephora Skincare Concerns", "Sephora pore minimizing tightener BHA liquid"),
    ("Sephora Skincare Concerns", "Sephora dryness barrier repair soothing moisturizer"),
    ("Sephora Skincare Concerns", "Sephora fine lines wrinkles smoothing serum"),
    ("Sephora Skincare Concerns", "Sephora dullness brightening vitamin c serum"),

    # --- SPECIAL FORMATS & COLLECTIONS ---
    ("Sephora Skincare Formats", "Sephora clean non toxic certified skincare"),
    ("Sephora Skincare Formats", "Sephora vegan cruelty free skincare products"),
    ("Sephora Skincare Formats", "Sephora travel size mini skincare set kit"),
    ("Sephora Skincare Formats", "Sephora jumbo size value size skincare product"),
    ("Sephora Skincare Formats", "Sephora refillable eco friendly skincare cream"),
    ("Sephora Skincare Formats", "Sephora collection private label skincare"),
    ("Sephora Skincare Formats", "Sephora luxury high end medical grade skincare"),

    # --- KOREAN SKINCARE & TRENDS ---
    ("Sephora Korean Skincare", "Korean skincare glass skin serum toner rice water"),
    ("Sephora Korean Skincare", "Korean sunscreens zero white cast SPF 50"),
    ("Sephora Korean Skincare", "Korean snail mucin essence hydrating serum"),
    ("Sephora Skincare Aesthetics", "Minimalist skincare routine 4 step skin glow"),
    ("Sephora Skincare Aesthetics", "Best skincare 45 and under affordable finds")
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
        desc = f"Discover {p['title']}. Sephora viral skincare essential & luxury find!"

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

async def mine_sephora_skincare_master():
    print("🚀 Starting Sephora Ultimate Skincare Master Subcategory Miner v2.0...")
    total_seeded = 0
    seen_urls = set()

    bm = BrowserManager()
    await bm.initialize()

    for idx, (cat_label, vector_query) in enumerate(SEPHORA_SKINCARE_SUBCATEGORY_VECTORS, start=1):
        print(f"\n[{idx:02d}/{len(SEPHORA_SKINCARE_SUBCATEGORY_VECTORS)}] 📦 Skincare Subcategory: {cat_label} | Vector: '{vector_query}'")
        
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
    print(f" 🎉 TOTAL NEW SEPHORA SKINCARE PRODUCTS SEEDED INTO DB: {total_seeded}")
    print("═════════════════════════════════════════════════════════════════")

def main():
    asyncio.run(mine_sephora_skincare_master())

if __name__ == "__main__":
    main()
