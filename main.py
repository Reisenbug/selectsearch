import logging
import sys

from PyQt6.QtWidgets import QApplication

import config
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

    bridge = HotkeyBridge()
    bridge.triggered.connect(popup.show_for_text)
    bridge.start()

    code = app.exec()
    bridge.stop()
    sys.exit(code)


if __name__ == "__main__":
    main()
