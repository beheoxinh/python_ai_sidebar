from PyQt6.QtWidgets import QFrame, QVBoxLayout, QPushButton, QSpacerItem, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal

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

        # Top section layout
        top_layout = QVBoxLayout()
        top_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        # btn_refresh = self.create_button("↺", "Refresh", self.refreshClicked)
        # top_layout.addWidget(btn_refresh, 0, Qt.AlignmentFlag.AlignHCenter)

        # Center section layout
        center_layout = QVBoxLayout()
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_chatgpt = self.create_button("images/chatgpt.svg", "Go to ChatGPT", self.chatgptClicked)
        btn_claude = self.create_button("images/claude.svg", "Go to Claude", self.claudeClicked)
        btn_mistral = self.create_button("images/mistral.svg", "Go to Mistral", self.mistralClicked)
        btn_hugging = self.create_button("images/hugging.svg", "Go to Hugging", self.huggingClicked)
        btn_copilot = self.create_button("images/copilot.svg", "Go to Copilot", self.copilotClicked)
        btn_gemini = self.create_button("images/gemini.svg", "Go to Gemini", self.geminiClicked)
        center_layout.addWidget(btn_chatgpt, 0, Qt.AlignmentFlag.AlignHCenter)
        center_layout.addWidget(btn_claude, 0, Qt.AlignmentFlag.AlignHCenter)
        center_layout.addWidget(btn_mistral, 0, Qt.AlignmentFlag.AlignHCenter)
        center_layout.addWidget(btn_hugging, 0, Qt.AlignmentFlag.AlignHCenter)
        center_layout.addWidget(btn_copilot, 0, Qt.AlignmentFlag.AlignHCenter)
        center_layout.addWidget(btn_gemini, 0, Qt.AlignmentFlag.AlignHCenter)

        # Bottom section layout
        bottom_layout = QVBoxLayout()
        bottom_layout.setAlignment(Qt.AlignmentFlag.AlignBottom)
        # btn_back = self.create_button("←", "Back", self.backClicked)
        # btn_forward = self.create_button("→", "Forward", self.forwardClicked)
        # bottom_layout.addWidget(btn_back, 0, Qt.AlignmentFlag.AlignHCenter)
        # bottom_layout.addWidget(btn_forward, 0, Qt.AlignmentFlag.AlignHCenter)

        # Add all sections to the main layout with spacers
        main_layout.addLayout(top_layout)
        main_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        main_layout.addLayout(center_layout)
        main_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        main_layout.addLayout(bottom_layout)

    def create_button(self, image_path, tooltip, signal):
        btn = QPushButton()
        btn.setFixedSize(60, 90)
        btn.setToolTip(tooltip)
        btn.clicked.connect(signal)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #2D2D2D;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 16px;
                cursor: pointer;
                background-image: url({image_path});
                background-repeat: no-repeat;
                background-position: center;
                background-size: contain;  /* Ensure the image fits within the button */
            }}
            QPushButton:hover {{
                background-color: #3D3D3D;
            }}
            QPushButton:pressed {{
                background-color: #404040;
            }}
        """)
        return btn