import os
from fastapi import HTTPException, UploadFile

# Maximum file size allowed: 5MB
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
# Maximum text size allowed: 1,000,000 characters
MAX_TEXT_SIZE_CHARS = 1000000

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

def verify_file_signature(filename: str, content: bytes):
    """
    Verifies the file content matches its expected signature (magic numbers) to prevent extension spoofing.
    """
    ext = os.path.splitext(filename.lower())[1]
    if ext == ".pdf":
        if not content.startswith(b"%PDF"):
            raise HTTPException(
                status_code=400,
                detail="MIME verification failed: File contents do not match PDF signature."
            )
    elif ext == ".docx":
        # DOCX files are standard zip files
        if not content.startswith(b"PK\x03\x04"):
            raise HTTPException(
                status_code=400,
                detail="MIME verification failed: File contents do not match DOCX signature."
            )
    elif ext == ".txt":
        # Check for binary characters (null bytes)
        if b"\x00" in content:
            raise HTTPException(
                status_code=400,
                detail="MIME verification failed: Text file contains binary/null character data."
            )

async def read_and_validate_file_size(file: UploadFile) -> bytes:
    """
    Reads file content bytes, enforces the maximum size limit, and verifies signatures.
    """
    # Read the file in memory
    content = await file.read()
    file_size = len(content)
    
    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File '{file.filename}' is too large ({file_size / (1024 * 1024):.2f}MB). The maximum allowed size is 5.00MB."
        )
    
    # Run signature validation
    verify_file_signature(file.filename, content)
        
    return content

def validate_text_size(text: str):
    """
    Enforces size limits on copy-pasted raw contract text.
    """
    if len(text) > MAX_TEXT_SIZE_CHARS:
        raise HTTPException(
            status_code=413,
            detail=f"The provided text is too large ({len(text):,} characters). The maximum allowed limit is {MAX_TEXT_SIZE_CHARS:,} characters."
        )
