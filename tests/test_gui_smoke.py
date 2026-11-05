"""GUI smoke tests. Skipped automatically when no display / tkinter is available (CI uses xvfb)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

tk = pytest.importorskip("tkinter")
try:
    _probe = tk.Tk()
    _probe.destroy()
except tk.TclError:                       # no display
    pytest.skip("no display available", allow_module_level=True)

from tkinter import messagebox  # noqa: E402

from sample_save import build  # noqa: E402
from stone_story_editor import catalog, config, core, gui, ops, sections  # noqa: E402

PD = "progress_data"


@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "cfg.json")
    f = tmp_path / "primary_save.txt"
    build(f)
    for name in ("showinfo", "showerror"):
        monkeypatch.setattr(messagebox, name, lambda *a, **k: None)
    monkeypatch.setattr(messagebox, "askyesno", lambda *a, **k: True)
    errors = []
    monkeypatch.setattr(tk.Tk, "report_callback_exception", lambda self, e, v, t: errors.append(v))
    a = gui.App()
    # modal dialogs: accept previews automatically
    def fake_wait(w):
        if hasattr(w, "accepted"):
            w.accepted = True
        w.destroy()
    monkeypatch.setattr(a, "wait_window", fake_wait)
    a.open_path(f)
    a.errors = errors
    a.file = f
    yield a
    assert not errors, errors
    a.destroy()


def goto(app, cat):
    app.goto(cat)
    app.update()
    return app.simple.content


def data(app):
    return app.root_data[app.current_slot]


def test_home_tiles_and_sections(app):
    assert app.nb.select() == str(app.home)
    for cat in ("inventory", "resources", "cosmetics", "player", "quests", "events", "progress", "locations"):
        content = goto(app, cat)
        assert content.special is not None, cat          # every section has its own page
        assert content.special_kind == cat
    app.goto("catalog")
    assert app.nb.select() == str(app.catalog_tab)


def test_inventory_uses_real_layout_and_wizard_adds_from_catalog(app):
    inv = goto(app, "inventory").special
    assert len(inv.cards) == 5
    first = list(inv.cards.values())[0]
    first.steppers[0]._bump(1)
    assert core.get_at(data(app), sections.INVENTORY_PATH + (0, "co")) == 2
    # wizard path: build + insert (same code the "Add" button runs)
    from stone_story_editor.catalog_ui import ItemWizard
    wiz = ItemWizard(app, "heavy_hammer")
    app.update()
    assert wiz.item.key == "heavy_hammer"
    wiz.vars["qty"].set("3")
    wiz.vars["stars"].set("5")
    wiz._add()
    items = core.get_at(data(app), sections.INVENTORY_PATH)
    assert items[-1] == {"id": "heavy_hammer", "co": 3, "da": {"hI": False, "lv": 5}}
    # unknown id items cannot be added from the catalogue
    wiz._chosen(catalog.BY_KEY["war_hammer"])
    assert "qty" not in wiz.vars
    wiz.destroy()
    app.undo()
    assert len(core.get_at(data(app), sections.INVENTORY_PATH)) == 5


def test_inventory_filters_are_separate_characteristics(app):
    inv = goto(app, "inventory").special
    assert "sword" in inv._type_keys and "unknown" in inv._type_keys
    inv.el_key = "Fire"
    inv.rebuild()
    assert len(inv.filtered) == 1 and inv.filtered[0].name == "socketed_sword"


def test_events_pass_bulk_preview_and_undo(app):
    ev = goto(app, "events").special
    assert len(ev.pass_paths) == 2 and len(ev.point_paths) == 2
    ev._pass(True)
    assert all(core.get_at(data(app), p) is True for p in ev.pass_paths)
    ev.points_var.set("35")
    ev._points()
    assert [core.get_at(data(app), p) for p in ev.point_paths] == [35, 35]
    app.undo()
    app.undo()
    assert all(core.get_at(data(app), p) is False for p in ev.pass_paths)


def test_player_resources_pages(app):
    page = goto(app, "player").special
    assert (PD, "xp", "currentLevel") in page.cards
    page._max_level()
    assert core.get_at(data(app), (PD, "xp", "currentLevel")) == 60
    res = goto(app, "resources").special
    res.n_var.set("100")
    res._bulk("add")
    assert core.get_at(data(app), (PD, "inventory_data", "Stone")) == 220


def test_cosmetics_progress_locations(app):
    cos = goto(app, "cosmetics").special
    cos._bulk("golden", True)
    owned = core.get_at(data(app), ops.COSMETICS + ("golden",))
    assert len(owned) >= 50 and "sword;new" in owned
    prog = goto(app, "progress").special
    prog._bulk("progress_locations", gui.kd.LOCATIONS if hasattr(gui, "kd") else __import__("stone_story_editor.knowledge_data", fromlist=["x"]).LOCATIONS, "avail", True)
    assert "waterfall" in core.get_at(data(app), ops.AVAILABLE)
    loc = goto(app, "locations").special
    loc.n_var.set("7")
    loc._all_set()
    assert core.get_at(data(app), ops.STAR_LEVELS)["temple"] == 7
    while app.history.undo():
        pass
    assert core.diff(app.original[app.current_slot], data(app)) == []


def test_old_features_still_work(app, tmp_path):
    content = goto(app, "all")
    assert content.special is None
    content.view_var.set("list")
    content._view_changed()
    assert content.row_paths
    app.nb.select(app.tree_tab)
    app.tree_tab.reveal((PD, "xp", "currentXP"))
    app.update()
    app.apply_set([(PD, "xp", "currentXP")], lambda _o: 77)
    app.undo()
    app.redo()
    assert core.get_at(data(app), (PD, "xp", "currentXP")) == 77
    app.toggle_language()
    app.toggle_theme()
    app.update()
    assert app.root_data is not None
    app.save_current()
    root, _ = core.load_save(app.file)
    assert root["save_file_1"][PD]["xp"]["currentXP"] == 77 or root["save_file_2"][PD]["xp"]["currentXP"] == 77
    assert core.list_backups(app.file)           # a backup was made
