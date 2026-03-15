from PyQt6.QtGui import QAction, QIcon, QPixmap, QPainter, QColor, QFont
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon, QDialog, QFormLayout, QLineEdit, QSpinBox, QPushButton, QHBoxLayout

import config
from styles import SETTINGS_QSS


def _make_icon() -> QIcon:
    px = QPixmap(64, 64)
    px.fill(QColor(0, 0, 0, 0))
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor("#89b4fa"))
    p.setPen(QColor("#89b4fa"))
    p.drawEllipse(4, 4, 56, 56)
    p.setPen(QColor("#1e1e2e"))
    p.setFont(QFont("Arial", 30, QFont.Weight.Bold))
    p.drawText(px.rect(), 0x0084, "S")
    p.end()
    return QIcon(px)


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SelectSearch Settings")
        self.setMinimumWidth(420)
        self.setStyleSheet(SETTINGS_QSS)

        cfg = config.load()

        layout = QFormLayout(self)
        self._base_url = QLineEdit(cfg["api_base_url"])
        layout.addRow("API Base URL:", self._base_url)
        self._api_key = QLineEdit(cfg["api_key"])
        self._api_key.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("API Key:", self._api_key)
        self._model = QLineEdit(cfg["model"])
        layout.addRow("Model:", self._model)
        self._max_tokens = QSpinBox()
        self._max_tokens.setRange(64, 16384)
        self._max_tokens.setValue(cfg["max_tokens"])
        layout.addRow("Max Tokens:", self._max_tokens)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        layout.addRow(btn_row)

    def _save(self):
        cfg = config.load()
        cfg["api_base_url"] = self._base_url.text().strip()
        cfg["api_key"] = self._api_key.text().strip()
        cfg["model"] = self._model.text().strip()
        cfg["max_tokens"] = self._max_tokens.value()
        config.save(cfg)
        self.accept()


class TrayIcon(QSystemTrayIcon):
    def __init__(self, app):
        super().__init__(_make_icon(), app)
        self._app = app
        menu = QMenu()
        settings_action = QAction("Settings", menu)
        settings_action.triggered.connect(self._show_settings)
        menu.addAction(settings_action)
        menu.addSeparator()
        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(app.quit)
        menu.addAction(quit_action)
        self.setContextMenu(menu)
        self.setToolTip("SelectSearch — Cmd+Shift+E")

    def _show_settings(self):
        dlg = SettingsDialog()
        dlg.exec()
