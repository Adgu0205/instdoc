import os
from fastapi import HTTPException, UploadFile

# Maximum file size allowed: 5MB
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024

# Allowed extensions and MIME types
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}
SUPPORTED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain"
}

def validate_file_metadata(filename: str, content_type: str = None):
    """
    Validates file extension and content type metadata.
    """
    ext = os.path.splitext(filename.lower())[1]
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Only .pdf, .docx, and .txt files are supported."
        )
        
    if content_type and content_type not in SUPPORTED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file content type '{content_type}'. Must be PDF, Word (DOCX), or plain text."
        )

async def read_and_validate_file_size(file: UploadFile) -> bytes:
    """
    Reads file content bytes and enforces the maximum size limit.
    """
    # Read the file in memory
    content = await file.read()
    file_size = len(content)
    
    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File '{file.filename}' is too large ({file_size / (1024 * 1024):.2f}MB). The maximum allowed size is 5.00MB."
        )
        
    return content
