#!/bin/bash

APP_NAME="SmartAI"
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/dist/SmartAI"
ICON_PATH="$APP_DIR/images/tray.svg"
EXEC_PATH="$APP_DIR/SmartAI"
DESKTOP_FILE="$HOME/.local/share/applications/smartai.desktop"

echo "Creating desktop entry at $DESKTOP_FILE..."

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=Smart AI Sidebar
Comment=AI Sidebar Assistant
Exec="$EXEC_PATH"
Icon=$ICON_PATH
Terminal=false
Type=Application
Categories=Utility;
StartupNotify=false
EOF

chmod +x "$DESKTOP_FILE"

echo "Done! You can now find 'Smart AI Sidebar' in your Application Launcher."
