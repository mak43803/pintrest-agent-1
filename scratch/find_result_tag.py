with open("scratch/after_search.html", "r", encoding="utf-8") as f:
    content = f.read()

idx = 474614

# Let's print 2000 characters before idx to see the container tags
print("=== HTML BEFORE IMAGE ===")
print(content[idx-1000:idx])
