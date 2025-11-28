@echo off
echo ======================================
echo Starting RAG Document Q&A Demo
echo ======================================
echo.

REM Check if .env file exists
if not exist ".env" (
    echo ERROR: .env file not found!
    echo.
    echo Please create a .env file with your Google Gemini API key:
    echo 1. Get a free API key from: https://aistudio.google.com/app/apikey
    echo 2. Copy .env.example to .env
    echo 3. Add: GEMINI_API_KEY=your_api_key_here
    echo.
    pause
    exit /b 1
)

REM Check if API key is set in .env
findstr /C:"GEMINI_API_KEY=" .env >nul
if errorlevel 1 (
    echo ERROR: GEMINI_API_KEY not found in .env file!
    echo.
    echo Please add your API key to .env file:
    echo GEMINI_API_KEY=your_api_key_here
    echo.
    echo Get a free key from: https://aistudio.google.com/app/apikey
    echo.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo Starting server...
echo.
echo The demo will open in your browser at: http://localhost:8000
echo Press Ctrl+C to stop the server
echo.

REM Open browser after a short delay
start "" cmd /c "timeout /t 3 /nobreak >nul & start http://localhost:8000"

uvicorn main:app --host 0.0.0.0 --port 8000
