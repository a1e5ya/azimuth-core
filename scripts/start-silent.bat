@echo off
REM Open splash screen immediately
start "" "%~dp0splash.html"

REM Clean up any existing processes first
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8001') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5173') do taskkill /F /PID %%a >nul 2>&1

timeout /t 2 /nobreak >nul

REM Start Ollama
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if "%ERRORLEVEL%"=="1" (
    start /MIN "Ollama Service" ollama serve
    timeout /t 5 /nobreak >nul
)

REM Start Backend
cd backend
start /MIN "Azimuth Backend" cmd /k "call venv\Scripts\activate.bat && python -m uvicorn app.main:app --host 0.0.0.0 --port 8001"
cd ..

timeout /t 12 /nobreak >nul

REM Start Frontend
cd frontend
start /MIN "Azimuth Frontend" cmd /k "npm run dev"
cd ..

REM Don't open browser manually - splash will auto-redirect when ready