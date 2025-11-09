#!/bin/bash
# Silent startup - no terminals

cd "$(dirname "$0")/.."

# Start Ollama silently
if ! pgrep -f "ollama serve" > /dev/null; then
    nohup ollama serve > /dev/null 2>&1 &
    sleep 3
fi

# Start Backend silently
cd backend
source venv/bin/activate
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 > /dev/null 2>&1 &
cd ..

# Wait for backend
sleep 8

# Start Frontend silently
cd frontend
nohup npm run dev > /dev/null 2>&1 &
cd ..

# Wait for frontend
sleep 10

# Open browser
if command -v xdg-open > /dev/null; then
    xdg-open "http://localhost:5173" 2>/dev/null
elif command -v open > /dev/null; then
    open "http://localhost:5173" 2>/dev/null
fi