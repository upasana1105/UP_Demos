import fitz

def inspect_pdf_images():
    doc = fitz.open("uploads/5g-edge-computing-value-opportunity.pdf")
    for page_num in range(len(doc)):
        page = doc[page_num]
        images = page.get_images(full=True)
        print(f"--- Page {page_num} ---")
        print(f"Found {len(images)} images.")
        for idx, img in enumerate(images):
            xref = img[0]
            width = img[2]
            height = img[3]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            ext = base_image["ext"]
            print(f"  Image {idx}: xref={xref}, width={width}, height={height}, ext={ext}, size={len(image_bytes)} bytes")

if __name__ == "__main__":
    inspect_pdf_images()
