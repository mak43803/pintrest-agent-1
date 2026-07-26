import sqlite3
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

db_path = "database/pinterest_ai_agent.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

row = cursor.execute("""
    SELECT id, product_name, category, board_name, title, description, image_path, pin_url, affiliate_link, status, created_at
    FROM products ORDER BY id DESC LIMIT 1
""").fetchone()

if row:
    print("=== LATEST PUBLISHED PIN METADATA ===")
    print(f"ID: {row['id']}")
    print(f"Product: {row['product_name']}")
    print(f"Board: {row['board_name']}")
    print(f"Title: {row['title']}")
    print(f"Image: {row['image_path']}")
    print(f"Pin URL: {row['pin_url']}")
    print(f"Affiliate URL: {row['affiliate_link']}")
    print(f"Created: {row['created_at']}")

conn.close()
