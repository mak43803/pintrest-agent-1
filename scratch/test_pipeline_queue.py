"""
Test Pipeline DB Queue Processing
"""
import sqlite3
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def main():
    conn = sqlite3.connect("database/pinterest_ai_agent.db")
    row = conn.execute("SELECT id, product_name, category, board_name, title, image_path, affiliate_link FROM products WHERE status = 'Pending_Pin' ORDER BY id ASC LIMIT 1").fetchone()
    conn.close()

    print("═════════════════════════════════════════════════════════════════")
    print(" 📦 NEXT QUEUED ITEM FOR AGENT AUTOMATION")
    print("═════════════════════════════════════════════════════════════════")

    if row:
        print(f" • Product ID   : #{row[0]}")
        print(f" • Product Name : {row[1]}")
        print(f" • Category     : {row[2]}")
        print(f" • Board Name   : {row[3]}")
        print(f" • Title        : {row[4]}")
        print(f" • Image Path   : {row[5]}")
        print(f" • Affiliate    : {row[6]}")
    else:
        print("No pending products found.")
    print("═════════════════════════════════════════════════════════════════")

if __name__ == "__main__":
    main()
