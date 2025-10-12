#!/bin/bash
# KI AutoAgent Update Script v6.1-alpha
# Updates existing KI AutoAgent installation

set -e

INSTALL_DIR="$HOME/.ki_autoagent"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default options
INSTRUCTIONS_MODE="interactive"
NO_PROMPT=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --instructions)
            INSTRUCTIONS_MODE="$2"
            shift 2
            ;;
        --no-prompt)
            NO_PROMPT=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --instructions MODE   How to handle instruction updates:"
            echo "                        - interactive: Ask for each file (default)"
            echo "                        - overwrite: Replace all without asking"
            echo "                        - preserve: Keep all existing"
            echo "                        - backup: Save new to staging area"
            echo "  --no-prompt          Skip all prompts (use with --instructions)"
            echo "  --help               Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔄 KI AutoAgent v6.1-alpha - Update"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if installation exists
if [ ! -d "$INSTALL_DIR" ]; then
    echo "❌ KI AutoAgent not installed at $INSTALL_DIR"
    echo ""
    echo "Run install.sh first:"
    echo "  ./install.sh"
    exit 1
fi

# Check current version
if [ -f "$INSTALL_DIR/version.json" ]; then
    CURRENT_VERSION=$(python3 -c "import json; print(json.load(open('$INSTALL_DIR/version.json'))['installed_version'])" 2>/dev/null || echo "unknown")
    echo "📦 Current version: $CURRENT_VERSION"
fi

NEW_VERSION=$(python3 -c "import sys; sys.path.insert(0, '$SCRIPT_DIR/backend'); from __version__ import __version__; print(__version__)")
echo "📦 New version: $NEW_VERSION"
echo ""

# Check if backend is running (v6.1-alpha uses port 8002)
PID=$(lsof -ti :8002 2>/dev/null)
if [ -n "$PID" ]; then
    if [ "$NO_PROMPT" = false ]; then
        echo "⚠️  Backend is currently running on port 8002 (PID: $PID)"
        read -p "Stop backend for update? [Y/n]: " stop_backend
        if [[ ! $stop_backend =~ ^[Nn]$ ]]; then
            kill $PID
            echo "✅ Backend stopped"
            sleep 2
        else
            echo "⚠️  Updating while backend is running may cause issues"
        fi
    else
        echo "🛑 Stopping v6.1-alpha backend (PID: $PID)..."
        kill $PID
        sleep 2
    fi
fi

# 1. Backup current installation
BACKUP_DIR="$INSTALL_DIR/backups/$(date +%Y%m%d_%H%M%S)"
echo "💾 Creating backup..."
mkdir -p "$BACKUP_DIR"
cp -r "$INSTALL_DIR/backend" "$BACKUP_DIR/" 2>/dev/null || true
cp "$INSTALL_DIR/version.json" "$BACKUP_DIR/" 2>/dev/null || true
echo "   ✓ Backup created: $BACKUP_DIR"

# 2. Update Backend Code
echo ""
echo "📦 Updating backend code..."
rsync -a --delete --exclude='*.pyc' --exclude='__pycache__' --exclude='*.log' \
    "$SCRIPT_DIR/backend/" "$INSTALL_DIR/backend/"
echo "   ✓ Backend updated"

# 3. Update Instructions
echo ""
echo "📝 Updating base instructions..."

# Check if instructions exist in source
if [ -d "$SCRIPT_DIR/backend/.kiautoagent/instructions" ]; then
    INSTRUCTIONS_SOURCE="$SCRIPT_DIR/backend/.kiautoagent/instructions"
elif [ -d "$SCRIPT_DIR/backend/.ki_autoagent/instructions" ]; then
    INSTRUCTIONS_SOURCE="$SCRIPT_DIR/backend/.ki_autoagent/instructions"
else
    echo "   ⚠️  No instructions found in source, skipping..."
    INSTRUCTIONS_SOURCE=""
fi

if [ -n "$INSTRUCTIONS_SOURCE" ]; then
    # Use Python script for intelligent update
    python3 "$SCRIPT_DIR/scripts/update_instructions.py" \
        --source "$INSTRUCTIONS_SOURCE" \
        --target "$INSTALL_DIR/config/instructions" \
        --mode "$INSTRUCTIONS_MODE" \
        $([ "$NO_PROMPT" = true ] && echo "--no-prompt")
else
    echo "   ⏭️  Instructions update skipped"
fi

# 4. Update Python dependencies
echo ""
echo "🐍 Updating Python dependencies..."
source "$INSTALL_DIR/venv/bin/activate"
pip install --quiet --upgrade pip
pip install --quiet -r "$INSTALL_DIR/backend/requirements.txt" --upgrade
echo "   ✓ Dependencies updated"

# 5. Update version.json
echo ""
echo "📋 Updating version info..."
python3 "$SCRIPT_DIR/scripts/create_version_info.py" \
    --install-dir "$INSTALL_DIR" \
    --update

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Update Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📦 Updated from $CURRENT_VERSION → $NEW_VERSION"
echo "💾 Backup: $BACKUP_DIR"
echo ""
echo "🚀 Start backend:"
echo "   $INSTALL_DIR/start.sh"
echo ""
echo "📝 Note: v6.1-alpha uses WebSocket init protocol"
echo "   Workspace is sent by VS Code extension during connection"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
