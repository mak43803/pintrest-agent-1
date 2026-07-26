import sqlite3

db_path = r"c:\Users\mazzu\OneDrive\Desktop\pintrest ai agent\database\pinterest_ai_agent.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get distinct statuses
cursor.execute("SELECT status, COUNT(*) FROM products GROUP BY status")
print("=== Product Statuses ===")
for status, count in cursor.fetchall():
    print(f"Status: '{status}' | Count: {count}")

# Let's also print 5 products that are in the failed/pending Linktree state
cursor.execute("SELECT id, product_name, category, status, source_url, affiliate_link FROM products WHERE status = 'Pinterest_Published' LIMIT 5")
print("\n=== Sample Failed Products ===")
for row in cursor.fetchall():
    print(row)

conn.close()
