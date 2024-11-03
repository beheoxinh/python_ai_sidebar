from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton

class TitleBar(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        self.setFixedHeight(30)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 5, 0)
        layout.setSpacing(0)

        title = QLabel("BeHeoXinh AI Sidebar")
        title.setStyleSheet("""
            color: white; 
            font-weight: bold;
            font-size: 12px;
        """)
        layout.addWidget(title)

        layout.addStretch()

        close_button = QPushButton("×")
        close_button.setFixedSize(30, 30)
        close_button.clicked.connect(self.parent.hide_sidebar)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                font-size: 20px;
                font-family: Arial;
                padding: 0;
                margin: 0;
            }
            QPushButton:hover {
                background-color: #ff0000;
            }
        """)
        layout.addWidget(close_button)

        self.setStyleSheet("""
            TitleBar {
                background-color: #282C34;
            }
        """)
