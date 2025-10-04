#!/bin/bash
# KI AutoAgent Installation Script v5.8.0
# Installs KI AutoAgent as a global service in $HOME/.ki_autoagent/

set -e

INSTALL_DIR="$HOME/.ki_autoagent"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 KI AutoAgent v5.8.0 - Global Agent Service Installation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if old installation exists
if [ -d "$HOME/.ki-autoagent" ]; then
    echo "⚠️  Old installation detected at: $HOME/.ki-autoagent"
    echo ""
    read -p "Migrate to new structure ($HOME/.ki_autoagent)? [Y/n]: " migrate

    if [[ ! $migrate =~ ^[Nn]$ ]]; then
        echo "📦 Migrating from old structure..."
        bash "$SCRIPT_DIR/scripts/migrate.sh"
        echo "✅ Migration complete!"
        echo ""
    fi
fi

# 1. Create directory structure
echo "📁 Creating directory structure..."
mkdir -p "$INSTALL_DIR"/{config/{instructions,instructions_updates/backups},data/{cache,embeddings,knowledge_base,models},logs}
echo "   ✓ Created $INSTALL_DIR"

# 2. Copy backend
echo ""
echo "📦 Installing backend..."
if [ -d "$INSTALL_DIR/backend" ]; then
    echo "   ⚠️  Backend already exists, creating backup..."
    mv "$INSTALL_DIR/backend" "$INSTALL_DIR/backend.backup.$(date +%Y%m%d_%H%M%S)"
fi

cp -r "$SCRIPT_DIR/backend" "$INSTALL_DIR/"
echo "   ✓ Backend installed"

# 3. Install base instructions
echo ""
echo "📝 Installing base instructions..."

# Check if instructions exist in backend
if [ -d "$SCRIPT_DIR/backend/.kiautoagent/instructions" ]; then
    INSTRUCTIONS_SOURCE="$SCRIPT_DIR/backend/.kiautoagent/instructions"
elif [ -d "$SCRIPT_DIR/backend/.ki_autoagent/instructions" ]; then
    INSTRUCTIONS_SOURCE="$SCRIPT_DIR/backend/.ki_autoagent/instructions"
else
    echo "   ⚠️  No instructions found in backend, skipping..."
    INSTRUCTIONS_SOURCE=""
fi

if [ -n "$INSTRUCTIONS_SOURCE" ]; then
    cp "$INSTRUCTIONS_SOURCE"/*.md "$INSTALL_DIR/config/instructions/" 2>/dev/null || true
    echo "   ✓ Base instructions installed"
else
    echo "   ⚠️  No base instructions found - agents will use defaults"
fi

# 4. Setup Python environment
echo ""
echo "🐍 Setting up Python environment..."
cd "$INSTALL_DIR"

# Check if venv already exists
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "   ✓ Virtual environment created"
else
    echo "   ✓ Virtual environment already exists"
fi

source venv/bin/activate

# Install dependencies
echo "   📦 Installing Python dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r backend/requirements.txt
echo "   ✓ Dependencies installed"

# 5. Copy/create .env if needed
echo ""
echo "🔐 Setting up configuration..."
if [ ! -f "$INSTALL_DIR/config/.env" ]; then
    if [ -f "$SCRIPT_DIR/.env" ]; then
        cp "$SCRIPT_DIR/.env" "$INSTALL_DIR/config/.env"
        echo "   ✓ .env copied from project"
    elif [ -f "$SCRIPT_DIR/.env.example" ]; then
        cp "$SCRIPT_DIR/.env.example" "$INSTALL_DIR/config/.env"
        echo "   ⚠️  .env created from example - please configure API keys!"
    else
        echo "   ⚠️  No .env file found - please create $INSTALL_DIR/config/.env with your API keys"
    fi
else
    echo "   ✓ .env already exists"
fi

# 6. Create version info
echo ""
echo "📋 Creating version info..."
python3 "$SCRIPT_DIR/scripts/create_version_info.py" --install-dir "$INSTALL_DIR"

# 7. Create convenience scripts
echo ""
echo "🔧 Creating convenience scripts..."

# Start script
cat > "$INSTALL_DIR/start.sh" << 'EOF'
#!/bin/bash
# Start KI AutoAgent Backend Server

INSTALL_DIR="$HOME/.ki_autoagent"
cd "$INSTALL_DIR"
source venv/bin/activate
cd backend

# Check for workspace parameter
if [ -n "$1" ]; then
    export KI_WORKSPACE_PATH="$1"
    echo "🎯 Workspace: $KI_WORKSPACE_PATH"
fi

python api/server_langgraph.py
EOF

chmod +x "$INSTALL_DIR/start.sh"
echo "   ✓ Created start.sh"

# Stop script
cat > "$INSTALL_DIR/stop.sh" << 'EOF'
#!/bin/bash
# Stop KI AutoAgent Backend Server

PID=$(lsof -ti :8001)
if [ -n "$PID" ]; then
    echo "🛑 Stopping backend (PID: $PID)..."
    kill $PID
    echo "✅ Backend stopped"
else
    echo "ℹ️  No backend process running on port 8001"
fi
EOF

chmod +x "$INSTALL_DIR/stop.sh"
echo "   ✓ Created stop.sh"

# Status script
cat > "$INSTALL_DIR/status.sh" << 'EOF'
#!/bin/bash
# Check KI AutoAgent Status

INSTALL_DIR="$HOME/.ki_autoagent"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 KI AutoAgent Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check installation
if [ -d "$INSTALL_DIR" ]; then
    echo "✅ Installation: $INSTALL_DIR"
else
    echo "❌ Installation not found"
    exit 1
fi

# Check version
if [ -f "$INSTALL_DIR/version.json" ]; then
    VERSION=$(python3 -c "import json; print(json.load(open('$INSTALL_DIR/version.json'))['installed_version'])")
    echo "📦 Version: $VERSION"
fi

# Check backend process
PID=$(lsof -ti :8001 2>/dev/null)
if [ -n "$PID" ]; then
    echo "✅ Backend: Running (PID: $PID)"
else
    echo "⏹️  Backend: Not running"
fi

# Check config
if [ -f "$INSTALL_DIR/config/.env" ]; then
    echo "✅ Config: $INSTALL_DIR/config/.env"
else
    echo "⚠️  Config: Missing .env file"
fi

# Check instructions
INSTRUCTIONS_COUNT=$(ls -1 "$INSTALL_DIR/config/instructions"/*.md 2>/dev/null | wc -l)
echo "📝 Base Instructions: $INSTRUCTIONS_COUNT files"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
EOF

chmod +x "$INSTALL_DIR/status.sh"
echo "   ✓ Created status.sh"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Installation Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📂 Installation directory: $INSTALL_DIR"
echo ""
echo "🚀 Quick Start:"
echo "   1. Configure API keys:"
echo "      vim $INSTALL_DIR/config/.env"
echo ""
echo "   2. Start backend:"
echo "      $INSTALL_DIR/start.sh [workspace_path]"
echo ""
echo "   3. Check status:"
echo "      $INSTALL_DIR/status.sh"
echo ""
echo "   4. Stop backend:"
echo "      $INSTALL_DIR/stop.sh"
echo ""
echo "📖 Documentation:"
echo "   - Installation: $SCRIPT_DIR/docs/INSTALLATION.md"
echo "   - Update Guide: $SCRIPT_DIR/docs/UPDATE_GUIDE.md"
echo "   - Usage: $SCRIPT_DIR/README.md"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
