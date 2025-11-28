@echo off
echo ======================================
echo RAG Document Q&A System - Demo Setup
echo ======================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo ======================================
echo Setup Complete!
echo ======================================
echo.
echo IMPORTANT: You need a Google Gemini API key to run this demo.
echo.
echo If you don't have a .env file with GEMINI_API_KEY:
echo 1. Get a free API key from: https://aistudio.google.com/app/apikey
echo 2. Copy .env.example to .env
echo 3. Add your API key to the .env file
echo.
echo To start the demo:
echo   Run: start_demo.bat
echo.
pause
