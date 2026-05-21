import io
import pdfplumber
from app.parsers.txt import clean_text

def parse_pdf(file_bytes: bytes) -> str:
    """
    Extracts text from PDF bytes page by page using pdfplumber.
    """
    text_content = []
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text_content.append(page_text)
    except Exception as e:
        raise ValueError(f"Failed to parse PDF document: {str(e)}")

    full_text = "\n\n".join(text_content)
    cleaned = clean_text(full_text)
    
    if not cleaned:
        raise ValueError("PDF does not contain any readable text. It might be scanned or empty.")
    
    return cleaned
