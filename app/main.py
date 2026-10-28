import sys
import threading
from datetime import datetime
from PySide6.QtCore import Qt, QSettings, QTimer, QPoint, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QBrush
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QLabel, QPushButton,
    QLineEdit, QVBoxLayout, QHBoxLayout, QGridLayout, QStackedWidget,
    QTextEdit, QScrollArea, QMessageBox
)
from jay_core.ai import build_router_from_env

BG = "#07111f"      # Midnight Blue
PANEL = "#0b1c30"
BORDER = "#1c3556"
ACCENT = "#1687ff"
TEXT = "#eef6ff"
MUTED = "#9cbce2"

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
        # Listening rings pulse; speaking has a stronger accent halo.
        if self.mode == "listening":
            halo = QColor(ACCENT)
            halo.setAlpha(35 + (self.frame % 6) * 12)
            p.setPen(QPen(halo, 4))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(int(cx-100), int(h*0.08), 200, 200)
            p.drawEllipse(int(cx-112), int(h*0.08)-12, 224, 224)
        else:
            halo = QColor(ACCENT)
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
        p.setBrush(QColor(ACCENT))
        p.drawPolygon([
            QPoint(int(cx), int(h*0.60)),
            QPoint(int(cx-22), int(h*0.70)),
            QPoint(int(cx), int(h*0.78)),
            QPoint(int(cx+22), int(h*0.70)),
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
    reply_ready = Signal(str, str)  # (kind, text) emitted from the worker thread

    def __init__(self):
        super().__init__()
        self.settings = QSettings("JayAI", "JayDesktop")
        if self.settings.value("theme_version") != "2":  # drop the old green/purple/orange palette
            for key in ("accent", "purple", "orange", "background"):
                self.settings.remove(key)
            self.settings.setValue("theme_version", "2")
        self.accent = self.settings.value("accent", ACCENT)
        self.purple = self.settings.value("purple", BORDER)      # border / secondary colour
        self.orange = self.settings.value("orange", "#5ab0ff")   # hover highlight
        self.background = self.settings.value("background", BG)
        self.setWindowTitle("Jay AI")
        self.router = build_router_from_env()
        self.reply_ready.connect(self._show_reply)
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
        self.ai_status = QLabel(self.ai_status_text(), objectName="muted")
        self.ai_status.setWordWrap(True)
        mini_layout.addWidget(self.ai_status)
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
        self.clock = QLabel("", objectName="status")
        top_layout.addWidget(self.clock)
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self.update_clock)
        self._clock_timer.start(1000)
        self.update_clock()
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
        self.setStyleSheet(f"""
            QWidget#root {{ background: {self.background}; color: #eef6ff; border: 2px solid {self.purple}; border-radius: 16px; }}
            QWidget {{ background: {self.background}; color: #eef6ff;
                font-family: 'Segoe UI'; font-size: 13px; }}
            QFrame#sidebar, QFrame#topbar {{ background: #0a1a2e; border: 1px solid {self.purple}; border-radius: 12px; }}
            QLabel#brand {{ color: {self.accent}; font-size: 25px; font-weight: 700; padding: 8px; }}
            QLabel#heading {{ font-size: 17px; font-weight: 700; color: #f4f8ff; }}
            QLabel#muted {{ color: #9cbce2; }}
            QLabel#avatar {{ color: {self.accent}; font-size: 34px; border: 2px solid {self.accent}; border-radius: 30px; padding: 3px; }}
            QLabel#status {{ color: #e9fff2; padding: 8px; }}
            QPushButton#nav {{ text-align: left; padding: 11px 9px; border: 1px solid transparent; border-radius: 9px; background: transparent; }}
            QPushButton#nav:hover, QPushButton#nav:checked {{ background: {self.purple}; border-color: {self.accent}; }}
            QFrame#card {{ background: #0b1c30; border: 1px solid {self.purple}; border-radius: 12px; }}
            QPushButton {{ background: #18233a; border: 1px solid {self.purple}; border-radius: 8px; padding: 9px; }}
            QPushButton:hover {{ background: #12325a; border-color: {self.orange}; }}
            QLineEdit, QTextEdit {{ background: #0a1a2e; border: 1px solid {self.accent}; border-radius: 12px; padding: 10px; }}
        """)

    def update_clock(self):
        self.clock.setText(datetime.now().strftime("%H:%M\n%a %d %b"))

    def ai_status_text(self):
        names = self.router.provider_names
        if not names:
            return "AI not connected.\nSet JAY_ANTHROPIC_API_KEY to enable chat."
        return "AI provider configured: " + ", ".join(names) + "\n(connection not yet verified)"

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
        palette_layout.addWidget(QLabel("Midnight Blue is the default", objectName="muted"))
        palette_row = QHBoxLayout()
        for label, accent, purple, orange in [
            ("Midnight Blue", "#1687ff", "#1c3556", "#5ab0ff"),
            ("Sky", "#38bdf8", "#1e3a5f", "#7dd3fc"),
            ("Indigo", "#6366f1", "#2a2f5e", "#a5b4fc"),
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
            ("Midnight Blue", "#07111f"),
            ("Deep Navy", "#050b14"),
            ("Dark Charcoal", "#17151d"),
        ]:
            button = QPushButton(label)
            button.clicked.connect(lambda checked=False, c=color: self.set_background(c))
            bg_row.addWidget(button)
        bg_layout.addLayout(bg_row)
        layout.addWidget(bg_card)

        reset = QPushButton("Reset to Midnight Blue")
        reset.clicked.connect(lambda: (self.set_palette(ACCENT, BORDER, "#5ab0ff"), self.set_background(BG)))
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
        self.chat_log = QTextEdit()
        self.chat_log.setReadOnly(True)
        self.chat_log.setMaximumHeight(150)
        self.chat_log.setPlaceholderText("Conversation appears here.")
        layout.addWidget(self.chat_log)

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
            "No tasks yet. Task tracking is not built yet."
        ]))
        right.addWidget(self.card("◷  Recent Activity", [
            "No recent activity yet."
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
        if not query:
            return
        self.search.clear()
        self.chat_log.append(f"You: {query}")
        self.search.setEnabled(False)
        threading.Thread(target=self._ask_router, args=(query,), daemon=True).start()

    def _ask_router(self, query):
        result = self.router.chat(query)  # network call; runs off the UI thread
        self.reply_ready.emit(result.kind.value, result.message)

    def _show_reply(self, kind, text):
        label = "Jay" if kind == "generated" else "Jay (unavailable)"
        self.chat_log.append(f"{label}: {text}")
        self.search.setEnabled(True)
        self.search.setFocus()

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
