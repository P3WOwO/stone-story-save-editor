import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sample_save import demo_progress  # noqa: E402
from stone_story_editor import core, ops  # noqa: E402

S = "save_file_1"


def hist():
    root = {S: {"player_name": "A", "progress_data": demo_progress("A", 1)}}
    return core.History(root), copy.deepcopy(root)


def test_members_and_undo():
    h, before = hist()
    assert ops.set_member(h, S, ops.AVAILABLE, "waterfall", True)
    assert not ops.set_member(h, S, ops.AVAILABLE, "waterfall", True)        # already there
    assert ops.set_member(h, S, ops.AVAILABLE, "temple", False)
    avail = core.get_at(h.root[S], ops.AVAILABLE)
    assert "waterfall" in avail and "temple" not in avail
    while h.undo():
        pass
    assert h.root == before


def test_legend_follows_ssrpgs_rules():
    h, _ = hist()
    g = h.new_group()
    assert ops.set_legend(h, S, "epic_ascension", True, g)
    rec = core.get_at(h.root[S], ops.RECORDS)
    assert {"questId": "epic_ascension", "unlocked": True} in rec
    assert "epic_ascension" in core.get_at(h.root[S], ops.REVEALED)
    assert ops.set_legend(h, S, "epic_titanic_accord", False, g)             # existing record gets locked
    rec = core.get_at(h.root[S], ops.RECORDS)
    assert {"questId": "epic_titanic_accord", "unlocked": False} in rec
    assert "epic_titanic_accord" not in core.get_at(h.root[S], ops.REVEALED)
    assert len(h.undo()) >= 4          # one group = one undo


def test_cosmetics_prismatic_keeps_colours_in_sync():
    h, before = hist()
    assert ops.cosmetic_owned(h, S, "golden", "sword") and ops.cosmetic_owned(h, S, "golden", "shield")
    assert ops.set_cosmetic(h, S, "prismatic", "bardiche", True)
    cos = core.get_at(h.root[S], ops.COSMETICS)
    assert cos["prismatic"] == ["crossbow", "bardiche;new"] and len(cos["extra"]) == 2
    assert ops.set_prismatic_color(h, S, "bardiche", "#123456")
    assert ops.prismatic_color(h, S, "bardiche") == "#123456"
    assert ops.set_cosmetic(h, S, "prismatic", "crossbow", False)             # removes its colour too
    cos = core.get_at(h.root[S], ops.COSMETICS)
    assert cos["prismatic"] == ["bardiche;new"] and cos["extra"] == [{"c": "#123456"}]
    assert ops.set_cosmetic(h, S, "glitch", "sword", True) and not ops.set_cosmetic(h, S, "glitch", "sword", True)
    while h.undo():
        pass
    assert h.root == before


def test_star_levels_create_or_change():
    h, _ = hist()
    assert ops.set_star_level(h, S, "temple", 7)
    assert ops.set_star_level(h, S, "bronze_mine", 2)
    stars = core.get_at(h.root[S], ops.STAR_LEVELS)
    assert stars["temple"] == 7 and stars["bronze_mine"] == 2
    assert not ops.set_star_level(h, S, "temple", 7)


def test_ensure_creates_missing_sections():
    root = {S: {"progress_data": {"quest_data": {}}}}
    h = core.History(root)
    assert ops.set_member(h, S, ops.AVAILABLE, "temple", True)
    assert root[S]["progress_data"]["quest_data"]["available"] == ["temple"]
