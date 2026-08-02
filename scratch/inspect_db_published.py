import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('database/pinterest_ai_agent.db')
conn.row_factory = sqlite3.Row

rows = conn.execute("SELECT * FROM products WHERE status LIKE '%Published%' ORDER BY updated_at DESC LIMIT 5").fetchall()

for r in rows:
    print(f"ID #{r['id']} | Status: {r['status']}")
    print(f"  Product Name   : {r['product_name']}")
    print(f"  Title          : {r['title']}")
    print(f"  Board          : {r['board_name']}")
    print(f"  Image Path     : {r['image_path']}")
    print(f"  Pin URL        : {r['pin_url']}")
    print(f"  Description    : {r['description']}")
    print(f"  Updated At     : {r['updated_at']}")
    print("=" * 80)
