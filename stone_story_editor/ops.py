"""Edits of lists / records that go through History (so Undo/Redo and bulk groups work). No GUI code."""
from __future__ import annotations

from typing import Any

from . import core

PD = "progress_data"
COSMETICS = (PD, "cosmetics")
COSMETIC_KINDS = ("golden", "glitch", "prismatic")
AVAILABLE = (PD, "quest_data", "available")
STAR_LEVELS = (PD, "quest_data", "star_levels")
REVEALED = (PD, "custom_quests", "revealed")
RECORDS = (PD, "custom_quests", "records")


def _get(h: core.History, slot: str, path: tuple, default: Any = None) -> Any:
    try:
        return core.get_at(h.root[slot], path)
    except (KeyError, IndexError, TypeError):
        return default


def ensure(h: core.History, slot: str, path: tuple, default: Any, group: int | None = None) -> Any:
    """Make sure `path` exists (creating it with a copy of `default`); returns the value there."""
    value = _get(h, slot, path, None)
    if value is None:
        parent = _get(h, slot, path[:-1], None)
        if not isinstance(parent, dict):
            raise KeyError(path)
        h.add_item(slot, path[:-1], path[-1], default, group=group)
        value = _get(h, slot, path)
    return value


# ---- plain id lists (unlocked locations / workbench / projects) ----
def has_member(h: core.History, slot: str, list_path: tuple, value: Any) -> bool:
    return value in (_get(h, slot, list_path, []) or [])


def set_member(h: core.History, slot: str, list_path: tuple, value: Any, on: bool, group: int | None = None) -> bool:
    """Add / remove `value` in a list. Returns True when something changed."""
    ensure(h, slot, list_path, [], group)
    lst = _get(h, slot, list_path)
    if on and value not in lst:
        h.add_item(slot, list_path, None, value, group=group)
        return True
    if not on and value in lst:
        h.delete_item(slot, list_path + (lst.index(value),), group=group)
        return True
    return False


# ---- legends: the revealed list plus a record per legend (same rules as the SSRPGS editor) ----
def legend_open(h: core.History, slot: str, legend: str) -> bool:
    return has_member(h, slot, REVEALED, legend)


def set_legend(h: core.History, slot: str, legend: str, on: bool, group: int | None = None) -> bool:
    ensure(h, slot, RECORDS, [], group)
    changed = set_member(h, slot, REVEALED, legend, on, group)
    records = _get(h, slot, RECORDS, [])
    idx = next((i for i, r in enumerate(records) if isinstance(r, dict) and r.get("questId") == legend), None)
    if on:
        if idx is None:
            h.add_item(slot, RECORDS, None, {"questId": legend, "unlocked": True}, group=group)
            changed = True
        elif records[idx].get("unlocked") is not True:
            h.set_value(slot, RECORDS + (idx, "unlocked"), True, group=group)
            changed = True
    elif idx is not None and records[idx].get("unlocked") is not False:
        h.set_value(slot, RECORDS + (idx, "unlocked"), False, group=group)
        changed = True
    return changed


# ---- cosmetics: lists of "id" or "id;new"; prismatic skins have a parallel "extra" list of colours ----
def cosmetic_index(h: core.History, slot: str, kind: str, key: str) -> int | None:
    for i, v in enumerate(_get(h, slot, COSMETICS + (kind,), []) or []):
        if isinstance(v, str) and v.split(";")[0] == key:
            return i
    return None


def cosmetic_owned(h: core.History, slot: str, kind: str, key: str) -> bool:
    return cosmetic_index(h, slot, kind, key) is not None


def set_cosmetic(h: core.History, slot: str, kind: str, key: str, on: bool, group: int | None = None) -> bool:
    ensure(h, slot, COSMETICS, {}, group)
    ensure(h, slot, COSMETICS + (kind,), [], group)
    idx = cosmetic_index(h, slot, kind, key)
    if on and idx is None:
        h.add_item(slot, COSMETICS + (kind,), None, f"{key};new", group=group)
        if kind == "prismatic":
            ensure(h, slot, COSMETICS + ("extra",), [], group)
            h.add_item(slot, COSMETICS + ("extra",), None, {"c": "#000000"}, group=group)
        return True
    if not on and idx is not None:
        h.delete_item(slot, COSMETICS + (kind, idx), group=group)
        extra = _get(h, slot, COSMETICS + ("extra",), None)
        if kind == "prismatic" and isinstance(extra, list) and idx < len(extra):
            h.delete_item(slot, COSMETICS + ("extra", idx), group=group)
        return True
    return False


def prismatic_color(h: core.History, slot: str, key: str) -> str | None:
    idx = cosmetic_index(h, slot, "prismatic", key)
    extra = _get(h, slot, COSMETICS + ("extra",), [])
    if idx is not None and isinstance(extra, list) and idx < len(extra) and isinstance(extra[idx], dict):
        return extra[idx].get("c")
    return None


def set_prismatic_color(h: core.History, slot: str, key: str, color: str, group: int | None = None) -> bool:
    idx = cosmetic_index(h, slot, "prismatic", key)
    extra = _get(h, slot, COSMETICS + ("extra",), None)
    if idx is None or not isinstance(extra, list) or idx >= len(extra):
        return False
    return h.set_value(slot, COSMETICS + ("extra", idx, "c"), color, group=group)


# ---- location stars ----
def set_star_level(h: core.History, slot: str, location: str, stars: int, group: int | None = None) -> bool:
    ensure(h, slot, STAR_LEVELS, {}, group)
    path = STAR_LEVELS + (location,)
    if _get(h, slot, path, None) is None:
        h.add_item(slot, STAR_LEVELS, location, int(stars), group=group)
        return True
    return h.set_value(slot, path, int(stars), group=group)
