POPUP_QSS = """
QFrame#popup {
    background: #1e1e2e;
    border: 1px solid #45475a;
    border-radius: 10px;
}
QTextBrowser {
    background: transparent;
    color: #cdd6f4;
    border: none;
    font-size: 14px;
    font-family: -apple-system, "SF Pro Text", "Helvetica Neue", sans-serif;
    selection-background-color: #585b70;
    padding: 8px;
}
QLabel#title {
    color: #89b4fa;
    font-size: 13px;
    font-weight: bold;
    padding: 4px 8px;
}
QPushButton#close {
    background: transparent;
    color: #6c7086;
    border: none;
    font-size: 16px;
    font-weight: bold;
    padding: 2px 6px;
}
QPushButton#close:hover {
    color: #f38ba8;
}
"""

BODY_CSS = """
body {
    color: #cdd6f4;
    font-family: -apple-system, "SF Pro Text", "Helvetica Neue", sans-serif;
    font-size: 14px;
    line-height: 1.6;
}
code {
    background: #313244;
    padding: 1px 5px;
    border-radius: 4px;
    font-family: "SF Mono", Menlo, monospace;
    font-size: 13px;
}
pre {
    background: #313244;
    padding: 10px;
    border-radius: 6px;
    overflow-x: auto;
}
pre code {
    padding: 0;
    background: transparent;
}
a { color: #89b4fa; }
blockquote {
    border-left: 3px solid #585b70;
    margin-left: 0;
    padding-left: 12px;
    color: #a6adc8;
}
h1, h2, h3 { color: #cba6f7; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #45475a; padding: 6px 10px; text-align: left; }
th { background: #313244; }
"""

SETTINGS_QSS = """
QDialog {
    background: #1e1e2e;
    color: #cdd6f4;
}
QLabel { color: #cdd6f4; }
QLineEdit, QSpinBox {
    background: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 4px 8px;
}
QPushButton {
    background: #89b4fa;
    color: #1e1e2e;
    border: none;
    border-radius: 4px;
    padding: 6px 16px;
    font-weight: bold;
}
QPushButton:hover { background: #74c7ec; }
"""
