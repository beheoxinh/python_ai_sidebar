# File: sidebar.py
import sys
from PyQt6.QtCore import Qt, QTimer, QPoint, QEvent
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QApplication
from PyQt6.QtGui import QCursor, QShortcut, QKeySequence

# Conditional imports for Windows
HAS_WIN32 = False
if sys.platform == 'win32':
    try:
        import win32gui
        import win32api
        HAS_WIN32 = True
    except ImportError:
        pass

from components.title_bar import TitleBar
from components.resize_handle import ResizeHandle
from components.content_widget import ContentWidget

class EdgeTrigger(QWidget):
    def __init__(self, sidebar_ref):
        super().__init__(None)
        self.sidebar_ref = sidebar_ref
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.ToolTip 
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setMouseTracking(True)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 1);")

    def enterEvent(self, event):
        if self.sidebar_ref:
            self.sidebar_ref.show_sidebar()
        super().enterEvent(event)
        
    def mousePressEvent(self, event):
        if self.sidebar_ref:
            self.sidebar_ref.show_sidebar()
        super().mousePressEvent(event)

class Sidebar(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SmartAI Sidebar")
        self.is_visible = False
        self.active_screen = None
        self.is_resizing = False
        self.has_active_popup = False
        self.popup_windows = []
        self.last_width = None
        self.edge_trigger = None
        self.init_ui()
        self.setup_shortcut()

        # Cài đặt bộ lọc sự kiện để bắt sự kiện mất focus
        QApplication.instance().installEventFilter(self)

    def setup_shortcut(self):
        shortcut = QShortcut(QKeySequence("Ctrl+Shift+F"), self)
        shortcut.activated.connect(self.toggle_sidebar)

    def init_ui(self):
        # Dùng Tool + Parent để ổn định focus và ẩn khỏi taskbar
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
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

        self.content_widget.web_view.popupCreated.connect(self.handle_popup_created)
        self.content_widget.web_view.authCompleted.connect(self.handle_auth_completed)

        container_layout.addWidget(main_widget)

        self.setCentralWidget(container)

        self.rightmost_screen = max(QApplication.screens(), key=lambda s: s.geometry().x() + s.geometry().width())
        
        if self.rightmost_screen:
            self.setFixedWidth(int(self.rightmost_screen.geometry().width() * 0.6))

        if not HAS_WIN32:
            self.setup_edge_trigger()

        self.setStyleSheet("""
            QMainWindow {
                background-color: #33322F;
                border-left: 1px solid #444;
            }
        """)

    def setup_edge_trigger(self):
        try:
            self.edge_trigger = EdgeTrigger(self)
            self.update_trigger_position()
            self.edge_trigger.show()
        except Exception as e:
            print(f"Failed to setup edge trigger: {e}")

    def update_trigger_position(self):
        if self.edge_trigger and self.rightmost_screen:
            geo = self.rightmost_screen.geometry()
            trigger_width = 5
            x = geo.x() + geo.width() - trigger_width
            y = geo.y()
            h = geo.height()
            self.edge_trigger.setGeometry(x, y, trigger_width, h)
            self.edge_trigger.raise_()

    def handle_popup_created(self, popup):
        self.popup_windows.append(popup)
        self.has_active_popup = True
        popup.popupClosed.connect(lambda: self.handle_popup_closed(popup))

    def handle_popup_closed(self, popup=None):
        if popup in self.popup_windows:
            self.popup_windows.remove(popup)
        if not self.popup_windows:
            self.has_active_popup = False
            self.activateWindow()

    def handle_auth_completed(self, callback_url):
        for popup in self.popup_windows[:]:
            popup.close()
        self.popup_windows.clear()
        self.has_active_popup = False
        self.activateWindow()

    def toggle_sidebar(self):
        if self.is_visible:
            self.hide_sidebar()
        else:
            self.show_sidebar()

    def hide_sidebar(self):
        self.hide()
        self.is_visible = False
        if self.edge_trigger:
            self.edge_trigger.show()
            self.edge_trigger.raise_()

    def show_sidebar(self):
        screen = self.rightmost_screen
        if screen:
            self.active_screen = screen
            if not self.is_resizing:
                self.setFixedWidth(self.last_width or int(screen.geometry().width() * 0.6))
            
            self.update_position()
            self.show()
            self.update_position()
            self.is_visible = True
            
            # Force focus sequence - Quan trọng để bắt sự kiện mất focus sau này
            self.raise_()
            self.activateWindow()
            self.setFocus(Qt.FocusReason.ActiveWindowFocusReason)
            
            # Double check focus sau 100ms
            QTimer.singleShot(100, self.ensure_focus)

    def ensure_focus(self):
        if self.is_visible:
            self.activateWindow()
            self.setFocus()

    def update_position(self):
        if not self.active_screen:
            return
        avail_geo = self.active_screen.availableGeometry()
        x = avail_geo.x() + avail_geo.width() - self.width()
        y = avail_geo.y()
        h = avail_geo.height()
        self.setGeometry(x, y, self.width(), h)
        self.move(x, y)
        
        if not HAS_WIN32 and self.edge_trigger:
            self.update_trigger_position()

    def showEvent(self, event):
        QTimer.singleShot(0, self.update_position)
        super().showEvent(event)

    def closeEvent(self, event):
        for popup in self.popup_windows[:]:
            popup.close()
        self.popup_windows.clear()
        if self.edge_trigger:
            self.edge_trigger.close()
        super().closeEvent(event)

    def eventFilter(self, obj, event):
        # Chỉ bắt sự kiện mất focus (WindowDeactivate)
        # Đây là cách duy nhất đáng tin cậy để biết người dùng đã click ra ngoài
        if event.type() == QEvent.Type.WindowDeactivate:
            if obj == self and self.is_visible and not self.is_resizing and not self.has_active_popup:
                # Kiểm tra xem focus có chuyển sang con của sidebar không (popup)
                # Nếu không phải con, tức là click ra ngoài -> Ẩn
                self.hide_sidebar()
                return False

        return super().eventFilter(obj, event)

    def get_current_screen_width(self):
        if self.active_screen:
            return self.active_screen.geometry().width()
        return QApplication.primaryScreen().geometry().width()

    def resizing_started(self):
        self.is_resizing = True

    def resizing_finished(self):
        self.is_resizing = False
        self.last_width = self.width()
