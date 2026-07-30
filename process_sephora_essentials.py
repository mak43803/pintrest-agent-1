"""
Process & Audit Sephora A+ Beauty Essentials Batch in Pinterest Agent DB
"""
import sys
import sqlite3
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SEPHORA_PRODUCTS = [
    "Glossier Balm Dotcom Lip Balm and Skin Salve",
    "ONE/SIZE by Patrick Starrr Mini Oil Sucker Liquid Blotting Paper Touch-Up Spray",
    "Summer Fridays Lip Butter Balm Treatment Strawberry Soft Serve",
    "Sincerely Yours Clear Intentions Hydrating and Pore-Clarifying Essential Toner",
    "Salt & Stone Lily & Yuzu Extra-Strength Aluminum-Free Deodorant",
    "Ariana Grande Cloud Aurora Eau de Parfum Travel Spray",
    "OUAI Mini St. Barts Ibiza Santorini Melrose Hair & Body Mist Set",
    "Emi Jay Angel Essentials Hair Styling Gift Set",
    "Tower 28 Beauty SOS Daily Hypochlorous Acid Spray for Breakouts & Redness",
    "REFY Lash Sculpt Lengthen and Lift Natural Looking Mascara",
    "SOFIE PAVITT FACE 3 Step Acne-Safe Clear Skin System with Mandelic Acid",
    "LANEIGE Lip Sleeping Mask Acai Mango Smoothie",
    "rhode Peptide Lip Tint Nourishing Glaze Jelly Bean",
    "Topicals Faded Tranexamic Acid Dark Spot Patches for Hyperpigmentation",
    "KAYALI VANILLA 28 Eau de Parfum Travel Spray",
    "Glossier Glossier You Eau de Parfum Travel Spray",
    "dae Cactus Fruit 3-in-1 Styling Cream with Taming Wand",
    "Saie Glowy Super Gel Lightweight Dewy Multipurpose Illuminator Sunglow",
    "Sol de Janeiro Cheirosa 48 Hair & Body Perfume Mist",
    "Glossier Glossier You Eau de Parfum",
    "KAYALI BOUJEE KITTY CARAMEL MILK 22 Eau de Parfum",
    "SKYLAR Boardwalk Delight Eau de Parfum",
    "Kérastase Gloss Absolu Glaze Drops Anti-Frizz Hair Oil",
    "K18 Biomimetic Hairscience AirWash Dry Shampoo"
]

def main():
    db_path = Path("database/pinterest_ai_agent.db")
    if not db_path.exists():
        db_path = Path("pinterest_ai_agent.db")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT title, product_name, status FROM products")
    db_rows = cursor.fetchall()
    conn.close()

    existing_titles = [f"{r[0] or ''} {r[1] or ''}".lower() for r in db_rows]

    print("═════════════════════════════════════════════════════════════════")
    print(" 🛍️  SEPHORA A+ BEAUTY ESSENTIALS BATCH AUDIT (24 ITEMS)")
    print("═════════════════════════════════════════════════════════════════")

    found_count = 0
    ready_count = 0

    for idx, p_name in enumerate(SEPHORA_PRODUCTS, start=1):
        clean_p = p_name.lower().strip()
        matched = any(clean_p[:15] in et for et in existing_titles)
        if matched:
            found_count += 1
            print(f" [{idx:02d}/24] ✅ Published in DB : {p_name}")
        else:
            ready_count += 1
            print(f" [{idx:02d}/24] 🚀 Queued for Agent: {p_name}")

    print("─────────────────────────────────────────────────────────────────")
    print(f" 📊 Already Published : {found_count} / 24")
    print(f" 🎯 Ready for Pinning  : {ready_count} / 24")
    print("═════════════════════════════════════════════════════════════════")

if __name__ == "__main__":
    main()
