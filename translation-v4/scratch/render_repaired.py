import fitz
import os

pdf_path = "uploads/studyDesignMatrix_fr.pdf"
doc = fitz.open(pdf_path)
page = doc[0]
pix = page.get_pixmap(dpi=150)

output_dir = "/Users/upasanapati/.gemini/jetski/brain/834b4986-f6e7-4426-9aa9-9bffb799f363"
os.makedirs(output_dir, exist_ok=True)

output_path = os.path.join(output_dir, "study_design_matrix_fr_rendered.png")
pix.save(output_path)
doc.close()
print(f"Rendered page 0 to {output_path}")

