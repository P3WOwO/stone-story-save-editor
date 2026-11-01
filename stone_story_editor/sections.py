"""Sorting save data into sections (inventory, events, player ...) - no GUI code.

The real key names of the game's save are not officially documented, so sections are
detected from key *words* instead of exact names. If the game uses a word that is not
recognised, edit the RULES table below (it is the only place you need to touch) -
anything unrecognised simply lands in the "other" section, nothing is hidden.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterator

from . import core

# order of the sections in the sidebar
UI_ORDER = ["inventory", "events", "player", "resources", "quests", "progress",
            "locations", "cosmetics", "time", "other"]

# order in which sections win when one key matches several (e.g. "event_tickets" -> events)
PRIORITY = ["events", "inventory", "quests", "cosmetics", "locations", "resources", "time", "progress", "player"]

# section -> (whole words, substrings)      <-- tweak here
RULES: dict[str, tuple[set[str], tuple[str, ...]]] = {
    "events": ({"event", "events", "season", "seasonal", "pass", "premium", "pp", "track", "reward", "rewards"},
               ("event", "premium")),
    "inventory": ({"inventory", "item", "items", "equip", "equipment", "equipped", "enchant", "enchantment",
                   "enchantments", "tag", "tags", "signature", "signatures", "shiny", "interacted", "trophy",
                   "trophies", "backpack", "bag", "loot"},
                  ("inventory", "enchant", "signature", "trophies")),
    "quests": ({"quest", "quests", "daily", "weekly", "legend", "legends", "objective", "objectives", "bounty",
                "mission", "missions"},
               ("quest", "legend", "objective")),
    "cosmetics": ({"cosmetic", "cosmetics", "skin", "skins", "golden", "prismatic", "glitch", "glitched", "color",
                   "colors", "colour", "colours", "outfit", "hat", "hats"},
                  ("cosmetic", "prismatic", "skin")),
    "locations": ({"location", "locations", "zone", "zones", "area", "areas", "star", "stars", "farm", "farms",
                   "offline", "besttime", "avgtime", "run", "runs"},
                  ("location", "offline")),
    "resources": ({"resource", "resources", "currency", "currencies", "coin", "coins", "gold", "ticket", "tickets",
                   "gem", "gems", "token", "tokens", "crystal", "crystals", "shard", "shards", "dust", "wood",
                   "ore", "ki"},
                  ("resource", "currency")),
    "time": ({"time", "times", "timer", "timers", "timeout", "timeouts", "restock", "haunted", "cooldown", "clock",
              "timestamp", "date", "seconds"},
             ("timeout", "timestamp", "restock")),
    "progress": ({"progress", "shop", "shops", "unlock", "unlocked", "task", "tasks", "achievement", "achievements",
                  "tutorial", "story", "visited", "discovered", "completed", "done"},
                 ("unlock", "achievement", "tutorial")),
    "player": ({"player", "name", "xp", "level", "exp", "experience", "chest", "chests", "profile", "version",
                "display", "stats", "stat"},
               ("player",)),
}

PASS_WORDS = {"pp", "premium", "paid", "pass"}
POINT_WORDS = {"points", "point", "pts", "level", "tier"}
PROGRESS_WORDS = POINT_WORDS | {"progress", "xp", "score", "stage"}
NAME_KEYS = ("name", "id", "item", "item_id", "itemid", "type", "key", "kind", "label")
COUNT_KEYS = ("count", "amount", "quantity", "qty", "stack", "num", "number", "q", "n", "c")


def tokens(key: Any) -> set[str]:
    """'maxHealth' -> {'max','health'}; also adds singular forms ('items' -> 'item')."""
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", str(key))
    out = {t for t in re.split(r"[^A-Za-z0-9]+", s.lower()) if t}
    out |= {t[:-1] for t in out if len(t) > 3 and t.endswith("s")}
    return out


def component_category(comp: Any) -> str | None:
    if isinstance(comp, int):
        return None
    raw = str(comp).lower()
    toks = tokens(comp)
    for cat in PRIORITY:
        words, subs = RULES[cat]
        if toks & words or any(s in raw for s in subs):
            return cat
    return None


def classify(path: tuple) -> str:
    """Which section a value belongs to. The outermost matching key wins."""
    if path and path[0] != "progress_data" and len(path) == 1:
        return "player"          # profile fields (name, version ...)
    for comp in path:
        if comp == "progress_data":
            continue
        cat = component_category(comp)
        if cat:
            return cat
    return "other"


# --------------------------------------------------------------------------
# Inventory
# --------------------------------------------------------------------------
@dataclass
class InventoryRef:
    path: tuple
    shape: str          # 'list' (list of dicts) | 'map_num' ({name: count}) | 'map_dict' ({name: {...}})


@dataclass
class Item:
    path: tuple          # where the item lives
    name: str
    count_path: tuple | None
    value: Any


def _shape_of(value: Any) -> str | None:
    if isinstance(value, list) and value and all(isinstance(v, dict) for v in value):
        return "list"
    if isinstance(value, dict) and value:
        vals = list(value.values())
        if all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in vals):
            return "map_num"
        if all(isinstance(v, dict) for v in vals):
            return "map_dict"
    return None


def _walk_containers(data: Any, path: tuple = (), depth: int = 0) -> Iterator[tuple[tuple, Any]]:
    if depth > 6:
        return
    if isinstance(data, (dict, list)):
        yield path, data
        children = data.items() if isinstance(data, dict) else enumerate(data)
        for k, v in children:
            if isinstance(v, (dict, list)):
                yield from _walk_containers(v, path + (k,), depth + 1)


def find_inventory(profile: dict) -> InventoryRef | None:
    """Best guess for the player's item list: an inventory-looking list/map with the most entries."""
    best: tuple[int, InventoryRef] | None = None
    for path, node in _walk_containers(profile):
        if not path:
            continue
        shape = _shape_of(node)
        if shape is None or classify(path) != "inventory":
            continue
        last = tokens(path[-1])
        score = len(node) + (1000 if last & {"inventory", "items", "item"} else 0)
        if "tags" in last or "enchantments" in last or "signatures" in last:
            score -= 900         # sub-lists inside an item, not the inventory itself
        if best is None or score > best[0]:
            best = (score, InventoryRef(path, shape))
    if best is None:      # an empty inventory: still let the user add items to it
        for path, node in _walk_containers(profile):
            if path and not node and tokens(path[-1]) & {"inventory", "items"} and classify(path) == "inventory":
                return InventoryRef(path, "list" if isinstance(node, list) else "map_num")
    return best[1] if best else None


def pick_name_key(item: dict) -> str | None:
    for k in NAME_KEYS:
        if isinstance(item.get(k), str):
            return k
    for k, v in item.items():
        if isinstance(v, str):
            return k
    return None


def pick_count_key(item: dict) -> str | None:
    for k in COUNT_KEYS:
        v = item.get(k)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return k
    return None


def list_items(profile: dict, ref: InventoryRef) -> list[Item]:
    node = core.get_at(profile, ref.path)
    items: list[Item] = []
    if ref.shape == "list":
        for i, entry in enumerate(node):
            nk, ck = pick_name_key(entry), pick_count_key(entry)
            name = str(entry[nk]) if nk else f"#{i + 1}"
            p = ref.path + (i,)
            items.append(Item(p, name, p + (ck,) if ck else None, entry))
    elif ref.shape == "map_num":
        for k, v in node.items():
            p = ref.path + (k,)
            items.append(Item(p, str(k), p, v))
    else:
        for k, entry in node.items():
            ck = pick_count_key(entry)
            p = ref.path + (k,)
            items.append(Item(p, str(k), p + (ck,) if ck else None, entry))
    return items


# --------------------------------------------------------------------------
# Events
# --------------------------------------------------------------------------
def is_pass_key(key: Any) -> bool:
    return bool(tokens(key) & PASS_WORDS) or "premium" in str(key).lower()


def is_points_key(key: Any) -> bool:
    return bool(tokens(key) & POINT_WORDS)


def is_progress_key(key: Any) -> bool:
    return bool(tokens(key) & PROGRESS_WORDS) or "point" in str(key).lower() or "progress" in str(key).lower()


def event_group_of(path: tuple) -> tuple:
    """Group leaves of one event together: .../events/<event name>/... -> .../events/<event name>."""
    idx = None
    for i, comp in enumerate(path):
        if comp != "progress_data" and component_category(comp) == "events":
            idx = i
            break
    if idx is None:
        return path[:-1]
    if len(path) - 1 > idx + 1:
        return path[:idx + 2]
    return path[:-1] if len(path) > 1 else path


def event_groups(profile: dict) -> dict[tuple, list[tuple[tuple, Any]]]:
    groups: dict[tuple, list[tuple[tuple, Any]]] = {}
    for path, value in core.iter_leaves(profile):
        if not path or path == ("encrypted",):
            continue
        if classify(path) == "events":
            groups.setdefault(event_group_of(path), []).append((path, value))
    return groups
