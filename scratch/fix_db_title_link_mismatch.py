import sqlite3
import re
from pathlib import Path

db_path = Path("database/pinterest_ai_agent.db")
if not db_path.exists():
    db_path = Path("pinterest_ai_agent.db")

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

rows = conn.execute("SELECT id, product_name, title, source_url, affiliate_link, status FROM products WHERE status = 'Pending_Pin'").fetchall()

print(f"Inspecting {len(rows)} Pending_Pin rows in DB for title <-> link consistency...")
mismatch_count = 0

for r in rows:
    p_id = r['id']
    name = (r['product_name'] or r['title'] or '').lower()
    link = (r['affiliate_link'] or r['source_url'] or '').lower()
    
    # Check if key brand/words in title exist in link or if link has different product name
    # Extract words from name (ignore common words)
    name_words = [w for w in re.findall(r'[a-z0-9]+', name) if len(w) > 3 and w not in ['beauty', 'finds', 'find', 'sephora', 'amazon', 'with', 'your', 'for', 'skin', 'care', 'routine', 'ulta']]
    
    # Check match ratio against link
    matches = [w for w in name_words if w in link]
    if name_words and len(matches) == 0 and len(name_words) >= 2:
        print(f"MISMATCH DETECTED in ID #{p_id}:")
        print(f"   Name: '{r['product_name']}'")
        print(f"   Title: '{r['title']}'")
        print(f"   Link: '{r['affiliate_link']}'")
        mismatch_count += 1

print(f"\nTotal Pending_Pin mismatches found: {mismatch_count}")
conn.close()
