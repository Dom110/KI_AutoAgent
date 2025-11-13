#!/bin/bash
# Start KI AutoAgent v7.0 MCP Server with venv Python

set -e

cd /Users/dominikfoert/git/KI_AutoAgent

echo "🚀 Starting KI AutoAgent v7.0 Pure MCP Server..."
echo "📌 Using Python: $(./venv/bin/python --version)"
echo ""

./venv/bin/python backend/api/server_v7_mcp.py