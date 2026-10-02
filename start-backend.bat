@echo off
title QMS ComplaintLens - Backend (FastAPI)
cd /d "%~dp0backend"
echo ========================================================
echo Starting QMS ComplaintLens Backend on http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo ========================================================
if exist .\.venv\Scripts\python.exe (
    .\.venv\Scripts\python.exe main.py
) else (
    python main.py
)
pause

