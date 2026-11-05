import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sample_save import demo_progress  # noqa: E402
from stone_story_editor import catalog as cat  # noqa: E402
from stone_story_editor import knowledge as kn  # noqa: E402
from stone_story_editor.i18n import set_language  # noqa: E402


def items():
    return demo_progress("A", 1)["inventory_data"]["itms"]


def test_catalog_is_consistent():
    assert len(cat.ITEMS) > 40
    keys = [i.key for i in cat.ITEMS]
    assert len(keys) == len(set(keys))
    for it in cat.ITEMS:
        assert it.category in cat.CATEGORIES and it.sub in cat.SUBCATEGORIES
        assert (it.id is None) == (it.id_source == ""), it.key       # an id always has a source
        assert it.id_source in cat.SOURCE_TEXT
        assert it.hand in cat.HAND_TEXT and it.element in cat.ELEMENT_TEXT


def test_known_ids_are_exact():
    assert cat.BY_KEY["sword"].id == "sword" and cat.BY_KEY["rune_sword"].id == "socketed_sword"
    assert cat.BY_KEY["hatchet"].id == "hatchet_lv1"
    assert cat.BY_KEY["war_hammer"].id is None          # not in the sources: stays unknown
    assert not cat.BY_KEY["war_hammer"].addable


def test_search():
    set_language("en")
    assert [i.key for i in cat.search("rune sword")][:1] == ["rune_sword"]
    assert cat.search("socketed_staff")
    assert all(i.category == "lost" for i in cat.search(category="lost"))
    assert all(i.addable for i in cat.search(only_addable=True))
    assert cat.search("zzzzzz") == []
    set_language("ru")
    assert cat.search("Многозарядный")[0].key == "repeating_crossbow"
    set_language("en")


def test_display_name():
    set_language("en")
    assert cat.display_name("sword") == "Sword"
    assert cat.display_name("mystery_item") == "mystery_item"      # unknown ids are shown as they are


def test_build_item_minimal_and_template():
    it, note = cat.build_item(items(), "heavy_hammer", 2, stars=5)
    assert note == "minimal" and it == {"id": "heavy_hammer", "co": 2, "da": {"hI": False, "lv": 5}}
    # template: structure comes from the player's sword, personal state does not
    it, note = cat.build_item(items(), "sword", 1)
    assert note == "template" and it["da"] == {"hI": False}
    it, _ = cat.build_item(items(), "socketed_sword", 1, stars=3, shiny=True, element="Ice",
                           enchant=dict(cat.MAX_ENCHANT_EXAMPLE))
    assert it["da"] == {"hI": False, "lv": 3, "sh": True, "el": "Ice", "ra": {"lv": 21, "ql": 12049, "sSS": 0}}


def test_known_values_come_from_the_save():
    assert cat.known_values(items(), "el") == ["Fire"]
    assert cat.known_values(items(), "el", "sword") == []
    assert len(cat.enchanted_examples(items())) == 1


def test_enchant_tiers():
    set_language("en")
    assert kn.enchant_tier(1)[0] == "Common" and kn.enchant_tier(3)[0] == "Rare"
    assert kn.enchant_tier(6)[0] == "Heroic" and kn.enchant_tier(10)[0] == "Epic"
    assert kn.enchant_tier(15)[0] == "Legendary" and kn.enchant_tier(21)[0] == "Transcendent"
    assert kn.enchant_tier(22) is None and kn.enchant_tier(0) is None


def test_knowledge_info_and_unknown():
    set_language("en")
    pd = "progress_data"
    assert kn.info((pd, "xp", "currentLevel")).name == "Player level"
    assert "30" in kn.info((pd, "events", "any_event", "pp")).hint
    assert kn.info((pd, "inventory_data", "itms", 3, "da", "sh")).name.startswith("Shiny")
    assert kn.info((pd, "misc", "ratio")) is None            # unknown stays unknown
    assert "does not guess" in kn.not_described()
    assert kn.id_name("temple") and kn.id_name("no_such_id") is None
    assert kn.resource_name("Xi") == "Ki"
