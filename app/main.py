import sys
from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QStackedWidget,
    QFrame, QCheckBox
)

APP_STYLE = """
QMainWindow, QWidget { background: #0b1020; color: #edf2ff; font-size: 14px; }
QFrame#sidebar { background: #10172a; border: 1px solid #25304b; border-radius: 14px; }
QLabel#brand { color: #8b9cff; font-size: 25px; font-weight: bold; }
QLabel#heading { font-size: 27px; font-weight: bold; }
QLabel#muted { color: #9ba8c7; }
QPushButton {
    background: #18223b; color: #edf2ff; border: 1px solid #2b395a;
    border-radius: 9px; padding: 11px; text-align: left;
}
QPushButton:hover { background: #29375b; }
QPushButton#primary { background: #665cff; border: none; font-weight: bold; }
QPushButton#primary:hover { background: #8178ff; }
QLineEdit, QTextEdit {
    background: #111a2e; color: #edf2ff; border: 1px solid #2b395a;
    border-radius: 9px; padding: 10px;
}
QCheckBox { spacing: 10px; }
"""

class JayWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("JayAI", "JayDesktop")
        self.setWindowTitle("Jay AI — Personal Assistant")
        self.resize(1050, 700)
        self.setMinimumSize(760, 520)

        root = QWidget()
        layout = QHBoxLayout(root)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(18)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        side = QVBoxLayout(sidebar)
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
                lambda checked=False, i=page_index: self.pages.setCurrentIndex(i)
            )
            side.addWidget(button)

        side.addStretch()
        side.addWidget(QLabel("DESKTOP EDITION", objectName="muted"))
        layout.addWidget(sidebar)
        layout.addWidget(self.pages, 1)

        self.pages.addWidget(self.make_home())
        self.pages.addWidget(self.make_personalization())
        self.pages.addWidget(self.make_about())
        self.setCentralWidget(root)

        self.dark_mode = self.settings.value("dark_mode", True, type=bool)
        self.apply_theme()

    def make_home(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addWidget(QLabel("YOUR PERSONAL ASSISTANT", objectName="muted"))
        layout.addWidget(QLabel("Good day. I'm Jay.", objectName="heading"))
        layout.addWidget(QLabel(
            "Your desktop command center starts here.", objectName="muted"
        ))

        self.chat = QTextEdit()
        self.chat.setReadOnly(True)
        self.chat.setPlainText(
            "JAY  •  READY\n\n"
            "Welcome! This is the first desktop foundation.\n"
            "Chat interface: ready\n"
            "Online AI, voice, news and weather: not connected yet\n\n"
            "Tell me what you would like to work on."
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
        text = self.message.text().strip()
        if not text:
            return
        self.chat.append(f"\nYOU\n{text}\n")
        self.chat.append(
            "JAY\nI'm ready for the next development step. "
            "My online AI services are not connected yet.\n"
        )
        self.message.clear()

    def make_personalization(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Personalization", objectName="heading"))
        layout.addWidget(QLabel(
            "Choose how your Jay AI desktop app looks and behaves.",
            objectName="muted"
        ))
        self.dark_check = QCheckBox("Use dark command-center theme")
        self.dark_check.setChecked(
            self.settings.value("dark_mode", True, type=bool)
        )
        self.dark_check.checkStateChanged.connect(self.save_theme)
        layout.addWidget(self.dark_check)
        layout.addWidget(QLabel("Your preference is saved on this computer."))
        layout.addStretch()
        return page

    def save_theme(self, state):
        self.dark_mode = state == Qt.CheckState.Checked.value
        self.settings.setValue("dark_mode", self.dark_mode)
        self.apply_theme()

    def apply_theme(self):
        if self.dark_mode:
            self.setStyleSheet(APP_STYLE)
        else:
            self.setStyleSheet("""
                QMainWindow, QWidget { background: #f3f5fb; color: #17213b; }
                QFrame#sidebar { background: #e4e9f7; border-radius: 14px; }
                QLabel#brand { color: #5147db; font-size: 25px; font-weight: bold; }
                QLabel#heading { font-size: 27px; font-weight: bold; }
                QLabel#muted { color: #66718a; }
                QPushButton { background: #e1e7f5; color: #17213b;
                    border: 1px solid #ccd4e8; border-radius: 9px; padding: 11px; }
                QPushButton#primary { background: #665cff; color: white; }
                QLineEdit, QTextEdit { background: white; color: #17213b;
                    border: 1px solid #ccd4e8; border-radius: 9px; padding: 10px; }
            """)

    def make_about(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("About Jay AI", objectName="heading"))
        layout.addWidget(QLabel("Jay AI — Windows Personal Assistant"))
        layout.addWidget(QLabel("Version 0.1.0"))
        layout.addWidget(QLabel(
            "This is the starting foundation. Online AI, voice, "
            "news, weather, installer and automatic updates are future steps."
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
