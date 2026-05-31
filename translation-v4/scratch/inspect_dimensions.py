import fitz

doc_orig = fitz.open("uploads/studyDesignMatrix.pdf")
doc_trans = fitz.open("uploads/studyDesignMatrix_fr.pdf")

page_orig = doc_orig[0]
page_trans = doc_trans[0]

tables = page_orig.find_tables()
t = tables.tables[0]

print("Extracted and re-assembled cell texts from translated PDF:")
for r_idx, row in enumerate(t.rows):
    if r_idx == 0:
        continue
    print(f"\nRow {r_idx}:")
    for c_idx, cell in enumerate(row.cells):
        if cell is None:
            print(f"  Cell {c_idx}: [Spanned]")
            continue
        
        cell_rect = fitz.Rect(cell)
        # Shrink slightly for clean extraction
        extraction_rect = fitz.Rect(cell_rect.x0 + 2, cell_rect.y0 + 2, cell_rect.x1 - 2, cell_rect.y1 - 2)
        words = page_trans.get_text("words", clip=extraction_rect)
        words.sort(key=lambda x: (x[1], x[0]))
        cell_text = " ".join([w[4] for w in words])
        cell_text = " ".join(cell_text.split())
        print(f"  Cell {c_idx} Text: '{cell_text}'")

doc_orig.close()
doc_trans.close()









