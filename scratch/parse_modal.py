with open("scratch/after_search.html", "r", encoding="utf-8") as f:
    content = f.read()

import re

# Let's search for "Cleverfy" in the file
match = re.search(r"Cleverfy", content)
if match:
    idx = match.start()
    print("=== HTML around Cleverfy ===")
    print(content[max(0, idx-400):idx+400])
else:
    print("Could not find Cleverfy in HTML.")

# Let's also print all elements with role="dialog" or class containing dialog
dialog_matches = [m.start() for m in re.finditer(r"<div[^>]*\bdialog\b[^>]*>", content, re.IGNORECASE)]
if not dialog_matches:
    dialog_matches = [m.start() for m in re.finditer(r"Add a Linked product", content)]

for idx in dialog_matches[:3]:
    print("\n=== Dialog HTML snippet ===")
    print(content[idx:idx+800])
