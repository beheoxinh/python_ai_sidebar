from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QSizePolicy
from .navigation_bar import NavigationBar
from .web_view import CustomWebView


class ContentWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Tạo WebView trước
        self.web_view = CustomWebView()
        self.web_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Tạo Navigation Bar
        self.nav_bar = NavigationBar()

        # Thêm widgets vào layout theo thứ tự WebView trước, NavBar sau
        layout.addWidget(self.web_view)
        layout.addWidget(self.nav_bar)

        self.setStyleSheet("""
            ContentWidget {
                background-color: #33322F;
            }
        """)

    def setup_connections(self):
        # Kết nối các signals từ navigation bar với web view
        self.nav_bar.homeClicked.connect(lambda: self.web_view.setUrl(QUrl("https://claude.ai/")))
        self.nav_bar.refreshClicked.connect(self.web_view.reload)
        self.nav_bar.backClicked.connect(self.web_view.back)
        self.nav_bar.forwardClicked.connect(self.web_view.forward)
