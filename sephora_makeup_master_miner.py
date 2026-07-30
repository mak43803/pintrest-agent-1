"""
Sephora Ultimate Makeup & Beauty Master Subcategory Miner
Scrapes 100% of Sephora Makeup Subcategories (Face, Eye, Lip, Cheek, Brushes, Accessories, Special Formats & Aesthetics)
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

SEPHORA_SUBCATEGORY_VECTORS = [
    # --- FACE SUBCATEGORIES ---
    ("Sephora Face", "Sephora foundation full coverage dewy matte"),
    ("Sephora Face", "Sephora BB CC cream skin tint"),
    ("Sephora Face", "Sephora tinted moisturizer hydrating SPF"),
    ("Sephora Face", "Sephora full coverage hydrating concealer"),
    ("Sephora Face", "Sephora face primer pore blurring glow"),
    ("Sephora Face", "Sephora setting spray waterproof translucent powder"),
    ("Sephora Face", "Sephora liquid powder highlighter glow"),
    ("Sephora Face", "Sephora contour stick cream sculpting"),
    ("Sephora Face", "Sephora color corrector green peach red"),
    ("Sephora Face", "Sephora face makeup value set kit"),

    # --- EYE SUBCATEGORIES ---
    ("Sephora Eye", "Sephora eyeshadow palette neutral nude shimmer"),
    ("Sephora Eye", "Sephora lengthening volumizing waterproof mascara"),
    ("Sephora Eye", "Sephora liquid gel eyeliner pencil liquid pen"),
    ("Sephora Eye", "Sephora eyebrow pencil pomade gel brow laminating"),
    ("Sephora Eye", "Sephora false eyelashes magnetic natural wispy"),
    ("Sephora Eye", "Sephora single eyeshadow liquid shimmer glitter"),
    ("Sephora Eye", "Sephora eyelash growth serum peptide conditioning"),
    ("Sephora Eye", "Sephora eyebrow growth serum thickening serum"),
    ("Sephora Eye", "Sephora eye primer longwear shadow base"),
    ("Sephora Eye", "Sephora eye makeup set kit mascara eyeliner"),

    # --- LIP SUBCATEGORIES ---
    ("Sephora Lip", "Sephora hydrating high shine lip gloss"),
    ("Sephora Lip", "Sephora matte satin lipstick longwear"),
    ("Sephora Lip", "Sephora viral lip oil nourishing tint"),
    ("Sephora Lip", "Sephora lip plumper gloss stinging shine"),
    ("Sephora Lip", "Sephora lip balm butter treatment mask overnight"),
    ("Sephora Lip", "Sephora liquid lipstick transferproof matte"),
    ("Sephora Lip", "Sephora lip liner pencil waterproof longwear"),
    ("Sephora Lip", "Sephora lip stain tint long lasting hydrating"),
    ("Sephora Lip", "Sephora lip care set value kit lipstick gloss"),

    # --- CHEEK SUBCATEGORIES ---
    ("Sephora Cheek", "Sephora liquid cream powder blush soft pinch"),
    ("Sephora Cheek", "Sephora bronzer stick cream powder sun kissed"),
    ("Sephora Cheek", "Sephora cheek highlighter liquid balm glow"),
    ("Sephora Cheek", "Sephora cheek contour cream stick bronze"),
    ("Sephora Cheek", "Sephora cheek palette blush bronzer highlighter"),

    # --- BRUSHES & APPLICATORS ---
    ("Sephora Brushes", "Sephora makeup brush set synthetic foundation powder"),
    ("Sephora Brushes", "Sephora face foundation concealer blush brush"),
    ("Sephora Brushes", "Sephora beauty makeup sponge blender applicator"),
    ("Sephora Brushes", "Sephora eye makeup brush blending shader liner"),
    ("Sephora Brushes", "Sephora lip brush precision application"),
    ("Sephora Brushes", "Sephora makeup brush cleaner spray soap solid"),

    # --- ACCESSORIES & TOOLS ---
    ("Sephora Accessories", "Sephora heated precision eyelash curler"),
    ("Sephora Accessories", "Sephora cosmetic pencil sharpener dual"),
    ("Sephora Accessories", "Sephora precision tweezers eyebrow shaping tool"),
    ("Sephora Accessories", "Sephora makeup travel bag case organizer vanity"),

    # --- SPECIAL FORMATS & COLLECTIONS ---
    ("Sephora Collections", "Sephora new arrivals beauty releases 2026"),
    ("Sephora Collections", "Sephora overall best seller makeup products"),
    ("Sephora Collections", "Sephora clean beauty certified makeup non toxic"),
    ("Sephora Collections", "Sephora vegan cruelty free makeup formulation"),
    ("Sephora Collections", "Sephora mini travel size beauty makeup product"),
    ("Sephora Collections", "Sephora jumbo size value size beauty product"),
    ("Sephora Collections", "Sephora refillable eco friendly makeup product"),
    ("Sephora Collections", "Sephora collection private label beauty makeup"),
    ("Sephora Collections", "Sephora luxury high end beauty editorial makeup"),
    ("Sephora Collections", "Sephora black owned beauty brand makeup"),

    # --- BEAUTY AESTHETICS & HELP ME CHOOSE ---
    ("Sephora Aesthetics", "Never enough lip viral lip combination"),
    ("Sephora Aesthetics", "Buttery silky juicy makeup look products"),
    ("Sephora Aesthetics", "The matte renaissance 90s matte makeup look"),
    ("Sephora Aesthetics", "Monochrome makeup monochromatic blush lip look"),
    ("Sephora Aesthetics", "Easy eye makeup quick beginner routine"),
    ("Sephora Aesthetics", "No makeup makeup natural skin finish look"),
    ("Sephora Aesthetics", "Super natural sculpting soft contouring face")
]

async def mine_sephora_makeup_master():
    print("🚀 Starting Sephora Ultimate Makeup & Beauty Master Subcategory Miner...")
    extracted_products = []
    seen_urls = set()

    bm = BrowserManager()
    await bm.initialize()

    for idx, (cat_label, vector_query) in enumerate(SEPHORA_SUBCATEGORY_VECTORS, start=1):
        print(f"\n[{idx:02d}/{len(SEPHORA_SUBCATEGORY_VECTORS)}] 📦 Subcategory: {cat_label} | Vector: '{vector_query}'")
        
        # Scrape 2 pages per subcategory vector
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

                print(f"   📄 Page {page_num}: Extracted {yield_count} items (Total Unique Sephora Subcategory Products: {len(extracted_products)})")

            except Exception as e:
                print(f"   ⚠️ Page {page_num} Error: {e}")
            finally:
                await page.close()
                await asyncio.sleep(1)

    await bm.close()
    print(f"\n🎉 Total Unique Sephora Makeup & Beauty Subcategory Products Extracted: {len(extracted_products)}")
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

        seo_title = f"{p['title']} | Sephora {p['category']} Essential 2026"
        desc = f"Discover {p['title']}. Sephora viral makeup & luxury beauty essential!"

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
    print(f" 🎉 MASS SEEDED {inserted_count} NEW SEPHORA SUBCATEGORY PRODUCTS INTO AGENT DB!")
    print("═════════════════════════════════════════════════════════════════")

def main():
    products = asyncio.run(mine_sephora_makeup_master())
    seed_to_db(products)

if __name__ == "__main__":
    main()
