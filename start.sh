#!/usr/bin/env bash
set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Starting KAUST Frontend Application${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if Python backend directory exists
if [ ! -d "server/python-api" ]; then
    echo -e "${RED}Error: Python backend directory not found!${NC}"
    exit 1
fi

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down servers...${NC}"
    if [ ! -z "${PYTHON_PID:-}" ]; then
        kill $PYTHON_PID 2>/dev/null || true
        echo -e "${GREEN}✓ Python backend stopped${NC}"
    fi
    if [ ! -z "${NODE_PID:-}" ]; then
        kill $NODE_PID 2>/dev/null || true
        echo -e "${GREEN}✓ Node.js frontend stopped${NC}"
    fi
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM EXIT

# Start Python backend
echo -e "${BLUE}Starting Python backend API on port 8001...${NC}"

# Set environment variables for dataset paths
# Get absolute path to project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export JD_PATH="${JD_PATH:-$PROJECT_ROOT/Dataset/normalized_jd.csv}"
export CV_PATH="${CV_PATH:-$PROJECT_ROOT/Dataset/summarized_cv.csv}"

echo -e "${GREEN}Dataset paths:${NC}"
echo -e "  JD_PATH: $JD_PATH"
echo -e "  CV_PATH: $CV_PATH"

cd server/python-api

# Check if conda is activated (check for CONDA_DEFAULT_ENV)
if [ ! -z "${CONDA_DEFAULT_ENV:-}" ]; then
    echo -e "${GREEN}Using conda environment: $CONDA_DEFAULT_ENV${NC}"
    PYTHON_CMD="python"
# Check if Python virtual environment exists (optional)
elif [ -d "venv" ]; then
    source venv/bin/activate
    PYTHON_CMD="python"
elif [ -d "../venv" ]; then
    source ../venv/bin/activate
    PYTHON_CMD="python"
else
    PYTHON_CMD="python3"
fi

# Check if uvicorn is available
if command -v uvicorn &> /dev/null; then
    UVICORN_CMD="uvicorn"
elif $PYTHON_CMD -m uvicorn --help &> /dev/null; then
    UVICORN_CMD="$PYTHON_CMD -m uvicorn"
else
    echo -e "${YELLOW}uvicorn not found. Checking if dependencies need to be installed...${NC}"
    if [ ! -f "requirements.txt" ]; then
        echo -e "${RED}Error: requirements.txt not found!${NC}"
        cd ../..
        exit 1
    fi
    
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    $PYTHON_CMD -m pip install -r requirements.txt --quiet || {
        echo -e "${RED}Error: Failed to install Python dependencies!${NC}"
        echo -e "${YELLOW}Please run manually: cd server/python-api && pip install -r requirements.txt${NC}"
        cd ../..
        exit 1
    }
    
    # Try again after installation
    if $PYTHON_CMD -m uvicorn --help &> /dev/null; then
        UVICORN_CMD="$PYTHON_CMD -m uvicorn"
    else
        echo -e "${RED}Error: uvicorn still not available after installation!${NC}"
        cd ../..
        exit 1
    fi
fi

# Set CUDA_VISIBLE_DEVICES if needed (from run.sh)
export CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-1}

# Start Python backend in background
$UVICORN_CMD app.api:app --host 0.0.0.0 --port 8001 --reload > /tmp/python-backend.log 2>&1 &
PYTHON_PID=$!
cd ../..

# Wait a moment for Python backend to start
sleep 2

# Check if Python backend started successfully
if ! kill -0 $PYTHON_PID 2>/dev/null; then
    echo -e "${RED}Error: Python backend failed to start!${NC}"
    echo -e "${YELLOW}Check the logs: /tmp/python-backend.log${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python backend started (PID: $PYTHON_PID)${NC}"
echo ""

# Start Node.js frontend
echo -e "${BLUE}Starting Node.js frontend on port 5000...${NC}"
echo ""

# Start Node.js frontend (this will run in foreground)
npm run dev &
NODE_PID=$!

# Wait a moment for Node.js to start
sleep 3

# Check if Node.js started successfully
if ! kill -0 $NODE_PID 2>/dev/null; then
    echo -e "${RED}Error: Node.js frontend failed to start!${NC}"
    cleanup
    exit 1
fi

echo -e "${GREEN}✓ Node.js frontend started (PID: $NODE_PID)${NC}"
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Both servers are running!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Backend API:${NC}  http://localhost:8001"
echo -e "${BLUE}Frontend App:${NC} http://localhost:5000"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop both servers${NC}"
echo ""
echo -e "${YELLOW}Python backend logs:${NC} /tmp/python-backend.log"
echo ""

# Wait for both processes
wait $PYTHON_PID $NODE_PID

