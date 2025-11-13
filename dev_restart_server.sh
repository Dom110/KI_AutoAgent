#!/bin/bash
# 🔄 Development Server Restart Script
# Quick way to restart server during development

set -e

PROJECT_ROOT="/Users/dominikfoert/git/KI_AutoAgent"

echo "=================================="
echo "🔄 KI AutoAgent Server Restart"
echo "=================================="

# Step 1: Kill existing server
echo "🛑 Stopping existing server..."
pkill -f "python backend/api/server_v7_mcp.py" || echo "   (no server running)"

# Step 2: Wait a bit for clean shutdown
sleep 2

# Step 3: Go to project root
cd "$PROJECT_ROOT"
echo "📁 Working directory: $(pwd)"

# Step 4: Activate venv
source venv/bin/activate
echo "✅ Venv activated"

# Step 5: Start server
echo ""
echo "🚀 Starting server..."
python backend/api/server_v7_mcp.py