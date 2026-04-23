#!/bin/bash
# Setup script for SpotFetch with latest yt-dlp from GitHub

set -e

echo "🚀 Setting up SpotFetch..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip3."
    exit 1
fi

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install Git."
    exit 1
fi

echo "✓ Python, pip, and git found"

# Check if ffmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  FFmpeg is not installed. This is required for audio conversion."
    echo "   Install it using:"
    echo "   - Ubuntu/Debian: sudo apt-get install ffmpeg"
    echo "   - macOS: brew install ffmpeg"
    echo "   - Windows: https://ffmpeg.org/download.html"
    exit 1
fi

echo "✓ FFmpeg found"

# Create virtual environment if specified
if [ "$1" == "--venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✓ Virtual environment created and activated"
fi

# Install base requirements
echo "📚 Installing base Python dependencies..."
pip install --upgrade pip setuptools wheel
pip install --no-cache-dir \
    --trusted-host pypi.python.org \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org \
    -r requirements.txt

# Clone and install yt-dlp from GitHub
echo "⬇️  Installing latest yt-dlp from GitHub..."
if [ -d "yt-dlp" ]; then
    rm -rf yt-dlp
fi

git clone https://github.com/yt-dlp/yt-dlp.git
cd yt-dlp
pip install --no-cache-dir \
    --trusted-host pypi.python.org \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org \
    -e .
cd ..
rm -rf yt-dlp

echo ""
echo "✅ SpotFetch setup complete!"
echo ""
echo "You can now use SpotFetch:"
echo "  - Menu mode:  python3 menu.py"
echo "  - CLI mode:   python3 cli.py --help"
echo ""
