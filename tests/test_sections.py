import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sample_save import demo_progress  # noqa: E402
from stone_story_editor import sections as sec  # noqa: E402


def profile():
    return {"player_name": "Hero", "version": "4.33.0", "progress_data": demo_progress("Hero", 5)}


def test_classify_basic():
    assert sec.classify(("player_name",)) == "player"
    assert sec.classify(("progress_data", "inventory", 0, "count")) == "inventory"
    assert sec.classify(("progress_data", "events", "spring_fest", "pp")) == "events"
    assert sec.classify(("progress_data", "resources", "gold")) == "resources"
    assert sec.classify(("progress_data", "quests", "daily", 0, "done")) == "quests"
    assert sec.classify(("progress_data", "cosmetics", "goldenSkins", "sword")) == "cosmetics"
    assert sec.classify(("progress_data", "locations", "forest", "stars")) == "locations"
    assert sec.classify(("progress_data", "zzz_unknown", "foo")) == "other"


def test_event_tickets_inside_resources_stay_resources():
    # the outermost matching key wins
    assert sec.classify(("progress_data", "resources", "event_tickets")) == "resources"


def test_find_inventory_list():
    ref = sec.find_inventory(profile())
    assert ref and ref.shape == "list" and ref.path == ("progress_data", "inventory")
    items = sec.list_items(profile(), ref)
    assert [i.name for i in items] == ["Wooden Stick", "Healing Herb", "Old [Map]"]
    assert items[1].count_path == ("progress_data", "inventory", 1, "count")


def test_inventory_map_shapes():
    p = {"progress_data": {"inventory": {"Stick": 2, "Herb": 7}}}
    ref = sec.find_inventory(p)
    assert ref.shape == "map_num"
    items = sec.list_items(p, ref)
    assert items[1].count_path == ("progress_data", "inventory", "Herb")
    p = {"progress_data": {"items": {"Stick": {"count": 2, "shiny": False}}}}
    ref = sec.find_inventory(p)
    assert ref.shape == "map_dict"
    assert sec.list_items(p, ref)[0].count_path == ("progress_data", "items", "Stick", "count")


def test_no_inventory():
    assert sec.find_inventory({"progress_data": {"gold": 1}}) is None


def test_event_groups_and_pass_detection():
    groups = sec.event_groups(profile())
    assert ("progress_data", "events", "spring_fest") in groups
    assert ("progress_data", "events", "green_part_1") in groups
    leaves = dict(groups[("progress_data", "events", "spring_fest")])
    assert leaves[("progress_data", "events", "spring_fest", "pp")] is False
    assert sec.is_pass_key("pp") and sec.is_pass_key("premiumUnlocked") and not sec.is_pass_key("points")
    assert sec.is_points_key("points") and sec.is_progress_key("progress")


def test_tokens():
    assert "max" in sec.tokens("maxHealth") and "item" in sec.tokens("items")
