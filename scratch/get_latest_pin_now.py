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
    print("=== LATEST PUBLISHED PIN IN DATABASE ===")
    print(f"ID: {row['id']}")
    print(f"Product Name: {row['product_name']}")
    print(f"Board Name: {row['board_name']}")
    print(f"Title: {row['title']}")
    print(f"Status: {row['status']}")
    print(f"Image Path: {row['image_path']}")
    print(f"Pin URL: {row['pin_url']}")
    print(f"Affiliate Link: {row['affiliate_link']}")
    print(f"Created At: {row['created_at']}")
    
    img_p = row['image_path']
    if img_p and os.path.exists(img_p):
        print(f"Image File Exists: YES ({os.path.getsize(img_p)/1024:.1f} KB)")
    else:
        print(f"Image File Exists: NO ({img_p})")

conn.close()
