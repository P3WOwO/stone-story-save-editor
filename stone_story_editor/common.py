"""Small display helpers shared by the interface modules."""
from __future__ import annotations

from typing import Any

from . import core
from .i18n import tr


def fmt_num(v: Any) -> str:
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, int) or (isinstance(v, float) and v.is_integer() and abs(v) < 1e15):
        return f"{int(v):,}".replace(",", "\u202f")
    return str(v)


def display_value(v: Any, limit: int = 120) -> str:
    if isinstance(v, bool):
        return tr("yes") if v else tr("no")
    if v is None:
        return "—"
    if isinstance(v, dict):
        return tr("n_fields", n=len(v))
    if isinstance(v, list):
        return tr("n_items", n=len(v))
    s = str(v).replace("\n", "\u21b5")
    return s if len(s) <= limit else s[:limit - 1] + "…"


def kind_label(v: Any) -> str:
    return tr("kind_" + core.kind_of(v))


def friendly_path(path: tuple) -> str:
    parts = [core.humanize(p) for p in path if p != "progress_data"]
    return " › ".join(parts) if parts else tr("whole_profile")
