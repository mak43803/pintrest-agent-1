import sqlite3

db_path = "database/pinterest_ai_agent.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Query count of products created today (July 15, 2026)
cursor.execute("SELECT COUNT(*) FROM products WHERE created_at LIKE '2026-07-15%'")
count_today = cursor.fetchone()[0]

print(f"=== PRODUCTS CREATED TODAY (2026-07-15) ===")
print(f"Total Products: {count_today}")

# Get breakdown of statuses for today
cursor.execute("SELECT status, COUNT(*) FROM products WHERE created_at LIKE '2026-07-15%' GROUP BY status")
print("\n--- Status Breakdown ---")
for status, count in cursor.fetchall():
    print(f"Status: '{status}' | Count: {count}")

# Print list of products created today
cursor.execute("SELECT id, product_name, category, status, created_at FROM products WHERE created_at LIKE '2026-07-15%' ORDER BY created_at ASC")
print("\n--- List of Products ---")
for idx, row in enumerate(cursor.fetchall()):
    print(f"{idx+1}. [{row[4]}] {row[1]} ({row[2]}) -> Status: {row[3]}")

conn.close()
