"""Builds a FAKE demo save (invented data) for tests and for trying the editor.

Run:  python tests/sample_save.py demo_save.txt
It is NOT a real Stone Story save - the key names are made up.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stone_story_editor.core import encrypt_progress, sjson_dumps  # noqa: E402


def demo_progress(name: str, gold: int) -> dict:
    return {
        "player_name": name,
        "gold": gold,
        "maxHealth": 120,
        "hardMode": False,
        "playTimeSeconds": 98765.5,
        "tutorial_done": True,
        "inventory": [
            {"item": "Wooden Stick", "count": 1, "stars": 1, "shiny": False},
            {"item": "Healing Herb", "count": 7, "stars": 0, "shiny": False},
            {"item": "Old [Map]", "count": 1, "stars": 0, "shiny": True},
        ],
        "resources": {"gold": 400, "event_tickets": 12, "crystals": 40},
        "events": {
            "spring_fest": {
                "pp": False, "points": 12,
                "tasks": [{"id": "t1", "progress": 3, "done": False}, {"id": "t2", "progress": 0, "done": False}],
            },
            "green_part_1": {"pp": False, "points": 0, "tasks": [{"id": "g1", "progress": 0, "done": False}]},
        },
        "quests": {"daily": [{"id": "d1", "done": False}], "weeklyDone": False},
        "cosmetics": {"goldenSkins": {"sword": False, "shield": True}},
        "locations": {"forest": {"stars": 2, "bestTime": 123.4}},
        "stats": {"kills": 342, "deaths": 12, "bestDepth": 27},
        "notes": "hello, world: {test}",
        "empty": None,
    }


def build(path: Path) -> None:
    root = {"save_file_last_id": 2}
    for i, (nm, gold) in enumerate([("Hero", 1500), ("Second Run", 90)], start=1):
        root[f"save_file_{i}"] = {
            "player_name": nm,
            "version": "4.33.0",
            "encrypted": True,
            "progress_data": encrypt_progress(sjson_dumps(demo_progress(nm, gold))),
        }
    path.write_text(sjson_dumps(root) + "\n", encoding="utf-8")


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "demo_save.txt")
    build(out)
    print("Created", out)
