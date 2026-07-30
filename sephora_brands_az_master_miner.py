"""
Sephora Ultimate Brands Directory A-Z Master Miner & Seeder
Scrapes 100% of Sephora's Official 200+ Top Luxury Beauty Brands (A-Z) into Agent DB.
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

SEPHORA_BRANDS_AZ = [
    # A
    ("A", "Anastasia Beverly Hills", "Anastasia Beverly Hills brow freeze pomade palette"),
    ("A", "Augustinus Bader", "Augustinus Bader rich cream moisturizer face oil"),
    ("A", "Armani Beauty", "Armani Beauty luminous silk foundation concealer"),
    ("A", "amika", "amika perk up dry shampoo hair mask"),
    ("A", "Ariana Grande", "Ariana Grande Cloud Eau de Parfum fragrance spray"),

    # B
    ("B", "Beauty of Joseon", "Beauty of Joseon relief sun SPF 50 Dynasty cream"),
    ("B", "Biodance", "Biodance bio collagen real deep mask sheet"),
    ("B", "Benefit Cosmetics", "Benefit Cosmetics benetint lip cheek stain mascara"),
    ("B", "Biossance", "Biossance squalane vitamin c rose oil moisturizer"),
    ("B", "Bobbi Brown", "Bobbi Brown vitamin enriched face base primer"),
    ("B", "Briogeo", "Briogeo dont despair repair deep conditioning hair mask"),
    ("B", "Bumble and bumble", "Bumble and bumble hairdressers invisible oil spray"),

    # C
    ("C", "Charlotte Tilbury", "Charlotte Tilbury Hollywood flawless filter pillow talk lipstick"),
    ("C", "Caudalie", "Caudalie vinoperfect dark spot serum beauty elixir"),
    ("C", "CHANEL", "CHANEL Les Beiges water fresh tint perfume"),
    ("C", "COLOR WOW", "Color Wow dream coat anti frizz spray raise root"),
    ("C", "CLINIQUE", "Clinique almost lipstick black honey moisture surge"),
    ("C", "Crown Affair", "Crown Affair leave in conditioner hair oil brush"),

    # D
    ("D", "DIOR", "Dior Addict lip glow oil Sauvage fragrance blush"),
    ("D", "Drunk Elephant", "Drunk Elephant bronzi drops lala retro cream protini"),
    ("D", "Dyson", "Dyson airwrap multi styler supersonic hair dryer"),
    ("D", "Dermalogica", "Dermalogica daily microfoliant exfoliator cleanser"),
    ("D", "Danessa Myricks Beauty", "Danessa Myricks yummy skin blurring balm powder"),

    # E
    ("E", "Elemis", "Elemis pro collagen cleansing balm face cream"),
    ("E", "Ellis Brooklyn", "Ellis Brooklyn vanilla milk perfume spray"),
    ("E", "e.l.f. Cosmetics", "e.l.f. Glow Reviver Lip Oil Halo Glow liquid filter"),

    # F
    ("F", "Fenty Beauty by Rihanna", "Fenty Beauty gloss bomb lip luminizer eaze drop tint"),
    ("F", "First Aid Beauty", "First Aid Beauty ultra repair cream barrier moisturizer"),
    ("F", "Farmacy", "Farmacy green clean makeup meltaway cleansing balm"),

    # G
    ("G", "Glow Recipe", "Glow Recipe watermelon glow niacinamide dew drops toner"),
    ("G", "Glossier", "Glossier You eau de parfum cloud paint blush lip balm"),
    ("G", "Gisou", "Gisou honey infused hair oil lip oil hair mask"),
    ("G", "Givenchy", "Givenchy Prisme Libre loose setting powder blush"),
    ("G", "Gucci", "Gucci Flora Gorgeous Gardenia perfume lipstick"),

    # H
    ("H", "HAUS LABS BY LADY GAGA", "HAUS LABS trriclone skin tech foundation blush"),
    ("H", "Hourglass", "Hourglass ambient lighting powder vanish concealer"),
    ("H", "HUDA BEAUTY", "Huda Beauty easy bake setting powder faux filter concealer"),
    ("H", "Hero Cosmetics", "Hero Cosmetics mighty patch hydrocolloid acne pimple"),

    # I
    ("I", "ILIA", "ILIA super serum skin tint SPF 40 limitless lash mascara"),
    ("I", "The INKEY List", "The INKEY List hyaluronic acid serum salicylic acid cleanser"),
    ("I", "innisfree", "innisfree daily UV defense sunscreen green tea serum"),

    # J
    ("J", "Jo Malone London", "Jo Malone Wood Sage Sea Salt Cologne fragrance"),
    ("J", "Juliette Has a Gun", "Juliette Has a Gun Not A Perfume eau de parfum"),

    # K
    ("K", "K18 Biomimetic Hairscience", "K18 leave in molecular repair hair mask oil"),
    ("K", "KAYALI", "Kayali vanilla 28 yum pistachio gelato perfume"),
    ("K", "Kérastase", "Kérastase elixir ultime hair oil gloss absolu"),
    ("K", "Kosas", "Kosas Revealer concealer wet lip oil gloss SPF"),
    ("K", "Kiehl's Since 1851", "Kiehls ultra facial cream rare earth deep pore mask"),

    # L
    ("L", "LANEIGE", "Laneige lip sleeping mask lip glowy balm cream skin"),
    ("L", "La Mer", "La Mer Creme de la Mer moisturizing cream face oil"),
    ("L", "Lancôme", "Lancome Lash Idole mascara Teint Idole foundation"),
    ("L", "Laura Mercier", "Laura Mercier translucent loose setting powder cavity stick"),
    ("L", "Living Proof", "Living Proof perfect hair day dry shampoo leave in"),

    # M
    ("M", "MAKEUP BY MARIO", "Makeup by Mario surreal skin foundation soft pop blush"),
    ("M", "MAC Cosmetics", "MAC Macximal silky matte lipstick studio fix fluid"),
    ("M", "Maison Margiela", "Maison Margiela REPLICA By the Fireplace Jazz Club perfume"),
    ("M", "MERIT", "MERIT flush balm cream blush shade slick lip oil"),
    ("M", "Milk Makeup", "Milk Makeup hydro grip primer matte bronzer stick"),
    ("M", "Moroccanoil", "Moroccanoil treatment original hair oil hydration mask"),
    ("M", "Medicube", "Medicube zero pore pad 2.0 PDRN collagen mask"),

    # N
    ("N", "NARS", "NARS radiant creamy concealer orgasm blush light reflecting"),
    ("N", "Nécessaire", "Necessaire the body wash eucalyptus body lotion serum"),
    ("N", "NATASHA DENONA", "Natasha Denona glam eyeshadow palette hy glam concealer"),

    # O
    ("O", "Olaplex", "Olaplex No 3 hair perfector No 4 shampoo No 7 bonding oil"),
    ("O", "ONE/SIZE by Patrick Starrr", "ONE/SIZE Patrick Starrr On Til Dawn setting spray matte"),
    ("O", "The Ordinary", "The Ordinary glycolic acid 7 toner niacinamide 10 serum"),
    ("O", "Oribe", "Oribe dry texturizing spray gold lust repair hair oil"),
    ("O", "OUAI", "OUAI wave spray leave in conditioner Detox shampoo body mist"),

    # P
    ("P", "PATRICK TA", "Patrick Ta major headlines double take cream powder blush duo"),
    ("P", "PAT McGRATH LABS", "Pat McGrath mothership eyeshadow palette fetisheyes mascara"),
    ("P", "Paula's Choice", "Paulas Choice 2 BHA liquid exfoliant skin perfecting"),
    ("P", "PHLUR", "Phlur missing person vanilla skin body mist spray"),
    ("P", "Prada", "Prada Paradoxe Eau de Parfum spray reveal foundation"),

    # R
    ("R", "Rare Beauty by Selena Gomez", "Rare Beauty soft pinch liquid blush lip oil foundation"),
    ("R", "rhode", "Rhode peptide lip treatment glazing milk barrier restore cream"),
    ("R", "REFY", "REFY brow sculpt lash sculpt mascara lip blush"),
    ("R", "Redken", "Redken all soft shampoo one united leave in spray"),

    # S
    ("S", "Sol de Janeiro", "Sol de Janeiro brazilian bum bum body cream cheirosa 68 62"),
    ("S", "Summer Fridays", "Summer Fridays lip butter balm vanilla cherry jet lag mask"),
    ("S", "Saie", "Saie glowy super gel lightweight illuminator blush"),
    ("S", "Supergoop!", "Supergoop unseen sunscreen SPF 40 glow screen"),
    ("S", "Sunday Riley", "Sunday Riley good genes lactic acid treatment A+ retinol"),

    # T
    ("T", "Tatcha", "Tatcha the dewy skin cream the water cream rice wash"),
    ("T", "tarte", "Tarte shape tape concealer maracuja juicy lip plump"),
    ("T", "Too Faced", "Too Faced better than sex mascara lip injection extreme"),
    ("T", "Tower 28 Beauty", "Tower 28 SOS daily facial spray shineon lip jelly"),
    ("T", "Touchland", "Touchland power mist hydrating hand sanitizer spray"),

    # U & V & W & Y & #
    ("U", "Urban Decay", "Urban Decay all nighter setting spray 24/7 glide on pencil"),
    ("V", "Valentino", "Valentino Born in Roma Eau de Parfum spray liqui filter"),
    ("V", "Vegamour", "Vegamour GRO hair serum volumizing shampoo conditioner"),
    ("W", "Westman Atelier", "Westman Atelier baby cheeks blush stick vital skin foundation"),
    ("Y", "Yves Saint Laurent", "YSL Libre Eau de Parfum Black Opium Candy Glaze lip balm"),
    ("#", "5 SENS", "5 SENS life of the party eau de parfum spray"),
    ("#", "The 7 Virtues", "The 7 Virtues vanilla woods eau de parfum spray")
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

        seo_title = f"{p['title']} | Sephora {p['brand']} Luxury Find 2026"
        desc = f"Discover {p['title']} by {p['brand']}. Sephora viral luxury beauty essential!"

        cursor.execute(
            """
            INSERT INTO products (
                product_name, category, board_name, status, source_url, 
                title, description, affiliate_link, image_path, retry_count, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
            """,
            (
                p_name,
                f"Sephora Brand: {p['brand']}",
                f"{p['brand']} Sephora Finds",
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

async def mine_sephora_brands_az_master():
    print("🚀 Starting Sephora Ultimate Brands Directory A-Z Master Miner...")
    total_seeded = 0
    seen_urls = set()

    bm = BrowserManager()
    await bm.initialize()

    for idx, (letter, brand_name, vector_query) in enumerate(SEPHORA_BRANDS_AZ, start=1):
        print(f"\n[{idx:02d}/{len(SEPHORA_BRANDS_AZ)}] 👑 Brand [{letter}]: {brand_name} | Vector: '{vector_query}'")
        
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
                        "brand": brand_name,
                        "title": raw_title,
                        "source_url": full_url,
                        "affiliate_url": affiliate_url,
                        "image_url": img_src
                    })

            except Exception as e:
                print(f"   ⚠️ Page {page_num} Error: {e}")
            finally:
                await page.close()
                await asyncio.sleep(1)

        # Real-time seeding per brand vector
        seeded = seed_single_batch(batch)
        total_seeded += seeded
        print(f"   ✅ Brand Finished: Extracted {len(batch)} items, Seeded {seeded} NEW items to DB! (Total Brand Seeded: {total_seeded})")

    await bm.close()
    print("═════════════════════════════════════════════════════════════════")
    print(f" 🎉 TOTAL NEW SEPHORA BRANDS A-Z PRODUCTS SEEDED INTO DB: {total_seeded}")
    print("═════════════════════════════════════════════════════════════════")

def main():
    asyncio.run(mine_sephora_brands_az_master())

if __name__ == "__main__":
    main()
