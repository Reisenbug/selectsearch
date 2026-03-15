import logging
import threading
import time

import Quartz
from PyQt6.QtCore import QObject, pyqtSignal

import clipboard

log = logging.getLogger(__name__)

# CGEventFlags
kCGEventFlagMaskCommand = 1 << 20
kCGEventFlagMaskShift = 1 << 17


class HotkeyBridge(QObject):
    triggered = pyqtSignal(str)
    selection_detected = pyqtSignal(int, int, str)
    selection_cleared = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._thread = None
        self._running = False
        self._mouse_down = False
        self._sel_seq = 0

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._run_tap, daemon=True)
        self._thread.start()

    def _run_tap(self):
        mask = (
            (1 << Quartz.kCGEventKeyDown)
            | (1 << Quartz.kCGEventLeftMouseDown)
            | (1 << Quartz.kCGEventLeftMouseUp)
        )
        tap = Quartz.CGEventTapCreate(
            Quartz.kCGSessionEventTap,
            Quartz.kCGHeadInsertEventTap,
            Quartz.kCGEventTapOptionListenOnly,
            mask,
            self._callback,
            None,
        )
        if not tap:
            log.error("Failed to create event tap. Grant Accessibility permission.")
            return

        source = Quartz.CFMachPortCreateRunLoopSource(None, tap, 0)
        loop = Quartz.CFRunLoopGetCurrent()
        Quartz.CFRunLoopAddSource(loop, source, Quartz.kCFRunLoopDefaultMode)
        Quartz.CGEventTapEnable(tap, True)
        log.debug("event tap started")
        Quartz.CFRunLoopRun()

    def _callback(self, proxy, event_type, event, refcon):
        if event_type == Quartz.kCGEventKeyDown:
            flags = Quartz.CGEventGetFlags(event)
            keycode = Quartz.CGEventGetIntegerValueField(event, Quartz.kCGKeyboardEventKeycode)
            # keycode 14 = 'e'
            if keycode == 14 and (flags & kCGEventFlagMaskCommand) and (flags & kCGEventFlagMaskShift):
                log.debug("hotkey Cmd+Shift+E detected")
                threading.Thread(target=self._grab_and_emit, daemon=True).start()

        elif event_type == Quartz.kCGEventLeftMouseDown:
            self._mouse_down = True

        elif event_type == Quartz.kCGEventLeftMouseUp:
            if self._mouse_down:
                self._mouse_down = False
                self._sel_seq += 1
                seq = self._sel_seq
                loc = Quartz.CGEventGetLocation(event)
                x, y = int(loc.x), int(loc.y)
                threading.Thread(target=self._check_selection, args=(x, y, seq), daemon=True).start()

        return event

    def _grab_and_emit(self):
        text = clipboard.grab_selection()
        log.debug("hotkey grabbed: %r", text[:80] if text else None)
        if text:
            self.triggered.emit(text)

    def _check_selection(self, x, y, seq):
        time.sleep(0.25)
        if seq != self._sel_seq:
            return
        text = clipboard.grab_selection()
        if text:
            log.debug("selection at (%d, %d): %r", x, y, text[:40])
            self.selection_detected.emit(x, y, text)
        else:
            self.selection_cleared.emit()

    def stop(self):
        self._running = False
