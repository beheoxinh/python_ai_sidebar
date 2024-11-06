import os
import sys
import logging
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from utils import AppPaths
from sidebar import Sidebar


def show_error(message):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setText("Error")
    msg.setInformativeText(message)
    msg.setWindowTitle("Application Error")
    msg.exec()


def main():
    try:
        app = QApplication(sys.argv)

        paths = AppPaths()

        # Log important paths
        logging.info(f"Current working directory: {os.getcwd()}")
        logging.info(f"Executable path: {sys.executable}")
        logging.info(f"System PATH: {os.environ.get('PATH')}")

        # Try to load icon
        icon_path = paths.get_path('images', 'tray.svg')
        logging.info(f"Trying to load icon from: {icon_path}")

        if not os.path.exists(icon_path):
            logging.error(f"Icon file not found: {icon_path}")
            raise FileNotFoundError(f"Icon file not found: {icon_path}")

        icon = QIcon(icon_path)
        if icon.isNull():
            logging.error("Failed to load icon")
            raise Exception("Failed to load icon")

        tray_icon = QSystemTrayIcon(icon, parent=app)
        tray_menu = QMenu()

        try:
            sidebar = Sidebar()
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

        return app.exec()

    except Exception as e:
        logging.exception("Fatal error in main")
        show_error(str(e))
        return 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        logging.exception("Fatal error")
        print(f"Fatal error: {e}")
        sys.exit(1)