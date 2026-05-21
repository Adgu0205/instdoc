import os
import logging
from fastapi import APIRouter, File, UploadFile, HTTPException
from app.schemas.analysis import TextAnalysisRequest, AnalysisResponse
from app.middleware.security import validate_file_metadata, read_and_validate_file_size
from app.parsers.txt import parse_txt
from app.parsers.pdf import parse_pdf
from app.parsers.docx import parse_docx
from app.services.risk_engine import run_hybrid_risk_engine
from app.services.gemini_service import analyze_contract_with_gemini

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/api/analyze", tags=["Analysis"])

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

@router.post("/file", response_model=AnalysisResponse)
async def analyze_file(file: UploadFile = File(...)):
    """
    Endpoint to upload a legal contract (.pdf, .docx, .txt), parse its contents,
    run the keyword risk engine, perform Gemini AI analysis, and return the structured report.
    """
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file was uploaded.")

    # 1. Validate File Metadata (Extension & MIME)
    validate_file_metadata(file.filename, file.content_type)
    
    # 2. Read and enforce size limits (Max 5MB)
    file_bytes = await read_and_validate_file_size(file)
    
    try:
        # 3. Extract text depending on file format
        logger.info(f"Extracting text from uploaded file: {file.filename}")
        extracted_text = extract_text_from_file_bytes(file.filename, file_bytes)
        
        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="The document was successfully parsed but contains no text.")
            
        # 4. Run hybrid risk engine (keyword deterministic analysis)
        logger.info("Executing deterministic hybrid risk engine scanner.")
        deterministic_results = run_hybrid_risk_engine(extracted_text)
        
        # 5. Call Gemini AI Service (which handles fallback if API key is missing or fails)
        logger.info("Requesting Gemini AI analysis.")
        analysis = analyze_contract_with_gemini(extracted_text, deterministic_results)
        
        # 6. Populate deterministic matches for front-end visual inspection/heatmap rendering
        analysis["deterministicMatches"] = deterministic_results["matches"]
        
        # Return structured response validated against Pydantic
        return AnalysisResponse(**analysis)
        
    except HTTPException as he:
        raise he
    except ValueError as ve:
        logger.error(f"Validation error in file processing: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Unexpected error analyzing file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/text", response_model=AnalysisResponse)
async def analyze_text(request: TextAnalysisRequest):
    """
    Endpoint to copy-paste raw contract text, run the keyword risk engine,
    perform Gemini AI analysis, and return the structured report.
    """
    raw_text = request.text.strip()
    if not raw_text:
        raise HTTPException(status_code=400, detail="No text was provided for analysis.")
        
    try:
        # 1. Clean the pasted text
        logger.info("Cleaning copy-pasted text.")
        # Re-use our TXT clean utility
        from app.parsers.txt import clean_text
        cleaned_text = clean_text(raw_text)
        
        if not cleaned_text:
            raise HTTPException(status_code=400, detail="The input text is empty after sanitization.")
            
        # 2. Run hybrid risk engine (keyword deterministic analysis)
        logger.info("Executing deterministic hybrid risk engine scanner for pasted text.")
        deterministic_results = run_hybrid_risk_engine(cleaned_text)
        
        # 3. Call Gemini AI Service
        logger.info("Requesting Gemini AI analysis for pasted text.")
        analysis = analyze_contract_with_gemini(cleaned_text, deterministic_results)
        
        # 4. Populate deterministic matches
        analysis["deterministicMatches"] = deterministic_results["matches"]
        
        return AnalysisResponse(**analysis)
        
    except HTTPException as he:
        raise he
    except ValueError as ve:
        logger.error(f"Validation error in text processing: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Unexpected error analyzing text: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
