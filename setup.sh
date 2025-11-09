#!/bin/bash
# Setup script for Zero-Knowledge Identity System
# Creates a virtual environment and installs dependencies

set -e  # Exit on error

echo "🔧 Setting up Zero-Knowledge Identity System Python environment..."

# Check Python version (requires 3.11+)
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Error: Python 3.11+ is required. Found: $(python3 --version)"
    echo "Please install Python 3.11 or later."
    exit 1
fi

echo "✅ Python version: $(python3 --version)"

# Create virtual environment
VENV_DIR=".venv"
if [ -d "$VENV_DIR" ]; then
    echo "📦 Virtual environment already exists at $VENV_DIR"
    read -p "Do you want to recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  Removing existing virtual environment..."
        rm -rf "$VENV_DIR"
    else
        echo "Using existing virtual environment."
    fi
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1

# Install production dependencies
echo "📥 Installing production dependencies..."
pip install -r requirements.txt

# Ask about development dependencies
read -p "Install development dependencies (pytest, hypothesis)? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📥 Installing development dependencies..."
    pip install -r requirements-dev.txt
fi

# Install package in editable mode
echo "📦 Installing zkidentity package in editable mode..."
pip install -e .

echo ""
echo "✅ Setup complete!"
echo ""
echo "To activate the virtual environment in the future, run:"
echo "  source $VENV_DIR/bin/activate"
echo ""
echo "To use the CLI:"
echo "  zkidentity --help"
echo ""
echo "Or use Python directly:"
echo "  python3 -m cli.main --help"
echo ""

