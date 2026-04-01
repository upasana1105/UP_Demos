from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_micro_test_pdf(filename, text):
    c = canvas.Canvas(filename, pagesize=letter)
    c.setFont("Helvetica", 12)
    c.drawString(100, 700, text)
    c.save()

if __name__ == "__main__":
    create_micro_test_pdf("micro_test.pdf", "The business case for 5G is far stronger in B2B than in B2C, with US$4.3 trillion of upside identified.")
    print("micro_test.pdf created.")
