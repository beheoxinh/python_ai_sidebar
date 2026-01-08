#!/bin/bash

APP_NAME="SmartAI"
INSTALL_DIR="$HOME/.local/share/$APP_NAME"
DESKTOP_DIR="$HOME/.local/share/applications"

# Lấy đường dẫn thư mục chứa script này
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/SmartAI"

echo "Installing $APP_NAME..."

# 1. Xóa bản cũ
if [ -d "$INSTALL_DIR" ]; then
    rm -rf "$INSTALL_DIR"
fi

# 2. Copy ứng dụng
echo "Copying application files..."
mkdir -p "$INSTALL_DIR"
cp -r "$SOURCE_DIR"/* "$INSTALL_DIR/"

# 3. Cài đặt dependencies (Tạo venv để không ảnh hưởng hệ thống)
echo "Setting up Python environment..."
cd "$INSTALL_DIR"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 4. Tạo shortcut
echo "Creating desktop shortcut..."
mkdir -p "$DESKTOP_DIR"

cat > "$DESKTOP_DIR/smartai.desktop" << EOF
[Desktop Entry]
Name=Smart AI Sidebar
Comment=AI Assistant Sidebar
Exec="$INSTALL_DIR/SmartAI"
Icon=$INSTALL_DIR/images/tray.svg
Terminal=false
Type=Application
Categories=Utility;
StartupNotify=false
X-GNOME-Autostart-enabled=true
EOF

chmod +x "$DESKTOP_DIR/smartai.desktop"
chmod +x "$INSTALL_DIR/SmartAI"

echo "Installation complete!"
