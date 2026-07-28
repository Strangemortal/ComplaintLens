import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Import database, models, routers
from app.database import engine, Base
from app.routers import chat, upload, complaints

# Load environment
load_dotenv()

# Initialize tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="QMS AI Complaint Management API",
    description="Backend service with LangGraph orchestrating automated QMS product complaint workflows.",
    version="1.0.0"
)

# CORS configuration for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router)
app.include_router(upload.router)
app.include_router(complaints.router)

@app.get("/")
def health_check():
    return {
        "status": "healthy",
        "service": "QMS Complaint Co-Pilot API",
        "database": str(engine.url)
    }

if __name__ == "__main__":
    import uvicorn
    # Allow running directly via python app/main.py
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
