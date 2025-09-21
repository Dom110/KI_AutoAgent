#!/bin/bash

# KI AutoAgent Backend Test Script

echo "="
echo "🧪 KI AutoAgent Backend Tests"
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

# Check if server is running
echo "🔍 Checking if server is running..."
if curl -s http://localhost:8000 > /dev/null; then
    echo "✅ Server is running"
else
    echo "❌ Server is not running!"
    echo "Please run ./run.sh in another terminal"
    exit 1
fi

echo ""

# Run tests
python tests/test_server.py