#!/bin/bash

echo "Starting Financial Document Translator (VENV Mode)..."

# 1. Check for Python 3.10+
if command -v python3.11 &>/dev/null; then
    PYTHON_BIN="python3.11"
elif command -v python3.10 &>/dev/null; then
    PYTHON_BIN="python3.10"
else
    echo "ERROR: Python 3.10 or 3.11 not found."
    echo "Please run: brew install python@3.11"
    exit 1
fi

# 2. Setup Virtual Environment
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

if [ ! -d "venv" ]; then
    echo "Creating virtual environment with $PYTHON_BIN..."
    $PYTHON_BIN -m venv venv
fi

source venv/bin/activate

echo "Ensuring dependencies are installed in VENV..."
pip install --upgrade pip
pip install -r requirements.txt
pip install fastapi uvicorn python-multipart python-dotenv google-adk google-cloud-translate importlib-metadata

# 3. Kill any existing processes
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null

# 4. Starting processes
echo "Starting FastAPI Backend Orchestrator (Port 8000)..."
python -m uvicorn server:app --reload --host 0.0.0.0 --port 8000 &

echo "Starting React Frontend Dashboard (Port 5173)..."
cd frontend
# Ensure npm deps are up to date
if [ ! -d "node_modules" ]; then
    npm install
fi
npm run dev
