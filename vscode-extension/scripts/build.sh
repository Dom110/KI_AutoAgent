#!/bin/bash

# KI AutoAgent VS Code Extension Build Script
# This script builds, packages, and optionally installs the extension

set -e  # Exit on any error

echo "🤖 KI AutoAgent Extension Build Script"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    print_error "npm is not installed. Please install npm first."
    exit 1
fi

print_status "Node.js version: $(node --version)"
print_status "npm version: $(npm --version)"

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    print_status "Installing dependencies..."
    npm install
    print_success "Dependencies installed"
else
    print_status "Dependencies already installed"
fi

# Install vsce if not available
if ! command -v vsce &> /dev/null; then
    print_status "Installing Visual Studio Code Extension CLI (vsce)..."
    npm install -g vsce
    print_success "vsce installed globally"
fi

# Clean previous build
print_status "Cleaning previous build..."
rm -rf out/
rm -f *.vsix
print_success "Clean completed"

# Compile TypeScript
print_status "Compiling TypeScript..."
npm run compile
if [ $? -eq 0 ]; then
    print_success "TypeScript compilation completed"
else
    print_error "TypeScript compilation failed"
    exit 1
fi

# Package the extension
print_status "Packaging extension..."
vsce package --out ki-autoagent-vscode-1.0.0.vsix
if [ $? -eq 0 ]; then
    print_success "Extension packaged successfully: ki-autoagent-vscode-1.0.0.vsix"
else
    print_error "Extension packaging failed"
    exit 1
fi

# Get package size
PACKAGE_SIZE=$(du -h ki-autoagent-vscode-1.0.0.vsix | cut -f1)
print_status "Package size: $PACKAGE_SIZE"

# Ask if user wants to install locally
echo ""
read -p "Do you want to install the extension locally for testing? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Installing extension locally..."
    code --install-extension ki-autoagent-vscode-1.0.0.vsix --force
    if [ $? -eq 0 ]; then
        print_success "Extension installed successfully!"
        print_status "You can now test the extension in VS Code"
        print_status "Open VS Code Chat (Ctrl+Shift+I) and type '@ki hello' to test"
    else
        print_error "Extension installation failed"
        exit 1
    fi
fi

echo ""
print_success "Build process completed!"
echo ""
echo "📦 Package created: ki-autoagent-vscode-1.0.0.vsix"
echo "🚀 Ready for distribution!"
echo ""
echo "Next steps:"
echo "  1. Test the extension in VS Code"
echo "  2. Configure API keys in VS Code settings"
echo "  3. Try '@ki create a hello world function' in VS Code Chat"
echo "  4. Publish to marketplace: vsce publish"
echo ""