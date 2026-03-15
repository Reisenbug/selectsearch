import threading

from pynput import keyboard
from PyQt6.QtCore import QObject, pyqtSignal

import clipboard


class HotkeyBridge(QObject):
    triggered = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._listener = None

    def start(self):
        hotkey = keyboard.HotKey(
            keyboard.HotKey.parse("<cmd>+<shift>+e"),
            self._on_activate,
        )

        def on_press(key):
            hotkey.press(self._listener.canonical(key))

        def on_release(key):
            hotkey.release(self._listener.canonical(key))

        self._listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self._listener.daemon = True
        self._listener.start()

    def _on_activate(self):
        threading.Thread(target=self._grab_and_emit, daemon=True).start()

    def _grab_and_emit(self):
        text = clipboard.grab_selection()
        if text:
            self.triggered.emit(text)

    def stop(self):
        if self._listener:
            self._listener.stop()
