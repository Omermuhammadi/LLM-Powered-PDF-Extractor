# PDF Intelligence Extractor

AI-powered PDF extraction + resume intelligence: extract invoices, analyze resumes against a job description, and rank candidates.

## Features
- **Invoice Extraction**: vendor, dates, totals, line items (batch upload supported)
- **Resume Analyzer**: ATS score, fit score, red flags, strengths/weaknesses
- **Multi-Resume Ranking**: rank multiple candidates + compare two side-by-side

## AI (Groq Cloud)
This project was originally built with a local LLM (Ollama / Phi-3), then switched to **Groq Cloud** for faster and more reliable inference.

Set these in `backend/.env`:
```env
LLM_MODE=cloud
GROQ_API_KEY=YOUR_KEY
```

## Quick Start
Backend:
```bash
cd backend
poetry install
cp .env.example .env
poetry run uvicorn app.main:app --reload
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Sample PDFs (optional)
Generate a few sample invoices + resumes for demos/screenshots:
```bash
python samples/generate_samples.py
```

## Screenshots
<!-- Add screenshots here (landing page, invoice extraction, resume ranking) -->
