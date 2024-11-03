# File: components/navigation_bar.py
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal


class NavigationBar(QFrame):
    # homeClicked = pyqtSignal()
    refreshClicked = pyqtSignal()
    backClicked = pyqtSignal()
    forwardClicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.setFixedWidth(50)
        self.setStyleSheet("""
            NavigationBar {
                background-color: #1E1E1E;
                border: none;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Tạo các nút với callbacks
        nav_buttons = [
            # ("⌂", "Home", self.homeClicked),
            ("↺", "Refresh", self.refreshClicked),
            ("←", "Back", self.backClicked),
            ("→", "Forward", self.forwardClicked)
        ]

        for symbol, tooltip, signal in nav_buttons:
            btn = QPushButton(symbol)
            btn.setFixedSize(40, 40)
            btn.setToolTip(tooltip)
            btn.clicked.connect(signal)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2D2D2D;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    font-size: 16px;
                }
                QPushButton:hover {
                    background-color: #3D3D3D;
                }
                QPushButton:pressed {
                    background-color: #404040;
                }
            """)
            layout.addWidget(btn, 0, Qt.AlignmentFlag.AlignHCenter)

        layout.addStretch()
