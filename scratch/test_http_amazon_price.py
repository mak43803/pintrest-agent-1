import sys
sys.stdout.reconfigure(encoding="utf-8")
import requests
import re
import urllib.parse

urls = [
    "https://www.amazon.com/dp/B08AESTURA",
    "https://www.amazon.com/dp/B01CFL5A0G",
    "https://www.amazon.com/dp/B08C1KN9K9",
    "https://www.amazon.com/dp/B091B8756Y",
    "https://www.amazon.com/dp/B00V4L3J8U"
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Upgrade-Insecure-Requests": "1"
}

session = requests.Session()

for url in urls:
    print(f"\n--- Testing {url} ---")
    resp = session.get(url, headers=headers, timeout=10)
    print("Status:", resp.status_code)
    html = resp.text
    
    # 1. Title
    title = ""
    m_title = re.search(r'<span id="productTitle"[^>]*>(.*?)</span>', html, re.DOTALL)
    if m_title:
        title = m_title.group(1).strip()
    print("  Title:", title[:50])
    
    # 2. Price
    price = ""
    # Check priceToPay or main price span
    m_price = re.search(r'class="a-price aok-align-center[^"]*"[^>]*>.*?<span class="a-offscreen">\s*\$([0-9\.]+)', html, re.DOTALL)
    if not m_price:
        m_price = re.search(r'class="priceToPay"[^>]*>.*?<span class="a-offscreen">\s*\$([0-9\.]+)', html, re.DOTALL)
    if not m_price:
        m_price = re.search(r'class="a-offscreen">\s*\$([0-9\.]+)', html)
    if not m_price:
        m_w = re.search(r'class="a-price-whole"[^>]*>(\d+)', html)
        m_f = re.search(r'class="a-price-fraction"[^>]*>(\d+)', html)
        if m_w:
            frac = m_f.group(1) if m_f else "00"
            price = f"${m_w.group(1)}.{frac}"
    else:
        price = f"${m_price.group(1)}"
        
    print("  Price:", price)
    
    # 3. Rating & Reviews
    m_rat = re.search(r'([0-9\.]+)\s*out of 5 stars', html)
    rating = m_rat.group(1) if m_rat else "N/A"
    m_rev = re.search(r'id="acrCustomerReviewText"[^>]*>([0-9,]+)\s*ratings', html)
    reviews = m_rev.group(1) if m_rev else "N/A"
    print(f"  Rating: {rating}★ ({reviews} reviews)")

