import sys
from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QStackedWidget,
    QFrame, QCheckBox, QComboBox, QColorDialog, QMessageBox
)

DEFAULT_ACCENT = "#1687ff"
MIDNIGHT = "#07111f"

class JayWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("JayAI", "JayDesktop")

        self.dark_mode = self.settings.value("dark_mode", True, type=bool)
        self.accent = self.settings.value("accent", DEFAULT_ACCENT)
        if not QColor(self.accent).isValid():
            self.accent = DEFAULT_ACCENT

        self.layout_mode = self.settings.value(
            "layout_mode", "Command Center"
        )
        if self.layout_mode not in ("Minimal", "Compact", "Command Center"):
            self.layout_mode = "Command Center"

        self.setWindowTitle("Jay AI — Personal Assistant")
        self.resize(1050, 700)
        self.setMinimumSize(760, 520)

        root = QWidget()
        self.root_layout = QHBoxLayout(root)
        self.root_layout.setContentsMargins(18, 18, 18, 18)
        self.root_layout.setSpacing(18)

        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(220)
        side = QVBoxLayout(self.sidebar)
        side.setContentsMargins(16, 20, 16, 16)

        side.addWidget(QLabel("JAY AI", objectName="brand"))
        side.addWidget(QLabel("PERSONAL COMMAND CENTER", objectName="muted"))

        self.pages = QStackedWidget()
        for label, page_index in [
            ("⌂   Home", 0),
            ("⚙   Personalization", 1),
            ("ⓘ   About Jay", 2),
        ]:
            button = QPushButton(label)
            button.clicked.connect(
                lambda checked=False, i=page_index:
                self.pages.setCurrentIndex(i)
            )
            side.addWidget(button)

        side.addStretch()
        side.addWidget(QLabel("DESKTOP EDITION", objectName="muted"))

        self.root_layout.addWidget(self.sidebar)
        self.root_layout.addWidget(self.pages, 1)

        self.pages.addWidget(self.make_home())
        self.pages.addWidget(self.make_personalization())
        self.pages.addWidget(self.make_about())
        self.setCentralWidget(root)

        self.apply_layout()
        self.apply_theme()

    def make_home(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)

        # A simple placeholder until the cartoon avatar asset is integrated.
        avatar_row = QHBoxLayout()
        avatar_row.addStretch()
        self.avatar = QLabel("J")
        self.avatar.setObjectName("avatar")
        self.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar.setFixedSize(64, 64)
        avatar_row.addWidget(self.avatar)
        avatar_row.addStretch()
        layout.addLayout(avatar_row)

        layout.addWidget(QLabel("YOUR PERSONAL ASSISTANT", objectName="muted"))
        layout.addWidget(QLabel("Good day. I'm Jay.", objectName="heading"))
        layout.addWidget(QLabel(
            "Your desktop command center starts here.",
            objectName="muted"
        ))

        self.chat = QTextEdit()
        self.chat.setReadOnly(True)
        self.chat.setPlainText(
            "JAY  •  READY\n\n"
            "Welcome to Jay AI.\n"
            "Desktop interface: available\n"
            "Online AI, voice, news and weather: not connected yet\n\n"
            "Your personalization settings are saved on this computer."
        )
        layout.addWidget(self.chat, 1)

        row = QHBoxLayout()
        self.message = QLineEdit()
        self.message.setPlaceholderText("Type a message to Jay...")
        self.message.returnPressed.connect(self.send_message)

        send = QPushButton("Send  ➤")
        send.setObjectName("primary")
        send.clicked.connect(self.send_message)

        row.addWidget(self.message, 1)
        row.addWidget(send)
        layout.addLayout(row)
        return page

    def send_message(self):
        message = self.message.text().strip()
        if not message:
            return

        self.chat.append(f"\nYOU\n{message}\n")
        self.chat.append(
            "JAY\nI'm ready for the next development step. "
            "Online AI services are not connected yet.\n"
        )
        self.message.clear()

    def make_personalization(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)

        layout.addWidget(QLabel("Personalization", objectName="heading"))
        layout.addWidget(QLabel(
            "Make Jay feel like your own assistant.",
            objectName="muted"
        ))

        theme_title = QLabel("APPEARANCE")
        theme_title.setObjectName("section")
        layout.addWidget(theme_title)

        self.dark_check = QCheckBox("Use dark command-center theme")
        self.dark_check.setChecked(self.dark_mode)
        self.dark_check.toggled.connect(self.save_theme)
        layout.addWidget(self.dark_check)

        accent_row = QHBoxLayout()
        accent_text = QVBoxLayout()
        accent_text.addWidget(QLabel("Accent colour"))
        accent_text.addWidget(QLabel(
            "Choose the colour used for buttons and highlights.",
            objectName="muted"
        ))
        self.color_button = QPushButton("Choose colour")
        self.color_button.clicked.connect(self.choose_accent)
        accent_row.addLayout(accent_text, 1)
        accent_row.addWidget(self.color_button)
        layout.addLayout(accent_row)

        layout.addWidget(QLabel("LAYOUT", objectName="section"))
        layout.addWidget(QLabel(
            "Select how much space Jay uses on your screen.",
            objectName="muted"
        ))

        self.layout_combo = QComboBox()
        self.layout_combo.addItems([
            "Minimal", "Compact", "Command Center"
        ])
        self.layout_combo.setCurrentText(self.layout_mode)
        self.layout_combo.currentTextChanged.connect(self.save_layout)
        layout.addWidget(self.layout_combo)

        self.preference_status = QLabel("")
        self.preference_status.setObjectName("muted")
        layout.addWidget(self.preference_status)

        reset = QPushButton("Restore default appearance")
        reset.clicked.connect(self.reset_preferences)
        layout.addWidget(reset)

        layout.addStretch()
        return page

    def choose_accent(self):
        color = QColorDialog.getColor(
            QColor(self.accent), self, "Choose Jay's accent colour"
        )
        if color.isValid():
            self.accent = color.name()
            self.settings.setValue("accent", self.accent)
            self.apply_theme()
            self.preference_status.setText(
                f"Accent colour saved: {self.accent}"
            )

    def save_theme(self, checked):
        self.dark_mode = checked
        self.settings.setValue("dark_mode", checked)
        self.apply_theme()
        self.preference_status.setText("Theme preference saved.")

    def save_layout(self, mode):
        self.layout_mode = mode
        self.settings.setValue("layout_mode", mode)
        self.apply_layout()
        self.preference_status.setText(f"{mode} layout saved.")

    def reset_preferences(self):
        self.dark_mode = True
        self.accent = DEFAULT_ACCENT
        self.layout_mode = "Command Center"

        self.settings.setValue("dark_mode", self.dark_mode)
        self.settings.setValue("accent", self.accent)
        self.settings.setValue("layout_mode", self.layout_mode)

        self.dark_check.setChecked(self.dark_mode)
        self.layout_combo.setCurrentText(self.layout_mode)
        self.apply_layout()
        self.apply_theme()
        self.preference_status.setText("Default preferences restored.")

    def apply_layout(self):
        if self.layout_mode == "Minimal":
            self.sidebar.setFixedWidth(175)
            self.root_layout.setContentsMargins(10, 10, 10, 10)
            self.root_layout.setSpacing(10)
        elif self.layout_mode == "Compact":
            self.sidebar.setFixedWidth(195)
            self.root_layout.setContentsMargins(12, 12, 12, 12)
            self.root_layout.setSpacing(12)
        else:
            self.sidebar.setFixedWidth(220)
            self.root_layout.setContentsMargins(18, 18, 18, 18)
            self.root_layout.setSpacing(18)

    def apply_theme(self):
        accent = QColor(self.accent)
        hover = accent.lighter(120).name()
        base = MIDNIGHT if self.dark_mode else "#f3f5fb"
        panel = "#101a2b" if self.dark_mode else "#e4e9f7"
        field = "#0d1727" if self.dark_mode else "#ffffff"
        text = "#edf4ff" if self.dark_mode else "#17213b"
        muted = "#94a8c7" if self.dark_mode else "#66718a"
        border = "#263852" if self.dark_mode else "#ccd4e8"
        accent_text = "#ffffff"

        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background: {base};
                color: {text};
                font-size: 14px;
            }}
            QFrame#sidebar {{
                background: {panel};
                border: 1px solid {border};
                border-radius: 14px;
            }}
            QLabel#brand {{
                color: {accent.name()};
                font-size: 25px;
                font-weight: bold;
            }}
            QLabel#heading {{
                font-size: 27px;
                font-weight: bold;
            }}
            QLabel#muted {{
                color: {muted};
            }}
            QLabel#section {{
                color: {accent.name()};
                font-size: 13px;
                font-weight: bold;
            }}
            QLabel#avatar {{
                background: {panel};
                color: {accent.name()};
                border: 2px solid {accent.name()};
                border-radius: 32px;
                font-size: 30px;
                font-weight: bold;
            }}
            QPushButton {{
                background: {panel};
                color: {text};
                border: 1px solid {border};
                border-radius: 9px;
                padding: 10px;
                text-align: left;
            }}
            QPushButton:hover {{
                border-color: {accent.name()};
                background: {hover};
                color: {accent_text};
            }}
            QPushButton#primary {{
                background: {accent.name()};
                color: {accent_text};
                border: none;
                font-weight: bold;
            }}
            QLineEdit, QTextEdit, QComboBox {{
                background: {field};
                color: {text};
                border: 1px solid {border};
                border-radius: 9px;
                padding: 10px;
            }}
            QComboBox QAbstractItemView {{
                background: {field};
                color: {text};
                selection-background-color: {accent.name()};
            }}
            QCheckBox {{
                spacing: 10px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
            }}
            QCheckBox::indicator:checked {{
                background: {accent.name()};
                border: 1px solid {accent.name()};
            }}
        """)
        self.color_button.setText(f"●  {self.accent}")

    def make_about(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("About Jay AI", objectName="heading"))
        layout.addWidget(QLabel("Jay AI — Windows Personal Assistant"))
        layout.addWidget(QLabel("Version 0.2.0"))
        layout.addWidget(QLabel(
            "Personalization preferences are stored locally. "
            "Online AI, voice, news, weather, the real avatar, "
            "installer and automatic updates still require implementation."
        ))
        layout.addStretch()
        return page


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setOrganizationName("JayAI")
    app.setApplicationName("JayDesktop")
    window = JayWindow()
    window.show()
    sys.exit(app.exec())
