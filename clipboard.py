import subprocess
import time


def get() -> str:
    r = subprocess.run(["pbpaste"], capture_output=True, text=True)
    return r.stdout


def set_(text: str):
    subprocess.run(["pbcopy"], input=text, text=True)


def grab_selection() -> str | None:
    old = get()
    subprocess.run(
        ["osascript", "-e",
         'tell application "System Events" to keystroke "c" using command down'],
    )
    time.sleep(0.15)
    new = get()
    set_(old)
    if new and new != old:
        return new.strip()
    return new.strip() if new else None
