import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stone_story_editor import i18n  # noqa: E402

PKG = Path(__file__).resolve().parents[1] / "stone_story_editor"


def test_same_keys_in_both_languages():
    assert set(i18n.STRINGS["ru"]) == set(i18n.STRINGS["en"])


def test_all_used_keys_exist():
    used = set()
    for f in PKG.glob("*.py"):
        if f.name == "i18n.py":
            continue
        used |= set(re.findall(r'\btr\(\s*"([a-z0-9_]+)"', f.read_text(encoding="utf-8")))
    missing = sorted(k for k in used if not k.endswith("_") and k not in i18n.STRINGS["en"])
    assert not missing, missing


def test_dynamic_keys_exist():
    for k in ("all", "number", "bool", "text", "changed"):
        assert "filter_" + k in i18n.STRINGS["en"]
    for k in ("name", "value", "section", "field", "type"):
        assert "col_" + k in i18n.STRINGS["en"]
    for k in ("text", "number", "bool", "null", "object", "array", "profile"):
        assert "kind_" + k in i18n.STRINGS["en"]
    for k in ("changed", "added", "removed"):
        assert "chg_type_" + k in i18n.STRINGS["en"]
    for k in ("what", "type", "old", "new"):
        assert "chg_" + k in i18n.STRINGS["en"]
    for k in ("simple", "tree"):
        assert "panel_empty_text_" + k in i18n.STRINGS["en"]
    for k in ("object", "array"):
        assert "container_info_" + k in i18n.STRINGS["en"]
    for k in ("1", "2", "3"):
        for suf in ("title", "text"):
            assert f"step{k}_{suf}" in i18n.STRINGS["en"]


def test_format_placeholders_match():
    for key, ru in i18n.STRINGS["ru"].items():
        en = i18n.STRINGS["en"][key]
        assert set(re.findall(r"\{(\w+)\}", ru)) == set(re.findall(r"\{(\w+)\}", en)), key
