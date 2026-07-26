from html.parser import HTMLParser

class SimpleHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_button = False
        self.button_attrs = []
        self.button_text = ""
        self.headings = []
        self.in_heading = False
        self.current_heading_tag = ""
        self.heading_text = ""
        self.interest_texts = []
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "button":
            self.in_button = True
            self.button_attrs = attrs_dict
            self.button_text = ""
        elif tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            self.in_heading = True
            self.current_heading_tag = tag
            self.heading_text = ""
            
    def handle_endtag(self, tag):
        if tag == "button" and self.in_button:
            print(f"[button]: '{self.button_text.strip()}' | attrs: {self.button_attrs}")
            self.in_button = False
        elif tag in ["h1", "h2", "h3", "h4", "h5", "h6"] and self.in_heading:
            print(f"[{self.current_heading_tag}]: '{self.heading_text.strip()}'")
            self.in_heading = False
            
    def handle_data(self, data):
        clean_data = data.strip()
        if not clean_data:
            return
            
        if self.in_button:
            self.button_text += " " + clean_data
        elif self.in_heading:
            self.heading_text += " " + clean_data
            
        if any(k in clean_data.lower() for k in ["collection", "body care", "hair", "skin", "makeup"]):
            self.interest_texts.append(clean_data)

def main():
    with open("scratch/manage_tab.html", "r", encoding="utf-8") as f:
        html = f.read()
        
    parser = SimpleHTMLParser()
    
    print("=== PARSING HEADINGS AND BUTTONS ===")
    parser.feed(html)
    
    print("\n=== DUMPING TEXT CONTAINING KEYWORDS ===")
    for text in parser.interest_texts:
        print(f"Match: '{text}'")

if __name__ == "__main__":
    main()
