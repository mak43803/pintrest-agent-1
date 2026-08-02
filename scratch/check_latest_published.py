import sqlite3

conn = sqlite3.connect('database/pinterest_ai_agent.db')
cursor = conn.cursor()
cursor.execute("SELECT id, product_name, title, image_path, pin_url, status, updated_at FROM products WHERE status = 'Published' ORDER BY id DESC LIMIT 10")
rows = cursor.fetchall()

print("--- LATEST 10 PUBLISHED PINS IN DATABASE ---")
for r in rows:
    print(f"ID: {r[0]}")
    print(f"Name: {r[1]}")
    print(f"Title: {r[2]}")
    print(f"Image: {r[3]}")
    print(f"Pin URL: {r[4]}")
    print(f"Status: {r[5]}")
    print(f"Updated: {r[6]}")
    print("-" * 50)
