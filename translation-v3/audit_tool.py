import PyPDF2
from typing import Dict

def get_pdf_text(file_path: str) -> str:
    """Extracts all text from a PDF file.

    Args:
        file_path: Absolute path to the PDF file.
    """
    text = ""
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        return f"Error extracting text: {str(e)}"
    
    return text.strip()

if __name__ == "__main__":
    # Test with a sample file if needed
    import sys
    if len(sys.argv) > 1:
        print(get_pdf_text(sys.argv[1]))
