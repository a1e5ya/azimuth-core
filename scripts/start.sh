#!/bin/bash
# ================================================
# Azimuth Core - Local Personal Finance Planner
# Linux/Mac Startup Script
# ================================================

echo ""
echo "===================================================="
echo "  Azimuth Core - Local Personal Finance Planner"
echo "  Starting all services..."
echo "===================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# Configuration
BACKEND_PORT=8001
FRONTEND_PORT=5173
OLLAMA_PORT=11434

# Store PIDs for cleanup
PIDS=()

# Cleanup function
cleanup() {
    echo ""
    print_info "Stopping all services..."
    
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null
            echo "Stopped process $pid"
        fi
    done
    
    # Kill any remaining processes on our ports
    pkill -f "uvicorn.*app.main:app" 2>/dev/null
    pkill -f "npm run dev" 2>/dev/null
    
    print_success "All services stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Check if we're in the right directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    print_error "Please run this script from the azimuth-core root directory"
    exit 1
fi

# Create logs directory
mkdir -p logs

# Start Ollama service
print_info "Starting Ollama service..."
if pgrep -f "ollama serve" > /dev/null; then
    print_success "Ollama is already running"
else
    echo "Starting Ollama..."
    ollama serve > logs/ollama.log 2>&1 &
    OLLAMA_PID=$!
    PIDS+=($OLLAMA_PID)
    sleep 3
fi

# Check if Ollama is responding
print_info "Checking Ollama connection..."
if ! curl -s "http://localhost:$OLLAMA_PORT/api/tags" > /dev/null; then
    print_warning "Waiting for Ollama to start..."
    sleep 5
    if ! curl -s "http://localhost:$OLLAMA_PORT/api/tags" > /dev/null; then
        print_error "Ollama failed to start. Please check installation."
        echo "Try running: ollama serve"
        exit 1
    fi
fi
print_success "Ollama is running"

# Start Backend service
print_info "Starting backend service..."
cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_error "Virtual environment not found. Please run install.sh first."
    exit 1
fi

# Activate virtual environment and start backend
source venv/bin/activate
echo "Backend starting on port $BACKEND_PORT..."
python -m uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT --log-level info > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
PIDS+=($BACKEND_PID)

cd ..

# Wait for backend to start
print_info "Waiting for backend to start..."
sleep 5

# Check if backend is responding
if ! curl -s "http://localhost:$BACKEND_PORT/health" > /dev/null; then
    print_warning "Backend still starting, waiting longer..."
    sleep 5
    if ! curl -s "http://localhost:$BACKEND_PORT/health" > /dev/null; then
        print_warning "Backend may be slow to start, continuing anyway..."
    else
        print_success "Backend is running"
    fi
else
    print_success "Backend is running"
fi

# Start Frontend service
print_info "Starting frontend service..."
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    print_error "Node modules not found. Please run install.sh first."
    exit 1
fi

# Start frontend
echo "Frontend starting on port $FRONTEND_PORT..."
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
PIDS+=($FRONTEND_PID)

cd ..

# Wait for frontend to start
print_info "Waiting for frontend to start..."
sleep 8

# Check if frontend is responding
if ! curl -s "http://localhost:$FRONTEND_PORT" > /dev/null; then
    print_warning "Frontend still starting, waiting longer..."
    sleep 5
fi

print_success "Frontend is running"

# Open browser
print_info "Opening browser..."
sleep 2

# Cross-platform browser opening
if command -v xdg-open > /dev/null; then
    xdg-open "http://localhost:$FRONTEND_PORT" 2>/dev/null
elif command -v open > /dev/null; then
    open "http://localhost:$FRONTEND_PORT" 2>/dev/null
else
    echo "Please open your browser to: http://localhost:$FRONTEND_PORT"
fi

echo ""
echo "===================================================="
print_success "Azimuth Core is now running!"
echo "===================================================="
echo ""
echo "Services Status:"
echo "• Ollama (AI): http://localhost:$OLLAMA_PORT"
echo "• Backend (API): http://localhost:$BACKEND_PORT"
echo "• Frontend (Web): http://localhost:$FRONTEND_PORT"
echo ""
echo "Your browser should open automatically."
echo "If not, go to: http://localhost:$FRONTEND_PORT"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Keep script running
while true; do
    sleep 10
    
    # Check if any critical process died
    for pid in "${PIDS[@]}"; do
        if ! kill -0 "$pid" 2>/dev/null; then
            print_error "A service stopped unexpectedly. Check logs/ directory for details."
            cleanup
        fi
    done
done