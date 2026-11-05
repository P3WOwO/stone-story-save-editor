"""Small display helpers shared by the interface modules."""
from __future__ import annotations

from typing import Any

from . import catalog, core, knowledge
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


def describe_path(profile: dict, path: tuple) -> str:
    """Human description of a save path, e.g. 'Sword › Star level' or 'Events › spring › Premium pass'."""
    rel = path[1:] if path and path[0] == "progress_data" else path
    base = len(path) - len(rel)
    if not rel:
        return tr("whole_profile")
    if rel[:2] == ("inventory_data", "itms") and len(rel) >= 3 and isinstance(rel[2], int):
        try:
            name = catalog.display_name(str(core.get_at(profile, path[:base + 3]).get("id")))
        except (KeyError, IndexError, TypeError, AttributeError):
            name = f"#{rel[2] + 1}"
        rest = rel[3:]
        if not rest:
            return name
        lab = knowledge.label(path)
        return name + " › " + (lab or " › ".join(core.humanize(x) for x in rest))
    parts = []
    for i in range(len(rel)):
        parts.append(knowledge.label(path[:base + i + 1]) or core.humanize(rel[i]))
    return " › ".join(parts)
