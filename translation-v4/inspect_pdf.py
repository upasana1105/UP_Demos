import sys
import os
import fitz

pdf_path = '/Users/upasanapati/shrinkAI experiment/Antigravity_Experiments/UP_Demos/translation-v3/uploads/5g-edge-computing-value-opportunity.pdf'

doc = fitz.open(pdf_path)

for page_num in range(len(doc)):
    page = doc[page_num]
    print(f"--- Page {page_num} ---")
    images = page.get_images(full=True)
    print(f"Images found: {len(images)}")
    for img in images:
        print(f"  XREF: {img[0]}, Width: {img[2]}, Height: {img[3]}")
        
    drawings = page.get_drawings()
    print(f"Vector drawings: {len(drawings)}")
    if drawings:
        bbox = fitz.Rect()
        for d in drawings:
            bbox.include_rect(d['rect'])
        print(f"  Combined drawings bbox: {bbox}")
