"""
Export all published product names/ASINs from local DB
to a SQL file that can be imported on AWS to prevent duplicates.
"""
import sqlite3
import os

# Find the database
db_paths = [
    "database/pinterest_ai_agent.db",
    "pinterest_ai_agent.db",
    "database.db"
]

db_path = None
for p in db_paths:
    if os.path.exists(p):
        db_path = p
        print(f"Found DB: {p}")
        break

if not db_path:
    print("ERROR: No database found!")
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.execute("SELECT product_name, title, affiliate_link, board_name, status FROM products")
rows = cursor.fetchall()
conn.close()

print(f"Total products in local DB: {len(rows)}")

# Write SQL insert statements
with open("product_history.sql", "w", encoding="utf-8") as f:
    f.write("-- Product history export from local machine\n")
    f.write("-- Run this on AWS to prevent duplicate pins\n\n")
    
    for row in rows:
        product_name = (row["product_name"] or "").replace("'", "''")
        title = (row["title"] or "").replace("'", "''")
        affiliate_link = (row["affiliate_link"] or "").replace("'", "''")
        board_name = (row["board_name"] or "").replace("'", "''")
        status = row["status"] or "Published"
        
        f.write(f"""INSERT OR IGNORE INTO products (product_name, title, affiliate_link, board_name, status, category)
VALUES ('{product_name}', '{title}', '{affiliate_link}', '{board_name}', '{status}', 'imported');\n""")

print(f"Exported {len(rows)} products to product_history.sql")
print("Now run: git add product_history.sql && git commit -m 'temp: product history' && git push")
