import sys
import os
import fitz

pdf_path = '/Users/upasanapati/shrinkAI experiment/Antigravity_Experiments/UP_Demos/translation-v3/uploads/5g-edge-computing-value-opportunity.pdf'

doc = fitz.open(pdf_path)

page = doc[0]
img_info = page.get_image_info(hashes=True)
print(f"Page 0 image info: {len(img_info)} items")
for info in img_info:
    print(f"Keys: {info.keys()}")
    print(f"Full info: {info}")
