import os
import io
import time
import json
import logging
import asyncio
from typing import Dict, Any, Union, Optional
from fastapi import APIRouter, File, UploadFile, HTTPException, Request, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse

from app.schemas.analysis import TextAnalysisRequest, AnalysisResponse, TaskStatusResponse
from app.middleware.security import validate_file_metadata, read_and_validate_file_size, validate_text_size
from app.parsers.txt import parse_txt
from app.parsers.pdf import parse_pdf
from app.parsers.docx import parse_docx
from app.services.risk_engine import run_hybrid_risk_engine
from app.services.gemini_service import analyze_contract_with_gemini

from app.utils.limiter import limiter
from app.services.task_manager import create_task, tasks
from app.services.analytics_service import record_analysis, get_analytics
from app.utils.logger import (
    log_upload, log_parsing_failure, log_processing_time, log_api_error
)

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/api/analyze", tags=["Analysis"])

# Configurable constants
LARGE_CONTRACT_THRESHOLD_CHARS = int(os.getenv("LARGE_CONTRACT_THRESHOLD_CHARS", "25000"))
RATE_LIMIT_ANALYSIS = os.getenv("RATE_LIMIT_ANALYSIS", "10/minute")

def extract_text_from_file_bytes(filename: str, file_bytes: bytes) -> str:
    """
    Selects the correct parser based on file extension and returns cleaned text.
    """
    ext = os.path.splitext(filename.lower())[1]
    
    if ext == ".txt":
        return parse_txt(file_bytes)
    elif ext == ".pdf":
        return parse_pdf(file_bytes)
    elif ext == ".docx":
        return parse_docx(file_bytes)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported extension '{ext}'. Only .pdf, .docx, and .txt files are supported."
        )

# Background Task Execution Pipelines
async def run_file_analysis_pipeline(task_id: str, filename: str, file_bytes: bytes, gemini_key: Optional[str] = None):
    task = tasks[task_id]
    start_time = time.time()
    try:
        # Step 1: Parsing
        task.update_stage("Parsing", 20)
        extracted_text = await asyncio.to_thread(extract_text_from_file_bytes, filename, file_bytes)
        
        if not extracted_text.strip():
            raise ValueError("The document was successfully parsed but contains no text.")
            
        await run_common_pipeline_stages(task, extracted_text, filename, start_time, gemini_key)
    except Exception as e:
        log_parsing_failure(filename, str(e))
        task.fail(str(e))

async def run_pipeline_with_parsed_text(task_id: str, extracted_text: str, filename: str, gemini_key: Optional[str] = None):
    task = tasks[task_id]
    start_time = time.time()
    try:
        await run_common_pipeline_stages(task, extracted_text, filename, start_time, gemini_key)
    except Exception as e:
        task.fail(str(e))

async def run_text_analysis_pipeline(task_id: str, raw_text: str, gemini_key: Optional[str] = None):
    task = tasks[task_id]
    start_time = time.time()
    try:
        # Step 1: Parsing
        task.update_stage("Parsing", 20)
        from app.parsers.txt import clean_text
        cleaned_text = await asyncio.to_thread(clean_text, raw_text)
        
        if not cleaned_text.strip():
            raise ValueError("The input text is empty after sanitization.")
            
        await run_common_pipeline_stages(task, cleaned_text, "Pasted_Text", start_time, gemini_key)
    except Exception as e:
        task.fail(str(e))

async def run_common_pipeline_stages(task: Any, text: str, label: str, start_time: float, gemini_key: Optional[str] = None):
    # Step 2: Risk Analysis
    task.update_stage("Risk Analysis", 45)
    deterministic_results = await asyncio.to_thread(run_hybrid_risk_engine, text)
    
    # Step 3: AI Processing
    task.update_stage("AI Processing", 70)
    analysis = await asyncio.to_thread(analyze_contract_with_gemini, text, deterministic_results, gemini_key)
    
    # Step 4: Generating Report
    task.update_stage("Generating Report", 90)
    analysis["deterministicMatches"] = deterministic_results["matches"]
    
    # Validate structure
    validated_response = AnalysisResponse(**analysis).model_dump()
    
    # Update global stats
    record_analysis(validated_response.get("contractType"), validated_response.get("overallRisk", 0))
    
    duration = time.time() - start_time
    log_processing_time("background_analysis_pipeline", duration, {"label": label, "text_length_chars": len(text)})
    
    # Complete task
    task.complete(validated_response)

@router.post("/file", response_model=Union[AnalysisResponse, TaskStatusResponse])
@limiter.limit(RATE_LIMIT_ANALYSIS)
async def analyze_file(
    request: Request, 
    file: UploadFile = File(...), 
    background_tasks: BackgroundTasks = None
):
    """
    Endpoint to upload a legal contract (.pdf, .docx, .txt), parse its contents,
    run the keyword risk engine, perform Gemini AI analysis, and return the structured report.
    Offloads large files to background tasks to prevent timeout.
    """
    if not file or not file.filename:
        log_api_error("/api/analyze/file", 400, "No file uploaded.")
        raise HTTPException(status_code=400, detail="No file was uploaded.")

    # 1. Validate File Metadata (Extension & MIME)
    validate_file_metadata(file.filename, file.content_type)
    
    # 2. Read and enforce size limits (Max 5MB)
    file_bytes = await read_and_validate_file_size(file)
    log_upload(file.filename, file.content_type, len(file_bytes))
    
    # Extract API Key from headers if present
    gemini_key = request.headers.get("x-gemini-api-key")
    
    # 3. Detect large files beforehand by metadata to run entirely in background
    is_large = len(file_bytes) > 500 * 1024  # > 500KB is large
    if not is_large and file.filename.lower().endswith(".pdf"):
        # Quick page count check for PDFs
        import pdfplumber
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                if len(pdf.pages) > 3:
                    is_large = True
        except Exception:
            pass
            
    if is_large:
        task_id = create_task()
        background_tasks.add_task(run_file_analysis_pipeline, task_id, file.filename, file_bytes, gemini_key)
        return TaskStatusResponse(taskId=task_id, status="pending")

    # 4. Standard small file path
    start_time = time.time()
    try:
        # Extract text
        extracted_text = extract_text_from_file_bytes(file.filename, file_bytes)
        
        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="The document was successfully parsed but contains no text.")
            
        # 5. Check if it's large in characters despite small file footprint
        if len(extracted_text) > LARGE_CONTRACT_THRESHOLD_CHARS:
            task_id = create_task()
            background_tasks.add_task(run_pipeline_with_parsed_text, task_id, extracted_text, file.filename, gemini_key)
            return TaskStatusResponse(taskId=task_id, status="pending")
            
        # Run hybrid risk engine (keyword deterministic analysis)
        deterministic_results = run_hybrid_risk_engine(extracted_text)
        
        # Call Gemini AI Service
        analysis = analyze_contract_with_gemini(extracted_text, deterministic_results, gemini_key)
        analysis["deterministicMatches"] = deterministic_results["matches"]
        
        # Populate response
        resp_data = AnalysisResponse(**analysis)
        
        # Record analytics
        record_analysis(resp_data.contractType, resp_data.overallRisk)
        
        duration = time.time() - start_time
        log_processing_time("sync_file_analysis", duration, {"filename": file.filename, "text_length": len(extracted_text)})
        
        return resp_data
        
    except HTTPException as he:
        log_api_error("/api/analyze/file", he.status_code, he.detail)
        raise he
    except ValueError as ve:
        log_parsing_failure(file.filename, str(ve))
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        log_api_error("/api/analyze/file", 500, str(e))
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/text", response_model=Union[AnalysisResponse, TaskStatusResponse])
@limiter.limit(RATE_LIMIT_ANALYSIS)
async def analyze_text(
    request: Request, 
    analysis_req: TextAnalysisRequest, 
    background_tasks: BackgroundTasks = None
):
    """
    Endpoint to copy-paste raw contract text, run the keyword risk engine,
    perform Gemini AI analysis, and return the structured report.
    """
    raw_text = analysis_req.text.strip()
    if not raw_text:
        log_api_error("/api/analyze/text", 400, "No text provided.")
        raise HTTPException(status_code=400, detail="No text was provided for analysis.")
        
    # Enforce pasted text security limit
    validate_text_size(raw_text)
    
    # Extract API Key from headers if present
    gemini_key = request.headers.get("x-gemini-api-key")
    
    # Check if text size justifies background execution
    if len(raw_text) > LARGE_CONTRACT_THRESHOLD_CHARS:
        task_id = create_task()
        background_tasks.add_task(run_text_analysis_pipeline, task_id, raw_text, gemini_key)
        return TaskStatusResponse(taskId=task_id, status="pending")

    start_time = time.time()
    try:
        # Clean the pasted text
        from app.parsers.txt import clean_text
        cleaned_text = clean_text(raw_text)
        
        if not cleaned_text:
            raise HTTPException(status_code=400, detail="The input text is empty after sanitization.")
            
        # Run hybrid risk engine
        deterministic_results = run_hybrid_risk_engine(cleaned_text)
        
        # Call Gemini AI Service
        analysis = analyze_contract_with_gemini(cleaned_text, deterministic_results, gemini_key)
        analysis["deterministicMatches"] = deterministic_results["matches"]
        
        resp_data = AnalysisResponse(**analysis)
        
        # Record analytics
        record_analysis(resp_data.contractType, resp_data.overallRisk)
        
        duration = time.time() - start_time
        log_processing_time("sync_text_analysis", duration, {"text_length": len(cleaned_text)})
        
        return resp_data
        
    except HTTPException as he:
        log_api_error("/api/analyze/text", he.status_code, he.detail)
        raise he
    except ValueError as ve:
        log_api_error("/api/analyze/text", 400, str(ve))
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        log_api_error("/api/analyze/text", 500, str(e))
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """
    Polls the current execution status and results of a background task.
    """
    task = tasks.get(task_id)
    if not task:
        log_api_error(f"/api/analyze/status/{task_id}", 404, "Task not found.")
        raise HTTPException(status_code=404, detail="Task not found or expired.")
        
    return {
        "taskId": task.task_id,
        "status": task.status,
        "stage": task.stage,
        "progress": task.progress,
        "error": task.error,
        "result": task.result
    }

@router.get("/stream/{task_id}")
async def stream_task_status(task_id: str):
    """
    Establishes a Server-Sent Events (SSE) stream for tracking real-time task progress.
    """
    task = tasks.get(task_id)
    if not task:
        log_api_error(f"/api/analyze/stream/{task_id}", 404, "Task not found.")
        raise HTTPException(status_code=404, detail="Task not found or expired.")

    async def event_generator():
        # Handle early termination cases
        if task.status == "completed":
            yield f"event: completed\ndata: {json.dumps(task.result)}\n\n"
            return
        elif task.status == "failed":
            yield f"event: failed\ndata: {json.dumps({'error': task.error})}\n\n"
            return

        # Register event queue
        queue = asyncio.Queue()
        task.queues.append(queue)

        # Initial yield
        yield f"event: progress\ndata: {json.dumps({'status': task.status, 'stage': task.stage, 'progress': task.progress})}\n\n"

        try:
            while True:
                # Listen to updates
                update = await queue.get()
                status = update["status"]
                
                if status == "completed":
                    yield f"event: completed\ndata: {json.dumps(update['result'])}\n\n"
                    break
                elif status == "failed":
                    yield f"event: failed\ndata: {json.dumps({'error': update['error']})}\n\n"
                    break
                else:
                    yield f"event: progress\ndata: {json.dumps({'status': status, 'stage': update['stage'], 'progress': update['progress']})}\n\n"
        except asyncio.CancelledError:
            # Client disconnected
            pass
        finally:
            if task_id in tasks and queue in tasks[task_id].queues:
                tasks[task_id].queues.remove(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/analytics")
def read_analytics():
    """
    Retrieves aggregated anonymized contract analysis metrics.
    """
    return get_analytics()
