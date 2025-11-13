#!/bin/bash
# 🚀 E2E Test Setup Script
# Automatically creates test workspace and prepares everything

set -e

PROJECT_ROOT="/Users/dominikfoert/git/KI_AutoAgent"
TEST_WORKSPACE="$HOME/TestApps/e2e_test_workspace"

echo "=================================="
echo "🚀 E2E Test Setup"
echo "=================================="
echo ""

# Step 1: Create test workspace
echo "📁 Creating test workspace..."
mkdir -p "$TEST_WORKSPACE"
echo "   ✅ $TEST_WORKSPACE"

# Step 2: Copy test files
echo ""
echo "📋 Copying test files..."
cp "$PROJECT_ROOT/e2e_test_v7_0_supervisor.py" "$TEST_WORKSPACE/"
echo "   ✅ e2e_test_v7_0_supervisor.py"

# Step 3: Check project structure
echo ""
echo "🔍 Verifying project structure..."
if [ ! -f "$PROJECT_ROOT/backend/api/server_v7_mcp.py" ]; then
    echo "   ❌ ERROR: server_v7_mcp.py not found!"
    exit 1
fi
echo "   ✅ server_v7_mcp.py found"

if [ ! -d "$PROJECT_ROOT/venv" ]; then
    echo "   ❌ ERROR: venv not found! Run setup first"
    exit 1
fi
echo "   ✅ venv found"

# Step 4: Summary
echo ""
echo "=================================="
echo "✅ E2E Test Setup Complete!"
echo "=================================="
echo ""
echo "📝 Next steps:"
echo ""
echo "1️⃣  Start the server (Terminal 1):"
echo "   cd $PROJECT_ROOT"
echo "   source venv/bin/activate"
echo "   python backend/api/server_v7_mcp.py"
echo ""
echo "2️⃣  Run tests (Terminal 2):"
echo "   cd $TEST_WORKSPACE"
echo "   python e2e_test_v7_0_supervisor.py"
echo ""
echo "📚 See E2E_TEST_SETUP.md for detailed guide"
echo "=================================="