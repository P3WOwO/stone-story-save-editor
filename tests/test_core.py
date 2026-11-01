import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sample_save import build, demo_progress  # noqa: E402
from stone_story_editor import core  # noqa: E402


@pytest.fixture()
def save_file(tmp_path):
    p = tmp_path / "primary_save.txt"
    build(p)
    return p


def test_encrypt_decrypt_roundtrip():
    for n in (1, 31, 33, 65, 1000):
        text = "x" * n
        assert core.decrypt_progress(core.encrypt_progress(text)) == text
    # block-aligned input gets one harmless trailing newline (ignored by the parser)
    for n in (32, 64):
        text = "x" * n
        assert core.decrypt_progress(core.encrypt_progress(text)) == text + "\n"


def test_parser_roundtrip():
    data = demo_progress("A", 5)
    assert core.SJSONParser(core.sjson_dumps(data)).parse() == data


def test_parser_types():
    p = core.SJSONParser("{a:1,b:2.5,c:True,d:False,e:null,f:word,g:\"x y\",h:[1,2]}").parse()
    assert p == {"a": 1, "b": 2.5, "c": True, "d": False, "e": None, "f": "word", "g": "x y", "h": [1, 2]}


def test_load_decrypts_all_profiles(save_file):
    root, slots = core.load_save(save_file)
    assert slots == ["save_file_1", "save_file_2"]
    assert root["save_file_1"]["progress_data"]["gold"] == 1500
    assert root["save_file_2"]["progress_data"]["player_name"] == "Second Run"


def test_write_creates_backup_and_roundtrips(save_file):
    root, slots = core.load_save(save_file)
    root["save_file_1"]["progress_data"]["gold"] = 999999
    backup = core.write_save(root, slots, save_file, backup_existing=True)
    assert backup is not None and backup.exists()
    assert core.list_backups(save_file) == [backup]
    again, _ = core.load_save(save_file)
    assert again["save_file_1"]["progress_data"]["gold"] == 999999
    old, _ = core.load_save(backup)
    assert old["save_file_1"]["progress_data"]["gold"] == 1500


def test_looks_like_save(save_file, tmp_path):
    assert core.looks_like_save(save_file)
    other = tmp_path / "other.txt"
    other.write_text("hello")
    assert not core.looks_like_save(other)


def test_bad_file_rejected():
    with pytest.raises(Exception):
        core.load_save_text("this is not a save")
    with pytest.raises(ValueError):
        core.load_save_text("{a:1}")


def test_diff():
    a = {"x": 1, "y": [1, 2], "z": {"k": True}}
    b = {"x": 2, "y": [1, 2, 3], "z": {}, "n": 1}
    kinds = {(t, p) for t, p, _, _ in core.diff(a, b)}
    assert ("changed", ("x",)) in kinds
    assert ("added", ("y", 2)) in kinds
    assert ("removed", ("z", "k")) in kinds
    assert ("added", ("n",)) in kinds
    # bool vs int must count as a change
    assert core.diff({"a": 1}, {"a": True})


def test_history_undo_redo(save_file):
    root, _ = core.load_save(save_file)
    h = core.History(root)
    s = "save_file_1"
    snapshot = core.get_at(root[s], ())
    import copy
    before = copy.deepcopy(snapshot)
    assert h.set_value(s, ("progress_data", "gold"), 10)
    assert not h.set_value(s, ("progress_data", "gold"), 10)
    h.add_item(s, ("progress_data", "stats"), "wins", 3)
    h.add_item(s, ("progress_data", "inventory"), None, {"item": "X", "count": 1})
    h.delete_item(s, ("progress_data", "maxHealth"))
    h.delete_item(s, ("progress_data", "inventory", 0))
    after = copy.deepcopy(root[s])
    assert after != before
    while h.undo():
        pass
    assert root[s] == before
    assert list(root[s]["progress_data"].keys()) == list(before["progress_data"].keys())
    while h.redo():
        pass
    assert root[s] == after


def test_parse_typed():
    assert core.parse_typed("number", "1 000") == 1000
    assert core.parse_typed("number", "2,5") == 2.5
    assert core.parse_typed("bool", "Yes") is True
    with pytest.raises(ValueError):
        core.parse_typed("number", "abc")
    with pytest.raises(ValueError):
        core.parse_typed("number", "nan")


def test_humanize():
    assert core.humanize("maxHealth") == "Max health"
    assert core.humanize("play_time_seconds") == "Play time seconds"
    assert core.humanize(0) == "#1"


def test_grouped_undo(save_file):
    root, _ = core.load_save(save_file)
    h = core.History(root)
    s = "save_file_1"
    g = h.new_group()
    h.set_value(s, ("progress_data", "gold"), 1, group=g)
    h.set_value(s, ("progress_data", "maxHealth"), 2, group=g)
    assert root[s]["progress_data"]["gold"] == 1
    assert len(h.undo()) == 2
    assert root[s]["progress_data"]["gold"] == 1500
    assert root[s]["progress_data"]["maxHealth"] == 120
    assert len(h.redo()) == 2
    assert root[s]["progress_data"]["maxHealth"] == 2
    assert h.undo() and h.undo() == []
