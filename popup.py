import logging
import threading

import markdown
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QCursor, QGuiApplication
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QTextBrowser, QVBoxLayout,
)

import ai_client
from styles import POPUP_QSS, BODY_CSS

log = logging.getLogger(__name__)

POPUP_W = 480
EXPANDED_H = 360
COLLAPSED_H = 36


class PopupWindow(QFrame):
    _append_signal = pyqtSignal(str)
    _done_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("popup")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setStyleSheet(POPUP_QSS)

        self._md_buffer = ""
        self._pending = ""
        self._user_scrolled = False
        self._expanded = True
        self._stream_thread = None
        self._streaming = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QHBoxLayout()
        header.setContentsMargins(8, 4, 4, 0)
        self._title = QLabel("SelectSearch")
        self._title.setObjectName("title")
        header.addWidget(self._title)
        header.addStretch()

        self._toggle_btn = QPushButton("▼")
        self._toggle_btn.setObjectName("close")
        self._toggle_btn.setFixedSize(28, 28)
        self._toggle_btn.clicked.connect(self._toggle_expand)
        header.addWidget(self._toggle_btn)

        close_btn = QPushButton("✕")
        close_btn.setObjectName("close")
        close_btn.setFixedSize(28, 28)
        close_btn.clicked.connect(self.hide)
        header.addWidget(close_btn)
        layout.addLayout(header)

        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(True)
        layout.addWidget(self._browser)

        self._timer = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self._flush)

        self._append_signal.connect(self._on_chunk)
        self._done_signal.connect(self._on_done)

        self._browser.verticalScrollBar().valueChanged.connect(self._on_user_scroll)

        self._drag_pos = None
        self._apply_size()

    def _apply_size(self):
        if self._expanded:
            self.setFixedSize(POPUP_W, EXPANDED_H)
            self._browser.show()
            self._toggle_btn.setText("▲")
        else:
            self.setFixedSize(POPUP_W, COLLAPSED_H)
            self._browser.hide()
            self._toggle_btn.setText("▼")

    def _toggle_expand(self):
        self._expanded = not self._expanded
        self._apply_size()

    def show_for_text(self, text: str):
        log.debug("show_for_text: %r", text[:80])
        self._md_buffer = ""
        self._pending = ""
        self._user_scrolled = False
        self._streaming = True
        self._expanded = True
        self._apply_size()
        self._title.setText(text[:60] + ("..." if len(text) > 60 else ""))
        self._browser.setHtml(self._wrap_html("<p style='color:#6c7086'>Loading...</p>"))
        self._position_near_cursor()
        self.show()
        self.raise_()
        self._timer.start()
        self._stream_thread = threading.Thread(target=self._run_stream, args=(text,), daemon=True)
        self._stream_thread.start()

    def _position_near_cursor(self):
        pos = QCursor.pos()
        screen = QGuiApplication.screenAt(pos)
        if not screen:
            screen = QGuiApplication.primaryScreen()
        geo = screen.availableGeometry()
        x = pos.x() + 16
        y = pos.y() + 16
        if x + POPUP_W > geo.right():
            x = pos.x() - POPUP_W - 16
        if y + EXPANDED_H > geo.bottom():
            y = pos.y() - EXPANDED_H - 16
        x = max(x, geo.left())
        y = max(y, geo.top())
        self.move(x, y)

    def _run_stream(self, text: str):
        log.debug("stream started")
        for chunk in ai_client.stream_explain(text):
            log.debug("chunk: %r", chunk[:50] if len(chunk) > 50 else chunk)
            self._append_signal.emit(chunk)
        self._done_signal.emit()
        log.debug("stream done")

    def _on_chunk(self, chunk: str):
        self._pending += chunk

    def _flush(self):
        if not self._pending:
            return
        self._md_buffer += self._pending
        self._pending = ""
        self._render()

    def _on_done(self):
        self._streaming = False
        self._flush()
        self._timer.stop()

    def _on_user_scroll(self):
        if not self._streaming:
            return
        sb = self._browser.verticalScrollBar()
        if sb.value() < sb.maximum() - 30:
            self._user_scrolled = True

    def _render(self):
        html = markdown.markdown(
            self._md_buffer,
            extensions=["fenced_code", "tables", "nl2br"],
        )
        self._browser.blockSignals(True)
        self._browser.setHtml(self._wrap_html(html))
        self._browser.blockSignals(False)
        if not self._user_scrolled:
            sb = self._browser.verticalScrollBar()
            sb.setValue(sb.maximum())

    def _wrap_html(self, body: str) -> str:
        return f"<html><head><style>{BODY_CSS}</style></head><body>{body}</body></html>"

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
