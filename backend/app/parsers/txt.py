import re

def clean_text(text: str) -> str:
    """
    Normalizes spacing, removes control characters, and cleans up extra whitespace.
    """
    if not text:
        return ""
    # Normalize carriage returns and line feeds
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Replace non-breaking spaces and tabs with regular spaces
    text = re.sub(r"[ \t]+", " ", text)
    # Reduce consecutive newlines to maximum of 2 (preserves paragraph breaks)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Strip leading/trailing spaces on each line
    lines = [line.strip() for line in text.split("\n")]
    return "\n".join(lines).strip()

def parse_txt(file_bytes: bytes) -> str:
    """
    Safely decodes and cleans plain text files.
    """
    try:
        text = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = file_bytes.decode("latin-1")
        except Exception as e:
            raise ValueError(f"Failed to decode text file. Ensure it is UTF-8 or Latin-1 encoded: {str(e)}")
    
    return clean_text(text)
