# 🤖 PDF Intelligence Extractor

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **LLM-Powered PDF Intelligence Extraction System** - Extract structured data from PDFs using local LLMs, optimized for CPU-only environments.

## ✨ Features

- 📄 **PDF Text Extraction** - Extract text from text-based PDFs using pdfplumber
- 🧠 **Local LLM Processing** - Phi-3 Mini via Ollama (no GPU required)
- 🎯 **Document Type Detection** - Automatic detection of invoices, resumes, etc.
- ✅ **Structured Output** - Validated JSON with confidence scores
- 🎨 **Modern Web UI** - React + Tailwind with glassmorphism design
- ⚡ **Fast Processing** - ~5-10 seconds per document on CPU

## 🏗️ Architecture

```
Frontend (React/Vite) → FastAPI Backend → PDF Processor → LLM Extractor → Validator → JSON
```

## 📋 Supported Document Types

### Invoice (Primary)
- Vendor Name, Invoice Number, Invoice Date
- Total Amount, Currency, Tax Amount

### Resume (Coming Soon)
- Candidate Name, Email, Phone
- Skills, Experience, Education

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- [Ollama](https://ollama.ai/) with Phi-3 Mini model

### Backend Setup

```bash
# Clone and navigate
cd pdf-intelligence-extractor

# Install dependencies with Poetry
poetry install

# Copy environment file
cp backend/.env.example backend/.env

# Install Ollama and pull model
ollama pull phi3:mini

# Run backend
cd backend
poetry run uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## 📁 Project Structure

```
pdf-intelligence-extractor/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry
│   │   ├── api/v1/endpoints/    # API routes
│   │   ├── core/                # Config, logging, exceptions
│   │   ├── services/            # Business logic
│   │   │   ├── pdf/             # PDF processing
│   │   │   ├── llm/             # LLM client
│   │   │   └── extraction/      # Orchestration
│   │   ├── schemas/             # Pydantic models
│   │   └── utils/               # Utilities
│   └── tests/                   # Unit tests
├── frontend/                    # React app
├── samples/                     # Test PDFs
└── docs/                        # Documentation
```

## 🔧 Configuration

Key environment variables (see `backend/.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| `OLLAMA_HOST` | Ollama server URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | LLM model name | `phi3:mini` |
| `MAX_UPLOAD_SIZE_MB` | Max PDF size | `10` |
| `LLM_TIMEOUT` | Request timeout (seconds) | `60` |

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/extract` | Extract data from PDF |
| `GET` | `/api/v1/health` | Health check |

## 🎯 Output Format

```json
{
  "success": true,
  "document_type": "invoice",
  "processing_metadata": {
    "file_name": "invoice.pdf",
    "pages_processed": 1,
    "processing_time_ms": 5420,
    "model_used": "phi3:mini"
  },
  "extracted_fields": {
    "vendor_name": "ABC Corp",
    "invoice_number": "INV-001",
    "invoice_date": "2024-01-15",
    "total_amount": 1250.00
  },
  "confidence_scores": {
    "overall": 0.96
  }
}
```

## 💻 Hardware Requirements

- **CPU**: Intel Core i5 or equivalent (6+ cores recommended)
- **RAM**: 8GB minimum, 16GB recommended
- **GPU**: Not required (CPU-only inference)

## 🛠️ Development

```bash
# Run tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app

# Format code
poetry run black backend/
poetry run isort backend/

# Type check
poetry run mypy backend/app
```

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

---

Built with ❤️ using FastAPI, Phi-3 Mini, and React
