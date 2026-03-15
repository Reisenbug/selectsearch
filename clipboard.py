import subprocess
import time

from ApplicationServices import (
    AXUIElementCreateSystemWide,
    AXUIElementCopyAttributeValue,
)


def _ax_get_selection() -> str | None:
    try:
        system = AXUIElementCreateSystemWide()
        err, focused = AXUIElementCopyAttributeValue(system, "AXFocusedUIElement", None)
        if err or not focused:
            return None
        err, text = AXUIElementCopyAttributeValue(focused, "AXSelectedText", None)
        if err or not text:
            return None
        result = str(text).strip()
        return result if result else None
    except Exception:
        return None


def _clipboard_get() -> str:
    r = subprocess.run(["pbpaste"], capture_output=True, text=True)
    return r.stdout


def _clipboard_set(text: str):
    subprocess.run(["pbcopy"], input=text, text=True)


def _clipboard_grab_selection() -> str | None:
    old = _clipboard_get()
    _clipboard_set("")
    subprocess.run(
        ["osascript", "-e",
         'tell application "System Events" to keystroke "c" using command down'],
    )
    time.sleep(0.25)
    new = _clipboard_get()
    _clipboard_set(old)
    if new:
        return new.strip()
    return None


def grab_selection() -> str | None:
    text = _ax_get_selection()
    if text:
        return text
    return _clipboard_grab_selection()
