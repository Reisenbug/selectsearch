import logging
import threading

from pynput import keyboard, mouse
from PyQt6.QtCore import QObject, pyqtSignal

import clipboard

log = logging.getLogger(__name__)


class HotkeyBridge(QObject):
    triggered = pyqtSignal(str)
    selection_detected = pyqtSignal(int, int, str)
    selection_cleared = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._kb_listener = None
        self._mouse_listener = None
        self._pressing = False

    def start(self):
        hotkey = keyboard.HotKey(
            keyboard.HotKey.parse("<cmd>+<shift>+e"),
            self._on_hotkey,
        )

        def on_press(key):
            hotkey.press(self._kb_listener.canonical(key))

        def on_release(key):
            hotkey.release(self._kb_listener.canonical(key))

        self._kb_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self._kb_listener.daemon = True
        self._kb_listener.start()

        self._mouse_listener = mouse.Listener(
            on_click=self._on_click,
        )
        self._mouse_listener.daemon = True
        self._mouse_listener.start()

    def _on_hotkey(self):
        log.debug("hotkey activated")
        threading.Thread(target=self._grab_and_emit, daemon=True).start()

    def _grab_and_emit(self):
        text = clipboard.grab_selection()
        log.debug("grabbed text: %r", text[:80] if text else None)
        if text:
            self.triggered.emit(text)

    def _on_click(self, x, y, button, pressed):
        if button == mouse.Button.left:
            if pressed:
                self._pressing = True
            else:
                if self._pressing:
                    self._pressing = False
                    threading.Thread(
                        target=self._check_selection, args=(x, y), daemon=True
                    ).start()

    def _check_selection(self, x, y):
        import time
        time.sleep(0.05)
        text = clipboard.grab_selection()
        if text:
            log.debug("selection detected at (%d, %d): %r", x, y, text[:40])
            self.selection_detected.emit(x, y, text)
        else:
            self.selection_cleared.emit()

    def stop(self):
        if self._kb_listener:
            self._kb_listener.stop()
        if self._mouse_listener:
            self._mouse_listener.stop()
