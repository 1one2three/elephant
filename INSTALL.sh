#!/bin/bash

# Citation Mind Installation Script

echo "======================================"
echo "Citation Mind Installation"
echo "======================================"
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python 3.8 or higher is required. Found: $python_version"
    exit 1
fi

echo "✓ Python $python_version found"
echo ""

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 not found. Please install pip."
    exit 1
fi

echo "✓ pip3 found"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies"
    exit 1
fi

echo "✓ Dependencies installed"
echo ""

# Install the package
echo "Installing Citation Mind..."
pip3 install -e .

if [ $? -ne 0 ]; then
    echo "Error: Failed to install Citation Mind"
    exit 1
fi

echo "✓ Citation Mind installed"
echo ""

# Create config directory
config_dir="$HOME/.citation-mind"
echo "Creating configuration directory at $config_dir..."
mkdir -p "$config_dir"

# Copy example files
if [ ! -f "$config_dir/.env" ]; then
    cp .env.example "$config_dir/.env"
    echo "✓ Created .env file (add your API keys here)"
fi

echo ""
echo "======================================"
echo "Installation Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Initialize your profile:"
echo "   citation-mind init"
echo ""
echo "2. (Optional) Add API keys to $config_dir/.env"
echo ""
echo "3. Fetch your citation data:"
echo "   citation-mind fetch --all"
echo ""
echo "4. View your dashboard:"
echo "   citation-mind dashboard"
echo ""
echo "For more information, see USAGE_GUIDE.md"
echo ""
