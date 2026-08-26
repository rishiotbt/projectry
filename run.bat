@echo off
cd /d "%~dp0"
echo Starting Product Tree...
echo Open http://localhost:9988 in your browser
echo.
.venv\Scripts\python.exe -m app.main
pause
