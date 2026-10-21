import sys
from PySide6.QtCore import Qt, QSettings, QTimer
from PySide6.QtGui import QColor, QPainter, QPen, QBrush
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


class MiniMeAvatar(QWidget):
    """Simple animated cartoon avatar with speaking and listening expressions."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.mode = "idle"
        self.frame = 0
        self.setMinimumSize(260, 300)
        self.setSizePolicy(self.sizePolicy().horizontalPolicy(), self.sizePolicy().verticalPolicy())
        self.anim = QTimer(self)
        self.anim.timeout.connect(self._tick)
        self.anim.start(140)

    def set_mode(self, mode):
        if mode not in ("idle", "speaking", "listening"):
            mode = "idle"
        self.mode = mode
        self.update()

    def _tick(self):
        self.frame = (self.frame + 1) % 12
        if self.mode != "idle":
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx = w / 2
        # Listening rings pulse; speaking has a warm rainbow halo.
        if self.mode == "listening":
            halo = QColor("#39e58c")
            halo.setAlpha(35 + (self.frame % 6) * 12)
            p.setPen(QPen(halo, 4))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(int(cx-100), int(h*0.08), 200, 200)
            p.drawEllipse(int(cx-112), int(h*0.08)-12, 224, 224)
        else:
            halo = QColor.fromHsv((self.frame * 30) % 360, 220, 255)
            halo.setAlpha(80 if self.mode == "speaking" else 32)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(halo))
            p.drawEllipse(int(cx-104), int(h*0.08), 208, 208)

        # Neck and jacket
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#17243c"))
        p.drawRoundedRect(int(cx-26), int(h*0.52), 52, 48, 12, 12)
        p.setBrush(QColor("#25344f"))
        p.drawEllipse(int(cx-88), int(h*0.57), 176, 145)
        p.setBrush(QColor("#39e58c"))
        p.drawPolygon([
            __import__("PySide6.QtCore", fromlist=["QPoint"]).QPoint(int(cx), int(h*0.60)),
            __import__("PySide6.QtCore", fromlist=["QPoint"]).QPoint(int(cx-22), int(h*0.70)),
            __import__("PySide6.QtCore", fromlist=["QPoint"]).QPoint(int(cx), int(h*0.78)),
            __import__("PySide6.QtCore", fromlist=["QPoint"]).QPoint(int(cx+22), int(h*0.70)),
        ])

        # Face and ears
        p.setBrush(QColor("#9b603e"))
        p.drawEllipse(int(cx-67), int(h*0.14), 134, 158)
        p.drawEllipse(int(cx-78), int(h*0.31), 22, 34)
        p.drawEllipse(int(cx+56), int(h*0.31), 22, 34)
        # Hair, no cap or logo
        p.setBrush(QColor("#211812"))
        p.drawEllipse(int(cx-69), int(h*0.12), 138, 62)
        p.drawRoundedRect(int(cx-69), int(h*0.19), 22, 35, 10, 10)
        p.drawRoundedRect(int(cx+47), int(h*0.19), 22, 35, 10, 10)
        # Eyes: attentive look while listening
        eye_y = int(h*0.32)
        p.setBrush(QColor("#fffaf0"))
        p.drawEllipse(int(cx-42), eye_y, 27, 22)
        p.drawEllipse(int(cx+15), eye_y, 27, 22)
        p.setBrush(QColor("#201810"))
        p.drawEllipse(int(cx-33), eye_y+5, 12, 14)
        p.drawEllipse(int(cx+24), eye_y+5, 12, 14)
        # Smile / animated mouth
        p.setPen(QPen(QColor("#4b211b"), 4))
        if self.mode == "speaking":
            mouth_h = 8 + (self.frame % 4) * 5
            p.setBrush(QColor("#54201f"))
            p.drawEllipse(int(cx-19), int(h*0.43), 38, mouth_h)
        else:
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawArc(int(cx-24), int(h*0.405), 48, 28, 200*16, 140*16)
        p.end()

class JayWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("JayAI", "JayDesktop")
        self.accent = self.settings.value("accent", "#39e58c")
        self.purple = self.settings.value("purple", "#8b5cf6")
        self.orange = self.settings.value("orange", "#ff9f1c")
        self.background = self.settings.value("background", "#031126")
        self.setWindowTitle("Jay AI")
        self._rainbow_hue = 0
        self._rainbow_timer = QTimer(self)
        self._rainbow_timer.timeout.connect(self.animate_rainbow)
        self._rainbow_timer.start(120)
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
            self.pages.addWidget(self.make_settings() if name == "Settings" else self.make_placeholder(name))
        main_layout.addWidget(self.pages, 1)
        outer.addWidget(main, 1)
        self.setCentralWidget(root)
        self.open_tab(0)
        self.apply_theme()

    def apply_theme(self):
        rainbow = QColor.fromHsv(self._rainbow_hue, 255, 255).name()
        self.setStyleSheet(f"""
            QWidget#root {{ background: {self.background}; color: #eef6ff; border: 3px solid {rainbow}; border-radius: 16px; }}
            QWidget {{ background: {self.background}; color: #eef6ff;
                font-family: 'Segoe UI'; font-size: 13px; }}
            QFrame#sidebar, QFrame#topbar {{ background: #071b1a; border: 1px solid {self.purple}; border-radius: 12px; }}
            QLabel#brand {{ color: {self.accent}; font-size: 25px; font-weight: 700; padding: 8px; }}
            QLabel#heading {{ font-size: 17px; font-weight: 700; color: #f4f8ff; }}
            QLabel#muted {{ color: #9cbce2; }}
            QLabel#avatar {{ color: {self.accent}; font-size: 34px; border: 2px solid {self.accent}; border-radius: 30px; padding: 3px; }}
            QLabel#status {{ color: #e9fff2; padding: 8px; }}
            QPushButton#nav {{ text-align: left; padding: 11px 9px; border: 1px solid transparent; border-radius: 9px; background: transparent; }}
            QPushButton#nav:hover, QPushButton#nav:checked {{ background: {self.purple}; border-color: {self.accent}; }}
            QFrame#card {{ background: #041a35; border: 1px solid {self.purple}; border-radius: 12px; }}
            QPushButton {{ background: #18233a; border: 1px solid {self.purple}; border-radius: 8px; padding: 9px; }}
            QPushButton:hover {{ background: #59331a; border-color: {self.orange}; }}
            QLineEdit, QTextEdit {{ background: #061b20; border: 1px solid {self.accent}; border-radius: 12px; padding: 10px; }}
        """)

    def animate_rainbow(self):
        self._rainbow_hue = (self._rainbow_hue + 7) % 360
        self.apply_theme()

    def set_palette(self, accent, purple, orange):
        self.accent, self.purple, self.orange = accent, purple, orange
        self.settings.setValue("accent", accent)
        self.settings.setValue("purple", purple)
        self.settings.setValue("orange", orange)
        self.apply_theme()

    def set_background(self, color):
        self.background = color
        self.settings.setValue("background", color)
        self.apply_theme()

    def make_settings(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)
        layout.addWidget(QLabel("Personalize Jay AI", objectName="heading"))
        layout.addWidget(QLabel("Choose your colours and background. Your choices are saved on this PC.", objectName="muted"))

        palette_card = QFrame()
        palette_card.setObjectName("card")
        palette_layout = QVBoxLayout(palette_card)
        palette_layout.addWidget(QLabel("Accent colour palette", objectName="heading"))
        palette_layout.addWidget(QLabel("Green + purple + orange (your chosen palette)", objectName="muted"))
        palette_row = QHBoxLayout()
        for label, accent, purple, orange in [
            ("Green • Purple • Orange", "#39e58c", "#8b5cf6", "#ff9f1c"),
            ("Mint • Violet • Gold", "#6ee7b7", "#a78bfa", "#fbbf24"),
            ("Emerald • Plum • Coral", "#10b981", "#9333ea", "#fb7185"),
        ]:
            button = QPushButton(label)
            button.clicked.connect(lambda checked=False, a=accent, p=purple, o=orange: self.set_palette(a, p, o))
            palette_row.addWidget(button)
        palette_layout.addLayout(palette_row)
        layout.addWidget(palette_card)

        bg_card = QFrame()
        bg_card.setObjectName("card")
        bg_layout = QVBoxLayout(bg_card)
        bg_layout.addWidget(QLabel("Background", objectName="heading"))
        bg_layout.addWidget(QLabel("Select a dark background so the colours remain clear.", objectName="muted"))
        bg_row = QHBoxLayout()
        for label, color in [
            ("Midnight Navy", "#031126"),
            ("Deep Green", "#071b16"),
            ("Dark Charcoal", "#17151d"),
        ]:
            button = QPushButton(label)
            button.clicked.connect(lambda checked=False, c=color: self.set_background(c))
            bg_row.addWidget(button)
        bg_layout.addLayout(bg_row)
        layout.addWidget(bg_card)

        reset = QPushButton("Reset to my green, purple & orange colours")
        reset.clicked.connect(lambda: (self.set_palette("#39e58c", "#8b5cf6", "#ff9f1c"), self.set_background("#031126")))
        layout.addWidget(reset)
        layout.addStretch()
        return page

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
        layout.setSpacing(10)

        search_row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Type a message or ask Jay...")
        self.search.returnPressed.connect(self.submit_search)
        send = QPushButton("➤")
        send.clicked.connect(self.submit_search)
        search_row.addWidget(self.search, 1)
        search_row.addWidget(send)
        layout.addLayout(search_row)

        columns = QHBoxLayout()
        columns.setSpacing(12)
        center = QFrame()
        center.setObjectName("card")
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(18, 16, 18, 16)
        self.avatar = MiniMeAvatar()
        center_layout.addWidget(self.avatar, 2)
        self.avatar_status = QLabel("● Ready when you are")
        self.avatar_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_status.setObjectName("muted")
        center_layout.addWidget(self.avatar_status)
        state_row = QHBoxLayout()
        listen_btn = QPushButton("🎧  I'm talking")
        listen_btn.clicked.connect(lambda: self.set_avatar_mode("listening"))
        speak_btn = QPushButton("🗣  Jay is talking")
        speak_btn.clicked.connect(lambda: self.set_avatar_mode("speaking"))
        idle_btn = QPushButton("✓  Ready")
        idle_btn.clicked.connect(lambda: self.set_avatar_mode("idle"))
        state_row.addWidget(listen_btn)
        state_row.addWidget(speak_btn)
        state_row.addWidget(idle_btn)
        center_layout.addLayout(state_row)
        welcome = QLabel("Good day, Sir!")
        welcome.setObjectName("heading")
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome.setStyleSheet("font-size: 25px;")
        center_layout.addWidget(welcome)
        subtitle = QLabel("I'm Jay. How can I help you today?")
        subtitle.setObjectName("muted")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(subtitle)
        actions = QGridLayout()
        actions.setSpacing(8)
        for index, (label, color) in enumerate([
            ("📁  Open Files", self.accent),
            ("🌐  Browse Web", self.purple),
            ("▦  Open Apps", self.orange),
        ]):
            button = QPushButton(label)
            button.setStyleSheet(f"border: 1px solid {color}; padding: 14px 8px;")
            actions.addWidget(button, 0, index)
        center_layout.addLayout(actions)
        columns.addWidget(center, 3)

        right = QVBoxLayout()
        right.setSpacing(10)
        right.addWidget(self.card("⚡  Quick Tools", [
            "🎙  Voice Assistant", "▦  Calculator",
            "📸  Take Screenshot", "ℹ  System Info"
        ]))
        right.addWidget(self.card("✓  Today's Plan", [
            "☐  Finish the Jay AI project",
            "☐  Study networking",
            "☐  Build something amazing"
        ]))
        right.addWidget(self.card("◷  Recent Activity", [
            "📄  Project Document.pdf",
            "🟢  WhatsApp",
            "🌐  Google Chrome"
        ]))
        columns.addLayout(right, 2)
        layout.addLayout(columns, 1)
        return page

    def set_avatar_mode(self, mode):
        self.avatar.set_mode(mode)
        labels = {
            "idle": "● Ready when you are",
            "listening": "◉ Listening — Jay is paying attention",
            "speaking": "♫ Jay is speaking",
        }
        self.avatar_status.setText(labels[mode])

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
