import io
import logging
import pdfplumber
from app.parsers.txt import clean_text

logger = logging.getLogger("uvicorn.error")

def parse_pdf_ocr(file_bytes: bytes) -> str:
    """
    Falls back to OCR extraction using pypdfium2 and pytesseract.
    Runs entirely in memory.
    """
    import pypdfium2 as pdfium
    import pytesseract
    
    logger.info("Initializing OCR fallback processing for scanned or image-based PDF.")
    
    text_pages = []
    try:
        pdf = pdfium.PdfDocument(file_bytes)
        for i, page in enumerate(pdf):
            # Render page to bitmap at 150 DPI (scale=2) for better OCR accuracy
            bitmap = page.render(scale=2)
            pil_img = bitmap.to_pil()
            ocr_text = pytesseract.image_to_string(pil_img)
            if ocr_text.strip():
                text_pages.append(ocr_text)
    except Exception as e:
        logger.error(f"In-memory OCR extraction failed: {str(e)}")
        raise ValueError(f"OCR extraction failed: {str(e)}")
        
    full_text = "\n\n".join(text_pages)
    return clean_text(full_text)

def parse_pdf(file_bytes: bytes) -> str:
    """
    Extracts text from PDF bytes page by page using pdfplumber.
    Falls back to OCR if little or no text is extracted.
    """
    text_content = []
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text_content.append(page_text)
    except Exception as e:
        raise ValueError(f"Failed to parse PDF document structure: {str(e)}")

    full_text = "\n\n".join(text_content)
    cleaned = clean_text(full_text)
    
    # If the text is empty or less than 150 characters, trigger OCR fallback
    if len(cleaned) < 150:
        logger.info(f"Extracted text too short ({len(cleaned)} chars). Triggering OCR fallback...")
        try:
            cleaned = parse_pdf_ocr(file_bytes)
        except Exception as ocr_err:
            raise ValueError(f"Standard parser returned little text, and OCR fallback failed: {str(ocr_err)}")
            
    if not cleaned:
        raise ValueError("PDF does not contain any readable text. It might be scanned, password-protected, or empty.")
    
    return cleaned
