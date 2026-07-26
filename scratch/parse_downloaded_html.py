import re

filepath = r"C:\Users\mazzu\.gemini\antigravity-ide\brain\885ff94b-5557-497b-84a6-68618c5c26a5\.system_generated\steps\2039\content.md"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Let's find all img tags and extract their src and alt attributes
img_tags = re.findall(r'<img[^>]+>', content)

print(f"Found {len(img_tags)} image tags in the page HTML:")
for idx, tag in enumerate(img_tags):
    # Extract alt attribute
    alt_match = re.search(r'alt="([^"]*)"', tag)
    alt = alt_match.group(1) if alt_match else "No alt attribute"
    
    # Extract src attribute
    src_match = re.search(r'src="([^"]*)"', tag)
    src = src_match.group(1) if src_match else "No src"
    
    # We are interested in images that have non-empty alt tags
    if alt_match or "pin" in src:
        print(f"  Img [{idx}]:")
        print(f"    src: {src[:100]}")
        print(f"    alt: '{alt}'")
        print("-" * 50)
