#!/bin/bash

# Exit on error
set -e

echo "=== Starting Packaging Process ==="

# 1. Build ứng dụng trước
./build.sh

# 2. Chuẩn bị thư mục đóng gói
PACKAGE_DIR="SmartAI_Linux_Installer"
rm -rf "$PACKAGE_DIR"
mkdir -p "$PACKAGE_DIR"

# 3. Copy thư mục build (dist/SmartAI) vào thư mục đóng gói
echo "Copying build artifacts..."
cp -r dist/SmartAI "$PACKAGE_DIR/"

# 4. Copy script cài đặt vào thư mục đóng gói
echo "Adding installer script..."
cp install_template.sh "$PACKAGE_DIR/install.sh"
chmod +x "$PACKAGE_DIR/install.sh"

# 5. Tạo file hướng dẫn
echo "Creating README..."
cat > "$PACKAGE_DIR/README.txt" << EOF
Smart AI Sidebar - Linux Installation
=====================================

How to install:
1. Open Terminal in this folder.
2. Run the following command:
   ./install.sh

3. The app will be installed to ~/.local/share/SmartAI
   and a shortcut will be added to your Application Menu.

Enjoy!
EOF

# 6. Nén thành file .tar.gz
echo "Compressing package..."
tar -czf "${PACKAGE_DIR}.tar.gz" "$PACKAGE_DIR"

# 7. Dọn dẹp
rm -rf "$PACKAGE_DIR"

echo "=== Packaging Complete! ==="
echo "Your installer is ready: $(pwd)/${PACKAGE_DIR}.tar.gz"
