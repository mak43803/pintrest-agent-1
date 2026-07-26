with open(".env", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, val = line.split("=", 1)
            if "OLLAMA" in key:
                print(f"{key.strip()} = {val.strip()}")
