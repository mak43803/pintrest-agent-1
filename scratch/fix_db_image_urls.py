import sqlite3
import re
from pathlib import Path

def sanitize_url(url: str) -> str:
    if not url or not isinstance(url, str):
        return ""
    url = url.strip()
    if "media-amazon.com" in url or "ssl-images-amazon.com" in url or "images-na.ssl-images-amazon.com" in url:
        url = re.sub(r'\._[A-Z0-9_,-]+_\.', '._AC_SL1500_.', url)
    elif "sephora.com" in url or "sephora.ca" in url or "sephoramedia.com" in url:
        url = re.sub(r'imwidth=\d+', 'imwidth=1500', url)
    elif "ulta.com" in url:
        url = re.sub(r'w=\d+', 'w=1500', url)
        url = re.sub(r'h=\d+', 'h=1500', url)
    return url

db_path = Path("database/pinterest_ai_agent.db")
if db_path.exists():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, source_url FROM products WHERE source_url IS NOT NULL AND source_url != ''")
    rows = cursor.fetchall()
    
    updated_count = 0
    for pid, src in rows:
        upgraded = sanitize_url(src)
        if upgraded != src:
            cursor.execute("UPDATE products SET source_url = ? WHERE id = ?", (upgraded, pid))
            updated_count += 1
            
    conn.commit()
    print(f"Updated {updated_count} product image URLs in database/pinterest_ai_agent.db to 1500x1500 HD master URLs!")
    conn.close()
