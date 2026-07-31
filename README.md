# QMS Complaint Co-Pilot

QMS Complaint Co-Pilot is an AI-assisted quality management system for handling product complaints. It combines a React frontend with a FastAPI backend to help users log complaints, generate risk assessments, chat with an AI assistant, and manage complaint records in a searchable dashboard.

## Overview

This project is designed for teams that need a faster way to:

- capture product complaint details
- assess risk and suggest follow-up actions
- interact with an AI co-pilot during complaint entry
- upload and process complaint documents in PDF format
- review and manage complaint history from a dashboard

## Features

- Complaint form for logging product, batch, quantity, and defect details
- AI-powered risk evaluation for severity, priority, and recommended action
- Conversational AI assistant for complaint entry and editing
- PDF document upload and text extraction
- Dashboard with complaint history, search, and summary metrics
- REST API with FastAPI and SQLite-backed persistence

## Project Structure

- backend/ - FastAPI application and AI workflow logic
  - app/main.py - application entry point
  - app/routers/ - API routes for chat, complaints, and uploads
  - app/services/ - LLM integration, LangGraph workflow, and OCR helpers
  - app/models/ - database models
  - app/schemas/ - request and response schemas
- frontend/ - React + Vite user interface
  - src/components/ - reusable UI components
  - src/pages/ - dashboard and page-level views
  - src/redux/ - state management with Redux Toolkit

## Tech Stack

### Backend
- Python
- FastAPI
- SQLAlchemy
- LangChain / LangGraph
- Groq or Google Gemini APIs
- pypdf for PDF text extraction

### Frontend
- React
- Vite
- Redux Toolkit
- lucide-react

## Getting Started

### 1. Prerequisites

- Python 3.10+
- Node.js 18+
- npm

### 2. Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create a file named .env in the backend folder with your API credentials:

```env
GROQ_API_KEY=your_groq_key
# or
GEMINI_API_KEY=your_gemini_key
DATABASE_URL=sqlite:///./qms_complaints.db
```

Run the backend:

```bash
python app/main.py
```

The API will be available at:
- http://localhost:8000
- API docs: http://localhost:8000/docs

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at:
- http://localhost:5173

## API Overview

Main endpoints include:

- POST /api/chat - send a message to the AI complaint assistant
- POST /api/complaints - create a complaint record
- GET /api/complaints - list complaint records
- PUT /api/complaints/{id} - update a complaint record
- DELETE /api/complaints/{id} - delete a complaint record
- POST /api/upload - upload a PDF and extract complaint data

## Notes

- The backend can run in mock mode if AI credentials are not configured, but the experience is best with a real LLM API key.
- SQLite is used by default for local development.
- The project is intended as a prototype or internal tool and can be extended with auth, file storage, and production deployment setup.

## License

This project is for internal use and demonstration purposes unless otherwise specified.
