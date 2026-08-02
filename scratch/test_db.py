import sqlite3
import re
import requests
from PIL import Image
from io import BytesIO

db_path = 'database/pinterest_ai_agent.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT product_name, image_path, source_url FROM products WHERE image_path IS NOT NULL AND length(image_path)>5 LIMIT 10")
rows = cursor.fetchall()

for name, img_path, source_url in rows:
    print(f"Product    : {name[:40]}")
    print(f"Image Path : {img_path}")
    print(f"Source URL : {source_url}")
    if img_path.startswith("http"):
        high_res = re.sub(r'\._[A-Z0-9_,-]+_\.', '._AC_SL1500_.', img_path)
        print(f"Upgraded   : {high_res}")
        try:
            r1 = requests.get(img_path, timeout=5)
            im1 = Image.open(BytesIO(r1.content))
            print(f"Original Size : {im1.size[0]}x{im1.size[1]} ({len(r1.content)} bytes)")
            
            r2 = requests.get(high_res, timeout=5)
            im2 = Image.open(BytesIO(r2.content))
            print(f"Upgraded Size : {im2.size[0]}x{im2.size[1]} ({len(r2.content)} bytes)")
        except Exception as e:
            print("Error:", e)
    else:
        # Check local file size & image dimensions
        try:
            im = Image.open(img_path)
            print(f"Local Image Size: {im.size[0]}x{im.size[1]}")
        except Exception as e:
            print("Error loading local file:", e)
    print("-" * 60)
