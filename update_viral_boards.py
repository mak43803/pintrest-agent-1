"""
Update All 2,100+ Agent Database Products with High-Converting Viral Pinterest Boards
"""
import sqlite3
import sys
import re
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DB_PATH = Path("database/pinterest_ai_agent.db")

VIRAL_BOARDS_MAPPING = [
    (r'sunscreen|spf|sun protection|white cast', "Korean Sunscreens Zero White Cast"),
    (r'lip oil|lip gloss|lip tint|lip balm|dior lip|summer fridays lip|laneige lip', "Dior Lip Oil $8 Amazon Dupes"),
    (r'back to school|bts|school morning|class', "Back-To-School 5-Minute Skincare & Beauty"),
    (r'serum|hyaluronic|niacinamide|collagen|pdrn|exfoliat|korean|k-beauty', "K-Beauty Serums That Actually Work"),
    (r'body wash|shower gel|sugar scrub|body lotion|bum bum|bath', "Body Wash Shower Gels USA 2026"),
    (r'hair oil|anti frizz|k18|dyson|blow dry|shampoo|conditioner|scalp', "Anti-Frizz Hair Oils & Styling Secrets"),
    (r'perfume|cologne|body mist|cheirosa|fragrance|arabian|vanilla amber', "Luxury Perfumes & Arabian Oil Dupes"),
    (r'blush|contour|foundation|skin tint|setting spray|concealer|makeup', "Clean Girl Aesthetic Makeup"),
    (r'mini|travel size|gift set|favorites|value set|sampler', "Sephora Minis & Travel Favorites"),
    (r'ulta|under \$20|\$15|\$8', "Amazon Beauty Finds Under $20"),
]

def get_viral_board(product_name: str, category: str) -> str:
    combined = f"{product_name} {category}".lower()
    for pattern, board_name in VIRAL_BOARDS_MAPPING:
        if re.search(pattern, combined, re.I):
            return board_name
    return "Sephora Viral Beauty Finds 2026"

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id, product_name, category, board_name FROM products")
    rows = cursor.fetchall()

    updated_count = 0
    board_distribution = {}

    for r in rows:
        p_id, p_name, p_cat, old_board = r
        new_board = get_viral_board(p_name or "", p_cat or "")

        board_distribution[new_board] = board_distribution.get(new_board, 0) + 1

        if old_board != new_board:
            cursor.execute("UPDATE products SET board_name = ? WHERE id = ?", (new_board, p_id))
            updated_count += 1

    conn.commit()
    conn.close()

    print("═════════════════════════════════════════════════════════════════")
    print(f" 🎯 VIRAL BOARDS MAPPING COMPLETE! UPDATED {updated_count} PRODUCTS")
    print("═════════════════════════════════════════════════════════════════")
    print("📊 VIRAL BOARD DISTRIBUTION ACROSS ALL 2,100+ PRODUCTS:")
    for b_name, count in sorted(board_distribution.items(), key=lambda x: x[1], reverse=True):
        print(f"   📌 {b_name}: {count} products")
    print("═════════════════════════════════════════════════════════════════")

if __name__ == "__main__":
    main()
