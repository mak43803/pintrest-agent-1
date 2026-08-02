import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath("."))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from browser.amazon_client import AmazonClient
from browser.browser_manager import BrowserManager

async def test_image_filter():
    print("=== Testing Amazon Product Image Filter ===")
    
    # Test valid vs invalid image URLs
    valid_url = "https://m.media-amazon.com/images/I/61ZQlTnCUbL._AC_SL1500_.jpg"
    prime_url = "https://m.media-amazon.com/images/G/01/prime/prime_logo.png"
    banner_url = "https://m.media-amazon.com/images/G/01/digital/video/avd_banner.png"
    
    print("Valid Product Image:", AmazonClient.is_valid_product_image_url(valid_url))
    print("Prime Logo Image:", AmazonClient.is_valid_product_image_url(prime_url))
    print("Banner Image:", AmazonClient.is_valid_product_image_url(banner_url))
    
    assert AmazonClient.is_valid_product_image_url(valid_url) == True
    assert AmazonClient.is_valid_product_image_url(prime_url) == False
    assert AmazonClient.is_valid_product_image_url(banner_url) == False
    
    print("✅ Image URL filter validation passed!")

if __name__ == "__main__":
    asyncio.run(test_image_filter())
