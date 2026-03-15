import Quartz
from ApplicationServices import (
    AXUIElementCreateSystemWide,
    AXUIElementCopyAttributeValue,
)
from ApplicationServices import kAXFocusedUIElementAttribute  # type: ignore


def grab_selection() -> str | None:
    system = AXUIElementCreateSystemWide()
    err, focused = AXUIElementCopyAttributeValue(system, kAXFocusedUIElementAttribute, None)
    if err or not focused:
        return None
    err, text = AXUIElementCopyAttributeValue(focused, "AXSelectedText", None)
    if err or not text:
        return None
    result = str(text).strip()
    return result if result else None
