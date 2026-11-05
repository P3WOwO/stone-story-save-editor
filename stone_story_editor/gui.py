"""Tkinter user interface for the Stone Story RPG save editor."""
from __future__ import annotations

import copy
import datetime as _dt
import json
import shutil
import sys
import traceback
from pathlib import Path
from typing import Any, Callable
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from . import __version__, config, core, theme
from .cards import ValueCard, icon_for, smart_step  # noqa: F401
from .common import describe_path, display_value, fmt_num, friendly_path, kind_label
from . import sections as sec
from .i18n import tr, set_language, current_language, help_sections
from . import catalog, knowledge
from .catalog_ui import CatalogTab
from .pages import CosmeticsPage, LocationsPage, PlayerPage, ProgressPage, QuestsPage, ResourcesPage
from .views import EventsView, InventoryView

SPECIAL = {"inventory": InventoryView, "events": EventsView, "player": PlayerPage, "resources": ResourcesPage,
           "cosmetics": CosmeticsPage, "quests": QuestsPage, "progress": ProgressPage, "locations": LocationsPage}
SEARCH_KINDS = {"inventory", "cosmetics"}       # pages where the search box is useful
PRIMARY = ("inventory", "resources", "cosmetics", "player", "quests", "events", "progress", "locations")
from .widgets import FinderDialog, PickDialog, PreviewDialog, TextDialog, Tooltip, ValueDialog

MAX_ROWS = 3000          # rows shown at once in the simple list
BIG_INT = 2 ** 31        # values beyond this may overflow the game's counters
TECH_PATHS = {("encrypted",)}  # technical fields hidden from the simple list


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
# Edit panel (shared by simple list and tree)
# --------------------------------------------------------------------------
class EditPanel(ttk.Frame):
    """Right-hand card that shows the selected value and lets the user change it."""

    def __init__(self, parent, app: "App", mode: str):
        super().__init__(parent, style="Card.TFrame", padding=16, width=350)
        self.app, self.mode = app, mode
        self.pack_propagate(False)
        self.grid_propagate(False)
        self.paths: list[tuple] = []
        self.body = ttk.Frame(self, style="Inner.TFrame")
        self.body.pack(fill="both", expand=True)
        self._entry: tk.Widget | None = None
        self.show([])

    # ---- building blocks -------------------------------------------------
    def _clear(self) -> None:
        for w in self.body.winfo_children():
            w.destroy()
        self._entry = None

    def _label(self, text, style="Card.TLabel", **kw) -> ttk.Label:
        lb = ttk.Label(self.body, text=text, style=style, wraplength=310, justify="left", **kw)
        lb.pack(anchor="w", fill="x")
        return lb

    def focus_entry(self) -> None:
        if self._entry is not None:
            self._entry.focus_set()
            try:
                self._entry.selection_range(0, "end")
            except Exception:
                pass

    # ---- main entry point --------------------------------------------------
    def show(self, paths: list[tuple]) -> None:
        self._clear()
        self.paths = paths
        app = self.app
        if not paths or app.root_data is None:
            self._label(tr("panel_empty_title"), "H2.TLabel")
            ttk.Label(self.body, text="", style="Card.TLabel").pack()
            self._label(tr("panel_empty_text_" + self.mode), "CardMuted.TLabel")
            return
        data = app.root_data[app.current_slot]
        try:
            values = [core.get_at(data, p) for p in paths]
        except (KeyError, IndexError):
            self.show([])
            return
        if len(paths) > 1:
            self._show_many(paths, values)
        else:
            self._show_one(paths[0], values[0])

    # ---- one value ----------------------------------------------------------
    def _show_one(self, path: tuple, value: Any) -> None:
        app = self.app
        kind = core.kind_of(value)
        name = (knowledge.label(path) or core.humanize(path[-1])) if path else tr("whole_profile")
        self._label(name, "H1.TLabel")
        self._label(friendly_path(path[:-1]) if len(path) > 1 else "", "CardMuted.TLabel")
        self._label(f"{tr('technical_key')}: {core.path_str(path) or '—'}", "CardMuted.TLabel")
        known_hint = knowledge.hint_for(path)
        if known_hint:
            self._label(known_hint, "Card.TLabel")

        changed = path in app.changed_paths(app.current_slot)
        if kind in ("object", "array"):
            self._container_ui(path, value, kind)
        elif kind == "number":
            self._number_ui(path, value)
        elif kind == "bool":
            self._bool_ui(path, value)
        elif kind == "text":
            self._text_ui(path, value)
        else:
            self._label(tr("value_empty"), "CardMuted.TLabel")
            ttk.Button(self.body, text=tr("set_value"), style="Accent.TButton",
                       command=lambda: self._advanced(path, value)).pack(anchor="w", pady=8)

        if changed and core.is_leaf(value):
            orig = app.original_value(path)
            box = ttk.Frame(self.body, style="Inner.TFrame")
            box.pack(fill="x", pady=(14, 0))
            ttk.Label(box, text=f"{tr('was')}: {display_value(orig[1]) if orig[0] else tr('did_not_exist')}",
                      style="CardMuted.TLabel", wraplength=300).pack(anchor="w")
            if orig[0]:
                ttk.Button(box, text=tr("restore_original"),
                           command=lambda: app.apply_set([path], lambda _o: orig[1])).pack(anchor="w", pady=(6, 0))

        ttk.Separator(self.body).pack(fill="x", pady=14)
        row = ttk.Frame(self.body, style="Inner.TFrame")
        row.pack(fill="x")
        if core.is_leaf(value):
            ttk.Button(row, text=tr("advanced_edit"), command=lambda: self._advanced(path, value)).pack(side="left")
        if self.mode == "tree" and path:
            ttk.Button(row, text=tr("delete"), style="Danger.TButton",
                       command=lambda: app.delete_path(path)).pack(side="right")
        if self.mode == "simple":
            ttk.Button(self.body, text=tr("show_in_tree"),
                       command=lambda: app.show_in_tree(path)).pack(anchor="w", pady=(8, 0))

    def _advanced(self, path: tuple, value: Any) -> None:
        dlg = ValueDialog(self.app, tr("advanced_edit"), self.app.pal, value)
        self.app.wait_window(dlg)
        if dlg.accepted:
            self.app.apply_set([path], lambda _o: dlg.result)

    def _container_ui(self, path: tuple, value: Any, kind: str) -> None:
        app = self.app
        self._label(tr("container_info_" + kind, n=len(value)), "Card.TLabel")
        ttk.Label(self.body, text="", style="Card.TLabel").pack()
        ttk.Button(self.body, text=tr("add_field") if kind == "object" else tr("add_item"),
                   style="Accent.TButton", command=lambda: app.add_child(path)).pack(anchor="w", pady=2)
        ttk.Button(self.body, text=tr("edit_as_json"), command=lambda: self._json_edit(path, value)
                   ).pack(anchor="w", pady=2)

    def _json_edit(self, path: tuple, value: Any) -> None:
        dlg = ValueDialog(self.app, tr("edit_as_json"), self.app.pal, value, allow_kind_change=False,
                          hint=tr("json_hint"))
        self.app.wait_window(dlg)
        if dlg.accepted:
            self.app.apply_set([path], lambda _o: dlg.result)

    # ---- number -------------------------------------------------------------
    def _number_ui(self, path: tuple, value: Any) -> None:
        app = self.app
        self._label(tr("new_value"), "CardMuted.TLabel")
        var = tk.StringVar(value=str(value))
        entry = ttk.Entry(self.body, textvariable=var, font="SSEEntry")
        entry.pack(fill="x", pady=(2, 2))
        self._entry = entry
        hint = ttk.Label(self.body, text="", style="CardMuted.TLabel")
        hint.pack(anchor="w")

        def update_hint(*_a):
            try:
                v = core.parse_typed("number", var.get())
                hint.configure(text=f"= {fmt_num(v)}")
            except ValueError:
                hint.configure(text=tr("not_a_number"))

        var.trace_add("write", update_hint)
        update_hint()

        def commit(_e=None):
            try:
                v = core.parse_typed("number", var.get())
            except ValueError:
                messagebox.showerror(tr("err_bad_value"), tr("err_bad_for_kind", kind=tr("kind_number")), parent=app)
                return
            app.apply_set([path], lambda old: app.coerce_number(old, v))

        entry.bind("<Return>", commit)
        ttk.Button(self.body, text=tr("apply"), style="Accent.TButton", command=commit).pack(fill="x", pady=(8, 10))
        self._label(tr("quick_add"), "CardMuted.TLabel")
        self._quick_buttons(app, [path], [(f"+{fmt_num(n)}", n) for n in (10, 100, 1000, 10000)], "add")
        self._quick_buttons(app, [path], [("−100", -100)], "add")
        self._quick_buttons(app, [path], [("×2", 2), ("×10", 10)], "mul", new_row=False)
        self._quick_buttons(app, [path], [("= 0", 0)], "set", new_row=False)

    def _quick_buttons(self, app: "App", paths: list[tuple], items, op: str, new_row: bool = True) -> None:
        if new_row or not hasattr(self, "_qrow") or not self._qrow.winfo_exists():
            self._qrow = ttk.Frame(self.body, style="Inner.TFrame")
            self._qrow.pack(fill="x", pady=(2, 2))
        for text, n in items:
            def run(n=n):
                if op == "add":
                    app.apply_set(paths, lambda old, n=n: app.coerce_number(old, old + n))
                elif op == "mul":
                    app.apply_set(paths, lambda old, n=n: app.coerce_number(old, old * n))
                else:
                    app.apply_set(paths, lambda old, n=n: app.coerce_number(old, n))
            ttk.Button(self._qrow, text=text, style="Quick.TButton", width=6, command=run).pack(side="left", padx=2)

    # ---- bool ---------------------------------------------------------------
    def _bool_ui(self, path: tuple, value: bool) -> None:
        app = self.app
        self._label(tr("switch"), "CardMuted.TLabel")
        row = ttk.Frame(self.body, style="Inner.TFrame")
        row.pack(fill="x", pady=6)
        ttk.Button(row, text=tr("yes"), style="Big.Accent.TButton" if value else "Big.TButton",
                   command=lambda: app.apply_set([path], lambda _o: True)).pack(side="left", expand=True, fill="x",
                                                                                  padx=(0, 4))
        ttk.Button(row, text=tr("no"), style="Big.Accent.TButton" if not value else "Big.TButton",
                   command=lambda: app.apply_set([path], lambda _o: False)).pack(side="left", expand=True, fill="x")

    # ---- text ---------------------------------------------------------------
    def _text_ui(self, path: tuple, value: str) -> None:
        app = self.app
        self._label(tr("new_value"), "CardMuted.TLabel")
        multiline = "\n" in value or len(value) > 50
        if multiline:
            txt = tk.Text(self.body, height=5, wrap="word", bg=app.pal["input"], fg=app.pal["text"],
                          insertbackground=app.pal["text"], relief="solid", bd=1, highlightthickness=0, padx=6, pady=4)
            txt.insert("1.0", value)
            txt.pack(fill="x", pady=(2, 8))
            self._entry = txt
            get = lambda: txt.get("1.0", "end-1c")
            txt.bind("<Control-Return>", lambda _e: (app.apply_set([path], lambda _o: get()), "break")[1])
        else:
            var = tk.StringVar(value=value)
            entry = ttk.Entry(self.body, textvariable=var, font="SSEEntry")
            entry.pack(fill="x", pady=(2, 8))
            self._entry = entry
            get = var.get
            entry.bind("<Return>", lambda _e: app.apply_set([path], lambda _o: get()))
        ttk.Button(self.body, text=tr("apply"), style="Accent.TButton",
                   command=lambda: app.apply_set([path], lambda _o: get())).pack(fill="x")

    # ---- several values -----------------------------------------------------
    def _show_many(self, paths: list[tuple], values: list[Any]) -> None:
        app = self.app
        self._label(tr("selected_n", n=len(paths)), "H1.TLabel")
        ttk.Label(self.body, text="", style="Card.TLabel").pack()
        kinds = {core.kind_of(v) for v in values}
        if kinds != {"number"}:
            self._label(tr("bulk_numbers_only"), "CardMuted.TLabel")
            return
        self._label(tr("bulk_hint"), "CardMuted.TLabel")
        var = tk.StringVar(value="")
        entry = ttk.Entry(self.body, textvariable=var, font="SSEEntry")
        entry.pack(fill="x", pady=(8, 8))
        self._entry = entry

        def set_all(_e=None):
            try:
                v = core.parse_typed("number", var.get())
            except ValueError:
                messagebox.showerror(tr("err_bad_value"), tr("err_bad_for_kind", kind=tr("kind_number")), parent=app)
                return
            app.apply_set(paths, lambda old: app.coerce_number(old, v))

        entry.bind("<Return>", set_all)
        ttk.Button(self.body, text=tr("set_all_to"), style="Accent.TButton", command=set_all).pack(fill="x")
        self._label(tr("quick_add"), "CardMuted.TLabel")
        self._quick_buttons(app, paths, [(f"+{fmt_num(n)}", n) for n in (10, 100, 1000, 10000)], "add")
        self._quick_buttons(app, paths, [("−100", -100)], "add")
        self._quick_buttons(app, paths, [("×2", 2), ("×10", 10)], "mul", new_row=False)
        self._quick_buttons(app, paths, [("= 0", 0)], "set", new_row=False)


# --------------------------------------------------------------------------
# Simple tab: friendly cards  +  classic list
# --------------------------------------------------------------------------
class ContentTab(ttk.Frame):
    CARD_W = 300     # preferred card width in pixels
    PAGE = 90        # cards created at once ("Show more" adds another page)

    def __init__(self, parent, app: "App"):
        super().__init__(parent, padding=(0, 10, 0, 0))
        self.app = app
        self.leaves: list[tuple[tuple, str, str, str]] = []
        self.row_paths: dict[str, tuple] = {}
        self.path_iid: dict[tuple, str] = {}
        self.cards: dict[tuple, ValueCard] = {}
        self._sections: list[tuple[tk.Widget, list[ValueCard]]] = []
        self._extra: list[tk.Widget] = []
        self.sort_col, self.sort_rev = "section", False
        self.card_limit = self.PAGE
        self.category = "all"
        self.cat_counts: dict[str, int] = {}
        self.special: ttk.Frame | None = None
        self.special_kind: str | None = None
        self.special_off: set[str] = set()
        self._job = None
        self._layout_job = None
        self._ncols = 0
        self._maxcols = 0
        p = app.pal

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        top = ttk.Frame(self)
        self.top = top
        top.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        self.view_var = tk.StringVar(value=app.cfg.get("view", "cards"))
        self.viewbar = ttk.Frame(top)
        self.viewbar.pack(side="right")
        for key in ("list", "cards"):
            rb = ttk.Radiobutton(self.viewbar, text=tr("view_" + key), value=key, variable=self.view_var,
                                 style="Chip.TRadiobutton", command=self._view_changed)
            rb.pack(side="right", padx=2)
            Tooltip(rb, tr("tip_view_" + key), p)
        ttk.Separator(self.viewbar, orient="vertical").pack(side="right", fill="y", padx=8, pady=2)
        self.smart_btn = ttk.Button(top, text="★  " + tr("use_special"), command=lambda: self.set_special(True))
        ttk.Label(top, text=tr("search_hint") + ":", style="Muted.TLabel").pack(side="left", padx=(0, 8))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search)
        self.search = ttk.Entry(top, textvariable=self.search_var, font="SSEEntry", width=12)
        self.search.pack(side="left", fill="x", expand=True, ipady=3)
        ttk.Button(top, text="✕", width=3, command=lambda: self.search_var.set("")).pack(side="left", padx=(4, 12))
        self.filter_var = tk.StringVar(value="all")
        self.chips = ttk.Frame(top)
        self.chips.pack(side="left")
        for key in ("all", "number", "bool", "text", "changed"):
            ttk.Radiobutton(self.chips, text=tr("filter_" + key), value=key, variable=self.filter_var,
                            style="Chip.TRadiobutton", command=self._filter_changed).pack(side="left", padx=2)

        # ---- classic list view ----
        self.list_card = ttk.Frame(self, style="Card.TFrame")
        self.list_card.rowconfigure(0, weight=1)
        self.list_card.columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(self.list_card, columns=("name", "value", "section"), show="headings",
                                 selectmode="extended")
        for col, w in (("name", 220), ("value", 190), ("section", 260)):
            self.tree.heading(col, text=tr("col_" + col), command=lambda c=col: self._sort_by(c))
            self.tree.column(col, width=w, minwidth=80, anchor="w")
        ys = ttk.Scrollbar(self.list_card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=ys.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        ys.grid(row=0, column=1, sticky="ns")
        self.tree.tag_configure("odd", background=p["row_alt"])
        self.tree.tag_configure("changed", background=p["changed"])
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", lambda _e: self.panel.focus_entry())
        self.tree.bind("<Return>", lambda _e: self.panel.focus_entry())
        self.panel = EditPanel(self, app, "simple")

        # ---- cards view ----
        self.cards_wrap = ttk.Frame(self, style="Card.TFrame")
        self.cards_wrap.rowconfigure(0, weight=1)
        self.cards_wrap.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(self.cards_wrap, bg=p["bg"], highlightthickness=0)
        self.vsb = ttk.Scrollbar(self.cards_wrap, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.vsb.grid(row=0, column=1, sticky="ns")
        self.inner = tk.Frame(self.canvas, bg=p["bg"])
        self.win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.bind_all("<MouseWheel>", self._wheel, add="+")
        self.bind_all("<Button-4>", self._wheel, add="+")
        self.bind_all("<Button-5>", self._wheel, add="+")

        self.info = ttk.Label(self, text="", style="Muted.TLabel")
        self.info.grid(row=2, column=0, sticky="w", pady=(6, 0))
        self._apply_view()

    # ---- view switching ----
    @property
    def cards_mode(self) -> bool:
        return self.view_var.get() == "cards"

    def _apply_view(self) -> None:
        if self.special is not None:
            self.list_card.grid_remove()
            self.panel.grid_remove()
            self.cards_wrap.grid_remove()
            return
        if self.cards_mode:
            self.list_card.grid_remove()
            self.panel.grid_remove()
            self.cards_wrap.grid(row=1, column=0, columnspan=2, sticky="nsew")
        else:
            self.cards_wrap.grid_remove()
            self.list_card.grid(row=1, column=0, sticky="nsew")
            self.panel.grid(row=1, column=1, rowspan=2, sticky="ns", padx=(12, 0))

    def _view_changed(self) -> None:
        self.app.cfg["view"] = self.view_var.get()
        config.save(self.app.cfg)
        self._apply_view()
        self.refresh()

    def _filter_changed(self) -> None:
        self.card_limit = self.PAGE
        self.refresh()

    # ---- data ----
    def load_profile(self, reset: bool = False) -> None:
        app = self.app
        self.leaves = []
        if reset:
            self.card_limit = self.PAGE
        if app.root_data is None or app.current_slot is None:
            self.refresh()
            return
        profile = app.root_data[app.current_slot]
        for path, _v in core.iter_leaves(profile):
            if path in TECH_PATHS or not path:
                continue
            name = knowledge.label(path) or core.humanize(path[-1])
            section = " › ".join(knowledge.label(path[:i + 1]) or core.humanize(x)
                                 for i, x in enumerate(path[:-1]) if x != "progress_data")
            if not section and path[0] != "progress_data":
                section = tr("section_profile")
            self.leaves.append((path, name, section, sec.classify(path)))
        self.cat_counts = {}
        for _p, _n, _s, cat in self.leaves:
            self.cat_counts[cat] = self.cat_counts.get(cat, 0) + 1
        self.refresh()

    def _on_search(self, *_a) -> None:
        if self._job:
            self.after_cancel(self._job)
        self.card_limit = self.PAGE
        self._job = self.after(180, self.refresh)

    def _sort_by(self, col: str) -> None:
        self.sort_rev = (not self.sort_rev) if self.sort_col == col else False
        self.sort_col = col
        self.refresh()

    def _filtered_rows(self) -> list[tuple]:
        app = self.app
        profile = app.root_data[app.current_slot]
        changed = app.changed_paths(app.current_slot)
        words = self.search_var.get().strip().casefold().split()
        flt = self.filter_var.get()
        rows = []
        for path, name, section, cat in self.leaves:
            if self.category != "all" and cat != self.category:
                continue
            try:
                v = core.get_at(profile, path)
            except (KeyError, IndexError):
                continue
            k = core.kind_of(v)
            if flt == "number" and k != "number":
                continue
            if flt == "bool" and k != "bool":
                continue
            if flt == "text" and k not in ("text", "null"):
                continue
            if flt == "changed" and path not in changed:
                continue
            if words:
                hay = f"{name} {section} {core.path_str(path)} {display_value(v)} {v}".casefold()
                if not all(w in hay for w in words):
                    continue
            rows.append((path, name, section, v, k))
        return rows

    # ---- sections (inventory / events get a dedicated view) ----
    def _bar_mode(self, kind: str | None) -> None:
        """Dedicated views hide the filter chips / view switch (and the whole bar for events)."""
        if kind and kind not in SEARCH_KINDS:
            self.top.grid_remove()
            return
        self.top.grid()
        if kind in SEARCH_KINDS:
            self.chips.pack_forget()
            self.viewbar.pack_forget()
        else:
            if not self.chips.winfo_manager():
                self.chips.pack(side="left")
            if not self.viewbar.winfo_manager():
                self.viewbar.pack(side="right")

    def _special_kind(self) -> str | None:
        if self.category in SPECIAL and self.category not in self.special_off:
            return self.category
        return None

    def set_category(self, cat: str) -> None:
        self.category = cat
        self.card_limit = self.PAGE
        self.panel.show([])
        self.refresh()

    def set_special(self, on: bool) -> None:
        if on:
            self.special_off.discard(self.category)
        else:
            self.special_off.add(self.category)
        self.refresh()

    def _show_special(self, kind: str) -> None:
        if self.special is None or self.special_kind != kind:
            if self.special is not None:
                self.special.destroy()
            cls = SPECIAL[kind]
            self.special = cls(self, self.app, self)
            self.special_kind = kind
        self.special.grid(row=1, column=0, columnspan=2, sticky="nsew")
        self._apply_view()
        self._bar_mode(kind)
        self.special.rebuild()
        self.info.configure(text="")
        self.smart_btn.pack_forget()

    def _hide_special(self) -> None:
        if self.special is not None:
            self.special.destroy()
            self.special = None
            self.special_kind = None
        self._apply_view()
        self._bar_mode(None)
        if self.category in SPECIAL and self.category in self.special_off:
            self.smart_btn.pack(side="right", padx=6)
        else:
            self.smart_btn.pack_forget()

    def refresh(self) -> None:
        self._job = None
        app = self.app
        if app.root_data is None or app.current_slot is None:
            self._clear_cards()
            self.tree.delete(*self.tree.get_children())
            return
        kind = self._special_kind()
        if kind:
            self._show_special(kind)
            return
        self._hide_special()
        rows = self._filtered_rows()
        if self.cards_mode:
            self._fill_cards(rows)
        else:
            self._fill_list(rows)

    # ---- list view ----
    def _fill_list(self, rows: list[tuple]) -> None:
        app = self.app
        changed = app.changed_paths(app.current_slot)
        prev_sel = [self.row_paths[i] for i in self.tree.selection() if i in self.row_paths]
        self.tree.delete(*self.tree.get_children())
        self.row_paths.clear()
        self.path_iid.clear()
        key = {"name": lambda r: (r[1].casefold(), r[2]),
               "section": lambda r: (r[2].casefold(), r[1].casefold()),
               "value": lambda r: (0, r[3]) if r[4] == "number" else (1, display_value(r[3]).casefold())}[self.sort_col]
        if self.sort_col != "section" or self.sort_rev:
            try:
                rows.sort(key=key, reverse=self.sort_rev)
            except TypeError:
                pass
        total = len(rows)
        for i, (path, name, section, v, _k) in enumerate(rows[:MAX_ROWS]):
            tags = ("changed",) if path in changed else (("odd",) if i % 2 else ())
            iid = str(i)
            self.tree.insert("", "end", iid=iid, values=(name, display_value(v), section), tags=tags)
            self.row_paths[iid] = path
            self.path_iid[path] = iid
        if total > MAX_ROWS:
            self.info.configure(text=tr("rows_capped", shown=MAX_ROWS, total=total))
        else:
            self.info.configure(text=tr("rows_shown", n=total, all=len(self.leaves)))
        keep = [self.path_iid[p] for p in prev_sel if p in self.path_iid]
        if keep:
            self.tree.selection_set(keep)
            self.tree.see(keep[0])
        else:
            self.panel.show([])

    # ---- cards view ----
    def _clear_cards(self) -> None:
        for w in self.inner.winfo_children():
            w.destroy()
        self.cards.clear()
        self._sections = []
        self._extra = []

    def _fill_cards(self, rows: list[tuple]) -> None:
        p = self.app.pal
        frac = self.canvas.yview()[0]
        self._clear_cards()
        shown = rows[:self.card_limit]
        groups: dict[str, list[tuple]] = {}
        for r in shown:
            groups.setdefault(r[2], []).append(r)
        for section, items in groups.items():
            head = tk.Label(self.inner, text=section or tr("section_general"), bg=p["bg"], fg=p["muted"],
                            font="SSEBold", anchor="w")
            cards = []
            for path, name, sec, v, _k in items:
                card = ValueCard(self.inner, self, path, name, "", v, hint=knowledge.hint_for(path))
                self.cards[path] = card
                cards.append(card)
            self._sections.append((head, cards))
        if len(rows) > len(shown):
            more = ttk.Button(self.inner, text=tr("card_more", n=len(rows) - len(shown)),
                              command=self._more, style="Tool.TButton")
            self._extra.append(more)
        if not rows:
            self._extra.append(tk.Label(self.inner, text=tr("cards_empty"), bg=p["bg"], fg=p["muted"],
                                        wraplength=520, pady=40))
        self.info.configure(text=tr("rows_shown", n=min(len(rows), self.card_limit), all=len(rows))
                            if len(rows) > self.card_limit else tr("rows_shown", n=len(rows), all=len(self.leaves)))
        self._layout_cards()
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(frac)

    def _more(self) -> None:
        self.card_limit += self.PAGE
        self.refresh()

    def _layout_cards(self) -> None:
        width = max(self.canvas.winfo_width(), 320)
        ncols = max(1, (width - 12) // self.CARD_W)
        self._ncols = ncols
        for c in range(max(self._maxcols, ncols)):
            self.inner.columnconfigure(c, weight=1 if c < ncols else 0, uniform="card" if c < ncols else "")
        self._maxcols = max(self._maxcols, ncols)
        row = 0
        for head, cards in self._sections:
            head.grid(row=row, column=0, columnspan=ncols, sticky="ew", padx=6, pady=(14, 2))
            row += 1
            for i, card in enumerate(cards):
                card.grid(row=row + i // ncols, column=i % ncols, sticky="nsew", padx=5, pady=5)
            row += (len(cards) + ncols - 1) // ncols
        for w in self._extra:
            w.grid(row=row, column=0, columnspan=ncols, pady=16)
            row += 1

    def _on_canvas_resize(self, event) -> None:
        self.canvas.itemconfigure(self.win, width=event.width)
        if max(1, (max(event.width, 320) - 12) // self.CARD_W) != self._ncols:
            self._layout_cards()

    def _wheel(self, event) -> None:
        try:
            if not self.cards_wrap.winfo_viewable():
                return
            w = self.winfo_containing(event.x_root, event.y_root)
        except (tk.TclError, KeyError):
            return
        if w is None or not str(w).startswith(str(self.cards_wrap)):
            return
        if getattr(event, "num", 0) == 4:
            units = -3
        elif getattr(event, "num", 0) == 5:
            units = 3
        else:
            units = -int(event.delta / 120) * 3 if abs(event.delta) >= 120 else -event.delta * 3
        self.canvas.yview_scroll(units, "units")

    # ---- shared ----
    def update_rows(self, paths: list[tuple]) -> None:
        """Refresh only the rows/cards that changed (keeps scroll position and selection)."""
        app = self.app
        profile = app.root_data[app.current_slot]
        changed = app.changed_paths(app.current_slot)
        if self.special is not None:
            self.special.update_values(paths)
        for path in paths:
            card = self.cards.get(path)
            if card is not None:
                card.refresh()
            iid = self.path_iid.get(path)
            if iid is None:
                continue
            try:
                v = core.get_at(profile, path)
            except (KeyError, IndexError):
                continue
            vals = list(self.tree.item(iid, "values"))
            vals[1] = display_value(v)
            tags = ("changed",) if path in changed else (("odd",) if int(iid) % 2 else ())
            self.tree.item(iid, values=vals, tags=tags)

    def _on_select(self, _e=None) -> None:
        paths = [self.row_paths[i] for i in self.tree.selection() if i in self.row_paths]
        self.panel.show(paths)

    def select_path(self, path: tuple) -> None:
        self.search_var.set("")
        self.filter_var.set("all")
        self.refresh()
        iid = self.path_iid.get(path)
        if iid:
            self.tree.selection_set(iid)
            self.tree.see(iid)


# --------------------------------------------------------------------------
# Simple tab = section sidebar + content
# --------------------------------------------------------------------------
class SimpleTab(ttk.Frame):
    """Left: sections (Inventory, Events, Player ...). Right: cards / list / dedicated view."""

    CAT_ICONS = {"all": "☰", "inventory": "▣", "events": "★", "player": "☺", "resources": "$", "quests": "⚑",
                 "progress": "✔", "locations": "⌂", "cosmetics": "✦", "time": "◷", "other": "…"}

    def __init__(self, parent, app: "App"):
        super().__init__(parent)
        self.app = app
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        side = ttk.Frame(self, style="Card.TFrame", padding=8)
        side.grid(row=0, column=0, sticky="ns", padx=(0, 10), pady=(10, 0))
        ttk.Label(side, text=tr("sections_title"), style="CardMuted.TLabel").pack(anchor="w", padx=6, pady=(2, 6))
        self.cat_var = tk.StringVar(value="all")
        self.cat_order = ["all"] + sec.UI_ORDER
        self.cat_buttons: dict[str, ttk.Radiobutton] = {}
        for cid in self.cat_order:
            self.cat_buttons[cid] = ttk.Radiobutton(side, text="", value=cid, variable=self.cat_var,
                                                    style="Cat.TRadiobutton", command=self._cat_changed)
        self.content = ContentTab(self, app)
        self.content.grid(row=0, column=1, sticky="nsew")
        self._update_sidebar()

    def __getattr__(self, name: str):
        content = self.__dict__.get("content")
        if content is None:
            raise AttributeError(name)
        return getattr(content, name)

    def load_profile(self, reset: bool = False) -> None:
        self.content.load_profile(reset)
        counts = self.content.cat_counts
        cat = self.cat_var.get()
        if cat != "all" and cat not in PRIMARY and not counts.get(cat):
            self.cat_var.set("all")
            self.content.category = "all"
            self.content.refresh()
        self._update_sidebar()

    def _cat_changed(self) -> None:
        self.content.set_category(self.cat_var.get())

    def _update_sidebar(self) -> None:
        counts = self.content.cat_counts
        total = sum(counts.values())
        for cid in self.cat_order:
            rb = self.cat_buttons[cid]
            rb.pack_forget()
            n = total if cid == "all" else counts.get(cid, 0)
            if cid != "all" and n == 0 and cid not in PRIMARY:
                continue
            rb.configure(text=f"{self.CAT_ICONS[cid]}   {tr('cat_' + cid)}   ({n})")
            rb.pack(fill="x", pady=1)


# --------------------------------------------------------------------------
# Home tab: what do you want to change?
# --------------------------------------------------------------------------
class HomeTab(ttk.Frame):
    TILES = [("inventory", "▣", "#0e8f9e"), ("resources", "$", "#d99a00"), ("cosmetics", "✦", "#a855f7"),
             ("player", "☺", "#3b6cf6"), ("quests", "⚑", "#c2571a"), ("events", "★", "#d64545"),
             ("progress", "✔", "#1f9d57"), ("locations", "⌂", "#3b6cf6"), ("catalog", "⌕", "#7a5cf0")]

    def __init__(self, parent, app: "App"):
        super().__init__(parent, padding=(10, 14))
        self.app = app
        self.counts: dict[str, ttk.Label] = {}
        ttk.Label(self, text=tr("home_title"), style="Title.TLabel").pack(anchor="w")
        self.profile_lbl = ttk.Label(self, text="", style="Muted.TLabel")
        self.profile_lbl.pack(anchor="w", pady=(0, 12))
        grid = ttk.Frame(self)
        grid.pack(fill="x", anchor="n")
        for i, (cid, icon, color) in enumerate(self.TILES):
            tile = self._tile(grid, cid, icon, color)
            tile.grid(row=i // 3, column=i % 3, padx=6, pady=6, sticky="nsew")
            grid.columnconfigure(i % 3, weight=1, uniform="tile")
        ttk.Label(self, text=tr("home_tip"), style="Muted.TLabel", wraplength=900, justify="left"
                  ).pack(anchor="w", pady=(12, 0))

    def _tile(self, parent, cid: str, icon: str, color: str) -> tk.Frame:
        pal = self.app.pal
        tile = tk.Frame(parent, bg=pal["card"], highlightthickness=1, highlightbackground=pal["border"],
                        padx=14, pady=10, cursor="hand2")
        cv = tk.Canvas(tile, width=52, height=52, bg=pal["card"], highlightthickness=0, cursor="hand2")
        cv.create_oval(2, 2, 50, 50, fill=color, outline="")
        cv.create_text(26, 26, text=icon, fill="#ffffff", font="SSEIcon")
        cv.pack(side="left", anchor="n")
        box = tk.Frame(tile, bg=pal["card"], cursor="hand2")
        box.pack(side="left", fill="x", expand=True, padx=(12, 0))
        title = tr("catalog_tile") if cid == "catalog" else tr("cat_" + cid)
        tk.Label(box, text=title, bg=pal["card"], fg=pal["text"], font="SSEBold", anchor="w").pack(anchor="w")
        tk.Label(box, text=tr("home_" + cid), bg=pal["card"], fg=pal["muted"], anchor="w", justify="left",
                 wraplength=250).pack(anchor="w")
        cnt = tk.Label(box, text="", bg=pal["card"], fg=pal["accent"], font="SSESmall", anchor="w")
        cnt.pack(anchor="w", pady=(4, 0))
        self.counts[cid] = cnt
        for w in [tile, cv, box] + list(box.winfo_children()):
            w.bind("<Button-1>", lambda _e, c=cid: self.app.goto(c))
        return tile

    def refresh(self) -> None:
        app = self.app
        if app.root_data is None or app.current_slot is None:
            return
        p = app.root_data[app.current_slot]
        name = (p.get("player_name") or tr("no_name")) if isinstance(p, dict) else ""
        try:
            lvl = core.get_at(p, ("progress_data", "xp", "currentLevel"))
        except (KeyError, IndexError, TypeError):
            lvl = None
        self.profile_lbl.configure(text=tr("home_profile", name=name) + (f" · {tr('level_short', n=lvl)}" if lvl is not None else ""))
        counts = app.simple.content.cat_counts
        for cid, lbl in self.counts.items():
            if cid == "catalog":
                lbl.configure(text=tr("catalog_count_short", n=len(catalog.ITEMS)))
            else:
                lbl.configure(text=tr("home_count", n=counts.get(cid, 0)))


# --------------------------------------------------------------------------
# Tree tab
# --------------------------------------------------------------------------
class TreeTab(ttk.Frame):
    def __init__(self, parent, app: "App"):
        super().__init__(parent, padding=(0, 10, 0, 0))
        self.app = app
        self.node_paths: dict[str, tuple] = {}
        self.path_nodes: dict[tuple, str] = {}
        self.pending: set[str] = set()
        self.matches: list[tuple] = []
        self.match_pos = -1
        self.last_query = ""
        self._counter = 0

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        top = ttk.Frame(self)
        top.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        self.search_var = tk.StringVar()
        e = ttk.Entry(top, textvariable=self.search_var, font="SSEEntry")
        e.pack(side="left", fill="x", expand=True, ipady=3)
        e.bind("<Return>", lambda _e: self.find_next())
        ttk.Button(top, text=tr("find_next"), command=self.find_next).pack(side="left", padx=(8, 0))
        ttk.Button(top, text=tr("collapse_all"), command=self.collapse_all).pack(side="left", padx=(8, 0))
        self.search_entry = e

        card = ttk.Frame(self, style="Card.TFrame")
        card.grid(row=1, column=0, sticky="nsew")
        card.rowconfigure(0, weight=1)
        card.columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(card, columns=("value", "type"), show="tree headings", selectmode="browse")
        self.tree.heading("#0", text=tr("col_field"))
        self.tree.heading("value", text=tr("col_value"))
        self.tree.heading("type", text=tr("col_type"))
        self.tree.column("#0", width=280, minwidth=160)
        self.tree.column("value", width=280, minwidth=120)
        self.tree.column("type", width=90, minwidth=70, anchor="center")
        ys = ttk.Scrollbar(card, orient="vertical", command=self.tree.yview)
        xs = ttk.Scrollbar(card, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=ys.set, xscrollcommand=xs.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        ys.grid(row=0, column=1, sticky="ns")
        xs.grid(row=1, column=0, sticky="ew")
        p = app.pal
        self.tree.tag_configure("changed", background=p["changed"])
        self.tree.bind("<<TreeviewOpen>>", self._on_open)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", self._on_double)
        self.tree.bind("<Delete>", lambda _e: self._delete_selected())
        self.tree.bind("<Button-3>", self._context)
        self.tree.bind("<Button-2>", self._context)
        self.menu = tk.Menu(self, tearoff=0)
        self.panel = EditPanel(self, app, "tree")
        self.panel.grid(row=1, column=1, rowspan=2, sticky="ns", padx=(12, 0))

    # ---- rendering ----
    def render(self, keep_state: bool = False) -> None:
        open_paths: list[tuple] = []
        sel: tuple | None = None
        if keep_state:
            open_paths = [self.node_paths[i] for i in self.node_paths if self.tree.exists(i)
                          and self.tree.item(i, "open")]
            s = self.tree.selection()
            sel = self.node_paths.get(s[0]) if s else None
        self.tree.delete(*self.tree.get_children())
        self.node_paths.clear()
        self.path_nodes.clear()
        self.pending.clear()
        self.matches, self.match_pos, self.last_query = [], -1, ""
        app = self.app
        if app.root_data is None or app.current_slot is None:
            return
        profile = app.root_data[app.current_slot]
        root_iid = self._insert("", (), tr("whole_profile"), profile, root=True)
        self.tree.item(root_iid, open=True)
        self._populate(root_iid)
        if keep_state:
            for p in sorted(open_paths, key=len):
                iid = self.path_nodes.get(p)
                if iid:
                    self.tree.item(iid, open=True)
                    self._populate(iid)
            if sel is not None and sel in self.path_nodes:
                self.tree.selection_set(self.path_nodes[sel])
                self.tree.see(self.path_nodes[sel])
        else:
            self.panel.show([])

    def _insert(self, parent: str, path: tuple, label: str, value: Any, root: bool = False) -> str:
        self._counter += 1
        iid = f"n{self._counter}"
        changed = self.app.changed_paths(self.app.current_slot)
        tags = ("changed",) if path in changed else ()
        self.tree.insert(parent, "end", iid=iid, text=label, tags=tags,
                         values=(display_value(value), kind_label(value) if not root else tr("kind_profile")))
        self.node_paths[iid] = path
        self.path_nodes[path] = iid
        if isinstance(value, (dict, list)) and len(value) > 0:
            self.tree.insert(iid, "end", iid=f"{iid}_dummy", text="…")
            self.pending.add(iid)
        return iid

    def _populate(self, iid: str) -> None:
        if iid not in self.pending:
            return
        self.pending.discard(iid)
        self.tree.delete(f"{iid}_dummy")
        path = self.node_paths[iid]
        value = core.get_at(self.app.root_data[self.app.current_slot], path)
        if isinstance(value, dict):
            for k, v in value.items():
                self._insert(iid, path + (k,), str(k), v)
        elif isinstance(value, list):
            for i, v in enumerate(value):
                self._insert(iid, path + (i,), f"[{i}]", v)

    def _on_open(self, _e=None) -> None:
        iid = self.tree.focus()
        if iid:
            self._populate(iid)

    def collapse_all(self) -> None:
        for iid in self.tree.get_children():
            for ch in self.tree.get_children(iid):
                self.tree.item(ch, open=False)

    def reveal(self, path: tuple) -> str | None:
        root = self.path_nodes.get(())
        if root is None:
            return None
        self.tree.item(root, open=True)
        self._populate(root)
        for i in range(1, len(path) + 1):
            iid = self.path_nodes.get(path[:i])
            if iid is None:
                return None
            if i < len(path):
                self.tree.item(iid, open=True)
                self._populate(iid)
        iid = self.path_nodes.get(path)
        if iid:
            self.tree.selection_set(iid)
            self.tree.focus(iid)
            self.tree.see(iid)
        return iid

    def update_nodes(self, paths: list[tuple]) -> None:
        app = self.app
        profile = app.root_data[app.current_slot]
        changed = app.changed_paths(app.current_slot)
        for path in paths:
            iid = self.path_nodes.get(path)
            if not iid or not self.tree.exists(iid):
                continue
            try:
                v = core.get_at(profile, path)
            except (KeyError, IndexError):
                continue
            self.tree.item(iid, values=(display_value(v), kind_label(v)),
                           tags=("changed",) if path in changed else ())

    # ---- interaction ----
    def _selected_path(self) -> tuple | None:
        s = self.tree.selection()
        return self.node_paths.get(s[0]) if s else None

    def _on_select(self, _e=None) -> None:
        p = self._selected_path()
        self.panel.show([] if p is None else [p])

    def _on_double(self, event) -> None:
        iid = self.tree.identify_row(event.y)
        if not iid:
            return
        path = self.node_paths.get(iid)
        value = core.get_at(self.app.root_data[self.app.current_slot], path)
        if core.is_leaf(value):
            self.panel.focus_entry()

    def _delete_selected(self) -> None:
        p = self._selected_path()
        if p:
            self.app.delete_path(p)

    def _context(self, event) -> None:
        iid = self.tree.identify_row(event.y)
        if not iid:
            return
        self.tree.selection_set(iid)
        path = self.node_paths[iid]
        value = core.get_at(self.app.root_data[self.app.current_slot], path)
        self.menu.delete(0, "end")
        if core.is_leaf(value):
            self.menu.add_command(label=tr("advanced_edit"), command=lambda: self.panel._advanced(path, value))
        else:
            self.menu.add_command(label=tr("add_field") if isinstance(value, dict) else tr("add_item"),
                                  command=lambda: self.app.add_child(path))
            self.menu.add_command(label=tr("edit_as_json"), command=lambda: self.panel._json_edit(path, value))
        self.menu.add_command(label=tr("copy_path"), command=lambda: self._copy(core.path_str(path)))
        if path:
            self.menu.add_separator()
            self.menu.add_command(label=tr("delete"), command=lambda: self.app.delete_path(path))
        self.menu.tk_popup(event.x_root, event.y_root)

    def _copy(self, text: str) -> None:
        self.clipboard_clear()
        self.clipboard_append(text)
        self.app.say(tr("copied"))

    def find_next(self) -> None:
        app = self.app
        if app.root_data is None:
            return
        query = self.search_var.get().strip().casefold()
        if not query:
            return
        if query != self.last_query or not self.matches or self.match_pos >= len(self.matches) - 1:
            matches: list[tuple] = []
            self.last_query = query

            def walk(value: Any, path: tuple) -> None:
                if len(matches) >= 10000:
                    return
                if isinstance(value, dict):
                    for k, ch in value.items():
                        cp = path + (k,)
                        if query in str(k).casefold() or query in core.humanize(k).casefold():
                            matches.append(cp)
                        walk(ch, cp)
                elif isinstance(value, list):
                    for i, ch in enumerate(value):
                        walk(ch, path + (i,))
                elif query in str(value).casefold():
                    matches.append(path)

            walk(app.root_data[app.current_slot], ())
            self.matches = list(dict.fromkeys(matches))
            self.match_pos = -1
        if not self.matches:
            app.say(tr("nothing_found", q=query))
            return
        self.match_pos = (self.match_pos + 1) % len(self.matches)
        path = self.matches[self.match_pos]
        self.reveal(path)
        app.say(tr("match_n", pos=self.match_pos + 1, n=len(self.matches), path=core.path_str(path)))


# --------------------------------------------------------------------------
# Changes tab
# --------------------------------------------------------------------------
class ChangesTab(ttk.Frame):
    def __init__(self, parent, app: "App"):
        super().__init__(parent, padding=(0, 10, 0, 0))
        self.app = app
        self.entries: dict[str, tuple] = {}
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        ttk.Label(self, text=tr("changes_intro"), style="Muted.TLabel", wraplength=900, justify="left"
                  ).grid(row=0, column=0, sticky="w", pady=(0, 8))
        card = ttk.Frame(self, style="Card.TFrame")
        card.grid(row=1, column=0, sticky="nsew")
        card.rowconfigure(0, weight=1)
        card.columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(card, columns=("what", "type", "old", "new"), show="headings", selectmode="extended")
        for col, w in (("what", 320), ("type", 100), ("old", 200), ("new", 200)):
            self.tree.heading(col, text=tr("chg_" + col))
            self.tree.column(col, width=w, minwidth=80, anchor="w")
        ys = ttk.Scrollbar(card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=ys.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        ys.grid(row=0, column=1, sticky="ns")
        p = app.pal
        self.tree.tag_configure("changed", foreground=p["warn"])
        self.tree.tag_configure("added", foreground=p["ok"])
        self.tree.tag_configure("removed", foreground=p["danger"])
        self.empty = ttk.Label(card, text=tr("no_changes"), style="CardMuted.TLabel")
        bar = ttk.Frame(self)
        bar.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        ttk.Button(bar, text=tr("revert_selected"), command=self.revert_selected).pack(side="left")
        ttk.Button(bar, text=tr("revert_all"), style="Danger.TButton", command=app.revert_all).pack(side="left", padx=8)

    def refresh(self) -> None:
        self.tree.delete(*self.tree.get_children())
        self.entries.clear()
        app = self.app
        diffs = app.diffs(app.current_slot) if app.root_data else []
        if not diffs:
            self.empty.place(relx=0.5, rely=0.4, anchor="center")
            return
        self.empty.place_forget()
        for i, (typ, path, old, new) in enumerate(diffs[:2000]):
            iid = str(i)
            self.tree.insert("", "end", iid=iid, tags=(typ,), values=(
                friendly_path(path), tr("chg_type_" + typ),
                display_value(old) if typ != "added" else "—",
                display_value(new) if typ != "removed" else "—"))
            self.entries[iid] = (typ, path, old, new)

    def revert_selected(self) -> None:
        app = self.app
        sel = [self.entries[i] for i in self.tree.selection() if i in self.entries]
        if not sel:
            messagebox.showinfo(tr("revert_selected"), tr("select_first"), parent=app)
            return
        skipped = 0
        group = app.history.new_group()
        for typ, path, old, _new in reversed(sel):
            try:
                if typ == "changed":
                    app.history.set_value(app.current_slot, path, old, group=group)
                elif typ == "added":
                    app.history.delete_item(app.current_slot, path)
                else:
                    skipped += 1
            except (KeyError, IndexError):
                skipped += 1
        app.after_structural_edit()
        if skipped:
            messagebox.showinfo(tr("revert_selected"), tr("revert_removed_hint"), parent=app)


# --------------------------------------------------------------------------
# Main application
# --------------------------------------------------------------------------
class App(tk.Tk):
    def __init__(self, initial_path: str | None = None):
        super().__init__()
        self.cfg = config.load()
        set_language(self.cfg["lang"])
        self.pal = theme.apply(self, self.cfg["theme"])
        self.geometry("1240x800")
        self.minsize(1000, 640)

        self.file_path: Path | None = None
        self.root_data: dict | None = None
        self.slots: list[str] = []
        self.original: dict[str, Any] = {}
        self.history = core.History({})
        self.current_slot: str | None = None
        self._diff_cache: dict[str, list] = {}
        self._changed_cache: dict[str, set] = {}
        self.confirmed_save = False
        self.status_var = tk.StringVar()
        self.dirty_var = tk.StringVar()

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self._build()
        self._bind_keys()
        if initial_path and Path(initial_path).exists():
            self.after(100, lambda: self.open_path(Path(initial_path)))

    # ------------------------------------------------------------------ UI
    def _build(self) -> None:
        for w in self.winfo_children():
            w.destroy()
        self.title(tr("app_title") + f"  {__version__}")
        self._build_header()
        self.status_bar = ttk.Frame(self, style="Soft.TFrame")
        self.status_bar.pack(side="bottom", fill="x")
        ttk.Label(self.status_bar, textvariable=self.status_var, style="Status.TLabel").pack(side="left", fill="x",
                                                                                              expand=True)
        self.dirty_label = ttk.Label(self.status_bar, textvariable=self.dirty_var, style="Status.TLabel")
        self.dirty_label.pack(side="right")
        self.container = ttk.Frame(self, padding=(18, 4, 18, 12))
        self.container.pack(fill="both", expand=True)
        self._build_welcome()
        self._build_editor()
        if self.root_data is None:
            self.show_welcome()
        else:
            self.show_editor()
            self._fill_profiles(keep=self.current_slot)
        self._update_state()

    def _build_header(self) -> None:
        bar = ttk.Frame(self, padding=(18, 12, 18, 4))
        bar.pack(side="top", fill="x")
        ttk.Label(bar, text="Stone Story RPG", style="Title.TLabel").pack(side="left")
        ttk.Label(bar, text="  " + tr("header_sub"), style="Muted.TLabel").pack(side="left", pady=(10, 0))
        right = ttk.Frame(bar)
        right.pack(side="right")
        b = ttk.Button(right, text=tr("help_btn"), style="Tool.TButton", command=self.show_help)
        b.pack(side="left", padx=3)
        Tooltip(b, tr("tip_help"), self.pal)
        b = ttk.Button(right, text="☾" if self.cfg["theme"] == "light" else "☀", width=3, style="Tool.TButton",
                       command=self.toggle_theme)
        b.pack(side="left", padx=3)
        Tooltip(b, tr("tip_theme"), self.pal)
        b = ttk.Button(right, text="EN" if current_language() == "ru" else "RU", width=4, style="Tool.TButton",
                       command=self.toggle_language)
        b.pack(side="left", padx=3)
        Tooltip(b, tr("tip_language"), self.pal)

    # ---- welcome ----
    def _build_welcome(self) -> None:
        self.welcome = ttk.Frame(self.container)
        outer = ttk.Frame(self.welcome)
        outer.place(relx=0.5, rely=0.46, anchor="center")
        ttk.Label(outer, text=tr("welcome_title"), style="Title.TLabel", font="SSEHero"
                  ).pack(pady=(0, 6))
        ttk.Label(outer, text=tr("welcome_sub"), style="Muted.TLabel", wraplength=720, justify="center",
                  font="SSEEntry").pack(pady=(0, 22))
        steps = ttk.Frame(outer)
        steps.pack(pady=(0, 24))
        for i, key in enumerate(("step1", "step2", "step3"), start=1):
            card = ttk.Frame(steps, style="Card.TFrame", padding=16)
            card.grid(row=0, column=i - 1, padx=8, sticky="nsew")
            ttk.Label(card, text=str(i), style="Step.TLabel", width=3).pack(anchor="w")
            ttk.Label(card, text=tr(key + "_title"), style="H2.TLabel").pack(anchor="w", pady=(10, 2))
            ttk.Label(card, text=tr(key + "_text"), style="CardMuted.TLabel", wraplength=210,
                      justify="left").pack(anchor="w")
        btns = ttk.Frame(outer)
        btns.pack()
        ttk.Button(btns, text=tr("open_save"), style="Big.Accent.TButton", command=self.open_dialog).pack(side="left",
                                                                                                          padx=6)
        ttk.Button(btns, text=tr("find_save"), style="Big.TButton", command=self.find_saves).pack(side="left", padx=6)
        self.recent_frame = ttk.Frame(outer)
        self.recent_frame.pack(pady=(26, 0))
        recent = [p for p in self.cfg.get("recent", []) if Path(p).exists()]
        if recent:
            ttk.Label(self.recent_frame, text=tr("recent_files"), style="Muted.TLabel").pack(anchor="w")
            for p in recent[:5]:
                link = ttk.Button(self.recent_frame, text=p if len(p) < 80 else "…" + p[-78:],
                                  command=lambda p=p: self.open_path(Path(p)))
                link.pack(fill="x", pady=2)
        ttk.Label(outer, text=tr("safe_note"), style="Muted.TLabel", wraplength=720, justify="center"
                  ).pack(pady=(26, 0))

    # ---- editor ----
    def _build_editor(self) -> None:
        self.editor = ttk.Frame(self.container)
        tb = ttk.Frame(self.editor)
        tb.pack(fill="x", pady=(0, 8))
        self.btn_open = self._tool(tb, tr("open"), self.open_dialog, tr("tip_open"))
        self._sep(tb)
        self.btn_undo = self._tool(tb, "↶  " + tr("undo"), self.undo, tr("tip_undo"))
        self.btn_redo = self._tool(tb, "↷  " + tr("redo"), self.redo, tr("tip_redo"))
        self._sep(tb)
        self.btn_save = ttk.Button(tb, text=tr("save"), style="Accent.TButton", command=self.save_current)
        self.btn_save.pack(side="left", padx=(0, 4))
        Tooltip(self.btn_save, tr("tip_save"), self.pal)
        self.btn_saveas = self._tool(tb, tr("save_as"), self.save_as, tr("tip_save_as"))
        self._sep(tb)
        self.btn_restore = self._tool(tb, tr("restore_backup"), self.restore_backup, tr("tip_restore"))
        self.btn_export = self._tool(tb, tr("export_json"), self.export_json, tr("tip_export"))

        pf = ttk.Frame(self.editor, style="Card.TFrame", padding=(14, 10))
        pf.pack(fill="x", pady=(0, 8))
        ttk.Label(pf, text=tr("profile"), style="CardMuted.TLabel").pack(side="left")
        self.profile_var = tk.StringVar()
        self.profile_box = ttk.Combobox(pf, textvariable=self.profile_var, state="readonly", width=42)
        self.profile_box.pack(side="left", padx=10)
        self.profile_box.bind("<<ComboboxSelected>>", lambda _e: self._profile_changed())
        self.profile_info = ttk.Label(pf, text="", style="CardMuted.TLabel")
        self.profile_info.pack(side="left", padx=8)
        self.file_label = ttk.Label(pf, text="", style="CardMuted.TLabel")
        self.file_label.pack(side="right")

        self.nb = ttk.Notebook(self.editor)
        self.nb.pack(fill="both", expand=True)
        self.home = HomeTab(self.nb, self)
        self.simple = SimpleTab(self.nb, self)
        self.catalog_tab = CatalogTab(self.nb, self)
        self.tree_tab = TreeTab(self.nb, self)
        self.changes_tab = ChangesTab(self.nb, self)
        self.nb.add(self.home, text="  " + tr("tab_home") + "  ")
        self.nb.add(self.simple, text="  " + tr("tab_simple") + "  ")
        self.nb.add(self.catalog_tab, text="  " + tr("tab_catalog") + "  ")
        self.nb.add(self.tree_tab, text="  " + tr("tab_tree") + "  ")
        self.nb.add(self.changes_tab, text="  " + tr("tab_changes") + "  ")

    def _tool(self, parent, text, cmd, tip) -> ttk.Button:
        b = ttk.Button(parent, text=text, style="Tool.TButton", command=cmd)
        b.pack(side="left", padx=(0, 4))
        Tooltip(b, tip, self.pal)
        return b

    def _sep(self, parent) -> None:
        ttk.Separator(parent, orient="vertical").pack(side="left", fill="y", padx=8, pady=3)

    def show_welcome(self) -> None:
        self.editor.pack_forget()
        self.welcome.pack(fill="both", expand=True)

    def show_editor(self) -> None:
        self.welcome.pack_forget()
        self.editor.pack(fill="both", expand=True)

    def _bind_keys(self) -> None:
        self.bind_all("<Control-o>", lambda _e: self.open_dialog())
        self.bind_all("<Control-s>", lambda _e: self.save_current())
        self.bind_all("<Control-z>", lambda e: self._shortcut(e, self.undo))
        self.bind_all("<Control-y>", lambda e: self._shortcut(e, self.redo))
        self.bind_all("<Control-f>", lambda _e: self._focus_search())
        self.bind_all("<F1>", lambda _e: self.show_help())

    def _shortcut(self, event, fn: Callable) -> str | None:
        # leave Ctrl+Z / Ctrl+Y alone while typing in a text field
        if isinstance(event.widget, (tk.Text, ttk.Entry, tk.Entry)):
            return None
        fn()
        return "break"

    def _focus_search(self) -> None:
        if self.root_data is None:
            return
        cur = self.nb.nametowidget(self.nb.select())
        if cur is self.simple:
            self.simple.search.focus_set()
        elif cur is self.tree_tab:
            self.tree_tab.search_entry.focus_set()
        elif cur is self.catalog_tab:
            self.catalog_tab.list.entry.focus_set()

    # --------------------------------------------------------- small helpers
    def say(self, text: str) -> None:
        self.status_var.set(text)

    def toggle_theme(self) -> None:
        self.cfg["theme"] = "dark" if self.cfg["theme"] == "light" else "light"
        config.save(self.cfg)
        self.pal = theme.apply(self, self.cfg["theme"])
        self._rebuild()

    def toggle_language(self) -> None:
        self.cfg["lang"] = "en" if current_language() == "ru" else "ru"
        config.save(self.cfg)
        set_language(self.cfg["lang"])
        self._rebuild()

    def _rebuild(self) -> None:
        tab = 0
        try:
            tab = self.nb.index(self.nb.select())
        except Exception:
            pass
        self._build()
        if self.root_data is not None:
            self.nb.select(tab)
        self.say(tr("ready") if self.root_data is None else self.status_var.get())

    # ------------------------------------------------------- change tracking
    def diffs(self, slot: str | None) -> list:
        if slot is None or self.root_data is None:
            return []
        if slot not in self._diff_cache:
            self._diff_cache[slot] = core.diff(self.original[slot], self.root_data[slot])
        return self._diff_cache[slot]

    def changed_paths(self, slot: str | None) -> set:
        if slot is None or self.root_data is None:
            return set()
        if slot not in self._changed_cache:
            paths: set = set()
            for typ, p, _old, new in self.diffs(slot):
                if typ in ("changed", "added"):
                    paths.add(p)
                    if not core.is_leaf(new):
                        paths.update(lp for lp, _v in core.iter_leaves(new, p))
            self._changed_cache[slot] = paths
        return self._changed_cache[slot]

    def original_value(self, path: tuple) -> tuple[bool, Any]:
        try:
            return True, core.get_at(self.original[self.current_slot], path)
        except (KeyError, IndexError, TypeError):
            return False, None

    def total_changes(self) -> int:
        return sum(len(self.diffs(s)) for s in self.slots)

    def _invalidate(self, slot: str | None = None) -> None:
        if slot is None:
            self._diff_cache.clear()
            self._changed_cache.clear()
        else:
            self._diff_cache.pop(slot, None)
            self._changed_cache.pop(slot, None)

    def _update_state(self) -> None:
        loaded = self.root_data is not None
        can = lambda ok: "normal" if ok else "disabled"
        for b in (self.btn_saveas, self.btn_export):
            b.configure(state=can(loaded))
        self.btn_undo.configure(state=can(loaded and bool(self.history.undo_stack)))
        self.btn_redo.configure(state=can(loaded and bool(self.history.redo_stack)))
        self.btn_save.configure(state=can(loaded))
        self.btn_restore.configure(state=can(loaded and self.file_path is not None
                                             and bool(core.list_backups(self.file_path))))
        n = self.total_changes() if loaded else 0
        if loaded:
            self.dirty_var.set(tr("unsaved_n", n=n) if n else tr("all_saved"))
            self.dirty_label.configure(foreground=self.pal["warn"] if n else self.pal["ok"])
            try:
                self.nb.tab(self.changes_tab, text="  " + tr("tab_changes") + (f" ({len(self.diffs(self.current_slot))})"
                                                                 if self.diffs(self.current_slot) else "") + "  ")
            except tk.TclError:
                pass
        else:
            self.dirty_var.set("")
            self.status_var.set(tr("ready"))
        self.file_label.configure(text=str(self.file_path.name) if self.file_path else "")
        if loaded and hasattr(self, "home"):
            self.home.refresh()

    # ------------------------------------------------------------- opening
    def open_dialog(self) -> None:
        name = filedialog.askopenfilename(title=tr("open_title"), parent=self,
                                          filetypes=[(tr("ft_save"), "*.txt"), (tr("ft_all"), "*.*")])
        if name:
            self.open_path(Path(name))

    def find_saves(self) -> None:
        dlg = FinderDialog(self, self.pal)
        self.wait_window(dlg)
        if dlg.result:
            self.open_path(dlg.result)

    def _confirm_discard(self) -> bool:
        if self.root_data is not None and self.total_changes():
            return messagebox.askyesno(tr("unsaved_title"), tr("unsaved_ask"), icon="warning", parent=self)
        return True

    def open_path(self, path: Path) -> None:
        if not self._confirm_discard():
            return
        try:
            data, slots = core.load_save(path)
        except Exception as exc:  # noqa: BLE001 - show any problem to the user
            detail = f"{exc}\n\n{traceback.format_exc(limit=2)}" if not isinstance(exc, (ValueError, RuntimeError)) \
                else str(exc)
            messagebox.showerror(tr("err_open_title"), tr("err_open_text", detail=detail), parent=self)
            return
        self.file_path = Path(path)
        self.root_data = data
        self.slots = slots
        self.original = {s: copy.deepcopy(data[s]) for s in slots}
        self.history = core.History(data)
        self._invalidate()
        self.confirmed_save = False
        config.add_recent(self.cfg, str(path))
        last = f"save_file_{data.get('save_file_last_id', '')}"
        self.current_slot = last if last in slots else slots[0]
        self.show_editor()
        self._fill_profiles(keep=self.current_slot)
        self._reload_views()
        self.nb.select(self.home)
        self.say(tr("opened", name=self.file_path.name, n=len(slots)))
        self._update_state()

    def _fill_profiles(self, keep: str | None = None) -> None:
        if self.root_data is None:
            return
        last = f"save_file_{self.root_data.get('save_file_last_id', '')}"
        choices = []
        for i, slot in enumerate(self.slots, start=1):
            p = self.root_data[slot]
            name = p.get("player_name") or p.get("display_name") or tr("no_name")
            star = "  ★" if slot == last else ""
            choices.append(f"{tr('slot')} {i} — {name}{star}")
        self.profile_box.configure(values=choices)
        idx = self.slots.index(keep) if keep in self.slots else 0
        self.profile_box.current(idx)
        self._update_profile_info()

    def _update_profile_info(self) -> None:
        if self.current_slot is None or self.root_data is None:
            return
        p = self.root_data[self.current_slot]
        self.profile_info.configure(text=tr("profile_info", ver=p.get("version", "?"), slot=self.current_slot))

    def _profile_changed(self) -> None:
        idx = self.profile_box.current()
        if 0 <= idx < len(self.slots):
            self.current_slot = self.slots[idx]
            self._update_profile_info()
            self._reload_views()
            self._update_state()

    def _reload_views(self) -> None:
        self.simple.load_profile(reset=True)
        self.tree_tab.render()
        self.changes_tab.refresh()

    # ------------------------------------------------------------- editing
    @staticmethod
    def coerce_number(old: Any, new: Any) -> Any:
        """Keep integer fields integer (5.0 -> 5) so the game keeps reading them correctly."""
        if isinstance(old, int) and not isinstance(old, bool) and isinstance(new, float):
            return int(round(new))
        return new

    def apply_set(self, paths: list[tuple], fn: Callable[[Any], Any], preview: bool = True,
                  title: str | None = None, note: str = "") -> bool:
        """Change several values at once. Bulk changes (2+ values) show a before/after preview first."""
        if self.root_data is None or self.current_slot is None:
            return False
        slot = self.current_slot
        data = self.root_data[slot]
        planned = []
        for p in paths:
            old = core.get_at(data, p)
            try:
                new = fn(old)
            except Exception as exc:  # noqa: BLE001
                messagebox.showerror(tr("err_bad_value"), str(exc), parent=self)
                return False
            planned.append((p, old, new))
        differing = [(p, o, n) for p, o, n in planned if not (type(o) is type(n) and o == n)]
        if preview and len(differing) > 1:
            rows = [(describe_path(data, p), display_value(o), display_value(n)) for p, o, n in differing]
            dlg = PreviewDialog(self, title or tr("preview_title"), self.pal, rows,
                                unchanged=len(planned) - len(differing), note=note)
            self.wait_window(dlg)
            if not dlg.accepted:
                return False
        big = [n for _p, o, n in planned if isinstance(n, (int, float)) and not isinstance(n, bool)
               and abs(n) >= BIG_INT and not (isinstance(o, (int, float)) and abs(o) >= BIG_INT)]
        if big and not messagebox.askyesno(tr("big_title"), tr("big_text", v=fmt_num(big[0])), icon="warning",
                                           parent=self):
            return
        group = self.history.new_group() if len(planned) > 1 else None
        changed_paths = []
        for p, old, new in planned:
            try:
                if self.history.set_value(slot, p, new, group=group):
                    changed_paths.append(p)
            except Exception as exc:  # noqa: BLE001
                messagebox.showerror(tr("err_bad_value"), str(exc), parent=self)
                return
        if not changed_paths:
            return False
        self._invalidate(slot)
        containers = [p for p in changed_paths if not core.is_leaf(core.get_at(self.root_data[slot], p))]
        if containers:
            self.after_structural_edit()
        else:
            self.simple.update_rows(changed_paths)
            self.tree_tab.update_nodes(changed_paths)
            self.changes_tab.refresh()
            self._refresh_panels()
            self._update_state()
        if len(changed_paths) == 1:
            self.say(tr("changed_one", name=core.humanize(changed_paths[0][-1]),
                        v=display_value(core.get_at(self.root_data[slot], changed_paths[0]))))
        else:
            self.say(tr("changed_many", n=len(changed_paths)))
        return True

    def _refresh_panels(self) -> None:
        self.simple.panel.show(self.simple.panel.paths)
        self.tree_tab.panel.show(self.tree_tab.panel.paths)

    def goto(self, target: str) -> None:
        """Jump from the Home tiles to a section page (or the catalogue)."""
        if target == "catalog":
            self.nb.select(self.catalog_tab)
            return
        self.nb.select(self.simple)
        self.simple.cat_var.set(target)
        self.simple._cat_changed()

    def run_ops(self, fn: Callable, rows: list | None = None, title: str | None = None, note: str = "") -> bool:
        """Run list/record edits as one undo step; bulk edits (2+ rows) show a before/after preview first."""
        if self.root_data is None or self.current_slot is None:
            return False
        if rows is not None and len(rows) > 1:
            dlg = PreviewDialog(self, title or tr("preview_title"), self.pal, rows, note=note)
            self.wait_window(dlg)
            if not dlg.accepted:
                return False
        group = self.history.new_group()
        try:
            changed = fn(self.history, self.current_slot, group)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(tr("err_bad_value"), str(exc), parent=self)
            return False
        if changed:
            self.after_structural_edit()
            self.say(tr("changed_many", n=int(changed)))
        return bool(changed)

    def after_structural_edit(self) -> None:
        slot = self.current_slot
        self._invalidate(slot)
        self.simple.load_profile()
        self.tree_tab.render(keep_state=True)
        self.changes_tab.refresh()
        self._update_state()

    def add_child(self, path: tuple) -> None:
        if self.root_data is None:
            return
        slot = self.current_slot
        target = core.get_at(self.root_data[slot], path)
        if isinstance(target, dict):
            dlg = ValueDialog(self, tr("add_field"), self.pal, "", ask_name=True, hint=tr("add_hint"))
        elif isinstance(target, list):
            dlg = ValueDialog(self, tr("add_item"), self.pal, "", hint=tr("add_hint"))
        else:
            messagebox.showinfo(tr("add_field"), tr("add_pick_container"), parent=self)
            return
        self.wait_window(dlg)
        if not dlg.accepted:
            return
        try:
            new_path = self.history.add_item(slot, path, dlg.name, dlg.result)
        except KeyError:
            messagebox.showerror(tr("err_bad_value"), tr("err_key_exists"), parent=self)
            return
        self.after_structural_edit()
        self.tree_tab.reveal(new_path)
        self.say(tr("added_ok", path=core.path_str(new_path)))

    def delete_path(self, path: tuple) -> None:
        if self.root_data is None or not path:
            return
        slot = self.current_slot
        value = core.get_at(self.root_data[slot], path)
        if not messagebox.askyesno(tr("delete"), tr("delete_ask", name=friendly_path(path), kind=kind_label(value)),
                                   icon="warning", parent=self):
            return
        self.history.delete_item(slot, path)
        self.after_structural_edit()
        self.tree_tab.panel.show([])
        self.say(tr("deleted_ok", path=core.path_str(path)))

    def show_in_tree(self, path: tuple) -> None:
        self.nb.select(self.tree_tab)
        self.tree_tab.reveal(path)

    def undo(self) -> None:
        self._history_step(self.history.undo(), tr("undone"))

    def redo(self) -> None:
        self._history_step(self.history.redo(), tr("redone"))

    def _history_step(self, ops: list, msg: str) -> None:
        if not ops:
            return
        slots = {o.slot for o in ops}
        for s in slots:
            self._invalidate(s)
        if self.current_slot not in slots:
            self.current_slot = ops[0].slot
            self.profile_box.current(self.slots.index(self.current_slot))
            self._update_profile_info()
        self.simple.load_profile()
        self.tree_tab.render(keep_state=True)
        self.changes_tab.refresh()
        self._update_state()
        self.say(msg)

    def revert_all(self) -> None:
        slot = self.current_slot
        if self.root_data is None or not self.diffs(slot):
            return
        if not messagebox.askyesno(tr("revert_all"), tr("revert_all_ask"), icon="warning", parent=self):
            return
        self.root_data[slot] = copy.deepcopy(self.original[slot])
        self.history.undo_stack = [o for o in self.history.undo_stack if o.slot != slot]
        self.history.redo_stack = [o for o in self.history.redo_stack if o.slot != slot]
        self.after_structural_edit()
        self.say(tr("reverted_all"))

    # -------------------------------------------------------------- saving
    def _after_write(self) -> None:
        self.original = {s: copy.deepcopy(self.root_data[s]) for s in self.slots}
        self._invalidate()
        self.simple.load_profile()
        self.tree_tab.render(keep_state=True)
        self.changes_tab.refresh()
        self._update_state()

    def save_current(self) -> None:
        if self.root_data is None:
            return
        if self.file_path is None or not self.file_path.exists():
            self.save_as()
            return
        if not self.confirmed_save:
            if not messagebox.askyesno(tr("save_confirm_title"),
                                       tr("save_confirm_text", name=self.file_path.name), icon="question",
                                       parent=self):
                return
        try:
            backup = core.write_save(self.root_data, self.slots, self.file_path, backup_existing=True)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(tr("err_save_title"), tr("err_save_text", detail=str(exc)), parent=self)
            return
        self.confirmed_save = True
        self._after_write()
        self.say(tr("saved_ok", name=self.file_path.name))
        messagebox.showinfo(tr("saved_title"), tr("saved_text", name=self.file_path.name,
                                                   backup=backup.name if backup else "—"), parent=self)

    def save_as(self) -> None:
        if self.root_data is None:
            return
        default = (self.file_path.stem + "_edited.txt") if self.file_path else "primary_save_edited.txt"
        name = filedialog.asksaveasfilename(title=tr("save_as_title"), defaultextension=".txt", initialfile=default,
                                            initialdir=str(self.file_path.parent) if self.file_path else None,
                                            filetypes=[(tr("ft_save"), "*.txt"), (tr("ft_all"), "*.*")], parent=self)
        if not name:
            return
        dest = Path(name)
        try:
            backup = core.write_save(self.root_data, self.slots, dest, backup_existing=dest.exists())
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(tr("err_save_title"), tr("err_save_text", detail=str(exc)), parent=self)
            return
        self.file_path = dest
        config.add_recent(self.cfg, str(dest))
        self.confirmed_save = True
        self._after_write()
        self.say(tr("saved_ok", name=dest.name))
        messagebox.showinfo(tr("saved_title"), tr("saved_text", name=dest.name, backup=backup.name if backup else "—"),
                            parent=self)

    def restore_backup(self) -> None:
        if self.file_path is None:
            return
        backups = core.list_backups(self.file_path)
        if not backups:
            messagebox.showinfo(tr("restore_backup"), tr("no_backups"), parent=self)
            return
        items = []
        for b in backups:
            st = b.stat()
            when = _dt.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            items.append((f"{when}    ({st.st_size // 1024} KB)    {b.name}", b))
        dlg = PickDialog(self, tr("restore_backup"), tr("restore_pick"), self.pal, items, ok_text=tr("restore"))
        self.wait_window(dlg)
        if not dlg.result:
            return
        if not messagebox.askyesno(tr("restore_backup"), tr("restore_ask", name=dlg.result.name), icon="warning",
                                   parent=self):
            return
        try:
            if self.file_path.exists():
                core.make_backup(self.file_path)
            shutil.copy2(dlg.result, self.file_path)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(tr("err_save_title"), str(exc), parent=self)
            return
        path = self.file_path
        self.original = {s: copy.deepcopy(self.root_data[s]) for s in self.slots}  # avoid discard prompt
        self._invalidate()
        self.open_path(path)
        self.say(tr("restored_ok"))

    def export_json(self) -> None:
        if self.root_data is None:
            return
        name = filedialog.asksaveasfilename(title=tr("export_title"), defaultextension=".json",
                                            initialfile="stone_story_decrypted.json",
                                            filetypes=[("JSON", "*.json")], parent=self)
        if not name:
            return
        data = copy.deepcopy(self.root_data)
        for slot in self.slots:
            if isinstance(data[slot].get("progress_data"), dict):
                data[slot]["encrypted"] = False
        try:
            Path(name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(tr("err_save_title"), str(exc), parent=self)
            return
        self.say(tr("exported_ok", name=name))
        messagebox.showinfo(tr("export_title"), tr("exported_text", name=name), parent=self)

    # ---------------------------------------------------------------- misc
    def show_help(self) -> None:
        TextDialog(self, tr("help_title"), self.pal, help_sections())

    def on_close(self) -> None:
        if self.root_data is not None and self.total_changes():
            if not messagebox.askyesno(tr("unsaved_title"), tr("unsaved_quit"), icon="warning", parent=self):
                return
        self.destroy()


def run(path: str | None = None) -> None:
    if sys.platform.startswith("win"):
        try:  # crisp text on high-DPI screens
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
    App(path).mainloop()
