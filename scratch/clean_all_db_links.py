import sqlite3
import re
from pathlib import Path

db_path = Path("database/pinterest_ai_agent.db")
if not db_path.exists():
    db_path = Path("pinterest_ai_agent.db")

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

def clean_amazon_url(url, tag="savvyshop0965-20"):
    if not url:
        return ""
    match = re.search(r'/(?:dp|gp/product|gp/video|d)/([A-Z0-9]{10})', url, re.IGNORECASE)
    if match:
        asin = match.group(1).upper()
        return f"https://www.amazon.com/dp/{asin}?tag={tag}"
    return url

rows = conn.execute("SELECT id, affiliate_link FROM products").fetchall()
cleaned_count = 0

for r in rows:
    old_link = r['affiliate_link'] or ''
    new_link = clean_amazon_url(old_link)
    if new_link != old_link:
        conn.execute("UPDATE products SET affiliate_link = ? WHERE id = ?", (new_link, r['id']))
        cleaned_count += 1

conn.commit()
print(f"Successfully cleaned {cleaned_count} product affiliate links in database to direct https://www.amazon.com/dp/ASIN?tag=savvyshop0965-20 format!")

# Show sample of cleaned links
sample_rows = conn.execute("SELECT id, product_name, affiliate_link FROM products ORDER BY id DESC LIMIT 5").fetchall()
for s in sample_rows:
    print(f"ID #{s['id']}: {s['product_name'][:35]} -> {s['affiliate_link']}")

conn.close()
