import fitz

pdf_path = "uploads/cancer-treatment1.pdf"
doc = fitz.open(pdf_path)
page = doc[0]
blocks = page.get_text("dict")["blocks"]

print("--- Scanning ALL text blocks on Original Page 0 ---")
for b_idx, b in enumerate(blocks):
    if "lines" in b:
        text = "".join(["".join([s["text"] for s in l["spans"]]) for l in b["lines"]]).strip()
        sizes = [s["size"] for l in b["lines"] for s in l["spans"]]
        fonts = [s["font"] for l in b["lines"] for s in l["spans"]]
        if "GP" in text or "surgeon" in text or "professionals" in text:
            print(f"Block {b_idx} | Text: '{text}'")
            print(f"  Sizes: {sizes}")
            print(f"  Fonts: {fonts}")
            print(f"  BBox: {b['bbox']}")
doc.close()
