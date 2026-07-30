"""
Master Single-File Exporter for ALL Agent Products (1,600+ Items)
Dumps 100% of products in database into all_products_master_list.txt
"""
import sqlite3
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def main():
    db_path = Path("database/pinterest_ai_agent.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Total count
    cursor.execute("SELECT COUNT(*) FROM products")
    total_count = cursor.fetchone()[0]

    # Published vs Pending
    cursor.execute("SELECT status, COUNT(*) FROM products GROUP BY status")
    status_counts = dict(cursor.fetchall())

    # Fetch all items ordered by ID
    cursor.execute("SELECT id, product_name, category, board_name, status, source_url, affiliate_link, created_at FROM products ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()

    out_file = Path("all_products_master_list.txt")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write("=================================================================================\n")
        f.write(f" 👑 BADDIES BEAUTY AGENT — ALL-IN-ONE MASTER PRODUCTS LIST (TOTAL: {total_count})\n")
        f.write("=================================================================================\n")
        f.write(f" 🌐 Fully Published (Pinterest + Linktree): {status_counts.get('Pinterest_Published', 0)}\n")
        f.write(f" ⏳ Pending Pin Queue: {status_counts.get('Pending_Pin', 0)}\n")
        f.write("=================================================================================\n\n")

        for idx, r in enumerate(rows, start=1):
            p_id, p_name, cat, board, status, source_url, aff_url, created_at = r
            f.write(f"#{idx:04d} | ID: {p_id} | Status: [{status}] | Category: {cat or 'General'}\n")
            f.write(f"      Product Name  : {p_name}\n")
            f.write(f"      Source URL    : {source_url}\n")
            f.write(f"      Affiliate Link: {aff_url}\n")
            f.write("---------------------------------------------------------------------------------\n")

    print("═════════════════════════════════════════════════════════════════")
    print(f" 🎉 SUCCESS! EXPORTED ALL {total_count} PRODUCTS INTO SINGLE MASTER FILE!")
    print(f" 📄 Master File Location: {out_file.resolve()}")
    print("═════════════════════════════════════════════════════════════════")

if __name__ == "__main__":
    main()
