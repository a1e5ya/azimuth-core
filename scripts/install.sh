#!/bin/bash
# ================================================
# Azimuth Core - Local Personal Finance Planner
# Linux/Mac Installation Script
# ================================================

echo ""
echo "===================================================="
echo "  Azimuth Core - Local Personal Finance Planner"
echo "  Linux/Mac Installation Script"
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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if Python is installed
if ! command_exists python3; then
    print_error "Python 3 is not installed"
    echo "Please install Python 3.8+ using your package manager:"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "  macOS: brew install python3"
    echo "  Or download from: https://python.org"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    print_error "Python version $PYTHON_VERSION is too old. Required: $REQUIRED_VERSION+"
    exit 1
fi

print_success "Python $PYTHON_VERSION found"

# Check if Node.js is installed
if ! command_exists node; then
    print_error "Node.js is not installed"
    echo "Please install Node.js 18+ using your package manager:"
    echo "  Ubuntu/Debian: curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash - && sudo apt-get install -y nodejs"
    echo "  macOS: brew install node"
    echo "  Or download from: https://nodejs.org"
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | sed 's/v//')
REQUIRED_NODE_VERSION="18.0.0"

if [ "$(printf '%s\n' "$REQUIRED_NODE_VERSION" "$NODE_VERSION" | sort -V | head -n1)" != "$REQUIRED_NODE_VERSION" ]; then
    print_error "Node.js version $NODE_VERSION is too old. Required: $REQUIRED_NODE_VERSION+"
    exit 1
fi

print_success "Node.js $NODE_VERSION found"

# Check if Ollama is installed
if ! command_exists ollama; then
    print_error "Ollama is not installed"
    echo "Please install Ollama:"
    echo "  Linux: curl -fsSL https://ollama.ai/install.sh | sh"
    echo "  macOS: brew install ollama"
    echo "  Or download from: https://ollama.ai"
    echo ""
    echo "After installation, run: ollama pull llama3.2:3b"
    exit 1
fi

print_success "All prerequisites found!"
echo ""

# Install backend dependencies
print_info "Installing backend dependencies..."
cd backend || {
    print_error "Backend directory not found"
    exit 1
}

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    print_error "Failed to install backend dependencies"
    exit 1
fi

print_success "Backend dependencies installed"
cd ..

# Install frontend dependencies
print_info "Installing frontend dependencies..."
cd frontend || {
    print_error "Frontend directory not found"
    exit 1
}

npm install

if [ $? -ne 0 ]; then
    print_error "Failed to install frontend dependencies"
    exit 1
fi

print_success "Frontend dependencies installed"
cd ..

# Create data directory
mkdir -p data

# Initialize database
print_info "Initializing database..."
cd backend
source venv/bin/activate
python init_db.py

if [ $? -ne 0 ]; then
    print_error "Database initialization failed"
    exit 1
fi

print_success "Database initialized"
cd ..

# Check if Ollama model exists
print_info "Checking Ollama model..."
if ! ollama list | grep -q "llama3.2:3b"; then
    echo "Downloading Llama 3.2 3B model (this may take a few minutes)..."
    ollama pull llama3.2:3b
    
    if [ $? -ne 0 ]; then
        print_error "Failed to download Ollama model"
        echo "You can try manually: ollama pull llama3.2:3b"
        exit 1
    fi
fi

print_success "Ollama model ready"

# Make scripts executable
chmod +x scripts/*.sh

echo ""
echo "===================================================="
print_success "Installation Complete!"
echo "===================================================="
echo ""
echo "Next steps:"
echo "1. Run ./scripts/start.sh to launch Azimuth Core"
echo "2. Your browser will open to http://localhost:5173"
echo "3. Create an account and start importing your CSV files"
echo ""
echo "For help, check the README.md file"
echo ""