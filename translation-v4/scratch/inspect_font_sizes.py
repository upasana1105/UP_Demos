import fitz

pdf_path = "uploads/cancer-treatment1_fr.pdf"
doc = fitz.open(pdf_path)
for page_num in range(len(doc)):
    page = doc[page_num]
    print(f"--- Page {page_num} ---")
    blocks = page.get_text("dict")["blocks"]
    for b_idx, b in enumerate(blocks):
        if "lines" in b:
            text = "".join(["".join([s["text"] for s in l["spans"]]) for l in b["lines"]]).strip()
            sizes = []
            fonts = []
            for l in b["lines"]:
                for s in l["spans"]:
                    sizes.append(s["size"])
                    fonts.append(s["font"])
            print(f"Block {b_idx} | Text: '{text[:60]}' | Sizes: {sizes} | Fonts: {fonts} | BBox: {b['bbox']}")
doc.close()
