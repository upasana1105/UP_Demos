import fitz

pdf_path = "uploads/cancer-treatment1_fr.pdf"
doc = fitz.open(pdf_path)
page = doc[0] # Page 0
blocks = page.get_text("dict")["blocks"]

print("--- Scanning ALL text blocks on Page 0 ---")
for b_idx, b in enumerate(blocks):
    if "lines" in b:
        text = "".join(["".join([s["text"] for s in l["spans"]]) for l in b["lines"]]).strip()
        sizes = [s["size"] for l in b["lines"] for s in l["spans"]]
        fonts = [s["font"] for l in b["lines"] for s in l["spans"]]
        # If size is tiny, or contains GP/médecin
        if any(size < 8.0 for size in sizes) or "GP" in text or "médecin" in text or "généraliste" in text:
            print(f"Block {b_idx} | Text: '{text}'")
            print(f"  Sizes: {sizes}")
            print(f"  Fonts: {fonts}")
            print(f"  BBox: {b['bbox']}")
doc.close()
