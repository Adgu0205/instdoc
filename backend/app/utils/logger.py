import logging
import json
import time
from typing import Dict, Any

# Route all logs through uvicorn.error so they are piped to stdout/stderr in production
logger = logging.getLogger("uvicorn.error")

def log_event(event_type: str, data: Dict[str, Any]):
    """
    Core logging function. Filters out raw text and formats as clean JSON.
    """
    # Guard to prevent logging any contract contents or large inputs
    forbidden_keys = {"text", "content", "file_bytes", "raw_text", "file_bytes_base64"}
    filtered_data = {
        k: v for k, v in data.items() 
        if k.lower() not in forbidden_keys and not isinstance(v, (bytes, bytearray))
    }
    
    payload = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "event": event_type,
        "details": filtered_data
    }
    
    # Write structured JSON log to stdout/stderr
    logger.info(f"[STRUCTURED_LOG] {json.dumps(payload)}")

def log_upload(filename: str, mime_type: str, size_bytes: int):
    """
    Logs metadata about file uploads.
    """
    log_event("file_uploaded", {
        "filename": filename,
        "mime_type": mime_type,
        "size_bytes": size_bytes
    })

def log_parsing_failure(filename: str, error_msg: str):
    """
    Logs failure to parse a PDF, Word, or Text document.
    """
    log_event("parsing_failed", {
        "filename": filename,
        "error": error_msg
    })

def log_ai_failure(error_msg: str, duration_sec: float):
    """
    Logs Gemini API errors and fallbacks.
    """
    log_event("ai_analysis_failed", {
        "error": error_msg,
        "duration_seconds": round(duration_sec, 3)
    })

def log_api_error(endpoint: str, status_code: int, detail: str):
    """
    Logs client or server errors returned by routes.
    """
    log_event("api_error", {
        "endpoint": endpoint,
        "status_code": status_code,
        "detail": detail
    })

def log_processing_time(stage: str, duration_sec: float, extra: Dict[str, Any] = None):
    """
    Logs processing time taken by various pipelines.
    """
    details = {
        "stage": stage,
        "duration_seconds": round(duration_sec, 3)
    }
    if extra:
        details.update(extra)
    log_event("processing_time", details)
