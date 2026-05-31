import fitz
import os

doc = fitz.open("uploads/0000646.pdf")
output_dir = "/Users/upasanapati/.gemini/jetski/brain/834b4986-f6e7-4426-9aa9-9bffb799f363"
os.makedirs(output_dir, exist_ok=True)

for i in range(len(doc)):
    page = doc[i]
    pix = page.get_pixmap(dpi=150)
    path = os.path.join(output_dir, f"0000646_page{i}.png")
    pix.save(path)
    print(f"Rendered Page {i} to {path}")
doc.close()
