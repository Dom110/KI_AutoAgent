#!/bin/bash

# KI AutoAgent Backend Run Script

echo "="
echo "🚀 Starting KI AutoAgent Backend"
echo "="
echo ""

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ Virtual environment not found!"
    echo "Please run ./setup.sh first"
    exit 1
fi

# Run the server
echo "🌐 Starting FastAPI server on http://localhost:8000"
echo "📚 API docs available at http://localhost:8000/docs"
echo "🔌 WebSocket endpoint: ws://localhost:8000/ws/chat"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python -m uvicorn api.server:app --reload --host 0.0.0.0 --port 8000