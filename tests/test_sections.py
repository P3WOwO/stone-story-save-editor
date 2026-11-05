import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sample_save import demo_progress  # noqa: E402
from stone_story_editor import sections as sec  # noqa: E402

PD = "progress_data"


def profile():
    return {"player_name": "Hero", "version": "4.33.0", PD: demo_progress("Hero", 5)}


def test_classify_real_paths():
    assert sec.classify(("player_name",)) == "player"
    assert sec.classify((PD, "hero_settings", "playerName")) == "player"
    assert sec.classify((PD, "xp", "currentLevel")) == "player"
    assert sec.classify((PD, "inventory_data", "itms", 0, "co")) == "inventory"
    assert sec.classify((PD, "inventory_data", "Stone")) == "resources"
    assert sec.classify((PD, "inventory_data", "Xi")) == "resources"
    assert sec.classify((PD, "cosmetics", "golden", 0)) == "cosmetics"
    assert sec.classify((PD, "events", "spring_demo", "pp")) == "events"
    assert sec.classify((PD, "custom_quests", "active", 0, "completed")) == "quests"
    assert sec.classify((PD, "weekly_quest", "activeQuest", "completed")) == "quests"
    assert sec.classify((PD, "custom_quests", "revealed", 0)) == "progress"
    assert sec.classify((PD, "quest_data", "available", 0)) == "progress"
    assert sec.classify((PD, "quest_data", "star_levels", "temple")) == "locations"
    assert sec.classify((PD, "quest_data", "lastRewardTime")) == "time"
    assert sec.classify((PD, "treasure_factory", "goldDate")) == "time"


def test_unknown_goes_to_other_or_keywords():
    assert sec.classify((PD, "zzz_unknown", "foo")) == "other"
    assert sec.classify((PD, "misc", "notes")) == "other"


def test_find_inventory_real():
    ref = sec.find_inventory(profile())
    assert ref and ref.shape == "list" and ref.path == sec.INVENTORY_PATH
    items = sec.list_items(profile(), ref)
    assert [i.name for i in items][:2] == ["sword", "shield"]
    assert items[0].count_path == sec.INVENTORY_PATH + (0, "co")


def test_inventory_map_shapes_still_work():
    p = {PD: {"inventory": {"Stick": 2, "Herb": 7}}}
    ref = sec.find_inventory(p)
    assert ref.shape == "map_num"
    p = {PD: {"items": {"Stick": {"count": 2, "shiny": False}}}}
    assert sec.find_inventory(p).shape == "map_dict"


def test_no_inventory():
    assert sec.find_inventory({PD: {"gold": 1}}) is None


def test_event_groups_real():
    groups = sec.event_groups(profile())
    assert (PD, "events", "spring_demo") in groups
    leaves = dict(groups[(PD, "events", "spring_demo")])
    assert leaves[(PD, "events", "spring_demo", "pp")] is False
    assert sec.is_pass_key("pp") and not sec.is_pass_key("points")
    assert sec.is_points_key("rp") and sec.is_progress_key("p") is False


def test_tokens():
    assert "max" in sec.tokens("maxHealth") and "item" in sec.tokens("items")
