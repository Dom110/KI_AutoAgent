#!/bin/bash

# Build script for KI AutoAgent VS Code Extension

echo "🚀 Building KI AutoAgent VS Code Extension..."

# Navigate to extension directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Compile TypeScript
echo "🔨 Compiling TypeScript..."
npm run compile

# Package extension
echo "📦 Packaging extension..."
npx vsce package

echo "✅ Build complete! Extension package created."
echo ""
echo "To install the extension locally:"
echo "1. Open VS Code"
echo "2. Go to Extensions view (Cmd+Shift+X)"
echo "3. Click '...' menu > 'Install from VSIX...'"
echo "4. Select the generated .vsix file"
echo ""
echo "Or install via command line:"
echo "code --install-extension ki-autoagent-vscode-*.vsix"
