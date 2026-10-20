import sys
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QLabel, QPushButton,
    QLineEdit, QVBoxLayout, QHBoxLayout, QGridLayout, QStackedWidget,
    QTextEdit, QScrollArea
)

BG = "#031126"
PANEL = "#041a35"
BORDER = "#8b5cf6"
CYAN = "#39e58c"
TEXT = "#eef6ff"
MUTED = "#9cbce2"
ACCENT = "#7c3aed"

TABS = [
    ("⌂", "Home"), ("♩", "Voice Assistant"), ("⌕", "Files & Search"),
    ("▦", "Apps & Software"), ("▣", "Messages & Calls"),
    ("▱", "Device Control"), ("⚙", "Settings"), ("▤", "Memory & Notes"),
    ("▦", "News & Weather"), ("?", "Help & Support")
]

class JayWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("JayAI", "JayDesktop")
        self.setWindowTitle("Jay AI")
        self.resize(1500, 920)
        self.setMinimumSize(1050, 700)
        root = QWidget()
        root.setObjectName("root")
        outer = QHBoxLayout(root)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(12)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(228)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(8, 12, 8, 8)
        brand = QLabel("✦  Jay AI")
        brand.setObjectName("brand")
        side.addWidget(brand)
        tagline = QLabel("Your Personal AI Assistant")
        tagline.setObjectName("muted")
        tagline.setWordWrap(True)
        side.addWidget(tagline)
        side.addSpacing(18)

        self.pages = QStackedWidget()
        self.nav_buttons = []
        for i, (symbol, name) in enumerate(TABS):
            b = QPushButton(f"{symbol}   {name}")
            b.setObjectName("nav")
            b.setCheckable(True)
            b.clicked.connect(lambda checked=False, index=i: self.open_tab(index))
            side.addWidget(b)
            self.nav_buttons.append(b)
        side.addStretch()
        mini = QFrame()
        mini.setObjectName("card")
        mini_layout = QVBoxLayout(mini)
        mini_layout.addWidget(QLabel("◉  Jay AI", objectName="heading"))
        mini_layout.addWidget(QLabel("🟢 Online", objectName="muted"))
        mini_layout.addWidget(QLabel("Always here, whenever you need me.", objectName="muted"))
        side.addWidget(mini)
        outer.addWidget(sidebar)

        main = QWidget()
        main_layout = QVBoxLayout(main)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)
        top = QFrame()
        top.setObjectName("topbar")
        top_layout = QHBoxLayout(top)
        top_layout.addWidget(QLabel("◉", objectName="avatar"))
        greeting = QVBoxLayout()
        greeting.addWidget(QLabel("Good day, Sir!", objectName="heading"))
        greeting.addWidget(QLabel("How can I help you today?", objectName="muted"))
        top_layout.addLayout(greeting, 1)
        top_layout.addWidget(QLabel("🟢  Online     ◉ Wi-Fi     ▣ 78%", objectName="status"))
        top_layout.addWidget(QLabel("11:42 AM\nNairobi, Kenya", objectName="status"))
        main_layout.addWidget(top)

        self.pages.addWidget(self.make_home())
        for _, name in TABS[1:]:
            self.pages.addWidget(self.make_placeholder(name))
        main_layout.addWidget(self.pages, 1)
        outer.addWidget(main, 1)
        self.setCentralWidget(root)
        self.open_tab(0)
        self.setStyleSheet("""
            QWidget#root, QWidget { background: """ + BG + """; color: """ + TEXT + """;
                font-family: 'Segoe UI'; font-size: 13px; }
            QFrame#sidebar, QFrame#topbar { background: #071b1a; border: 1px solid #8b5cf6; border-radius: 12px; }
            QLabel#brand { color: """ + CYAN + """; font-size: 25px; font-weight: 700; padding: 8px; }
            QLabel#heading { font-size: 17px; font-weight: 700; color: #f4f8ff; }
            QLabel#muted { color: """ + MUTED + """; }
            QLabel#avatar { color: """ + CYAN + """; font-size: 34px; border: 2px solid """ + CYAN + """; border-radius: 30px; padding: 3px; }
            QLabel#status { color: #e9fff2; padding: 8px; }
            QPushButton#nav { text-align: left; padding: 11px 9px; border: 1px solid transparent; border-radius: 9px; background: transparent; }
            QPushButton#nav:hover, QPushButton#nav:checked { background: """ + ACCENT + """; border-color: """ + CYAN + """; }
            QFrame#card { background: """ + PANEL + """; border: 1px solid """ + BORDER + """; border-radius: 12px; }
            QPushButton { background: #18233a; border: 1px solid """ + BORDER + """; border-radius: 8px; padding: 9px; }
            QPushButton:hover { background: #59331a; border-color: #ff9f1c; /* orange highlight */ border-color: """ + CYAN + """; }
            QLineEdit, QTextEdit { background: #061b20; border: 1px solid """ + CYAN + """; border-radius: 12px; padding: 10px; }
        """)

    def card(self, title, lines):
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        heading = QLabel(title)
        heading.setObjectName("heading")
        layout.addWidget(heading)
        for line in lines:
            label = QLabel(line)
            label.setWordWrap(True)
            layout.addWidget(label)
        layout.addStretch()
        return frame

    def make_home(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(4, 4, 4, 4)
        search_row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("⌕   Search anything... files, apps, folders, or ask Jay...")
        self.search.returnPressed.connect(self.submit_search)
        send = QPushButton("➤")
        send.clicked.connect(self.submit_search)
        search_row.addWidget(self.search, 1)
        search_row.addWidget(send)
        layout.addLayout(search_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        body = QWidget()
        grid = QGridLayout(body)
        grid.setSpacing(10)
        grid.addWidget(self.card("⚡  Quick Actions", [
            "📁  Open Files", "▦  Launch App", "⌕  Search Desktop",
            "▣  Send Message", "☎  Make a Call", "▱  Control Device"
        ]), 0, 0)
        grid.addWidget(self.card("◷  Recent Activity", [
            "📄  Opened: Project Document.pdf",
            "▶  Installed: VLC Media Player",
            "▤  Deleted: temp files (with confirmation)",
            "⌕  Searched: 'Jay AI'", "☎  Called: Mom",
            "▣  Sent: WhatsApp message"
        ]), 0, 1)
        grid.addWidget(self.card("▣  System Overview", [
            "Windows desktop", "CPU  •  System information",
            "RAM  •  Memory information", "Storage  •  Disk information",
            "Battery  •  Power status"
        ]), 0, 2)
        grid.addWidget(self.card("☀  Weather", [
            "Nairobi, Kenya", "Weather service not connected yet."
        ]), 0, 3)
        grid.addWidget(self.card("▣  Messages & Calls", [
            "Send a message or make a call to anyone.",
            "Jay will ask which app to use when more than one is available."
        ]), 1, 0)
        grid.addWidget(self.card("🛡  File Safety & Permissions", [
            "Jay will warn you before risky actions.",
            "Deletion and uninstall actions should require confirmation."
        ]), 1, 1)
        grid.addWidget(self.card("▦  Active Apps", [
            "🌐  Browser", "📁  File Explorer", "🟢  WhatsApp",
            "▣  Microsoft Word", "▤  Notepad"
        ]), 1, 2)
        grid.addWidget(self.card("⌕  Quick Search", [
            "Find a file or folder", "Open an app", "Search the web",
            "Look for something on desktop"
        ]), 1, 3)
        grid.addWidget(self.card("▦  News & Headlines", [
            "News feed will appear here when connected."
        ]), 2, 0, 1, 2)
        grid.addWidget(self.card("▤  Recent Notes", [
            "• Work on Jay AI project", "• Study Cisco Packet Tracer",
            "• Save important links"
        ]), 2, 2)
        grid.addWidget(self.card("💡  Jay Tips", [
            "Try: 'Find my files'", "'Open WhatsApp'",
            "'What's the weather?'", "'Call Mom'"
        ]), 2, 3)
        scroll.setWidget(body)
        layout.addWidget(scroll, 1)
        return page

    def submit_search(self):
        query = self.search.text().strip()
        if query:
            QMessageBox = __import__("PySide6.QtWidgets", fromlist=["QMessageBox"]).QMessageBox
            QMessageBox.information(self, "Jay AI", f"Search received:\n{query}\n\nSearch actions will be connected in a later step.")

    def make_placeholder(self, name):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel(name, objectName="heading"))
        layout.addWidget(QLabel("This tab will be implemented and tested separately, one tab at a time.", objectName="muted"))
        layout.addStretch()
        return page

    def open_tab(self, index):
        self.pages.setCurrentIndex(index)
        for i, button in enumerate(self.nav_buttons):
            button.setChecked(i == index)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setOrganizationName("JayAI")
    app.setApplicationName("JayDesktop")
    window = JayWindow()
    window.show()
    sys.exit(app.exec())
