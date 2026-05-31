import os
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
except ImportError:
    import subprocess
    subprocess.check_call(['pip', 'install', 'reportlab'])
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet

os.makedirs('UP_Demos/translation/uploads', exist_ok=True)

# 1. Generate Overlap Test PDF
c = canvas.Canvas('UP_Demos/translation/uploads/layout_overlap_test.pdf', pagesize=letter)
c.setFont("Helvetica", 14)
c.drawString(100, 700, "The strict adherence to EBITDA targets is a critical GAAP requirement.")
c.setFont("Helvetica-Bold", 14)
c.setFillColorRGB(1, 0, 0, alpha=0.5) # Translucent red for visible overlap
c.drawString(100, 700, "OVERLAPPING TEXT: THIS REGION HAS SEVERE BOUNDARY COLLISION ON ROI METRICS.")
c.setFillColorRGB(0, 0, 0)
c.drawString(100, 680, "Compliance with GDPR regulations is mandated by BlackRock.")
c.drawString(10, 800, "[MARGIN SPILL] This text deliberately violates the top page boundary constraints.")
c.drawString(500, 10, "[MARGIN SPILL] Goldman Sachs quarterly report footnote that runs off the page edge.")
c.save()
print("Created: UP_Demos/translation/uploads/layout_overlap_test.pdf")

# 2. Generate Spillage Test PDF (Multi-page table with overflowing text)
styles = getSampleStyleSheet()
data = [["Metric ID", "Financial Entity", "Compliance & Reporting Notes"]]
for i in range(1, 45): # Enough rows to force a page break
    note = "The EBITDA structure must align with GAAP standards. BlackRock and Goldman Sachs consistently monitor ROI KPIs. "
    # Intentional long unbroken text to test cell spillage if renderer breaks
    spill_text = note * 2 + "VERY_LONG_UNBROKEN_STRING_TO_FORCE_CELL_OVERFLOW_AND_TEST_LAYOUT_PRESERVATION_ENGINE_CAPABILITIES_" * 2
    data.append([f"IDX-{i:03d}", f"Entity {i}", Paragraph(spill_text, styles['Normal'])])

doc = SimpleDocTemplate("UP_Demos/translation/uploads/layout_spillage_test.pdf", pagesize=letter)
t = Table(data, colWidths=[60, 100, 380])
t.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
    ('GRID', (0, 0), (-1, -1), 1, colors.black)
]))

doc.build([t])
print("Created: UP_Demos/translation/uploads/layout_spillage_test.pdf")
