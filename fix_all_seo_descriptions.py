"""
Fix & Upgrade 100% of Agent Database Descriptions to Ultra SEO Keyword Stacking & CTA Standard
"""
import sqlite3
import sys
import re
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DB_PATH = Path("database/pinterest_ai_agent.db")

def generate_ultra_seo_description(title: str, category: str, board_name: str) -> str:
    clean_title = re.sub(r'[^\w\s-]', '', title).strip()
    words = clean_title.split()[:7]
    short_title = " ".join(words)

    t_low = title.lower()
    if any(k in t_low for k in ["bronzer", "contour", "blush", "highlighter", "foundation", "powder", "setting spray", "primer"]):
        copy_body = "Achieve an effortless sun-kissed glow and seamless matte finish with this Sephora viral makeup essential. Long-lasting, lightweight, and perfect for your daily clean girl makeup routine."
        hashtags = "#AmazonBeautyFinds #SephoraDupes #CleanGirlMakeup #MakeupMustHaves #ViralBeauty"
    elif any(k in t_low for k in ["lip oil", "lip gloss", "lip balm", "lip sleeping mask", "tint"]):
        copy_body = "Get ultra-hydrated, high-shine glass lips with this lightweight viral lip treatment. Non-sticky, deeply moisturizing formula for effortless everyday glamour."
        hashtags = "#AmazonBeautyFinds #LipOil #SephoraDupes #GlassLips #BeautyFavorites"
    elif any(k in t_low for k in ["hair", "shampoo", "conditioner", "spray", "bond", "frizz"]):
        copy_body = "Transform your hair care routine with this salon-quality hydrating formula. Protects against humidity, repairs split ends, and delivers 3X smoother, glossy locks."
        hashtags = "#AmazonBeautyFinds #HairCareSecrets #AntiFrizz #SephoraDupes #ShinyHair"
    else:
        copy_body = "This high-performance formula is the ultimate Sephora & Amazon beauty find! Deeply nourishes, restores skin barrier, and gives you a healthy, glowing complexion."
        hashtags = "#AmazonBeautyFinds #SkincareRoutine #SephoraDupes #GlassSkin #CleanGirlAesthetic"

    board_clean = board_name.strip() if board_name else "Beauty Favorites"

    desc = (
        f"Looking for the best {short_title} for your everyday beauty routine in the US, UK, and Canada? "
        f"{copy_body} "
        f"Click the link to check today's live price & read 15,000+ verified 5-star customer reviews on Amazon. "
        f"💾 Save this pin to your {board_clean} board! {hashtags}"
    )
    return desc

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, category, board_name, description FROM products")
    rows = cursor.fetchall()

    fixed_count = 0

    for r in rows:
        p_id, p_title, p_cat, p_board, old_desc = r
        p_title = p_title or "Viral Beauty Find"
        p_cat = p_cat or "Beauty"
        p_board = p_board or "Amazon Beauty Finds"

        # Check if description needs upgrade (if missing, or generic fallback, or lacks category specific copy)
        is_generic_fallback = "glowing glass skin" in (old_desc or "").lower() and not any(k in p_title.lower() for k in ["skin", "moisturizer", "serum", "hydrator", "mask"])
        if not old_desc or "Click the link to check" not in old_desc or is_generic_fallback:
            new_desc = generate_ultra_seo_description(p_title, p_cat, p_board)
            cursor.execute("UPDATE products SET description = ? WHERE id = ?", (new_desc, p_id))
            fixed_count += 1

    conn.commit()
    conn.close()

    print("═════════════════════════════════════════════════════════════════")
    print(f" 🎯 ULTRA SEO DESCRIPTIONS FIX COMPLETE! UPGRADED {fixed_count} PRODUCTS")
    print("═════════════════════════════════════════════════════════════════")

if __name__ == "__main__":
    main()
