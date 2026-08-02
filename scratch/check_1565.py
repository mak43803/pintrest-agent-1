import sqlite3

conn = sqlite3.connect('database/pinterest_ai_agent.db')
cursor = conn.cursor()
cursor.execute("SELECT id, product_name, source_url, image_path FROM products WHERE id=1565")
row = cursor.fetchone()
print("ID:", row[0])
print("Name:", row[1])
print("Source URL:", row[2])
print("Image Path:", row[3])
