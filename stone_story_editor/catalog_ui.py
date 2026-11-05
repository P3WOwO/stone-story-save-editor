"""Item catalogue interface: searchable list, details panel and the "add item" wizard."""
from __future__ import annotations

import copy
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from typing import Any, Callable

from . import catalog, core, knowledge, sections
from .cards import guard_range
from .catalog import CatalogItem
from .i18n import tr
from .widgets import BaseDialog

INV_PARENT = ("progress_data", "inventory_data")


def inventory_items(app) -> list[dict] | None:
    """The player's item list (progress_data.inventory_data.itms), or None when the save has none."""
    try:
        node = core.get_at(app.root_data[app.current_slot], sections.INVENTORY_PATH)
    except (KeyError, IndexError, TypeError):
        return None
    return node if isinstance(node, list) else None


# --------------------------------------------------------------------------
class CatalogList(ttk.Frame):
    """Search box + category / type filters + list of catalogue items."""

    ALL = "__all__"

    def __init__(self, parent, app, on_select: Callable[[CatalogItem | None], None],
                 on_activate: Callable[[CatalogItem], None] | None = None):
        super().__init__(parent)
        self.app, self.on_select, self.on_activate = app, on_select, on_activate
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)
        top = ttk.Frame(self)
        top.grid(row=0, column=0, sticky="ew")
        ttk.Label(top, text=tr("search_hint") + ":", style="Muted.TLabel").pack(side="left", padx=(0, 8))
        self.q = tk.StringVar()
        self.q.trace_add("write", lambda *_a: self._refresh_later())
        e = ttk.Entry(top, textvariable=self.q, font="SSEEntry")
        e.pack(side="left", fill="x", expand=True, ipady=3)
        self.entry = e
        ttk.Button(top, text="✕", width=3, command=lambda: self.q.set("")).pack(side="left", padx=(4, 0))
        flt = ttk.Frame(self)
        flt.grid(row=1, column=0, sticky="ew", pady=8)
        self.cat_keys = [self.ALL] + list(catalog.CATEGORIES)
        self.cat_box = ttk.Combobox(flt, state="readonly", width=24,
                                    values=[tr("cat_filter_all")] + [catalog.category_name(c)
                                                                      for c in catalog.CATEGORIES])
        self.cat_box.current(0)
        self.cat_box.pack(side="left")
        self.cat_box.bind("<<ComboboxSelected>>", lambda _e: self._cat_changed())
        self.sub_keys: list[str] = [self.ALL]
        self.sub_box = ttk.Combobox(flt, state="readonly", width=20, values=[tr("type_filter_all")])
        self.sub_box.current(0)
        self.sub_box.pack(side="left", padx=8)
        self.sub_box.bind("<<ComboboxSelected>>", lambda _e: self.refresh())
        self.only_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(flt, text=tr("only_addable"), variable=self.only_var, command=self.refresh).pack(side="left")
        card = ttk.Frame(self, style="Card.TFrame")
        card.grid(row=2, column=0, sticky="nsew")
        card.rowconfigure(0, weight=1)
        card.columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(card, columns=("type", "element", "id"), show="tree headings", selectmode="browse")
        self.tree.heading("#0", text=tr("col_item"))
        self.tree.heading("type", text=tr("col_item_type"))
        self.tree.heading("element", text=tr("col_element"))
        self.tree.heading("id", text="ID")
        self.tree.column("#0", width=210, minwidth=140)
        self.tree.column("type", width=110, minwidth=70)
        self.tree.column("element", width=100, minwidth=60)
        self.tree.column("id", width=130, minwidth=60)
        ys = ttk.Scrollbar(card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=ys.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        ys.grid(row=0, column=1, sticky="ns")
        self.tree.tag_configure("noid", foreground=app.pal["muted"])
        self.tree.bind("<<TreeviewSelect>>", self._selected)
        self.tree.bind("<Double-1>", lambda _e: self._activated())
        self.count = ttk.Label(self, text="", style="Muted.TLabel")
        self.count.grid(row=3, column=0, sticky="w", pady=(6, 0))
        self._job = None
        self.refresh()

    def _cat_changed(self) -> None:
        cat = self.cat_keys[self.cat_box.current()]
        subs = []
        for it in catalog.ITEMS:
            if (cat == self.ALL or it.category == cat) and it.sub not in subs:
                subs.append(it.sub)
        self.sub_keys = [self.ALL] + subs
        self.sub_box.configure(values=[tr("type_filter_all")] + [catalog.sub_name(s) for s in subs])
        self.sub_box.current(0)
        self.refresh()

    def _refresh_later(self) -> None:
        if self._job:
            self.after_cancel(self._job)
        self._job = self.after(150, self.refresh)

    def refresh(self) -> None:
        self._job = None
        cat = self.cat_keys[self.cat_box.current()]
        sub = self.sub_keys[self.sub_box.current()] if self.sub_box.current() >= 0 else self.ALL
        found = catalog.search(self.q.get(), None if cat == self.ALL else cat, None if sub == self.ALL else sub,
                               self.only_var.get())
        self.tree.delete(*self.tree.get_children())
        shown_cat = None
        for it in found:
            if it.category != shown_cat:
                shown_cat = it.category
                self.tree.insert("", "end", iid="cat:" + it.category, text=catalog.category_name(it.category),
                                 open=True, tags=("cat",))
            self.tree.insert("cat:" + it.category, "end", iid=it.key, text=it.name,
                             values=(catalog.sub_name(it.sub), it.tr_text(catalog.ELEMENT_TEXT, it.element),
                                     it.id or "—"), tags=() if it.addable else ("noid",))
        self.count.configure(text=tr("catalog_count", n=len(found), total=len(catalog.ITEMS)))
        self.on_select(None)

    def selected(self) -> CatalogItem | None:
        sel = self.tree.selection()
        return catalog.BY_KEY.get(sel[0]) if sel else None

    def select_key(self, key: str) -> None:
        self.q.set("")
        self.cat_box.current(0)
        self._cat_changed()
        if self.tree.exists(key):
            self.tree.selection_set(key)
            self.tree.see(key)

    def _selected(self, _e=None) -> None:
        self.on_select(self.selected())

    def _activated(self) -> None:
        it = self.selected()
        if it and self.on_activate:
            self.on_activate(it)


# --------------------------------------------------------------------------
class DetailPanel(ttk.Frame):
    """Name, category, type / hand / element (separate characteristics), description, recipe and the ID."""

    def __init__(self, parent, app, on_add: Callable[[CatalogItem], None] | None = None, compact: bool = False):
        super().__init__(parent, style="Card.TFrame", padding=16)
        self.app, self.on_add, self.compact = app, on_add, compact
        self.body = ttk.Frame(self, style="Inner.TFrame")
        self.body.pack(fill="both", expand=True)
        self.show(None)

    def _line(self, label: str, value: str) -> None:
        row = ttk.Frame(self.body, style="Inner.TFrame")
        row.pack(fill="x", pady=1)
        ttk.Label(row, text=label, style="CardMuted.TLabel", width=13).pack(side="left", anchor="n")
        ttk.Label(row, text=value, style="Card.TLabel", wraplength=300, justify="left").pack(side="left", fill="x")

    def show(self, item: CatalogItem | None) -> None:
        for w in self.body.winfo_children():
            w.destroy()
        if item is None:
            ttk.Label(self.body, text=tr("catalog_pick"), style="CardMuted.TLabel", wraplength=340,
                      justify="left").pack(anchor="w")
            return
        ttk.Label(self.body, text=item.name, style="H1.TLabel", wraplength=340, justify="left").pack(anchor="w")
        if item.name_ru and item.name_en != item.name_ru:
            other = item.name_en if self.app_lang_ru() else item.name_ru
            ttk.Label(self.body, text=other, style="CardMuted.TLabel").pack(anchor="w")
        ttk.Label(self.body, text="", style="Card.TLabel").pack()
        self._line(tr("cat_label"), catalog.category_name(item.category))
        self._line(tr("type_label"), catalog.sub_name(item.sub))
        if item.hand:
            self._line(tr("hand_label"), item.tr_text(catalog.HAND_TEXT, item.hand))
        if item.element:
            self._line(tr("element_label"), item.tr_text(catalog.ELEMENT_TEXT, item.element))
        if (item.can_stars or item.can_enchant) and not self.compact:
            self._line(tr("rarity_label"), tr("rarity_text"))
        ttk.Separator(self.body).pack(fill="x", pady=10)
        ttk.Label(self.body, text=item.description or tr("no_description"), style="Card.TLabel", wraplength=340,
                  justify="left").pack(anchor="w")
        if item.recipe and not self.compact:
            ttk.Label(self.body, text=tr("recipe_label") + ": " + item.recipe, style="CardMuted.TLabel",
                      wraplength=340, justify="left").pack(anchor="w", pady=(8, 0))
        ttk.Separator(self.body).pack(fill="x", pady=10)
        if item.id:
            self._line("ID", item.id)
            self._line(tr("id_source"), item.tr_text(catalog.SOURCE_TEXT, item.id_source))
        else:
            ttk.Label(self.body, text=tr("id_unknown"), style="Card.TLabel", wraplength=340, justify="left"
                      ).pack(anchor="w")
        if self.on_add:
            btn = ttk.Button(self.body, text=tr("add_to_inventory"), style="Accent.TButton",
                             command=lambda: self.on_add(item))
            btn.pack(anchor="w", pady=(14, 0))
            if not item.addable or self.app.root_data is None:
                btn.state(["disabled"])

    @staticmethod
    def app_lang_ru() -> bool:
        from .i18n import current_language
        return current_language() == "ru"


# --------------------------------------------------------------------------
class CatalogTab(ttk.Frame):
    """The "Item catalogue" tab: browse everything, open the wizard for the selected item."""

    def __init__(self, parent, app):
        super().__init__(parent, padding=(0, 10, 0, 0))
        self.app = app
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        ttk.Label(self, text=tr("catalog_intro"), style="Muted.TLabel", wraplength=900, justify="left"
                  ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        self.detail = DetailPanel(self, app, on_add=self.open_wizard)
        self.list = CatalogList(self, app, on_select=self.detail.show, on_activate=self.open_wizard)
        self.list.grid(row=1, column=0, sticky="nsew")
        self.detail.grid(row=1, column=1, sticky="ns", padx=(12, 0))
        self.detail.configure(width=400)
        self.detail.grid_propagate(False)

    def open_wizard(self, item: CatalogItem | None = None) -> None:
        if self.app.root_data is None:
            return
        dlg = ItemWizard(self.app, item.key if item else None)
        self.app.wait_window(dlg)

    def refresh_detail(self) -> None:
        self.detail.show(self.list.selected())


class ScrollFrame(ttk.Frame):
    """A frame whose content scrolls vertically (used for the wizard's options)."""

    def __init__(self, parent, pal: dict):
        super().__init__(parent, style="Card.TFrame")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(self, bg=pal["card"], highlightthickness=0)
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vsb.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        self.inner = ttk.Frame(self.canvas, style="Inner.TFrame", padding=14)
        win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(win, width=e.width))
        for ev in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.bind_all(ev, self._wheel, add="+")

    def _wheel(self, event) -> None:
        try:
            w = self.winfo_containing(event.x_root, event.y_root)
        except (tk.TclError, KeyError):
            return
        if w is None or not str(w).startswith(str(self)):
            return
        num = getattr(event, "num", 0)
        units = -3 if num == 4 else 3 if num == 5 else (-int(event.delta / 120) * 3 if abs(event.delta) >= 120
                                                       else -event.delta * 3)
        self.canvas.yview_scroll(units, "units")


# --------------------------------------------------------------------------
class ItemWizard(BaseDialog):
    """Find an item by name, choose amount and characteristics, add it - no JSON, no ids."""

    def __init__(self, app, preselect: str | None = None):
        super().__init__(app, tr("wizard_title"), app.pal, "1120x780")
        self.minsize(900, 600)
        self.app = app
        self.pal = app.pal
        self.item: CatalogItem | None = None
        self.added = 0
        ttk.Label(self, text=tr("wizard_title"), style="Title.TLabel").pack(anchor="w", padx=18, pady=(14, 0))
        ttk.Label(self, text=tr("wizard_intro"), style="Muted.TLabel", wraplength=1000, justify="left"
                  ).pack(anchor="w", padx=18, pady=(0, 8))
        main = ttk.Frame(self)
        main.pack(fill="both", expand=True, padx=18)
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=0)
        main.rowconfigure(0, weight=1)
        right = ttk.Frame(main, width=440)
        right.grid(row=0, column=1, sticky="ns", padx=(12, 0))
        right.grid_propagate(False)
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)
        self.detail = DetailPanel(right, app, compact=True)
        self.detail.grid(row=0, column=0, sticky="ew")
        self.opts_wrap = ScrollFrame(right, app.pal)
        self.opts_wrap.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        self.opts = self.opts_wrap.inner
        self.list = CatalogList(main, app, on_select=self._chosen, on_activate=lambda _i: None)
        self.list.grid(row=0, column=0, sticky="nsew")
        foot = ttk.Frame(self)
        foot.pack(fill="x", padx=18, pady=12)
        self.status = ttk.Label(foot, text="", style="Ok.TLabel")
        self.status.pack(side="left")
        ttk.Button(foot, text=tr("close"), command=self.destroy).pack(side="right")
        ttk.Button(foot, text=tr("add_by_id"), command=self._add_by_id).pack(side="right", padx=8)
        self.add_btn = ttk.Button(foot, text="+  " + tr("add_btn"), style="Accent.TButton", command=self._add)
        self.add_btn.pack(side="right")
        self.add_btn.state(["disabled"])
        self._build_options(None)
        if preselect:
            self.list.select_key(preselect)
        self.present()
        self.list.entry.focus_set()

    # ---- selection ----
    def _chosen(self, item: CatalogItem | None) -> None:
        self.item = item
        self.detail.show(item)
        self._build_options(item)

    def _build_options(self, item: CatalogItem | None) -> None:
        for w in self.opts.winfo_children():
            w.destroy()
        self.vars: dict[str, Any] = {}
        if hasattr(self, "add_btn"):
            self.add_btn.state(["disabled"])
        if item is None:
            ttk.Label(self.opts, text=tr("wizard_pick_first"), style="CardMuted.TLabel").pack(anchor="w")
            return
        if not item.addable:
            ttk.Label(self.opts, text=tr("wizard_no_id"), style="Card.TLabel", wraplength=400, justify="left"
                      ).pack(anchor="w")
            return
        items = inventory_items(self.app)
        if items is None:
            ttk.Label(self.opts, text=tr("wizard_no_inventory"), style="Card.TLabel", wraplength=400,
                      justify="left").pack(anchor="w")
            return
        v = self.vars
        ttk.Label(self.opts, text=tr("wizard_options"), style="H2.TLabel").pack(anchor="w")
        row = ttk.Frame(self.opts, style="Inner.TFrame")
        row.pack(fill="x", pady=(8, 0))
        ttk.Label(row, text=tr("inv_item_count"), style="Card.TLabel", width=16).pack(side="left")
        v["qty"] = tk.StringVar(value="1")
        ttk.Entry(row, textvariable=v["qty"], width=10, justify="center").pack(side="left")
        if item.can_stars:
            row = ttk.Frame(self.opts, style="Inner.TFrame")
            row.pack(fill="x", pady=(8, 0))
            ttk.Label(row, text=tr("stars_label"), style="Card.TLabel", width=16).pack(side="left")
            v["stars"] = tk.StringVar(value="0")
            ttk.Spinbox(row, from_=0, to=knowledge.STAR_MAX, textvariable=v["stars"], width=6).pack(side="left")
            ttk.Label(row, text=tr("stars_hint", n=knowledge.STAR_MAX), style="CardMuted.TLabel").pack(side="left",
                                                                                                    padx=8)
            v["shiny"] = tk.BooleanVar(value=False)
            ttk.Checkbutton(self.opts, text=tr("shiny_label"), variable=v["shiny"], style="Card.TCheckbutton"
                            ).pack(anchor="w", pady=(8, 0))
        if item.element == "varies":
            row = ttk.Frame(self.opts, style="Inner.TFrame")
            row.pack(fill="x", pady=(8, 0))
            ttk.Label(row, text=tr("element_label"), style="Card.TLabel", width=16).pack(side="left")
            known = [str(x) for x in catalog.known_values(items, "el")]
            v["el"] = tk.StringVar(value="")
            ttk.Combobox(row, textvariable=v["el"], values=[""] + known, width=16).pack(side="left")
            ttk.Label(self.opts, text=tr("element_hint") if known else tr("element_none_known"),
                      style="CardMuted.TLabel", wraplength=400, justify="left").pack(anchor="w")
        if item.can_enchant:
            ttk.Label(self.opts, text=tr("enchant_label"), style="Card.TLabel").pack(anchor="w", pady=(10, 2))
            v["ench"] = tk.StringVar(value="none")
            ttk.Radiobutton(self.opts, text=tr("ench_none"), value="none", variable=v["ench"]).pack(anchor="w")
            examples = catalog.enchanted_examples(items)
            if examples:
                ttk.Radiobutton(self.opts, text=tr("ench_copy"), value="copy", variable=v["ench"]).pack(anchor="w")
                labels = []
                for ex in examples:
                    ra = ex["da"]["ra"]
                    tier = knowledge.enchant_tier(ra.get("lv", 0)) if isinstance(ra.get("lv"), int) else None
                    labels.append(f"{catalog.display_name(str(ex.get('id')))}: +{ra.get('lv', '?')}"
                                  + (f" ({tier[0]})" if tier else ""))
                self._examples = examples
                v["ex"] = ttk.Combobox(self.opts, state="readonly", values=labels, width=34)
                v["ex"].current(0)
                v["ex"].pack(anchor="w", padx=(22, 0))
            ttk.Radiobutton(self.opts, text=tr("ench_max", lv=knowledge.ENCHANT_MAX), value="max",
                            variable=v["ench"]).pack(anchor="w")
            ttk.Label(self.opts, text=tr("ench_hint"), style="CardMuted.TLabel", wraplength=400, justify="left"
                      ).pack(anchor="w", pady=(2, 0))
        same = catalog.find_templates(items, item.id)
        ttk.Label(self.opts, text=tr("tmpl_from", name=catalog.display_name(item.id)) if same else tr("tmpl_minimal"),
                  style="CardMuted.TLabel", wraplength=400, justify="left").pack(anchor="w", pady=(10, 0))
        self.add_btn.state(["!disabled"])

    # ---- adding ----
    def _read_int(self, name: str, default: int, lo: int | None = None) -> int | None:
        var = self.vars.get(name)
        if var is None:
            return default
        try:
            val = core.parse_typed("number", var.get())
            val = int(val)
        except (ValueError, OverflowError):
            messagebox.showerror(tr("err_bad_value"), tr("err_bad_for_kind", kind=tr("kind_number")), parent=self)
            return None
        if lo is not None and val < lo:
            messagebox.showerror(tr("err_bad_value"), tr("err_min_value", lo=lo), parent=self)
            return None
        return val

    def _add(self) -> None:
        item = self.item
        app = self.app
        items = inventory_items(app)
        if item is None or not item.id or items is None:
            return
        qty = self._read_int("qty", 1, 1)
        if qty is None:
            return
        stars = None
        if "stars" in self.vars:
            stars = self._read_int("stars", 0, 0)
            if stars is None or not guard_range(app, stars, (0, knowledge.STAR_MAX)):
                return
        element = self.vars["el"].get().strip() if "el" in self.vars else None
        enchant = None
        mode = self.vars["ench"].get() if "ench" in self.vars else "none"
        if mode == "copy" and "ex" in self.vars:
            enchant = copy.deepcopy(self._examples[self.vars["ex"].current()]["da"]["ra"])
        elif mode == "max":
            enchant = dict(catalog.MAX_ENCHANT_EXAMPLE)
        shiny = bool(self.vars["shiny"].get()) if "shiny" in self.vars else False
        self._insert(items, item.id, qty, stars, shiny, element, enchant, catalog.display_name(item.id))

    def _insert(self, items, item_id, qty, stars, shiny, element, enchant, name) -> None:
        app = self.app
        new, _note = catalog.build_item(items, item_id, qty, stars=stars, shiny=shiny, element=element,
                                        enchant=enchant)
        for i, it in enumerate(items):          # an identical stack already exists: just raise its amount
            if isinstance(it, dict) and it.get("id") == new["id"] and it.get("da") == new["da"] \
                    and isinstance(it.get("co"), (int, float)):
                app.apply_set([sections.INVENTORY_PATH + (i, "co")], lambda old, q=qty: old + q, preview=False)
                self.status.configure(text=tr("wizard_added_more", name=name, n=qty))
                return
        app.history.add_item(app.current_slot, sections.INVENTORY_PATH, None, new)
        app.after_structural_edit()
        app.say(tr("inv_added", name=name))
        self.status.configure(text=tr("wizard_added", name=name, n=qty))
        self.added += 1
        self._build_options(self.item)

    def _add_by_id(self) -> None:
        items = inventory_items(self.app)
        if items is None:
            messagebox.showinfo(tr("wizard_title"), tr("wizard_no_inventory"), parent=self)
            return
        item_id = simpledialog.askstring(tr("add_by_id"), tr("add_by_id_ask"), parent=self)
        if not item_id or not item_id.strip():
            return
        item_id = item_id.strip()
        if not catalog.find_templates(items, item_id) and not messagebox.askyesno(
                tr("add_by_id"), tr("add_by_id_warn", id=item_id), icon="warning", parent=self):
            return
        self._insert(items, item_id, 1, None, False, None, None, item_id)
