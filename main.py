"""
Pinterest AI Agent — Main Entry Point.
======================================

Runs the autonomous affiliate marketer in a continuous loop.
Publishes 40 pins per 24 hours continuously without long scheduling delays.
Resets automatically every 24 hours.

RESUME SUPPORT:
- Agent state is tracked via SQLite DB (products table).
- On restart (e.g., power outage), it resumes from where it left off.
- Waits for internet connectivity before starting.
- Can be added to Windows Startup for auto-launch on boot.
"""

import asyncio
import logging
import sys
import random
import datetime
import socket
import time
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Force stdout/stderr to use UTF-8 to prevent charmap UnicodeEncodeErrors in Windows background tasks
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

load_dotenv()

from agent.pinterest_agent import PinterestAgent
from utils.exceptions import FatalLoginError

# Setup local logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s │ %(levelname)-8s │ %(message)s")
logger = logging.getLogger("pinterest_agent.main")


# ──────────────────────────────────────────────────────────────────────
# INTERNET CONNECTIVITY CHECK
# ──────────────────────────────────────────────────────────────────────

def is_internet_available() -> bool:
    """Check if internet is available by trying to connect to DNS or Google HTTP."""
    for target in [("8.8.8.8", 53), ("1.1.1.1", 53), ("www.google.com", 80), ("www.cloudflare.com", 80)]:
        try:
            socket.create_connection(target, timeout=3)
            return True
        except OSError:
            continue
    return False


async def wait_for_internet(max_wait_minutes: int = 30) -> bool:
    """
    Wait until internet connectivity is restored.
    Checks every 10 seconds for up to max_wait_minutes.
    Returns True if internet came back, False if timed out.
    """
    if is_internet_available():
        return True

    logger.warning("⚡ No internet connection detected. Waiting for connectivity...")
    start = time.time()
    max_wait_seconds = max_wait_minutes * 60

    while time.time() - start < max_wait_seconds:
        await asyncio.sleep(10)
        if is_internet_available():
            logger.info("✅ Internet connection restored!")
            # Wait a few more seconds for network to stabilize
            await asyncio.sleep(5)
            return True
        elapsed = int(time.time() - start)
        if elapsed % 60 == 0:  # Log every minute
            logger.info(f"  Still waiting for internet... ({elapsed // 60} min elapsed)")

    logger.error(f"❌ No internet after {max_wait_minutes} minutes. Giving up.")
    return False


# ──────────────────────────────────────────────────────────────────────
# WINDOWS STARTUP SHORTCUT
# ──────────────────────────────────────────────────────────────────────

def setup_windows_startup():
    """
    Create a batch file in the Windows Startup folder so the agent
    auto-launches when the laptop turns on.
    """
    startup_folder = Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    batch_file = startup_folder / "PinterestAIAgent.bat"
    
    project_dir = Path(__file__).parent.resolve()
    python_exe = sys.executable
    
    batch_content = f'''@echo off
title Pinterest AI Agent
cd /d "{project_dir}"
"{python_exe}" watchdog.py
pause
'''
    
    try:
        batch_file.write_text(batch_content, encoding="utf-8")
        logger.info(f"✅ Windows startup shortcut created: {batch_file}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create startup shortcut: {e}")
        return False


def remove_windows_startup():
    """Remove the Windows startup shortcut."""
    startup_folder = Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    batch_file = startup_folder / "PinterestAIAgent.bat"
    
    if batch_file.exists():
        batch_file.unlink()
        logger.info("✅ Windows startup shortcut removed.")
        return True
    return False


# ──────────────────────────────────────────────────────────────────────
# ANALYTICS FEEDBACK LOOP CATEGORY SELECTION
# ──────────────────────────────────────────────────────────────────────

def get_next_category_based_on_analytics(db, categories: list[str]) -> str:
    """
    Select next category ensuring 100% equal rotation across categories,
    with heavy priority for August Back-To-School Impulse Beauty categories (60% weight).
    """
    import random
    import datetime

    # High-Affinity & High-CTR Priority Categories (CSV Analytics 30-Day Verified Winners)
    bts_priority_categories = [
        "Korean Sunscreens Zero White Cast",
        "K-Beauty Serums That Actually Work",
        "Body Wash Shower Gels USA 2026",
        "Amazon Beauty Finds Under $20",
        "Affordable Skincare Finds 2026",
        "Acne patches & pimple patches",
        "Overnight acne & pimple patches",
        "Dior lip oil dupes",
        "Dior Lip Oil $8 Amazon dupes",
        "TirTir cushion foundation",
        "Clean girl aesthetic makeup",
        "Back-To-School 5-Minute Skincare & Beauty",
        "Sephora A+ Beauty Essentials Back-To-School",
        "New and Trending Under $50 Beauty Finds",
        "Summer Fridays lip butter balm dupes",
        "Biodance Bio-Collagen deep mask",
        "Sol de Janeiro dupes",
        "Arabian perfume oils & vanilla mists",
        "Signature perfumes & luxury fragrances",
        "Korean Glass Skin holy grails"
    ]

    today = datetime.date.today()
    is_bts_season = (today.month == 8 or (today.month == 7 and today.day >= 25))

    # 60% Priority for Back-To-School season (August)
    if is_bts_season and random.random() < 0.60:
        chosen_bts = random.choice(bts_priority_categories)
        logger.info("🎓 August Back-To-School Priority Mode: Selected '%s'", chosen_bts)
        return chosen_bts

    category_counts = {cat: 0 for cat in categories}
    category_scores = {cat: 1.0 for cat in categories}

    try:
        with db.connection() as conn:
            cursor = conn.execute(
                """
                SELECT category, COUNT(*) as cnt, SUM(impressions) as total_imp, SUM(clicks) as total_clicks, SUM(saves) as total_saves
                FROM products
                WHERE status IN ('Published', 'Pinterest_Published')
                GROUP BY category
                """
            )
            for row in cursor.fetchall():
                cat_db = (row["category"] or "").strip()
                for cat in categories:
                    if cat.lower().strip() == cat_db.lower():
                        category_counts[cat] = row["cnt"] or 0
                        clicks = row["total_clicks"] or 0
                        saves = row["total_saves"] or 0
                        imp = row["total_imp"] or 0
                        category_scores[cat] += (clicks * 5.0) + (saves * 2.0) + (imp * 0.1)
                        break
    except Exception as e:
        logger.debug(f"Failed to query category counts: {e}")

    # Find the minimum post count among all categories
    min_count = min(category_counts.values()) if category_counts else 0
    least_posted = [cat for cat, count in category_counts.items() if count == min_count]

    # Pick randomly among categories with the FEWEST posts
    if least_posted and random.random() < 0.80:
        chosen = random.choice(least_posted)
        logger.info("Category Selection [Equal Coverage (Post Count: %d)]: Selected '%s'", min_count, chosen)
        return chosen

    total_score = sum(category_scores.values())
    choices = list(category_scores.keys())
    weights = [category_scores[c] / total_score for c in choices]
    chosen = random.choices(choices, weights=weights)[0]
    logger.info("Category Selection [Analytics Boost]: Selected category '%s'", chosen)
    return chosen


# ──────────────────────────────────────────────────────────────────────
# MAIN AGENT LOOP
# ──────────────────────────────────────────────────────────────────────

async def main() -> None:
    print("🚀 Starting Pinterest AI Agent Schedule Loop...")
    
    # ── Wait for internet before anything ──
    if not await wait_for_internet(max_wait_minutes=30):
        print("❌ Cannot start without internet. Exiting.")
        return
    
    while True:
        agent = PinterestAgent()
        try:
            await agent.initialize()
            
            # ── Run Baddies Beauty Watchdog Audit & Auto-Repair on Startup ──
            try:
                from baddies_watchdog import run_watchdog_audit
                run_watchdog_audit(auto_repair=True)
            except Exception as wd_err:
                logger.warning(f"Baddies Watchdog audit warning: {wd_err}")

            # ── Self-Healing Error Recovery Counters (Persistent across cycles) ──
            consecutive_failures = 0
            MAX_CONSECUTIVE_FAILURES = 5
            
            while True:
                # ── Periodic Analytics Sync (Every 24 hours) ──
                try:
                    last_sync_str = None
                    with agent.db.connection() as conn:
                        cursor = conn.execute("SELECT value FROM settings WHERE key = 'last_analytics_sync'")
                        row = cursor.fetchone()
                        if row:
                            last_sync_str = row["value"]
                            
                    should_sync = False
                    if not last_sync_str:
                        should_sync = True
                    else:
                        last_sync = datetime.datetime.fromisoformat(last_sync_str)
                        if datetime.datetime.now() - last_sync >= datetime.timedelta(hours=24):
                            should_sync = True
                            
                    if should_sync:
                        logger.info("🔄 Running daily Pinterest pin analytics sync...")
                        await agent.update_pin_analytics(scroll_count=4)
                        with agent.db.connection() as conn:
                            conn.execute(
                                "INSERT OR REPLACE INTO settings (key, value) VALUES ('last_analytics_sync', ?)",
                                (datetime.datetime.now().isoformat(),)
                            )
                except Exception as e:
                    logger.error(f"Periodic analytics sync failed: {e}")

                # ── Check internet before each cycle ──
                if not is_internet_available():
                    logger.warning("⚡ Internet lost! Waiting for reconnection...")
                    if not await wait_for_internet(max_wait_minutes=60):
                        logger.error("Internet not restored after 60 min. Stopping agent.")
                        break
                
                TOTAL_CAMPAIGN_DAYS = 90

                # ── 90-Day Campaign Tracker & Daily Limit Check ──
                with agent.db.connection() as conn:
                    cursor = conn.execute("SELECT value FROM settings WHERE key = 'campaign_start_date'")
                    row = cursor.fetchone()
                    if row:
                        start_dt = datetime.date.fromisoformat(row["value"])
                    else:
                        start_dt = datetime.date.today()
                        conn.execute(
                            "INSERT OR REPLACE INTO settings (key, value) VALUES ('campaign_start_date', ?)",
                            (start_dt.isoformat(),)
                        )
                    
                    cursor = conn.execute(
                        "SELECT COUNT(*) as cnt FROM products WHERE date(created_at) = date('now')"
                    )
                    row_cnt = cursor.fetchone()
                    today_count = row_cnt["cnt"] if row_cnt else 0
                    
                today_dt = datetime.date.today()
                campaign_day = (today_dt - start_dt).days + 1
                
                if campaign_day > TOTAL_CAMPAIGN_DAYS:
                    logger.info("🎉 90-DAY NON-STOP CAMPAIGN COMPLETE! All %d days finished. Total goal completed!", TOTAL_CAMPAIGN_DAYS)
                    await asyncio.sleep(3600)
                    continue

                logger.info("📅 90-Day Campaign [Day %d/%d]: %d Pins published today.", campaign_day, TOTAL_CAMPAIGN_DAYS, today_count)
                    
                categories = [
                    # ── A-Z Skincare & Treatments ──
                    "Acne patches & pimple patches", "Acne treatment & prevention", "Ampoules & Essences",
                    "Anti-aging skincare routine", "Anua heartleaf toner", "Azelaic acid serums",
                    "BB & CC Creams", "Blackhead removal & pore care", "Centella asiatica skincare",
                    "Ceramide moisturizers", "Chemical peels at home", "Cleansing balms & oils",
                    "Collagen supplements", "Dark circle treatments", "Dark spot correctors",
                    "Derma rollers & microneedling", "Double cleansing routine", "Eczema relief skincare",
                    "Eye creams & serums", "Face masks & clay masks", "Face oils for glowing skin",
                    "Facial cleansers", "Facial mists & setting sprays", "French pharmacy skincare",
                    "Glass skin routine", "Glow serums & illuminating drops", "Gua sha & facial massage",
                    "Hyaluronic acid serums", "Hyperpigmentation treatments", "J-Beauty skincare essentials",
                    "K-Beauty skincare routines", "Lactic acid exfoliants", "LED face masks & light therapy",
                    "Lip sleeping masks", "Microcurrent facial devices", "Moisturizers for dry skin",
                    "Moisturizers for oily skin", "Niacinamide serums", "Night creams & sleeping masks",
                    "Overnight skincare treatments", "Peptide skincare products", "Pore minimizing serums",
                    "Retinol & retinoid creams", "Rose quartz facial rollers", "Salicylic acid treatments",
                    "Self-tanner & bronzing drops", "Serums & essences", "Sheet masks for face",
                    "Skincare for sensitive skin", "Slugging skincare method", "Snail mucin skincare",
                    "SPF & daily sunscreen", "Spot treatments for acne", "Squalane face oils",
                    "Sunscreen for acne-prone skin", "Tanning oils & lotions", "Tinted moisturizers",
                    "Toners & astringents", "Under-eye patches & gels", "Vegan & cruelty-free skincare",
                    "Vitamin C serums for brightening", "Water-based moisturizers", "Youth-boosting serums",
                    "Zinc oxide mineral sunscreens",

                    # ── A-Z Makeup & Cosmetics ──
                    "Baking & setting powder", "Blush & bronzers", "Blush palettes",
                    "Bridal makeup essentials", "Charlotte Tilbury dupes", "Clean girl aesthetic makeup",
                    "Clear lip gloss", "Color correcting concealers", "Contour sticks & palettes",
                    "Cream blushes", "Dior lip oil dupes", "Douyin makeup style",
                    "Drugstore makeup must-haves", "E-girl makeup looks", "Eyebrow gels & soaps",
                    "Eyebrow pencils & pomades", "Eyelash curlers", "Eyelash serums for growth",
                    "Eyeliner (liquid & gel)", "Eye makeup tutorials", "Eye shadow palettes",
                    "Face primers (matte & dewy)", "False eyelashes & glue", "Fluffy brow tutorials",
                    "Foundation for oily skin", "Foundations & concealers", "Full coverage foundation",
                    "Glitter & shimmer eyeshadow", "High end makeup dupes", "Highlighters & illuminators",
                    "Latte makeup trend", "Lip liners & contouring", "Lip oils & balms",
                    "Lip plumping gloss", "Lip stains & tints", "Liquid blushes",
                    "Long-lasting lipsticks", "Mac lipstick dupes", "Makeup brushes & sponges",
                    "Makeup organizers & storage", "Makeup setting sprays", "Mascara for length & volume",
                    "Matte lipsticks", "Korean lip tints (Romand)", "Prom makeup looks",
                    "Sephora makeup favorites", "Soft glam makeup looks", "Strawberry makeup trend",
                    "TirTir cushion foundation", "Travel makeup bags", "Waterproof summer makeup",
                    "Y2K makeup trends",

                    # ── A-Z Hair Care & Styling ──
                    "90s blowout hair tutorial", "Anti-frizz hair products", "Balayage hair color ideas",
                    "Biotin hair growth supplements", "Blonde hair maintenance", "Blowout dryer brushes",
                    "Claw clips & hair accessories", "Color-treated hair care", "Curly girl method products",
                    "Dandruff treatments & scalp care", "Deep conditioning hair masks", "Dry shampoos",
                    "Dyson airwrap dupes", "Hair bond repair treatments", "Hair color & dyes",
                    "Hair combs & detangling brushes", "Hair extensions & wigs", "Hair growth serums",
                    "Hair oils & serums", "Hair perfumes & mists", "Hair removal & razors",
                    "Hair straighteners & flat irons", "Hair styling tools", "Hair thickening sprays",
                    "Heat protectant sprays", "Heatless hair curlers", "Leave-in conditioners",
                    "Olaplex dupes & alternatives", "Rosemary oil for hair growth", "Scalp massagers",
                    "Scalp scrubs & treatments", "Scrunchies & hair ties", "Shampoo & conditioner sets",
                    "Silk & satin pillowcases for hair", "Tiaras & wedding hair accessories", "Texture sprays",
                    "Veils & bridal hair accessories", "Viral hair care routines", "Wolf cut styling",

                    # ── A-Z Body Care & Fragrance ──
                    "Arabian perfumes & dupes", "At-home laser hair removal (IPL)", "Bath & body essentials",
                    "Bath bombs & shower steamers", "Body butters & souffles", "Body lotions & creams",
                    "Body makeup & shimmers", "Body scrubs & exfoliators", "Body washes & shower gels",
                    "Cellulite creams & treatments", "Deodorants & antiperspirants", "Epilators & waxing kits",
                    "Exfoliating gloves", "Feminine hygiene products", "Floral perfumes for women",
                    "Fragrance gift sets", "Gourmand vanilla perfumes", "Hand creams & lotions",
                    "Hand soaps & sanitizers", "Ingrown hair treatments", "Keratosis pilaris (KP) treatments",
                    "Perfume layering combinations", "Perfume rollerballs & travel sprays", "Pheromone perfumes",
                    "Shaving creams & oils", "Sol de Janeiro dupes", "Strawberry legs treatments",
                    "Summer body glow oils", "Viral body mists", "Whole body deodorants", "Women's Fragrances",

                    # ── A-Z Nails, Teeth, & Aesthetics ──
                    "Aesthetic bridesmaid gift bags", "Aesthetic college outfits", "Aesthetic gold jewelry",
                    "Aesthetic gym outfits", "Aesthetic oversized hoodies", "Aesthetic platform sneakers",
                    "Aesthetic tote bags", "Bachelorette party outfits", "Biab nails & builder gel",
                    "Bridal shower aesthetic", "Capsule wardrobe essentials", "Chic workwear outfits",
                    "Chrome nails & powders", "Chunky gold hoop earrings", "Cozy fall sweaters",
                    "Crossbody bags for women", "Cute lounge sets", "Cute summer dresses",
                    "Dainty gold necklaces", "Designer purse dupes on Amazon", "Everyday casual outfits",
                    "French tip nail designs", "Gel nail polish kits", "Glazed donut nails",
                    "High waisted wide leg pants", "Lululemon align dupes", "Mini skirts & skorts",
                    "Nail art tools & brushes", "Nail care & cuticle oils", "Nail polish removers",
                    "Old money aesthetic outfits", "Pilates princess aesthetic", "Press-on nails & glue",
                    "Quick-dry nail top coats", "Russian manicure tools", "Skims dupes on Amazon",
                    "Stanley cup accessories", "Stiletto & almond nails", "Tarnish-free rings",
                    "Teeth whitening kits", "Teeth whitening strips & pens", "Tennis bracelets",
                    "Vacation beauty essentials", "Vintage shoulder bags", "Whitening toothpastes",

                    # ── Hyper-Specific High-Converting Beauty Sub-Niches ──
                    "Charlotte Tilbury dupes on Amazon", "Dyson Airwrap alternative under $50", 
                    "Dior Lip Oil dupes", "Baccarat Rouge 540 perfume dupes", "Rare Beauty blush dupes",
                    "Hormonal acne clearing routine", "Pregnancy-safe skincare", "Anti-aging neck creams",
                    "Hair thinning & hair growth serums", "Strawberry legs treatment products",
                    "Bridal emergency touch-up kit", "Waterproof wedding makeup must-haves",
                    "6-month bridal skincare prep routine", "Best wedding day perfumes",
                    "Coquette makeup essentials", "Cherry Cola lips products", "Korean Glass Skin holy grails",
                    "TSA-approved travel skincare", "Vacation glow-up essentials", "Mini makeup products for purse",
                    
                    # ── Viral 2026 US/UK/Canada TikTok & Pinterest Trends ──
                    "M.ph by Mary Phillips Le Skin Foundation dupes", "Danessa Myricks Yummy Skin Blurring Balm Powder dupes",
                    "e.l.f. Power Grip Primer", "Rhode Peptide Lip Treatment 2026 shades",
                    "Merit Signature Lip Blush", "Summer Fridays Flushed Lip Stain dupes",
                    "Medicube Collagen Night Wrapping Mask", "Rhode Caffeine Reset sculpting tools",
                    "Beauty of Joseon Tinted Mineral SPF", "Skincare-makeup fusion base products",
                    "Jelly-to-foam Korean cleansers", "Trending 2026 hair perfumes and body mists",
                    "Effortless clean girl beauty routine 2026", "Viral high-speed hair dryers on Amazon",
                    
                    # ── Timeless Viral TikTok & Pinterest Trends ──
                    "Biodance Bio-Collagen deep mask", "Medicube Age-R Booster Pro alternatives", 
                    "Milk Makeup Cooling Water Jelly Tint dupes", "Rhode Pocket Blush & Peptide Lip Tint dupes", 
                    "Charlotte Tilbury Unreal Skin glow tint dupes", "Moira Love Steady liquid blush", 
                    "Aveeno Calm + Restore for sensitive skin", "Coquette aesthetic hair bows and ribbons", 
                    "Korean glass skin glowing toners", "Cherry cola lip liner and gloss combos", 
                    "Tenniscore clean beauty look essentials", "Broccoli freckles faux freckle pens",
                    "Viral overnight face masks", "Glow Recipe watermelon dew drops dupes",
                    "Summer Fridays lip butter balm dupes",
                    
                    # ── Extreme High-Conversion: Problem-Solving & Urgent Buys ──
                    "Overnight cystic acne patches", "Fast acting dark spot correctors",
                    "Keratosis pilaris strawberry legs scrub", "Best color corrector for severe dark circles",
                    "Hair thinning serums for women", "Heat protectant for severely damaged hair",
                    "Chapped lips overnight lip masks", "Painless at-home laser hair removal (IPL)",
                    "Anti-aging neck firming creams", "Fungal acne safe skincare routine",
                    
                    # ── Blank-Cheque Buyers: Bridal & Wedding Beauty ──
                    "Bridal emergency makeup touch-up kit", "Cry-proof waterproof wedding mascara",
                    "Long lasting setting spray for brides", "Pre-wedding 6-month skincare prep routine",
                    "At-home teeth whitening strips for brides", "Sweat-proof summer wedding foundation",
                    
                    # ── "Starter Packs" & Aesthetic Bundles ──
                    "Clean girl aesthetic makeup starter pack", "TSA-approved travel beauty essentials",
                    "Pilates princess gym beauty routine", "Old money aesthetic signature perfumes",
                    "Vanilla girl aesthetic shower routine", "Affordable vanity organization ideas",
                    
                    # ── Beauty + Decor Hybrids (Super High Conversion) ──
                    "Aesthetic makeup vanity mirror with lights", "Clear acrylic makeup organizers",
                    "Mini skincare fridge for serums", "Rotating perfume stand organizer"
                ]

                # ── Trend Miner Integration: Priority Daily Top 5 Viral Check ──
                trending_product = None
                trending_category = None
                trending_miner_id = None

                try:
                    from trend_miner.trend_db import TrendDatabaseManager
                    tm_db = TrendDatabaseManager()
                    top5_virals = tm_db.get_fresh_daily_top_5_virals()

                    if top5_virals:
                        top_viral = top5_virals[0]
                        prod_keyword = top_viral.product_name
                        trending_miner_id = top_viral.id

                        # Double check if already posted in main DB
                        with agent.db.connection() as conn:
                            chk = conn.execute("SELECT 1 FROM products WHERE LOWER(product_name) = LOWER(?)", (prod_keyword,))
                            if not chk.fetchone():
                                trending_product = prod_keyword
                                trending_category = top_viral.category or "Skincare"
                                logger.info("🔥 TREND MINER DAILY VIRAL PRIORITY [#%s]: '%s' (PIS: %d/40, Board: '%s'). Bypassing schedule!",
                                            top_viral.id, trending_product, top_viral.trend_score, top_viral.target_board)
                            else:
                                logger.info("Trend Miner product '%s' already in main DB. Marking pinned.", prod_keyword)
                                if top_viral.id:
                                    tm_db.mark_as_pinned(top_viral.id)
                except Exception as e:
                    logger.error(f"Error checking Trend Miner priority pool: {e}")

                # 2. Determine the category & product for this cycle
                if trending_product and trending_category:
                    current_category = trending_category
                    logger.info("Executing Pipeline Cycle (Pin #%d today) in Bypass Mode for Trending Product: '%s'...", today_count + 1, trending_product)
                else:
                    current_category = get_next_category_based_on_analytics(agent.db, categories)
                    logger.info("Executing Pipeline Cycle (Pin #%d today) for Category: '%s'...", today_count + 1, current_category)
                
                # ── Run pipeline with self-healing ──
                try:
                    success = await agent.run_affiliate_pipeline(niche=current_category, product_keyword=trending_product)
                    consecutive_failures = 0  # Reset on success
                except FatalLoginError as fatal_err:
                    logger.critical("=================================================================")
                    logger.critical("🛑 CRITICAL SECURITY STOP: PINTEREST LOGIN FAILED 2 TIMES IN A ROW!")
                    logger.critical("Pinterest may have served a Captcha or Suspicious Activity check.")
                    logger.critical("")
                    logger.critical("👉 TO FIX THIS SAFELY WITHOUT RISKING ACCOUNT LOCKS:")
                    logger.critical("   1. Open a terminal and run:  python login_pinterest_once.py")
                    logger.critical("   2. Log in manually in the opened Chrome window.")
                    logger.critical("   3. Once logged in, restart the agent: python main.py")
                    logger.critical("=================================================================")
                    await agent.shutdown()
                    sys.exit(1)
                except Exception as e:
                    consecutive_failures += 1
                    error_str = str(e).lower()
                    logger.error(f"Pipeline error (failure #{consecutive_failures}): {e}")
                    success = False
    
                    # ── Detect error type and self-heal ───────────────────────────
                    is_browser_crash = any(kw in error_str for kw in [
                        "playwright", "browser", "page", "context", "crashed",
                        "target closed", "connection refused", "websocket"
                    ])
                    is_network_error = any(kw in error_str for kw in [
                        "net::err_internet_disconnected",
                        "net::err_name_not_resolved",
                        "net::err_connection_refused",
                        "dns_probe_finished_no_internet",
                        "no internet connection"
                    ])
    
                    if is_browser_crash:
                        logger.warning("🔧 Browser crash detected! Attempting browser restart...")
                        try:
                            await agent.browser_manager.close()
                            await asyncio.sleep(5)
                            await agent.browser_manager.initialize()
                            logger.info("✅ Browser restarted successfully!")
                        except Exception as restart_err:
                            logger.error(f"Browser restart failed: {restart_err}. Reinitializing full agent...")
                            try:
                                await agent.shutdown()
                            except Exception:
                                pass
                            agent = PinterestAgent()
                            await agent.initialize()
                            logger.info("✅ Full agent reinitialized!")
    
                    elif is_network_error:
                        logger.warning("🌐 Network error detected! Waiting for connection...")
                        await wait_for_internet(max_wait_minutes=15)


    
                    # ── Exponential backoff based on failure count ─────────────────
                    if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                        logger.error(f"⚠️ {MAX_CONSECUTIVE_FAILURES} consecutive failures! Sleeping 30 min before retry...")
                        await asyncio.sleep(1800)  # 30 minutes
                        consecutive_failures = 0
                    elif consecutive_failures >= 3:
                        logger.warning("3 failures in a row. Sleeping 15 min...")
                        await asyncio.sleep(900)  # 15 minutes
                    else:
                        logger.warning("Pipeline step encountered error. Safe Schedule: Waiting 15-25 minutes before next cycle...")
                        # Fallthrough to regular 15-25 min delay below
    
                # ── Handle success / duplicate after try block ─────────────────
                if success == "DUPLICATE":
                    logger.warning("Duplicate detected. Retrying cycle immediately with next category...")
                    continue
                elif success:
                    logger.info("✅ Pin cycle completed successfully.")
                    if trending_miner_id:
                        try:
                            tm_db.mark_as_pinned(trending_miner_id)
                            logger.info("📌 Marked Trend Miner product ID #%s as Pinned (Zero Duplicate Guaranteed).", trending_miner_id)
                        except Exception as m_err:
                            logger.warning("Failed to mark Trend Miner ID #%s as pinned: %s", trending_miner_id, m_err)
                else:
                    logger.warning("Pipeline returned False or quality check skipped item. Scheduling next cycle with safe delay...")
                    
                # 3. Safe Zone Human Pacing: Random 15 to 25 minutes delay between pins (Non-stop for 90 Days)
                import random
                interval_mins = random.randint(15, 25)
                logger.info("⏳ Safe Zone Schedule: Next pin scheduled in %d minutes (Randomized 15-25 min delay)...", interval_mins)
                await asyncio.sleep(interval_mins * 60)
                
            # Exit outer loop cleanly if inner loop breaks without Exception
            break
            
        except KeyboardInterrupt:
            print("\n⚠️ Agent stopped by user.")
            break
        except Exception as e:
            logger.error(f"\n🔥 Fatal Error in scheduler: {e}. Restarting in 60 seconds...")
            await asyncio.sleep(60)
            logger.info("♻️ Auto-restarting main loop after fatal error...")
            continue
        finally:
            try:
                await agent.shutdown()
            except Exception:
                pass
            print("🛑 Agent shutdown cycle complete.")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Handle --setup-startup and --remove-startup flags
    if "--setup-startup" in sys.argv:
        setup_windows_startup()
        print("Agent will now auto-start when your laptop turns on!")
        sys.exit(0)
    elif "--remove-startup" in sys.argv:
        remove_windows_startup()
        print("Agent auto-start removed.")
        sys.exit(0)
    
    asyncio.run(main())
