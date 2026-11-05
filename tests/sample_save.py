"""Builds a FAKE demo save (invented data) for tests and for trying the editor.

Run:  python tests/sample_save.py demo_save.txt
It is NOT a real Stone Story save - the key names are made up.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stone_story_editor.core import encrypt_progress, sjson_dumps  # noqa: E402


def demo_progress(name: str, level: int) -> dict:
    """FAKE data that follows the real save layout (key names as documented by the SSRPGS project)."""
    return {
        "hero_settings": {"playerName": name},
        "xp": {"currentLevel": level, "currentXP": 5400},
        "inventory_data": {
            "Stone": 120, "Wood": 40, "Tar": 5, "Xi": 900, "Bronze": 0,
            "itms": [
                {"id": "sword", "co": 1, "da": {"hI": True, "lv": 10, "ra": {"lv": 21, "ql": 12049, "sSS": 123}}},
                {"id": "shield", "co": 1, "da": {"hI": True, "lv": 4}},
                {"id": "crossbow", "co": 2, "da": {"hI": False, "lv": 0}},
                {"id": "socketed_sword", "co": 1, "da": {"hI": True, "lv": 6, "el": "Fire", "sh": True}},
                {"id": "mystery_item", "co": 3, "da": {"hI": False}},
            ],
        },
        "cosmetics": {"golden": ["sword;new", "shield"], "glitch": [], "prismatic": ["crossbow"],
                      "extra": [{"c": "#ff00ff"}]},
        "events": {
            "sIds": ["spring_demo", "green_demo"],
            "spring_demo": {"pp": False, "rwds": {"rp": 12},
                            "objs": {"ids": ["t1", "t2"], "t1": {"p": 3}, "t2": {"p": 0}}},
            "green_demo": {"pp": False, "rwds": {"rp": 0}, "objs": {"ids": ["g1"], "g1": {"p": 0}}},
        },
        "custom_quests": {
            "nextSpawnDate": "01/01/2027 00:00:00", "epicSpawnPending": False, "basicQuestDate": "01/01/2027 00:00:00",
            "active": [{"customQuestId": "daily_demo", "completed": False}],
            "revealed": ["epic_titanic_accord"],
            "records": [{"questId": "epic_titanic_accord", "unlocked": True}],
        },
        "weekly_quest": {"activeQuest": {"type": "weekly_demo", "completed": False}},
        "quest_data": {
            "available": ["temple", "icy_ridge", "mutate", "find_shelter"],
            "star_levels": {"temple": 3, "icy_ridge": 1},
            "stats": [{"id": "temple3", "bT": 123.4, "aT": 150.0}],
            "lastRewardTime": "01/01/2027 00:00:00",
        },
        "treasure_factory": {"uniqueDate": "01/01/2027 00:00:00", "crystalDate": "01/01/2027 00:00:00",
                             "goldDate": "01/01/2027 00:00:00"},
        "crypt_intro": {"nextTreasureAvailableDate": "01/01/2027 00:00:00"},
        "misc": {"notes": "hello, world: {test}", "empty": None, "ratio": 98765.5, "flag": True},
    }


def build(path: Path) -> None:
    root = {"save_file_last_id": 2}
    for i, (nm, lvl) in enumerate([("Hero", 12), ("Second Run", 3)], start=1):
        root[f"save_file_{i}"] = {
            "player_name": nm,
            "version": "4.33.0",
            "encrypted": True,
            "progress_data": encrypt_progress(sjson_dumps(demo_progress(nm, lvl))),
        }
    path.write_text(sjson_dumps(root) + "\n", encoding="utf-8")


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "demo_save.txt")
    build(out)
    print("Created", out)
