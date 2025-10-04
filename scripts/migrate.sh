#!/bin/bash
# Migration Script from .ki-autoagent to .ki_autoagent structure

set -e

OLD_DIR="$HOME/.ki-autoagent"
NEW_DIR="$HOME/.ki_autoagent"

echo "📦 Migrating KI AutoAgent installation..."
echo "   From: $OLD_DIR"
echo "   To:   $NEW_DIR"
echo ""

if [ ! -d "$OLD_DIR" ]; then
    echo "❌ Old installation not found at: $OLD_DIR"
    exit 1
fi

if [ -d "$NEW_DIR" ]; then
    echo "⚠️  New directory already exists: $NEW_DIR"
    read -p "Overwrite? [y/N]: " overwrite
    if [[ ! $overwrite =~ ^[Yy]$ ]]; then
        echo "Migration cancelled"
        exit 0
    fi

    # Backup existing new directory
    BACKUP="$NEW_DIR.backup.$(date +%Y%m%d_%H%M%S)"
    mv "$NEW_DIR" "$BACKUP"
    echo "   ✓ Backed up existing to: $BACKUP"
fi

# Create new structure
mkdir -p "$NEW_DIR"/{config/{instructions,instructions_updates/backups},data/{cache,embeddings,knowledge_base,models},logs}

# Migrate backend
echo "📦 Migrating backend..."
if [ -d "$OLD_DIR/backend" ]; then
    cp -r "$OLD_DIR/backend" "$NEW_DIR/"
    echo "   ✓ Backend migrated"
fi

# Migrate venv
echo "🐍 Migrating virtual environment..."
if [ -d "$OLD_DIR/venv" ]; then
    cp -r "$OLD_DIR/venv" "$NEW_DIR/"
    echo "   ✓ venv migrated"
fi

# Migrate config
echo "🔐 Migrating configuration..."
if [ -f "$OLD_DIR/config/.env" ]; then
    cp "$OLD_DIR/config/.env" "$NEW_DIR/config/.env"
    echo "   ✓ .env migrated"
fi

# Migrate instructions from various possible locations
echo "📝 Migrating instructions..."
INSTRUCTIONS_FOUND=false

# Check possible locations for instructions
if [ -d "$OLD_DIR/config/.kiautoagent/instructions" ]; then
    cp "$OLD_DIR/config/.kiautoagent/instructions"/*.md "$NEW_DIR/config/instructions/" 2>/dev/null && INSTRUCTIONS_FOUND=true
elif [ -d "$OLD_DIR/config/.ki-autoagent/instructions" ]; then
    cp "$OLD_DIR/config/.ki-autoagent/instructions"/*.md "$NEW_DIR/config/instructions/" 2>/dev/null && INSTRUCTIONS_FOUND=true
elif [ -d "$OLD_DIR/config/instructions" ]; then
    cp "$OLD_DIR/config/instructions"/*.md "$NEW_DIR/config/instructions/" 2>/dev/null && INSTRUCTIONS_FOUND=true
fi

if [ "$INSTRUCTIONS_FOUND" = true ]; then
    echo "   ✓ Instructions migrated"
else
    echo "   ⚠️  No instructions found in old installation"
fi

# Migrate data if exists
echo "💾 Migrating data..."
if [ -d "$OLD_DIR/data" ]; then
    cp -r "$OLD_DIR/data"/* "$NEW_DIR/data/" 2>/dev/null || true
    echo "   ✓ Data migrated"
fi

# Migrate logs
echo "📋 Migrating logs..."
if [ -d "$OLD_DIR/logs" ]; then
    cp -r "$OLD_DIR/logs"/* "$NEW_DIR/logs/" 2>/dev/null || true
    echo "   ✓ Logs migrated"
fi

# Migrate version info if exists
if [ -f "$OLD_DIR/version.json" ]; then
    cp "$OLD_DIR/version.json" "$NEW_DIR/version.json"
    echo "   ✓ Version info migrated"
fi

echo ""
echo "✅ Migration complete!"
echo ""
echo "📂 New installation: $NEW_DIR"
echo "📂 Old installation: $OLD_DIR (can be safely deleted)"
echo ""
read -p "Delete old installation directory? [y/N]: " delete_old

if [[ $delete_old =~ ^[Yy]$ ]]; then
    rm -rf "$OLD_DIR"
    echo "✅ Old installation deleted"
else
    echo "⏭️  Old installation kept at: $OLD_DIR"
    echo "   You can delete it manually later if everything works correctly"
fi
