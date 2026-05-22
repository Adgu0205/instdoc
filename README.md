# Veritas Ledger — Simple Feature & Tech Summary

This repository contains Veritas Ledger: a web app that analyzes legal contracts and highlights risky or missing clauses. Below is a simple, plain-language description of what the project does, the exact features it includes, the technologies it uses, and how to run it locally.

## What this project does (simple language)

- Accepts documents (PDF, DOCX) or pasted text and extracts the contract text.
- Runs a hybrid risk analysis: a fast keyword-based scanner plus optional AI analysis (Gemini) for deeper understanding.
- Returns a structured report with an overall risk score, flagged clauses, translated plain-English redlines, and suggested negotiation items.
- Shows live progress during upload and background processing (Server-Sent Events).
- Provides a visual dashboard with: risk heatmap, clause list, missing clause highlights, scam/predatory signals, and scenario simulations for exit/penalty outcomes.
- Keeps simple anonymized usage statistics (total audits, average risk score, top document types).

## Exact features (what's implemented in the code)

- File upload endpoint for PDF/DOCX/TXT (`/api/analyze/file`).
- Text submission endpoint for pasted content (`/api/analyze/text`).
- Background processing with task IDs and SSE progress events (`/api/analyze/stream/{taskId}`).
- File metadata and content validation (allowed extensions, MIME checks, size limits).
- Deterministic keyword risk engine (rule-based scoring).
- Gemini AI integration for advanced clause translation and reasoning (used when `GEMINI_API_KEY` is set).
- Caching of analysis results to avoid reprocessing identical inputs.
- Simple in-memory analytics (total analyzed, average risk, contract type counts).
- Retry support for failed submissions (frontend stores last submission and retries).
- Friendly offline fallback: if no Gemini key is configured, the app still runs with keyword analysis.

## Tech stack (exact libraries and frameworks)

Backend

- FastAPI (web framework)
- Uvicorn (ASGI server)
- Pydantic v2 (request/response models)
- pdfplumber (PDF parsing)
- python-docx (DOCX parsing)
- google-generativeai (Gemini client)
- slowapi (rate limiting)

Frontend

- React (via Vite)
- Vite (dev server & build)
- TailwindCSS (styling)
- Lucide React (icons)
- Framer Motion (animations)

Other

- Uses simple JSON files / in-memory stores for cache and small analytics in this repo.

## Where to find important code (brief)

- Backend API routes: `backend/app/routes/analyze.py`
- Parsers: `backend/app/parsers/pdf.py`, `backend/app/parsers/docx.py`, `backend/app/parsers/txt.py`
- Gemini integration: `backend/app/services/gemini_service.py`
- Risk engine & helpers: `backend/app/services` and `backend/app/utils`
- Frontend app: `frontend/src/App.jsx`
- Upload component: `frontend/src/components/UploadZone.jsx`
- Dashboard and visualization components: `frontend/src/components/*`
- Frontend API client: `frontend/src/services/api.js`

## How to run locally (copyable commands)

Backend (macOS / Linux):

```bash
cd backend
# create venv if you don't have one
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# set environment variables (example)
export PORT=8000
export ALLOWED_ORIGINS=http://localhost:5173
export GEMINI_API_KEY=your_gemini_api_key_here   # optional
uvicorn app.main:app --reload --host 0.0.0.0 --port $PORT
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open the frontend at `http://localhost:5173` and the backend at `http://localhost:8000`.

## Tests / quick validation commands

- Frontend build check: `cd frontend && npm run build`
- Backend repo tests (simple harness): `cd backend && ../.venv/bin/python app/tests/run_tests.py`

## Environment variables used by the project

- `GEMINI_API_KEY` — (optional) API key for Gemini AI. When absent, the app uses keyword analysis only.
- `PORT` — backend port (default 8000)
- `ALLOWED_ORIGINS` — comma-separated list of allowed CORS origins for the frontend.

## Deployment notes (short)

- Backend: any container or Python host that can run `uvicorn app.main:app`. Keep `GEMINI_API_KEY` secret in deployment settings.
- Frontend: static build (`npm run build`) outputs `dist` for hosting on Netlify, Vercel, or similar. Point `VITE_API_URL` to the deployed backend.

## Simple troubleshooting

- If uploads fail, check backend logs for MIME or size validation errors.
- If the Gemini calls fail, ensure `GEMINI_API_KEY` is set and the key has sufficient quota.
- To re-run the included backend unit checks use `backend/app/tests/run_tests.py` (no external test runner required).

---

If you want the README shortened, reformatted, or translated to another language, tell me which sections to keep and I will update only the `README.md`.
