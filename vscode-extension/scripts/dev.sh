#!/bin/bash

# KI AutoAgent VS Code Extension Development Script
# Quick development setup and testing

set -e

echo "🛠️ KI AutoAgent Development Mode"
echo "================================"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[DEV]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Install dependencies
if [ ! -d "node_modules" ]; then
    print_status "Installing dependencies..."
    npm install
fi

# Start TypeScript compiler in watch mode
print_status "Starting TypeScript compiler in watch mode..."
echo "Press Ctrl+C to stop"
echo ""
print_success "Ready for development!"
echo ""
echo "Development workflow:"
echo "  1. Make changes to TypeScript files in src/"
echo "  2. Compiler will automatically recompile"
echo "  3. Press F5 in VS Code to launch Extension Development Host"
echo "  4. Test your changes in the new VS Code window"
echo "  5. Use Ctrl+R in Extension Development Host to reload changes"
echo ""
echo "Testing commands:"
echo "  • @ki hello world"
echo "  • @architect design a web API"
echo "  • @codesmith implement a Python class"
echo "  • @tradestrat create a trading strategy"
echo ""

# Start watch mode
npm run watch