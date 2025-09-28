@echo off
REM ================================================
REM Azimuth Core - Local Personal Finance Planner
REM Windows Stop Script
REM ================================================

echo.
echo ====================================================
echo   Azimuth Core - Local Personal Finance Planner
echo   Stopping all services...
echo ====================================================
echo.

REM Kill frontend processes
echo 🎨 Stopping frontend service...
tasklist /FI "WINDOWTITLE eq Azimuth Frontend*" /FO CSV | findstr /V "INFO:" > temp_frontend_processes.txt
for /f "tokens=2 delims=," %%a in (temp_frontend_processes.txt) do (
    set "pid=%%a"
    set "pid=!pid:"=!"
    if not "!pid!"=="PID" (
        taskkill /PID !pid! /F >nul 2>&1
    )
)
del temp_frontend_processes.txt >nul 2>&1

REM Alternative method - kill npm processes
taskkill /F /IM node.exe >nul 2>&1
taskkill /F /IM npm.cmd >nul 2>&1

REM Kill backend processes
echo 🔧 Stopping backend service...
tasklist /FI "WINDOWTITLE eq Azimuth Backend*" /FO CSV | findstr /V "INFO:" > temp_backend_processes.txt
for /f "tokens=2 delims=," %%a in (temp_backend_processes.txt) do (
    set "pid=%%a"
    set "pid=!pid:"=!"
    if not "!pid!"=="PID" (
        taskkill /PID !pid! /F >nul 2>&1
    )
)
del temp_backend_processes.txt >nul 2>&1

REM Alternative method - kill uvicorn processes
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV ^| findstr uvicorn') do (
    taskkill /PID %%i /F >nul 2>&1
)

REM Kill any remaining Python processes that might be our backend
wmic process where "name='python.exe' and commandline like '%%uvicorn%%'" delete >nul 2>&1

REM Stop Ollama service (optional - user might want to keep it running)
echo 🤖 Checking Ollama service...
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo Ollama is running. Do you want to stop it? (Y/N^)
    set /p choice="Stop Ollama? (Y/N): "
    if /i "%choice%"=="Y" (
        echo Stopping Ollama...
        taskkill /F /IM ollama.exe >nul 2>&1
        echo ✅ Ollama stopped
    ) else (
        echo ✅ Ollama left running
    )
) else (
    echo ✅ Ollama is not running
)

REM Clean up any remaining processes on our ports
echo 🧹 Cleaning up remaining processes...

REM Kill processes using our ports
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5173 "') do (
    taskkill /F /PID %%a >nul 2>&1
)

for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8001 "') do (
    taskkill /F /PID %%a >nul 2>&1
)

REM Close any browser tabs (optional)
echo 🌐 Note: Browser tabs may remain open

REM Clean up log files (optional)
if exist "logs" (
    echo 📝 Cleaning up log files...
    del /Q logs\*.log >nul 2>&1
)

echo.
echo ====================================================
echo   ✅ All Azimuth Core services stopped!
echo ====================================================
echo.
echo Services that were stopped:
echo • Frontend (Vue.js development server)
echo • Backend (FastAPI server)
echo • Associated Node.js and Python processes
echo.
echo Note: Ollama may still be running if you chose to keep it.
echo You can manually stop it with: taskkill /F /IM ollama.exe
echo.
echo To restart Azimuth Core, run: start.bat
echo.
pause