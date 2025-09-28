@echo off
REM ================================================
REM Azimuth Core - Local Personal Finance Planner
REM Windows Installation Script
REM ================================================

echo.
echo ====================================================
echo   Azimuth Core - Local Personal Finance Planner
echo   Windows Installation Script
echo ====================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js is not installed or not in PATH
    echo Please install Node.js 18+ from https://nodejs.org
    pause
    exit /b 1
)

REM Check if Ollama is installed
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Ollama is not installed
    echo Please install Ollama from https://ollama.ai
    echo After installation, run: ollama pull llama3.2:3b
    pause
    exit /b 1
)

echo ✅ All prerequisites found!
echo.

REM Install backend dependencies
echo 📦 Installing backend dependencies...
cd backend
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo ❌ Failed to install backend dependencies
    pause
    exit /b 1
)

echo ✅ Backend dependencies installed
cd ..

REM Install frontend dependencies
echo 📦 Installing frontend dependencies...
cd frontend
call npm install

if %errorlevel% neq 0 (
    echo ❌ Failed to install frontend dependencies
    pause
    exit /b 1
)

echo ✅ Frontend dependencies installed
cd ..

REM Create data directory
if not exist "data" mkdir data

REM Initialize database
echo 🗄️ Initializing database...
cd backend
call venv\Scripts\activate.bat
python init_db.py

if %errorlevel% neq 0 (
    echo ❌ Database initialization failed
    pause
    exit /b 1
)

echo ✅ Database initialized
cd ..

REM Pull Ollama model if not exists
echo 🤖 Checking Ollama model...
ollama list | findstr llama3.2:3b >nul
if %errorlevel% neq 0 (
    echo Downloading Llama 3.2 3B model (this may take a few minutes)...
    ollama pull llama3.2:3b
    
    if %errorlevel% neq 0 (
        echo ❌ Failed to download Ollama model
        echo You can try manually: ollama pull llama3.2:3b
        pause
        exit /b 1
    )
)

echo ✅ Ollama model ready

echo.
echo ====================================================
echo   ✅ Installation Complete!
echo ====================================================
echo.
echo Next steps:
echo 1. Run start.bat to launch Azimuth Core
echo 2. Your browser will open to http://localhost:5173
echo 3. Create an account and start importing your CSV files
echo.
echo For help, check the README.md file
echo.
pause