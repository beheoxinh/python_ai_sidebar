# File: sidebar.py
import win32gui
import win32con
import win32api
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QApplication
from PyQt6.QtGui import QCursor, QShortcut, QKeySequence

from components.title_bar import TitleBar
from components.resize_handle import ResizeHandle
from components.content_widget import ContentWidget


class Sidebar(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("sidebar")
        self.is_visible = False
        self.active_screen = None
        self.is_resizing = False
        self.has_active_popup = False
        self.popup_windows = []
        self.init_ui()
        self.setup_shortcut()

    def init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint
        )

        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        self.resize_handle = ResizeHandle(self)
        container_layout.addWidget(self.resize_handle)

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.title_bar = TitleBar(self)
        main_layout.addWidget(self.title_bar)

        self.content_widget = ContentWidget()
        main_layout.addWidget(self.content_widget)

        # Kết nối signals từ webview
        self.content_widget.web_view.popupCreated.connect(self.handle_popup_created)
        self.content_widget.web_view.authCompleted.connect(self.handle_auth_completed)

        container_layout.addWidget(main_widget)

        self.setCentralWidget(container)

        primary_screen = QApplication.primaryScreen()
        if primary_screen:
            self.setFixedWidth(int(primary_screen.geometry().width() * 0.5))

        self.mouse_timer = QTimer()
        self.mouse_timer.timeout.connect(self.check_mouse)
        self.mouse_timer.start(50)

        self.previous_state = win32api.GetKeyState(0x01)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #33322F;
            }
        """)

        self.hide()

    def handle_popup_created(self, popup):
        """Handler cho popup mới được tạo"""
        print("Sidebar: Popup created")
        self.popup_windows.append(popup)
        self.has_active_popup = True
        self.mouse_timer.stop()

        # Kết nối popup signals
        popup.popupClosed.connect(lambda: self.handle_popup_closed(popup))

    def handle_popup_closed(self, popup=None):
        """Handler cho popup đóng"""
        print("Sidebar: Popup closed")
        if popup in self.popup_windows:
            self.popup_windows.remove(popup)

        if not self.popup_windows:
            self.has_active_popup = False
            self.mouse_timer.start(50)

    def handle_auth_completed(self, callback_url):
        """Handle authentication completion"""
        print(f"Authentication completed: {callback_url}")

        # Đóng tất cả popup và khôi phục trạng thái sidebar sau khi xác thực xong
        for popup in self.popup_windows[:]:
            popup.close()
        self.popup_windows.clear()
        self.has_active_popup = False
        self.mouse_timer.start(50)  # Khởi động lại mouse timer

    def setup_shortcut(self):
        self.shortcut = QShortcut(QKeySequence("Ctrl+Shift+S"), self)
        self.shortcut.activated.connect(self.toggle_sidebar)

        self.global_timer = QTimer(self)
        self.global_timer.timeout.connect(self.check_hotkey)
        self.global_timer.start(100)

        self.ctrl_pressed = False
        self.shift_pressed = False
        self.s_pressed = False

    def check_hotkey(self):
        ctrl_state = win32api.GetKeyState(win32con.VK_CONTROL)
        shift_state = win32api.GetKeyState(win32con.VK_SHIFT)
        s_state = win32api.GetKeyState(0x53)  # 0x53 là mã ASCII của phím S

        if (ctrl_state < 0 and shift_state < 0 and s_state < 0 and
                not (self.ctrl_pressed and self.shift_pressed and self.s_pressed)):
            self.toggle_sidebar()

        self.ctrl_pressed = ctrl_state < 0
        self.shift_pressed = shift_state < 0
        self.s_pressed = s_state < 0

    def check_mouse(self):
        try:
            if self.is_resizing or self.has_active_popup:
                return

            screen = self.get_screen_at_cursor()
            if not screen:
                return

            cursor_pos = win32gui.GetCursorPos()
            screen_geometry = screen.geometry()

            is_near_edge = (cursor_pos[0] >= screen_geometry.x() + screen_geometry.width() - 5 and
                            cursor_pos[0] <= screen_geometry.x() + screen_geometry.width())

            if is_near_edge and not self.is_visible:
                self.active_screen = screen
                if not self.is_resizing:
                    self.setFixedWidth(int(screen.geometry().width() * 0.5))
                self.update_position()
                self.show()
                self.is_visible = True

            # Kiểm tra click chuột
            current_state = win32api.GetKeyState(0x01)
            if current_state != self.previous_state:
                self.previous_state = current_state
                if current_state < 0 and self.is_visible and not self.is_resizing:
                    window_rect = self.geometry()
                    cursor_point = QPoint(cursor_pos[0], cursor_pos[1])

                    if not window_rect.contains(cursor_point):
                        QTimer.singleShot(100, self._delayed_hide)

        except Exception as e:
            print(f"Error in check_mouse: {e}")

    def _delayed_hide(self):
        try:
            if self.has_active_popup:
                return

            cursor_pos = win32gui.GetCursorPos()
            cursor_point = QPoint(cursor_pos[0], cursor_pos[1])
            window_rect = self.geometry()

            if not window_rect.contains(cursor_point):
                self.hide()
                self.is_visible = False
        except Exception as e:
            print(f"Error in delayed hide: {e}")

    def toggle_sidebar(self):
        if self.is_visible:
            self.hide_sidebar()
        else:
            self.show_sidebar()

    def hide_sidebar(self):
        self.hide()
        self.is_visible = False

    def show_sidebar(self):
        screen = self.get_screen_at_cursor()
        if screen:
            self.active_screen = screen
            if not self.is_resizing:
                self.setFixedWidth(int(screen.geometry().width() * 0.5))
            self.update_position()
            self.show()
            self.is_visible = True

    def closeEvent(self, event):
        """Handle application closure"""
        for popup in self.popup_windows[:]:
            popup.close()
        self.popup_windows.clear()
        super().closeEvent(event)

    def get_current_screen_width(self):
        if self.active_screen:
            return self.active_screen.geometry().width()
        return QApplication.primaryScreen().geometry().width()

    def resizing_started(self):
        self.is_resizing = True

    def resizing_finished(self):
        self.is_resizing = False

    def get_screen_at_cursor(self):
        cursor_pos = QCursor.pos()
        for screen in QApplication.screens():
            if screen.geometry().contains(cursor_pos):
                return screen
        return None

    def update_position(self):
        if not self.active_screen:
            return

        screen_geometry = self.active_screen.geometry()
        taskbar_height = self.get_taskbar_height()

        self.setGeometry(
            screen_geometry.x() + screen_geometry.width() - self.width(),
            screen_geometry.y(),
            self.width(),
            screen_geometry.height() - taskbar_height
        )

    def get_taskbar_height(self):
        taskbar = win32gui.FindWindow('Shell_TrayWnd', None)
        if taskbar:
            rect = win32gui.GetWindowRect(taskbar)
            return rect[3] - rect[1]
        return 0

    def moveEvent(self, event):
        if self.active_screen:
            self.update_position()

    def mousePressEvent(self, event):
        if self.content_widget.web_view.underMouse():
            event.accept()
        else:
            super().mousePressEvent(event)
