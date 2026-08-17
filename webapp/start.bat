@echo off
REM Launch reAlIty Web — FastAPI server
REM Opens http://localhost:8000 in your browser automatically

echo Starting reAlIty Web server...
echo (First run will load the AI model — this may take 30-60 seconds)
echo.

start http://localhost:8000

.\..\.venv\Scripts\python -m uvicorn webapp.main:app --host 0.0.0.0 --port 8000 --reload
