from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(80)
        self.cell(30, 10, 'Technical Document Translation Test', 0, 0, 'C')
        self.ln(20)

    def chapter_title(self, label):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 6, label, 0, 1, 'L', 1)
        self.ln(4)

    def chapter_body(self, text):
        self.set_font('Times', '', 12)
        self.multi_cell(0, 5, text)
        self.ln()

def create_test_pdf(filename):
    pdf = PDF()
    pdf.add_page()
    
    pdf.chapter_title('1. Fiscal Year 2025 Executive Summary')
    pdf.chapter_body("This consolidated financial report provides an overview of the company's financial health "
                     "for the 2025 Fiscal Year. It highlights our Consolidated Revenue and operational efficiencies.")
    
    pdf.chapter_title('2. Income Statement Highlights')
    pdf.chapter_body('The following table summarizes the key performance indicators, including EBITDA '
                     'and Gross Profit Margin. These metrics are critical for evaluating our operational profitability.')

    # Table Header
    pdf.set_font('Arial', 'B', 9)
    pdf.set_fill_color(180, 200, 230)
    pdf.cell(40, 7, 'Metric', 1, 0, 'C', 1)
    pdf.cell(50, 7, 'Q1 2023 (USD)', 1, 0, 'C', 1)
    pdf.cell(50, 7, 'Q1 2024 (USD)', 1, 0, 'C', 1)
    pdf.cell(30, 7, 'YoY Growth', 1, 1, 'C', 1)

    # Table Rows
    pdf.set_font('Arial', '', 9)
    data = [
        ('Total Revenue', '$1,200,000', '$1,450,000', '20.8%'),
        ('Net Income', '$300,000', '$380,000', '26.7%'),
        ('EBITDA', '$450,000', '$520,000', '15.5%'),
        ('Operating Margin', '25%', '26.2%', '+120 bps')
    ]
    
    for metric, q1_23, q1_24, yoy in data:
        pdf.cell(40, 6, metric, 1)
        pdf.cell(50, 6, q1_23, 1)
        pdf.cell(50, 6, q1_24, 1)
        pdf.cell(30, 6, yoy, 1)
        pdf.ln()


    pdf.ln(5)
    pdf.chapter_title('3. Balance Sheet Summary')
    pdf.chapter_body('Our Balance Sheet remains strong with a healthy liquidity ratio and robust asset coverage.')

    # Balance Sheet Table
    pdf.set_font('Arial', 'B', 10)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(50, 7, 'Category', 1, 0, 'C', 1)
    pdf.cell(90, 7, 'Amount (in Millions USD)', 1, 1, 'C', 1)
    
    pdf.set_font('Arial', '', 10)
    bs_data = [
        ('Total Assets', ' $3,100.0'),
        ('Total Liabilities', '$1,450.0'),
        ('Shareholder Equity', '$1,650.0')
    ]
    for cat, amt in bs_data:
        pdf.cell(50, 6, cat, 1)
        pdf.cell(90, 6, amt, 1)
        pdf.ln()

    pdf.ln(10)
    pdf.set_font('Arial', 'I', 10)
    pdf.cell(0, 10, 'Internal Use Only - Confidential Financial Data.', 0, 1, 'C')
    
    pdf.output(filename)
    print(f"Generated Financial test PDF: {filename}")


if __name__ == "__main__":
    create_test_pdf('UP_Demos/translation/sample_doc.pdf')
