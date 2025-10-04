#!/bin/bash

# KI AutoAgent Backend Setup Script

echo "="
echo "🚀 KI AutoAgent Backend Setup"
echo "="
echo ""

# Check Python version
echo "🔍 Checking Python version..."
python3 --version

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "⚠️  Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "📈 Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo ""
echo "📥 Installing requirements..."
pip install -r requirements.txt

echo ""
echo "="
echo "✅ Setup complete!"
echo "="
echo ""
echo "To run the server:"
echo "  ./run.sh"
echo ""
echo "To run tests:"
echo "  ./test.sh"