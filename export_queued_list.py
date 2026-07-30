"""
Export Full Agent Database Products Summary & Full List
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

    # Total products
    cursor.execute("SELECT COUNT(*) FROM products")
    total_count = cursor.fetchone()[0]

    # Published vs Pending
    cursor.execute("SELECT status, COUNT(*) FROM products GROUP BY status")
    status_counts = dict(cursor.fetchall())

    # Category breakdown
    cursor.execute("SELECT category, COUNT(*) FROM products GROUP BY category ORDER BY COUNT(*) DESC")
    cat_counts = cursor.fetchall()

    # Export full list
    cursor.execute("SELECT id, product_name, category, status, source_url FROM products ORDER BY id DESC")
    all_rows = cursor.fetchall()
    conn.close()

    out_file = Path("full_agent_products_list.txt")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(f"=== BADDIES BEAUTY AGENT — FULL DATABASE PRODUCTS LIST (TOTAL: {total_count}) ===\n")
        f.write(f"Published (Pinterest+Linktree): {status_counts.get('Pinterest_Published', 0)}\n")
        f.write(f"Pending Pin Queue: {status_counts.get('Pending_Pin', 0)}\n\n")
        f.write("CATEGORY BREAKDOWN:\n")
        for cat, c_count in cat_counts:
            f.write(f"  • {cat or 'General'}: {c_count} products\n")
        f.write("\n=================================================================\n\n")
        for idx, r in enumerate(all_rows, start=1):
            f.write(f"{idx:04d}. [ID #{r[0]}] [{r[3]}] {r[1]} | Cat: {r[2]}\n")

    print("═════════════════════════════════════════════════════════════════")
    print(f" 📦 TOTAL PRODUCTS IN AGENT DATABASE: {total_count}")
    print(f" 🌐 Fully Published (Pinterest + Linktree): {status_counts.get('Pinterest_Published', 0)}")
    print(f" ⏳ Pending Pin Queue: {status_counts.get('Pending_Pin', 0)}")
    print("─────────────────────────────────────────────────────────────────")
    print("📊 CATEGORY BREAKDOWN:")
    for cat, c_count in cat_counts[:10]:
        print(f"   • {cat or 'General'}: {c_count} products")
    print(f" 📄 Exported Full List to: {out_file.resolve()}")
    print("═════════════════════════════════════════════════════════════════")

if __name__ == "__main__":
    main()
