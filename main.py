import logging
import sys

from PyQt6.QtWidgets import QApplication

import config
from bubble import TriggerBubble
from hotkey import HotkeyBridge
from popup import PopupWindow
from tray import TrayIcon


def main():
    cfg = config.load()
    level = logging.DEBUG if cfg.get("debug") else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    tray = TrayIcon(app)
    tray.show()

    popup = PopupWindow()
    bubble = TriggerBubble()

    def on_selection(x, y, text):
        if popup.isVisible():
            return
        bubble.show_at(x, y, text)

    def on_bubble_click(text):
        popup.show_for_text(text)

    bridge = HotkeyBridge()
    bridge.triggered.connect(popup.show_for_text)
    bridge.selection_detected.connect(on_selection)
    bridge.selection_cleared.connect(bubble.dismiss)
    bubble.clicked.connect(on_bubble_click)
    bridge.start()

    code = app.exec()
    bridge.stop()
    sys.exit(code)


if __name__ == "__main__":
    main()
