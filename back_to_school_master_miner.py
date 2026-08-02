"""
August Back-To-School Impulse Beauty Scaling & Seeding Engine
Mines and seeds high-converting Back-To-School impulse products ($8-$20) targeting US High School & College girls (ages 18-24).
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

BTS_VIRAL_VECTORS = [
    ("Back-To-School 5-Minute Skincare & Beauty", "Hero Cosmetics Mighty Patch original hydrocolloid pimple patches acne"),
    ("Back-To-School 5-Minute Skincare & Beauty", "e.l.f. Glow Reviver Lip Oil nourishing tinted lip oil dior dupe"),
    ("Back-To-School 5-Minute Skincare & Beauty", "TIRTIR Mask Fit Red Cushion Foundation full coverage long lasting tint"),
    ("Back-To-School 5-Minute Skincare & Beauty", "ONE SIZE Patrick Starrr On Til Dawn setting spray waterproof matte"),
    ("Back-To-School 5-Minute Skincare & Beauty", "Tower 28 Beauty SOS daily facial spray hypochlorous acid redness breakout"),
    ("Back-To-School 5-Minute Skincare & Beauty", "Anua heartleaf 77 soothing toner pore control cleansing oil acne"),
    ("Back-To-School 5-Minute Skincare & Beauty", "La Roche Posay Effaclar Duo acne treatment benzoyl peroxide dual action"),
    ("Back-To-School 5-Minute Skincare & Beauty", "Sol de Janeiro cheirosa travel perfume mist spray 90ml backpack")
]

BTS_VIRAL_HOOKS = [
    "5-Minute Back-To-School Morning Skincare That Erased My Acne In 7 Days",
    "The $8 Amazon Lip Oil That Replaces $40 Dior For Class",
    "2-Minute Filter Skin Cushion Foundation For Busy School Mornings",
    "Waterproof All-Day Setting Spray That Holds Through School & Gym",
    "The $12 Acne Pimple Patch Secret Every High School & College Girl Needs",
    "Back-To-School Backpack Skincare Essential Under $15"
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

    for idx, p in enumerate(products):
        p_name = p["title"]
        if p_name.lower().strip() in existing_set or p["source_url"].lower().strip() in existing_set:
            continue

        clean_short_title = " ".join(p_name.split()[:7])
        seo_title = f"{clean_short_title} | Back-To-School Beauty Find 2026"
        desc = f"Discover {p_name}. Back-To-School beauty essential under $20 on Amazon!"

        cursor.execute(
            """
            INSERT INTO products (
                product_name, category, board_name, status, source_url, 
                title, description, affiliate_link, image_path, retry_count, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
            """,
            (
                p_name,
                "Back-To-School Impulse Beauty",
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

async def mine_back_to_school_master():
    print("🎒 Starting August Back-To-School Impulse Beauty Scaling Engine...")
    total_seeded = 0
    seen_urls = set()

    bm = BrowserManager()
    await bm.initialize()

    for idx, (board_name, vector_query) in enumerate(BTS_VIRAL_VECTORS, start=1):
        print(f"\n[{idx:02d}/{len(BTS_VIRAL_VECTORS)}] 🎒 BTS Vector: '{vector_query}'")
        
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
                        "board_name": board_name,
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
        print(f"   ✅ Vector Finished: Extracted {len(batch)} items, Seeded {seeded} NEW items to DB! (Total BTS Seeded: {total_seeded})")

    await bm.close()
    print("═════════════════════════════════════════════════════════════════")
    print(f" 🎉 TOTAL NEW BACK-TO-SCHOOL IMPULSE PRODUCTS SEEDED INTO DB: {total_seeded}")
    print("═════════════════════════════════════════════════════════════════")

def main():
    asyncio.run(mine_back_to_school_master())

if __name__ == "__main__":
    main()
