import sqlite3
from pathlib import Path

db_path = Path("database/pinterest_ai_agent.db")
if not db_path.exists():
    print("Database not found!")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Total products by status
cursor.execute("SELECT status, COUNT(*) FROM products GROUP BY status")
status_counts = cursor.fetchall()
print("=== PRODUCT STATUS DISTRIBUTION ===")
for st, cnt in status_counts:
    print(f"  • {st}: {cnt}")

# 2. Check Linktree vs Published mismatch
cursor.execute("SELECT COUNT(*) FROM products WHERE status = 'Pinterest_Published'")
published_cnt = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM products WHERE status = 'Completed' OR status = 'Linktree_Added'")
linktree_cnt = cursor.fetchone()[0]

print(f"\n=== LINKTREE SYNC STATUS ===")
print(f"  • Pinterest Published (Pending Linktree Sync): {published_cnt}")
print(f"  • Linktree Sync Completed: {linktree_cnt}")

# 3. Check affiliate tags in Amazon links
cursor.execute("SELECT affiliate_link FROM products WHERE affiliate_link IS NOT NULL AND length(affiliate_link)>5 LIMIT 50")
links = [r[0] for r in cursor.fetchall()]
tag_correct = sum(1 for l in links if "savvyshop0965-20" in l)
print(f"\n=== AFFILIATE TAG CHECK (Sample {len(links)}) ===")
print(f"  • Correct tag 'savvyshop0965-20': {tag_correct}/{len(links)}")

# 4. Top boards and impressions/clicks if stored
cursor.execute("SELECT board_name, COUNT(*), SUM(impressions), SUM(clicks), SUM(saves) FROM products GROUP BY board_name ORDER BY SUM(clicks) DESC LIMIT 10")
board_stats = cursor.fetchall()
print(f"\n=== TOP BOARDS PERFORMANCE ===")
for b_name, cnt, imp, clk, sav in board_stats:
    print(f"  • Board: {b_name} | Pins: {cnt} | Impr: {imp or 0} | Clicks: {clk or 0} | Saves: {sav or 0}")

conn.close()
