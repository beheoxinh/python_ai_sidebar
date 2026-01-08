#!/bin/bash

# Exit on error
set -e

# Get absolute path to project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Cleaning up previous builds..."
rm -rf build dist

echo "Creating Source Distribution..."
mkdir -p dist/SmartAI

# Copy source files
cp *.py dist/SmartAI/
cp -r components dist/SmartAI/
cp -r images dist/SmartAI/
cp icon.svg dist/SmartAI/
cp requirements.txt dist/SmartAI/

# Create a runner script
cat > dist/SmartAI/SmartAI << 'EOF'
#!/bin/bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

# Activate venv if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Set environment variables for Linux/Wayland/Fcitx
export QT_QPA_PLATFORM=xcb
export GTK_IM_MODULE=fcitx
export QT_IM_MODULE=fcitx
export XMODIFIERS=@im=fcitx
export QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1

# Run the app
exec python3 main.py "$@"
EOF

chmod +x dist/SmartAI/SmartAI

echo "Source build complete! Files are in dist/SmartAI/"
