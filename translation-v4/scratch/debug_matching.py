import fitz

doc_orig = fitz.open("uploads/cancer-treatment1.pdf")
page = doc_orig[0]
blocks = page.get_text("dict")["blocks"]

def get_bbox_center(rect):
    return (rect.x0 + rect.x1) / 2.0, (rect.y0 + rect.y1) / 2.0

print("--- ALL Blocks on Original Page 0 ---")
for b_idx, b in enumerate(blocks):
    if "lines" in b:
        text = "".join(["".join([s["text"] for s in l["spans"]]) for l in b["lines"]]).strip()
        rect = fitz.Rect(b["bbox"])
        center = get_bbox_center(rect)
        print(f"Block {b_idx} | Text: '{text}' | Center: {center} | BBox: {b['bbox']}")
doc_orig.close()
