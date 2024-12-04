from PyQt6.QtWidgets import QFrame, QVBoxLayout, QPushButton, QSpacerItem, QSizePolicy, QMenu
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from utils import AppPaths


class NavigationBar(QFrame):
    refreshClicked = pyqtSignal()
    backClicked = pyqtSignal()
    forwardClicked = pyqtSignal()
    chatgptClicked = pyqtSignal()
    claudeClicked = pyqtSignal()
    mistralClicked = pyqtSignal()
    copilotClicked = pyqtSignal()
    geminiClicked = pyqtSignal()
    huggingClicked = pyqtSignal()
    clearCacheRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.setFixedWidth(70)
        self.setStyleSheet("""
            NavigationBar {
                background-color: #1E1E1E;
                border: none;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 0, 5, 0)
        main_layout.setSpacing(20)

        paths = AppPaths()

        center_layout = QVBoxLayout()
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Tạo các buttons với icons
        buttons = [
            ("chatgpt.svg", 0.8, "ChatGPT", self.chatgptClicked),
            ("claude.svg", 0.8, "Claude", self.claudeClicked),
            ("mistral.svg", 0.6, "Mistral", self.mistralClicked),
            ("hugging.svg", 0.7, "Hugging", self.huggingClicked),
            ("copilot.svg", 0.7, "Copilot", self.copilotClicked),
            ("gemini.svg", 0.7, "Gemini", self.geminiClicked)
        ]

        for icon_file, image_size, tooltip, signal in buttons:
            btn = self.create_button(paths.get_path('images', icon_file), image_size, tooltip, signal)
            center_layout.addWidget(btn, 0, Qt.AlignmentFlag.AlignHCenter)

        main_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        main_layout.addLayout(center_layout)
        main_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

    def create_button(self, image_path, image_size, tooltip, signal):
        btn = QPushButton()
        btn.setFixedSize(60, 90)
        btn.setToolTip(tooltip)
        btn.clicked.connect(signal)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)

        # Set icon cho button
        icon = QIcon(image_path)
        btn.setIcon(icon)
        btn.setIconSize(btn.size() * image_size)  # Icon size 80% của button size

        # Style không còn background-image nữa
        btn.setStyleSheet("""
            QPushButton {
                background-color: #2D2D2D;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 16px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #3D3D3D;
            }
            QPushButton:pressed {
                background-color: #404040;
            }
        """)

        # Add context menu for clearing cache
        btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        btn.customContextMenuRequested.connect(lambda pos, b=btn: self.show_context_menu(pos, b))

        return btn

    def show_context_menu(self, pos, button):
        menu = QMenu(self)
        clear_cache_action = menu.addAction("Clear Cache")
        clear_cache_action.triggered.connect(lambda: self.clear_cache(button))
        menu.exec(button.mapToGlobal(pos))

    def clear_cache(self, button):
        self.clearCacheRequested.emit()