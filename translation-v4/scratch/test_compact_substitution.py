import fitz

def inspect_fonts(pdf_path):
    doc = fitz.open(pdf_path)
    page = doc[0]
    print(f"\n--- Font Spans in {pdf_path} ---")
    blocks = page.get_text("dict")["blocks"]
    for b in blocks:
        if "lines" in b:
            for l in b["lines"]:
                for s in l["spans"]:
                    print(f"  Span: '{s['text'].strip()}' | Font: {s['font']} | Size: {s['size']:.1f} | Color: {s['color']}")

inspect_fonts("uploads/5g-edge-computing-value-opportunity.pdf")
inspect_fonts("uploads/5g-edge-computing-value-opportunity_fr.pdf")
