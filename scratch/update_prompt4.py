import sys

file_path = r"c:\Users\mazzu\OneDrive\Desktop\pintrest ai agent\browser\gemini_web_client.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

start_idx = content.find('    async def generate_image_and_seo(')
end_idx = content.find('        response_text = await self._send_prompt(prompt, image_path=image_path)')
if start_idx == -1 or end_idx == -1:
    print("Could not find generate_image_and_seo boundaries")
    sys.exit(1)

new_method_start = '''    async def generate_image_and_seo(self, product_title: str, product_desc: str, image_path: str | None = None) -> tuple[str | None, PinterestSEOData]:
        """
        Ask Gemini to generate an aesthetic Pinterest image of the product AND the SEO text in one prompt.
        Requires the user to be logged in to Google.
        Returns:
         Tuple of (downloaded_image_url, PinterestSEOData).
        """
        allowed_boards = [
            "Affordable Skincare Finds", "Luxury Beauty", "Sensitive Skin Essentials", 
            "Body Wash Favorites", "Anti Aging Products", "K Beauty", "Amazon Beauty Finds", 
            "Hair Care Essentials", "Self Care Products", "Makeup Favorites", "Body Care", 
            "Face Serums", "Face Wash", "Moisturizers", "Lip Care", "Beauty Tools"
        ]
        prompt = f"""
###############################################################
CONTINUE AFTER PINTEREST PRODUCT RESEARCH
###############################################################

After selecting ONE trending beauty product from Pinterest Shopping Trends,
copy the Product Name.
Do not copy anything else.
Immediately continue with the following workflow.

###############################################################
STEP 1 - AMAZON PRODUCT SEARCH
###############################################################

Open: https://www.amazon.com
Search using the exact Product Name copied from Pinterest.
Wait until the search results are fully loaded.
Find the exact or closest matching product.
Open the product page.
Save:
• Product Name
• Brand
• Product Category
• Product URL
• Product Images

###############################################################
STEP 2 - DOWNLOAD PRODUCT IMAGE
###############################################################

Use the main product image as the visual reference.
Save the product image for AI content generation.

###############################################################
STEP 3 - GENERATE AMAZON AFFILIATE LINK
###############################################################

Generate the Amazon Affiliate Link for the selected product.
Verify the affiliate link works correctly.
Save the affiliate link for the Pinterest Pin.

###############################################################
STEP 4 - GEMINI AI
###############################################################

Open Gemini.
Upload the Amazon product image.
Use the uploaded image as the reference.
Generate ONE premium Pinterest-style marketing image.

Requirements:
• Luxury aesthetic
• Clean design
• Premium beauty branding
• Pinterest optimized
• Vertical 2:3 ratio
• Bright lighting
• High quality
• Attractive for women
• Product must remain realistic
• Modern lifestyle look
• No watermark
• No logo overlap
• No copyright text

###############################################################
STEP 5 - PINTEREST SEO
###############################################################

Using the selected product,
Generate:
1. Pinterest SEO Title
2. Pinterest SEO Description
3. Pinterest SEO Keywords
4. Pinterest Hashtags
5. Pinterest Alt Text

The Alt Text should be detailed (up to approximately 500 characters if supported by the platform) and accurately describe the image for accessibility and search relevance.

###############################################################
STEP 6 - LANGUAGE
###############################################################

Use ONLY: American English
Never use: British English, Indian English, Mixed English
All writing should sound natural to women living in the United States.

###############################################################
STEP 7 - TARGET AUDIENCE
###############################################################

Optimize the content for: Women in the United States
Age: 18-55
Beauty Interests:
• Skincare
• Makeup
• Hair Care
• Body Care
• Self Care
• K-Beauty
• Clean Beauty
• Luxury Beauty
• Drugstore Beauty
• Anti-Aging
• Beauty Trends

Write naturally for this audience. Do not attempt to manipulate or guarantee who will see the content; focus on high-quality, relevant, U.S.-oriented language and SEO.

###############################################################
STEP 8
###############################################################

After all assets are generated,
Continue with the remaining Pinterest publishing workflow exactly as previously instructed.
Do not modify any remaining workflow steps.
Only continue using the generated:
• AI Image
• SEO Title
• Description
• Keywords
• Hashtags
• Alt Text
• Amazon Affiliate Link

---------------------------------------------------------------
OUTPUT REQUIREMENTS FOR AUTOMATION SCRIPT
---------------------------------------------------------------
The product we are processing is: {product_title}
Product Details: {product_desc}

Based on the instructions above, please generate the final SEO details and select the best matching board from this list: {", ".join(allowed_boards)}.

Return ONLY a valid JSON object in the following format, with no markdown or extra text:
{{
    "title": "Optimized Pin Title",
    "description": "Engaging description with hashtags.",
    "alt_text": "Detailed alt text for visually impaired users.",
    "tags": "comma, separated, keywords",
    "board": "The Best Matching Board Name"
}}
"""
'''

new_content = content[:start_idx] + new_method_start + content[end_idx:]

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Updated generate_image_and_seo prompt!")
