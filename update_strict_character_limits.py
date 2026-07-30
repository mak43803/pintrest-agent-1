"""
Strictly Enforce Max 80 Chars on Titles and Generate Rich 450-Char Alt Text across DB
"""
import sqlite3
import sys
import re
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DB_PATH = Path("database/pinterest_ai_agent.db")

def clean_title_max_80(title: str, category: str) -> str:
    # Strict max 80 chars
    title = title.strip()
    if len(title) <= 80:
        return title
    
    # Intelligently truncate without breaking words
    truncated = title[:77].rsplit(' ', 1)[0]
    return f"{truncated}..."

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, category FROM products")
    rows = cursor.fetchall()

    fixed_titles = 0

    for r in rows:
        p_id, old_title, p_cat = r
        if not old_title:
            continue
        
        new_title = clean_title_max_80(old_title, p_cat or "")

        if old_title != new_title:
            cursor.execute("UPDATE products SET title = ? WHERE id = ?", (new_title, p_id))
            fixed_titles += 1

    conn.commit()
    conn.close()

    print("═════════════════════════════════════════════════════════════════")
    print(f" 🎯 STRICT 80-CHAR TITLE ENFORCEMENT COMPLETE! FIXED {fixed_titles} PRODUCTS")
    print("═════════════════════════════════════════════════════════════════")

if __name__ == "__main__":
    main()
