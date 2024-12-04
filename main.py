import os
import sys
import logging
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
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


class ClipboardHandler:
    def __init__(self, clipboard):
        self.clipboard = clipboard
        self.last_text = ""  # Lưu nội dung clipboard gần nhất
        self.is_updating = False  # Ngăn chặn vòng lặp sự kiện
        self.retry_count = 0  # Số lần thử lại khi xác minh clipboard thất bại
        self.max_retries = 3  # Số lần thử tối đa
        self.timer = QTimer()
        self.timer.setSingleShot(True)

    def on_clipboard_change(self):
        try:
            if self.is_updating:
                return

            if self.clipboard.mimeData().hasText():
                current_text = self.clipboard.text()

                if not current_text.strip():
                    logging.info("Clipboard content is empty; skipping.")
                    return

                if current_text == self.last_text:
                    logging.info("Clipboard content is unchanged; skipping.")
                    return

                logging.info(f"Clipboard changed. Current text: {current_text}")

                # Ghi đè nội dung clipboard
                self.is_updating = True
                self.retry_count = 0  # Reset số lần thử lại
                self.clipboard.setText(current_text)
                logging.info("Clipboard content overwritten with the same text.")

                # Đảm bảo nội dung được đặt lại thành công
                QTimer.singleShot(50, lambda: self.verify_clipboard(current_text))
            else:
                logging.info("Clipboard does not contain text; skipping.")

        except Exception as e:
            logging.exception("Error handling clipboard change")

    def verify_clipboard(self, expected_text):
        """Đảm bảo clipboard được ghi đúng nội dung."""
        if self.clipboard.text() != expected_text:
            self.retry_count += 1
            logging.warning(f"Clipboard verification failed. Retrying ({self.retry_count}/{self.max_retries})...")

            if self.retry_count <= self.max_retries:
                QTimer.singleShot(50, lambda: self.clipboard.setText(expected_text))
                QTimer.singleShot(100, lambda: self.verify_clipboard(expected_text))  # Tăng thời gian xác minh
            else:
                logging.error("Max retries reached. Unable to set clipboard content.")
        else:
            logging.info("Clipboard verification successful.")
            self.last_text = expected_text  # Cập nhật last_text nếu thành công
            self.is_updating = False  # Reset trạng thái sau khi hoàn tất

    def reset_updating_flag(self):
        self.is_updating = False  # Reset trạng thái


def main():
    try:
        app = QApplication(sys.argv)

        paths = AppPaths()

        # Log các đường dẫn quan trọng
        logging.info(f"Current working directory: {os.getcwd()}")
        logging.info(f"Executable path: {sys.executable}")
        logging.info(f"System PATH: {os.environ.get('PATH')}")

        # Load icon
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

        # Thiết lập Clipboard listener
        clipboard = app.clipboard()
        clipboard_handler = ClipboardHandler(clipboard)
        clipboard.dataChanged.connect(clipboard_handler.on_clipboard_change)

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
