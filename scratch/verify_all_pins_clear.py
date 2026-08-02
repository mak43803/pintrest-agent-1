import sys
sys.path.append('.')
import sqlite3
from PIL import Image
from tools.image_tools import ImageTools

conn = sqlite3.connect('database/pinterest_ai_agent.db')
cursor = conn.cursor()
cursor.execute("SELECT id, product_name, title, image_path, price FROM products ORDER BY id DESC LIMIT 3")
rows = cursor.fetchall()

print("--- TESTING PIN GENERATION ON LATEST 3 DATABASE PRODUCTS ---")
for r in rows:
    p_id, p_name, p_title, p_img, p_price = r
    print(f"\nProduct #{p_id}: {p_name[:30]}")
    print(f"Source Image: {p_img}")
    
    # Download high res
    try:
        raw_path = ImageTools.download_image(p_img)
        print(f"Downloaded high-res image: {raw_path}")
        
        # Generate pin
        pin_path = ImageTools.create_pinterest_pin(
            raw_path,
            title_text=p_title or p_name,
            badge_text="VIRAL FIND",
            cta_text="Shop Now →",
            pin_index=p_id,
            rating_text="4.8★ (15K+ REVIEWS)",
            price_text=p_price or "$24.00"
        )
        print(f"Generated Pin: {pin_path}")
        with Image.open(pin_path) as im:
            print(f"Pin Dimensions: {im.size} OK")
    except Exception as e:
        print(f"Error on #{p_id}: {e}")
