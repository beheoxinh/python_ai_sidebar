import os
import sys

# --- CẤU HÌNH MÔI TRƯỜNG LINUX (PHẢI ĐẶT TRƯỚC KHI IMPORT QT) ---
if sys.platform != 'win32':
    # 1. Ép dùng X11 (XWayland)
    os.environ["QT_QPA_PLATFORM"] = "xcb"
    
    # 2. Cấu hình bộ gõ Fcitx
    os.environ["GTK_IM_MODULE"] = "fcitx"
    os.environ["QT_IM_MODULE"] = "fcitx"
    os.environ["XMODIFIERS"] = "@im=fcitx"
    
    # 3. Kích hoạt Accessibility (Hỗ trợ tiếp cận)
    # Đôi khi Chromium cần cái này để kích hoạt IME trên Linux
    os.environ["QT_LINUX_ACCESSIBILITY_ALWAYS_ON"] = "1"

import logging
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox, QWidget
from utils import AppPaths
from sidebar import Sidebar

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Chỉ log ra console
    ]
)

def show_error(message):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setText("Error")
    msg.setInformativeText(message)
    msg.setWindowTitle("Application Error")
    msg.exec()


def main():
    try:
        logging.info("Starting application...")
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)

        paths = AppPaths()

        # --- DEBUG TIẾNG VIỆT ---
        if sys.platform != 'win32':
            plugin_path = os.path.join(paths.get_root(), 'PyQt6/Qt6/plugins/platforminputcontexts/libfcitx5platforminputcontextplugin.so')
            logging.info(f"Checking for Fcitx plugin at: {plugin_path}")
            if os.path.exists(plugin_path):
                logging.info("Fcitx plugin FOUND in application bundle.")
            else:
                logging.warning("Fcitx plugin NOT FOUND. Vietnamese input may not work.")
        # --- END DEBUG ---

        # Load icon
        icon_path = paths.get_path('images', 'tray.svg')
        logging.info(f"Trying to load icon from: {icon_path}")

        icon = QIcon(icon_path)
        if not os.path.exists(icon_path):
            logging.warning(f"Icon file not found: {icon_path}")
        elif icon.isNull():
            logging.warning("Failed to load icon (format might not be supported)")
        
        tray_icon = QSystemTrayIcon(icon, parent=app)
        tray_menu = QMenu()

        # Widget ẩn làm cha để ẩn Sidebar khỏi Taskbar
        dummy_parent = QWidget()
        dummy_parent.hide()

        logging.info("Creating sidebar...")
        try:
            sidebar = Sidebar(parent=dummy_parent)
        except Exception as e:
            logging.exception("Failed to create sidebar")
            raise Exception(f"Failed to create sidebar: {str(e)}")

        show_action = QAction("Show")
        show_action.triggered.connect(sidebar.show_sidebar)
        tray_menu.addAction(show_action)

        exit_action = QAction("Quit")
        exit_action.triggered.connect(app.quit)
        tray_menu.addAction(exit_action)

        tray_icon.setContextMenu(tray_menu)
        tray_icon.show()
        
        logging.info("Application started successfully.")
        return app.exec()

    except Exception as e:
        logging.exception("Fatal error in main")
        print(f"Fatal error: {e}")
        return 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        logging.exception("Fatal error")
        print(f"Fatal error: {e}")
        sys.exit(1)
