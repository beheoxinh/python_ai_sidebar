import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import win32gui
import win32con
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from sidebar import Sidebar

def bring_to_front(hwnd):
    """Bring window to front and restore if minimized"""
    if win32gui.IsIconic(hwnd):  # if minimized
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(hwnd)

def find_sidebar_window():
    """Find existing sidebar window"""
    def callback(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if "sidebar" in title.lower():
                extra.append(hwnd)

    windows = []
    win32gui.EnumWindows(callback, windows)
    return windows[0] if windows else None

def main():
    app = QApplication(sys.argv)

    # Check if this is a callback
    if len(sys.argv) > 1 and sys.argv[1].startswith('sidebarcallback://'):
        # Try to find existing sidebar window
        existing_hwnd = find_sidebar_window()
        if existing_hwnd:
            # Bring existing window to front
            bring_to_front(existing_hwnd)
            # Find the sidebar instance
            for widget in app.allWidgets():
                if isinstance(widget, Sidebar):
                    widget.content_widget.web_view.custom_page.handleAuthCallback(sys.argv[1])
                    break
        return

    # Normal startup
    sidebar = Sidebar()

    # Create system tray icon
    tray_icon = QSystemTrayIcon(QIcon("images/tray.svg"), parent=app)
    tray_menu = QMenu()

    show_action = QAction("Show")
    show_action.triggered.connect(sidebar.show_sidebar)
    tray_menu.addAction(show_action)

    exit_action = QAction("Exit App")
    exit_action.triggered.connect(app.quit)
    tray_menu.addAction(exit_action)

    tray_icon.setContextMenu(tray_menu)
    tray_icon.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    main()