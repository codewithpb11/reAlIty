@echo off
REM Launch reAlIty Web — FastAPI server
REM Run this file from the project root folder (App-reAlIty)

echo Starting reAlIty Web server...
echo.

.\.venv\Scripts\python webapp/launcher.py

echo.
echo Server stopped. Press any key to close.
pause > nul
