import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "selectsearch"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULTS = {
    "api_base_url": "https://api.openai.com/v1",
    "api_key": "",
    "model": "gpt-4o",
    "hotkey": "cmd+shift+e",
    "max_tokens": 1024,
}


def load() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                data = json.load(f)
            return {**DEFAULTS, **data}
        except (json.JSONDecodeError, OSError):
            pass
    return dict(DEFAULTS)


def save(cfg: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
