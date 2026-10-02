@echo off
title QMS ComplaintLens Launcher
echo ========================================================
echo Starting ComplaintLens Services...
echo ========================================================
start "ComplaintLens Backend" "%~dp0start-backend.bat"
start "ComplaintLens Frontend" "%~dp0start-frontend.bat"
echo.
echo Both servers have been launched in separate windows!
echo - Frontend:  http://localhost:5173
echo - Backend:   http://localhost:8000
echo - Swagger:   http://localhost:8000/docs
echo.
