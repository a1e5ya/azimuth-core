@echo off
REM ================================================
REM Azimuth Core - Local Personal Finance Planner
REM Windows Startup Script
REM ================================================

echo.
echo ====================================================
echo   Azimuth Core - Local Personal Finance Planner
echo   Starting all services...
echo ====================================================
echo.

REM Check if we're in the right directory
if not exist "backend" (
    echo ❌ Please run this script from the azimuth-core root directory
    pause
    exit /b 1
)

if not exist "frontend" (
    echo ❌ Please run this script from the azimuth-core root directory
    pause
    exit /b 1
)

REM Create logs directory
if not exist "logs" mkdir logs

REM Function to check if port is available
set BACKEND_PORT=8001
set FRONTEND_PORT=5173
set OLLAMA_PORT=11434

REM Start Ollama service
echo 🤖 Starting Ollama service...
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo ✅ Ollama is already running
) else (
    echo Starting Ollama...
    start "Ollama Service" /min ollama serve
    timeout /t 3 /nobreak >nul
)

REM Check if Ollama is responding
echo Checking Ollama connection...
curl -s http://localhost:%OLLAMA_PORT%/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo ⏳ Waiting for Ollama to start...
    timeout /t 5 /nobreak >nul
    curl -s http://localhost:%OLLAMA_PORT%/api/tags >nul 2>&1
    if %errorlevel% neq 0 (
        echo ❌ Ollama failed to start. Please check installation.
        echo Try running: ollama serve
        pause
        exit /b 1
    )
)
echo ✅ Ollama is running

REM Start Backend service
echo 🔧 Starting backend service...
cd backend

REM Check if virtual environment exists
if not exist "venv" (
    echo ❌ Virtual environment not found. Please run install.bat first.
    pause
    exit /b 1
)

REM Activate virtual environment and start backend
start "Azimuth Backend" cmd /k "call venv\Scripts\activate.bat && echo Backend starting on port %BACKEND_PORT%... && python -m uvicorn app.main:app --host 0.0.0.0 --port %BACKEND_PORT% --log-level info"

cd ..

REM Wait for backend to start
echo ⏳ Waiting for backend to start...
timeout /t 5 /nobreak >nul

REM Check if backend is responding
curl -s http://localhost:%BACKEND_PORT%/health >nul 2>&1
if %errorlevel% neq 0 (
    echo ⏳ Backend still starting, waiting longer...
    timeout /t 5 /nobreak >nul
    curl -s http://localhost:%BACKEND_PORT%/health >nul 2>&1
    if %errorlevel% neq 0 (
        echo ⚠️ Backend may be slow to start, continuing anyway...
    ) else (
        echo ✅ Backend is running
    )
) else (
    echo ✅ Backend is running
)

REM Start Frontend service
echo 🎨 Starting frontend service...
cd frontend

REM Check if node_modules exists
if not exist "node_modules" (
    echo ❌ Node modules not found. Please run install.bat first.
    pause
    exit /b 1
)

REM Start frontend
start "Azimuth Frontend" cmd /k "echo Frontend starting on port %FRONTEND_PORT%... && npm run dev"

cd ..

REM Wait for frontend to start
echo ⏳ Waiting for frontend to start...
timeout /t 8 /nobreak >nul

REM Check if frontend is responding
curl -s http://localhost:%FRONTEND_PORT% >nul 2>&1
if %errorlevel% neq 0 (
    echo ⏳ Frontend still starting, waiting longer...
    timeout /t 5 /nobreak >nul
)

echo ✅ Frontend is running

REM Open browser
echo 🌐 Opening browser...
timeout /t 2 /nobreak >nul
start http://localhost:%FRONTEND_PORT%

echo.
echo ====================================================
echo   ✅ Azimuth Core is now running!
echo ====================================================
echo.
echo Services Status:
echo • Ollama (AI): http://localhost:%OLLAMA_PORT%
echo • Backend (API): http://localhost:%BACKEND_PORT%
echo • Frontend (Web): http://localhost:%FRONTEND_PORT%
echo.
echo Your browser should open automatically.
echo If not, go to: http://localhost:%FRONTEND_PORT%
echo.
echo To stop all services, close this window or run stop.bat
echo.
echo Press any key to keep services running...
pause >nul

REM Keep script running to maintain services
echo Services are running. Close this window to stop all services.
:loop
timeout /t 10 /nobreak >nul
goto loop