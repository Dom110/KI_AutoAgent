#!/bin/bash

# KI AutoAgent Backend - Dependency Installation Script
# For macOS with Homebrew Python (Python 3.13+)

echo "🚀 Installing KI AutoAgent Backend Dependencies..."
echo "================================================"

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "📦 Python version: $python_version"

# Check if Redis is running
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo "✅ Redis is running"
    else
        echo "⚠️  Redis is installed but not running. Start with: redis-server"
    fi
else
    echo "❌ Redis not installed. Install with: brew install redis"
fi

echo ""
echo "📦 Installing Python packages..."
echo "--------------------------------"

# Install core packages with --break-system-packages flag for Homebrew Python
pip3 install --break-system-packages -r requirements.txt

# Check if installation was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All dependencies installed successfully!"
    echo ""
    echo "🎯 Next steps:"
    echo "   1. Set your API keys:"
    echo "      export OPENAI_API_KEY='your-key-here'"
    echo "      export ANTHROPIC_API_KEY='your-key-here'"
    echo ""
    echo "   2. Start Redis if not running:"
    echo "      redis-server"
    echo ""
    echo "   3. Start the backend server:"
    echo "      python3 api/server.py"
else
    echo ""
    echo "❌ Some packages failed to install."
    echo "   Try installing them individually with:"
    echo "   pip3 install --break-system-packages <package-name>"
fi