#!/bin/bash

# KI AutoAgent VS Code Extension Installer
# Automated installation script for development

set -e

echo "🤖 KI AutoAgent VS Code Extension Installer"
echo "============================================="
echo ""

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found"
    echo "Please run this script from the vscode-extension directory"
    exit 1
fi

# Check for VS Code
if ! command -v code &> /dev/null; then
    echo "❌ Error: VS Code CLI not found"
    echo "Please install VS Code and add 'code' to your PATH"
    echo "Instructions: https://code.visualstudio.com/docs/editor/command-line"
    exit 1
fi

# Get current version
CURRENT_VERSION=$(node -p "require('./package.json').version")
echo "📦 Current Version: $CURRENT_VERSION"
echo ""

# Install dependencies
echo "📥 Installing dependencies..."
npm install
echo "✅ Dependencies installed"
echo ""

# Compile extension
echo "🔨 Compiling extension..."
npm run compile
echo "✅ Extension compiled"
echo ""

# Create VSIX package
echo "📦 Creating VSIX package..."
if ! command -v vsce &> /dev/null; then
    echo "Installing vsce (Visual Studio Code Extension Manager)..."
    npm install -g @vscode/vsce
fi

vsce package --allow-star-activation
VSIX_FILE="ki-autoagent-vscode-${CURRENT_VERSION}.vsix"
echo "✅ VSIX package created: $VSIX_FILE"
echo ""

# Install extension
echo "🚀 Installing extension in VS Code..."
code --install-extension "$VSIX_FILE" --force
echo "✅ Extension installed successfully!"
echo ""

# Launch VS Code
echo "🎉 Installation Complete!"
echo ""
echo "Next steps:"
echo "1. Open VS Code (if not already open)"
echo "2. Check the Output panel: View > Output > 'KI AutoAgent'"  
echo "3. Open Chat panel: Ctrl+Shift+I or View > Chat"
echo "4. Test the agents: @ki, @richter, @architect, @codesmith, etc."
echo ""
echo "Configuration:"
echo "• Set your API keys in VS Code Settings"
echo "• Search for 'KI AutoAgent' in settings"
echo "• Configure OpenAI, Anthropic, and Perplexity keys"
echo ""

# Option to launch VS Code
read -p "Launch VS Code now? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Launching VS Code..."
    code .
fi

echo ""
echo "🎯 Happy coding with KI AutoAgent!"