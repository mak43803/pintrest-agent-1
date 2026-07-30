"""
Inspect Most Recently Seeded Product in Agent Database
"""
import sqlite3
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def main():
    db_path = Path("database/pinterest_ai_agent.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, product_name, category, board_name, status, source_url, 
               title, description, affiliate_link, image_path, created_at, pin_url 
        FROM products ORDER BY id DESC LIMIT 5
    """)
    rows = cursor.fetchall()
    conn.close()

    print("═════════════════════════════════════════════════════════════════")
    print(" 🌟 MOST RECENTLY SEEDED PRODUCTS IN AGENT DATABASE")
    print("═════════════════════════════════════════════════════════════════")

    for idx, r in enumerate(rows, start=1):
        print(f"\n[{idx}] PRODUCT ID #{r[0]}")
        print(f"    • Product Name  : {r[1]}")
        print(f"    • Category      : {r[2]}")
        print(f"    • Board Name    : {r[3]}")
        print(f"    • Status        : {r[4]}")
        print(f"    • Image Path/URL: {r[9]}")
        print(f"    • Source URL    : {r[5]}")
        print(f"    • Affiliate Link: {r[8]}")
        print(f"    • Created At    : {r[10]}")
        print(f"    • Pin URL       : {r[11] or 'Pending Pin Generation'}")

if __name__ == "__main__":
    main()
