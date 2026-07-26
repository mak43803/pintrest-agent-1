import sqlite3
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

db_path = "database/pinterest_ai_agent.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 1. Total product count
total_cnt = cursor.execute("SELECT COUNT(*) as cnt FROM products").fetchone()['cnt']
published_cnt = cursor.execute("SELECT COUNT(*) as cnt FROM products WHERE status = 'Published'").fetchone()['cnt']
pinterest_published_cnt = cursor.execute("SELECT COUNT(*) as cnt FROM products WHERE status = 'Pinterest_Published'").fetchone()['cnt']

earliest_date = cursor.execute("SELECT created_at FROM products ORDER BY id ASC LIMIT 1").fetchone()
latest_date = cursor.execute("SELECT created_at FROM products ORDER BY id DESC LIMIT 1").fetchone()

print("=== PINTEREST AGENT RUNTIME DATABASE METRICS ===")
print(f"Total Products in DB: {total_cnt}")
print(f"Fully Published (Pinterest + Linktree): {published_cnt}")
print(f"Pinterest Published: {pinterest_published_cnt}")
print(f"Earliest Product Date: {earliest_date['created_at'] if earliest_date else 'N/A'}")
print(f"Latest Product Date: {latest_date['created_at'] if latest_date else 'N/A'}")

# Top Boards distribution
print("\n=== TOP PUBLISHED BOARDS ===")
boards = cursor.execute("""
    SELECT board_name, COUNT(*) as cnt 
    FROM products GROUP BY board_name ORDER BY cnt DESC LIMIT 10
""").fetchall()

for b in boards:
    print(f"📌 '{b['board_name']}': {b['cnt']} pins")

conn.close()
