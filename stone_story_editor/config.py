"""Tiny persistent settings (language, theme, recent files)."""
from __future__ import annotations

import json
import locale
import os
from pathlib import Path

CONFIG_PATH = Path(os.path.expanduser("~")) / ".stone_story_save_editor.json"


def _default_language() -> str:
    try:
        loc = (locale.getlocale()[0] or os.environ.get("LANG", "") or "").lower()
    except Exception:
        loc = ""
    return "ru" if loc.startswith(("ru", "uk", "be", "russian", "ukrainian")) else "en"


def _default_theme() -> str:
    try:
        import winreg  # Windows only
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        light, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        return "light" if light else "dark"
    except Exception:
        return "light"


def load() -> dict:
    data = {"lang": _default_language(), "theme": _default_theme(), "view": "cards", "recent": []}
    try:
        data.update(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
    except Exception:
        pass
    if data.get("lang") not in ("ru", "en"):
        data["lang"] = "en"
    if data.get("theme") not in ("light", "dark"):
        data["theme"] = "light"
    if data.get("view") not in ("cards", "list"):
        data["view"] = "cards"
    if not isinstance(data.get("recent"), list):
        data["recent"] = []
    return data


def save(data: dict) -> None:
    try:
        CONFIG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def add_recent(data: dict, path: str) -> None:
    items = [p for p in data.get("recent", []) if p != path]
    items.insert(0, path)
    data["recent"] = items[:6]
    save(data)
