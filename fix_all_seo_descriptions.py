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
    words = clean_title.split()[:8]
    short_title = " ".join(words)

    tag_cat = re.sub(r'[^\w]', '', category) or "BeautyFinds"
    tag_board = re.sub(r'[^\w]', '', board_name) or "ViralBeauty"

    desc = (
        f"Looking for the best {short_title} for your everyday beauty routine in the US, UK, and Canada? "
        f"This high-performance formula is the ultimate Sephora & Amazon beauty find! "
        f"Click the link to check today's live price & read 15,000+ verified 5-star customer reviews on Amazon. "
        f"💾 Save this pin to your {board_name} board! "
        f"#{tag_cat} #{tag_board} #AmazonBeautyFinds #SephoraDupes #CleanGirlAesthetic"
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

        # Check if description needs upgrade
        if not old_desc or "Click the link to check today's live price" not in old_desc:
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
