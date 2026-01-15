# PDF Intelligence Extractor

🚀 **AI-powered PDF extraction system** using Large Language Models to convert unstructured documents into clean, structured data.

## 🌐 Live Demo

**Frontend:** https://llm-powered-pdf-extractor.vercel.app

**Backend API:** https://pdf-extracter-api.onrender.com

**API Health Check:** https://pdf-extracter-api.onrender.com/api/v1/health/

---

## ✨ Features

- **Smart Document Extraction**: Upload any PDF → Get structured JSON with confidence scores
- **Invoice Processing**: Extract vendor info, dates, totals, line items (batch upload supported)
- **Resume Analyzer**: ATS score, fit score, red flags, strengths/weaknesses analysis
- **Multi-Resume Ranking**: Rank multiple candidates against job descriptions
- **Candidate Comparison**: Side-by-side comparison of two resumes
- **Batch Processing**: Process multiple documents simultaneously
- **REST API**: Full API access for third-party integration

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 19, TypeScript, Tailwind CSS, Vite |
| **Backend** | Python, FastAPI, Pydantic |
| **AI/LLM** | Llama 3.3 70B via Groq API |
| **PDF Processing** | pdfplumber, pdfminer |
| **Deployment** | Vercel (Frontend), Render (Backend) |

## 🤖 AI Configuration

This project uses **Groq Cloud** for fast LLM inference with Llama 3.3 70B.

Set these in `backend/.env`:
```env
LLM_MODE=cloud
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
```

## 🚀 Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # Add your GROQ_API_KEY
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health/` | GET | Health check |
| `/api/v1/extract/` | POST | Extract data from PDF |
| `/api/v1/batch/extract/` | POST | Batch extraction |
| `/api/v1/resume/analyze/` | POST | Analyze resume against job |
| `/api/v1/resume/rank/` | POST | Rank multiple resumes |
| `/api/v1/resume/compare/` | POST | Compare two candidates |

## 📁 Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── core/         # Config, logging
│   │   ├── schemas/      # Pydantic models
│   │   ├── services/     # Business logic
│   │   └── utils/        # Helpers
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── services/     # API client
│   │   └── types/        # TypeScript types
│   └── package.json
└── samples/              # Sample PDF generator
```

## 📸 Screenshots

<!-- Add screenshots here -->

## 📄 License

MIT License

---

**Built with ❤️ using AI-powered document intelligence**
