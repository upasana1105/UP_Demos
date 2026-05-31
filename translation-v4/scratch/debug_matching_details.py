import fitz

doc_orig = fitz.open("uploads/cancer-treatment1.pdf")
doc_trans = fitz.open("uploads/cancer-treatment1_fr.pdf")

page_orig = doc_orig[0]
page_trans = doc_trans[0]

orig_blocks = page_orig.get_text("dict")["blocks"]
trans_blocks = page_trans.get_text("dict")["blocks"]

for tb_idx, tb in enumerate(trans_blocks):
    if "lines" not in tb:
        continue
    tb_text = "".join(["".join([s["text"] for s in l["spans"]]) for l in tb["lines"]]).strip()
    if "pratique" in tb_text or "reconstruction" in tb_text:
        tb_rect = fitz.Rect(tb["bbox"])
        print(f"\n--- Debugging Translated Block {tb_idx}: '{tb_text}' ---")
        print(f"Translated BBox: {tb['bbox']}")
        
        # Print overlap with all original blocks
        for ob_idx, ob in enumerate(orig_blocks):
            if "lines" not in ob:
                continue
            ob_text = "".join(["".join([s["text"] for s in l["spans"]]) for l in ob["lines"]]).strip()
            ob_rect = fitz.Rect(ob["bbox"])
            overlap = (tb_rect & ob_rect).get_area()
            print(f"  Original Block {ob_idx} | Text: '{ob_text[:40]}' | Overlap Area: {overlap:.1f}")
            
doc_orig.close()
doc_trans.close()
