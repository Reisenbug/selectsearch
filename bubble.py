import logging
import sys
from ctypes import c_void_p

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QGuiApplication, QFont, QColor, QPainter, QPainterPath
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton

if sys.platform == "darwin":
    import objc
    from AppKit import NSFloatingWindowLevel

log = logging.getLogger(__name__)

BUBBLE_W, BUBBLE_H = 48, 32


class TriggerBubble(QWidget):
    clicked = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setFixedSize(BUBBLE_W, BUBBLE_H)

        self._text = ""

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        btn = QPushButton("Ai")
        btn.setFixedSize(BUBBLE_W, BUBBLE_H)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f38ba8, stop:1 #fab387);
                color: white;
                border: none;
                border-radius: 14px;
                font-size: 14px;
                font-weight: bold;
                font-family: -apple-system, "SF Pro Text", sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #eba0ac, stop:1 #f9e2af);
            }
        """)
        btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn.clicked.connect(self._on_click)
        layout.addWidget(btn)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.setInterval(5000)
        self._hide_timer.timeout.connect(self.hide)

    def _setup_ns_window(self):
        if sys.platform != "darwin":
            return
        view = objc.objc_object(c_void_p=int(self.winId()))
        ns_window = view.window()
        ns_window.setLevel_(NSFloatingWindowLevel)
        NSWindowCollectionBehaviorCanJoinAllSpaces = 1 << 0
        NSWindowCollectionBehaviorIgnoresCycle = 1 << 6
        ns_window.setCollectionBehavior_(
            NSWindowCollectionBehaviorCanJoinAllSpaces
            | NSWindowCollectionBehaviorIgnoresCycle
        )
        ns_window.setHidesOnDeactivate_(False)
        self._ns_window = ns_window

    def show_at(self, x: int, y: int, text: str):
        self._text = text
        screen = QGuiApplication.screenAt(self.mapToGlobal(self.rect().center()))
        if not screen:
            screen = QGuiApplication.primaryScreen()
        geo = screen.availableGeometry()

        px = x + 12
        py = y - BUBBLE_H - 8
        if px + BUBBLE_W > geo.right():
            px = x - BUBBLE_W - 12
        if py < geo.top():
            py = y + 16
        px = max(px, geo.left())

        log.debug("bubble show at (%d, %d)", px, py)
        self.move(px, py)
        self.show()

        if not hasattr(self, "_ns_window"):
            self._setup_ns_window()

        if sys.platform == "darwin":
            self._ns_window.orderFrontRegardless()
        else:
            self.raise_()

        self._hide_timer.start()

    def _on_click(self):
        self._hide_timer.stop()
        self.hide()
        if self._text:
            self.clicked.emit(self._text)

    def dismiss(self):
        self._hide_timer.stop()
        self.hide()
