#!/bin/bash

# Start React App with FastAPI Backend

echo "🚀 Starting NJ Voter Chat React Application..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on the react-migration branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "react-migration" ]; then
    echo -e "${YELLOW}Warning: Not on react-migration branch. Current branch: $CURRENT_BRANCH${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down services...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}Services stopped.${NC}"
}

trap cleanup EXIT

# Install backend dependencies
echo -e "${GREEN}Installing backend dependencies...${NC}"
cd backend
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q -r requirements.txt

# Start backend
echo -e "${GREEN}Starting FastAPI backend on http://localhost:8000${NC}"
python main.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Install frontend dependencies
echo -e "${GREEN}Installing frontend dependencies...${NC}"
cd ../frontend
if [ ! -d "node_modules" ]; then
    npm install
fi

# Start frontend
echo -e "${GREEN}Starting React frontend on http://localhost:3000${NC}"
npm start &
FRONTEND_PID=$!

echo -e "${GREEN}✅ Application started successfully!${NC}"
echo -e "${YELLOW}Frontend: http://localhost:3000${NC}"
echo -e "${YELLOW}Backend API: http://localhost:8000${NC}"
echo -e "${YELLOW}API Docs: http://localhost:8000/docs${NC}"
echo -e "\nPress Ctrl+C to stop all services"

# Wait for processes
wait $BACKEND_PID
wait $FRONTEND_PID