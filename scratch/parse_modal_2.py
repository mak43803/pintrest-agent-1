with open("scratch/after_search.html", "r", encoding="utf-8") as f:
    content = f.read()

import re
matches = [m.start() for m in re.finditer(r"Cleverfy", content)]
print(f"Total matches found: {len(matches)}")
for i, idx in enumerate(matches):
    print(f"\nMatch [{i}] around index {idx}:")
    print(content[max(0, idx-200):idx+300])
