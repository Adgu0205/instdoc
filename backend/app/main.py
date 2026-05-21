import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.routes import analyze

BASE_DIR = Path(__file__).resolve().parents[2]


def parse_allowed_origins() -> list[str]:
    raw_origins = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]


# Load environment variables from the backend root when available.
load_dotenv(BASE_DIR / ".env")

# Initialize FastAPI App
app = FastAPI(
    title="Legal Contract Analyzer API",
    description="Production-ready FastAPI backend for parsing legal contracts and analyzing risk vectors with Gemini 2.5.",
    version="1.0.0"
)

# Configure CORS Middleware
# Allows React frontend on Vite (default port 5173) and production deploys
app.add_middleware(
    CORSMiddleware,
    allow_origins=parse_allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Include Routers
app.include_router(analyze.router)

# Health Check Endpoint
@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "service": "Legal Contract Analyzer API",
        "version": "1.0.0",
        "offlineFallback": "available" if not os.getenv("GEMINI_API_KEY") else "disabled"
    }

# Create temp uploads directory if not exists
@app.on_event("startup")
def startup_event():
    os.makedirs("uploads", exist_ok=True)

if __name__ == "__main__":
    # Get port from environment or default to 8000
    port = int(os.getenv("PORT", 8000))
    reload_enabled = os.getenv("UVICORN_RELOAD", "false").lower() == "true"
    # Run the server
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=reload_enabled)
