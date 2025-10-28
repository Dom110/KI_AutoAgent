#!/bin/bash
# Start v7.0 Server with correct environment

cd /Users/dominikfoert/git/KI_AutoAgent

# Kill any existing server
lsof -ti:8002 | xargs kill -9 2>/dev/null || true

# Activate venv and start server
source venv/bin/activate
export PYTHONPATH=/Users/dominikfoert/git/KI_AutoAgent

python backend/api/server_v7_supervisor.py
