# Veritas Ledger: AI Legal Contract Intelligence Platform

Veritas Ledger is a premium, production-ready full-stack AI SaaS application that analyzes legal contracts (PDF, DOCX, TXT) and copy-pasted legal clauses. It uses a **Hybrid Risk Engine** combining deterministic keyword signatures with **Gemini 2.5 Flash** for natural language understanding and clause translation.

The user interface is designed with a premium, elegant editorial aesthetic inspired by financial journals and legal publications, featuring cream backgrounds, serif typography, double-line borders, and clean, modular cards.

---

## Technical Stack

### Backend

- **Core**: FastAPI, Uvicorn (Asynchronous API endpoints)
- **Data Modeling & Validation**: Pydantic v2
- **Document Parsers**: `pdfplumber` (PDF parsing), `python-docx` (Word parsing), Native Python (Plain text normalization)
- **AI Engine**: Gemini 2.5 Flash (`google-generativeai` SDK)

### Frontend

- **Framework**: React 18, Vite
- **Styling**: TailwindCSS (Custom Editorial Palette)
- **Icons**: Lucide React
- **Animations**: Framer Motion

---

## Project Structure

```
instdoc/
├── backend/
│   ├── app/
│   │   ├── routes/
│   │   │   └── analyze.py      # /api/analyze/file and /api/analyze/text routes
│   │   ├── services/
│   │   │   ├── risk_engine.py  # Keyword scanner and score weights
│   │   │   └── gemini_service.py # Gemini prompts, validation, chunking & merge logic
│   │   ├── parsers/
│   │   │   ├── txt.py          # Text encoder and sanitization
│   │   │   ├── pdf.py          # PDF parser via pdfplumber
│   │   │   └── docx.py         # DOCX parser via python-docx
│   │   ├── schemas/
│   │   │   └── analysis.py     # Pydantic request/response models
│   │   ├── middleware/
│   │   │   └── security.py     # Max 5MB file sizes & extensions validation
│   │   ├── utils/
│   │   │   └── helpers.py      # Theme color helpers
│   │   └── main.py             # App initializer and CORS middleware
│   ├── requirements.txt        # Backend dependencies
│   └── .env                    # Local-only port, allowed origins, and GEMINI_API_KEY placeholder
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navigation.jsx  # Newspaper masthead & volume indicator
│   │   │   ├── UploadZone.jsx  # Drag-and-drop document upload + paste text panels
│   │   │   ├── Dashboard.jsx   # Main grid dashboard layout assembler
│   │   │   ├── RiskHeader.jsx  # Safety badge status card
│   │   │   ├── RiskHeatmap.jsx # Dynamic click-to-highlight keyword box
│   │   │   ├── RiskList.jsx    # Collapsible AI clause translation cards
│   │   │   ├── ScamSignals.jsx # Predatory patterns warning blocks
│   │   │   ├── MissingClauses.jsx # Omission highlight tables & text inserts
│   │   │   └── Simulations.jsx # Interactive exit and payment consequence trials
│   │   ├── services/
│   │   │   └── api.js          # Fetch API routes connector
│   │   ├── App.jsx             # View and state controller
│   │   ├── index.css           # Global custom editorial style classes
│   │   └── main.jsx            # DOM entrypoint
│   ├── package.json            # Node modules config
│   ├── tailwind.config.js      # Tailwind configurations & custom theme color hex codes
│   └── index.html              # Custom Google Fonts loading and metadata tags
└── README.md                   # Setup guide
```

---

## Setup & Installation

### Prerequisite

Obtain a Gemini API key from the [Google AI Studio](https://aistudio.google.com/).

### 1. Backend Server Setup

Navigate into the backend directory:

```bash
cd backend
```

Create a Python virtual environment:

```bash
# On macOS / Linux
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure your environment variables:
Open the `.env` file in the `backend/` directory and paste your API key locally only:

```env
PORT=8000
ALLOWED_ORIGINS=http://localhost:5173,https://your-netlify-site.netlify.app
GEMINI_API_KEY=your_gemini_api_key_here
```

Start the FastAPI application:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The server will start running on **`http://localhost:8000`**. You can verify the health check at `http://localhost:8000/` or access the interactive API docs at `http://localhost:8000/docs`.

_(Note: If no API key is specified, Veritas Ledger will automatically enter **Offline Fallback Mode**, allowing you to test the complete drag-and-drop workflow and interactive dashboard using local deterministic keyword analysis!)_

---

### 2. Frontend client Setup

Open a new terminal window and navigate into the frontend directory:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the Vite development client:

```bash
npm run dev
```

The dev client will open on **`http://localhost:5173`**. Access this link in your browser to interact with the platform.

---

## Deployment Guidelines

### Backend (Render)

- Deploy from the repository root with the `backend` directory as the service root.
- Use the start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- Add `GEMINI_API_KEY` and `ALLOWED_ORIGINS` as environment variables in Render.
- Keep the API key out of the repo; only store it in Render secrets or your local `.env`.

### Frontend (Netlify)

- Set the base directory to `frontend`.
- Use the build command `npm run build` and publish directory `dist`.
- Set `VITE_API_URL` to your deployed Render backend URL.
- You can keep `frontend/.env.example` as a local template and configure the real value in Netlify.
