import sqlite3
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

db_path = "database/pinterest_ai_agent.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 1. Fetch latest published products
print("=== TODAY'S RECENTLY PUBLISHED BEAUTY PRODUCTS (LIVE) ===")
rows = cursor.execute("""
    SELECT id, product_name, category, board_name, title, status, pin_url, created_at
    FROM products ORDER BY id DESC LIMIT 5
""").fetchall()

for r in rows:
    print(f"📌 [ID #{r['id']}] {r['product_name']}")
    print(f"   Board: {r['board_name']}")
    print(f"   Title: {r['title']}")
    print(f"   Pin URL: {r['pin_url']}")
    print(f"   Status: {r['status']}")
    print(f"   Created: {r['created_at']}\n")

# 2. Fetch latest agent execution logs
print("=== TODAY'S RECENT AGENT LOGS & RESEARCH EVENTS ===")
try:
    log_rows = cursor.execute("""
        SELECT level, module, message, created_at
        FROM logs ORDER BY id DESC LIMIT 10
    """).fetchall()

    for l in reversed(log_rows):
        print(f"[{l['created_at']}] [{l['level']}] [{l['module']}]: {l['message']}")
except Exception as e:
    print(f"Logs query notice: {e}")

conn.close()
