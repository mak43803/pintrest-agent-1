import sqlite3
import re
from pathlib import Path

db_path = Path("database/pinterest_ai_agent.db")
if not db_path.exists():
    db_path = Path("pinterest_ai_agent.db")

print(f"Connecting to database at {db_path}...")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

rows = conn.execute("SELECT id, product_name, title, source_url, affiliate_link, status FROM products WHERE status = 'Pending_Pin'").fetchall()
print(f"Inspecting {len(rows)} Pending_Pin items in database...")

mismatch_repaired = 0
link_repaired = 0

for r in rows:
    p_id = r['id']
    pname = (r['product_name'] or '').strip()
    title = (r['title'] or '').strip()
    source = (r['source_url'] or '').strip()
    aff_link = (r['affiliate_link'] or '').strip()

    # 1. Check title / product class mismatch
    pname_lower = pname.lower()
    title_lower = title.lower()

    conflicting_pairs = [
        ("patch", "lip oil"), ("patch", "cushion"), ("patch", "setting spray"), ("patch", "foundation"),
        ("lip oil", "foundation"), ("sunscreen", "lip balm"), ("shampoo", "lip oil"), ("perfume", "cleanser")
    ]
    
    is_mismatched = any((c1 in pname_lower and c2 in title_lower) for c1, c2 in conflicting_pairs)

    new_title = title
    if is_mismatched or not title:
        clean_short = " ".join(pname.split()[:7])
        new_title = f"{clean_short} | Sephora Beauty Finds 2026"
        mismatch_repaired += 1

    # 2. Check and clean affiliate link to direct /dp/ASIN if ASIN exists in link or source
    new_aff_link = aff_link
    target_tag = "savvyshop0965-20"
    
    asin_match = re.search(r'/(?:dp|gp/product|gp/video|d)/([A-Z0-9]{10})', aff_link or source, re.IGNORECASE)
    if asin_match:
        asin = asin_match.group(1).upper()
        clean_dp_url = f"https://www.amazon.com/dp/{asin}?tag={target_tag}"
        if aff_link != clean_dp_url:
            new_aff_link = clean_dp_url
            link_repaired += 1
    
    if new_title != title or new_aff_link != aff_link:
        conn.execute(
            "UPDATE products SET title = ?, affiliate_link = ? WHERE id = ?",
            (new_title, new_aff_link, p_id)
        )

conn.commit()
conn.close()

print("\n=== DATABASE CLEANUP COMPLETE ===")
print(f"  - Repaired mismatched titles: {mismatch_repaired}")
print(f"  - Repaired affiliate ASIN links: {link_repaired}")
