"""Specialised views: Inventory manager and Events / premium pass manager."""
from __future__ import annotations

import copy
from typing import Any
import tkinter as tk
from tkinter import ttk, messagebox

from . import catalog, core, knowledge, sections
from .cards import MiniField, NumberStepper, ValueCard, guard_range, icon_for, smart_step
from .common import display_value, fmt_num
from .i18n import tr
from .catalog_ui import ItemWizard
from .widgets import BaseDialog, PreviewDialog, Tooltip, ValueDialog


# --------------------------------------------------------------------------
# scrolling grid of widgets
# --------------------------------------------------------------------------
class ScrollGrid(ttk.Frame):
    """Scrollable area where 'card' widgets flow into columns and 'head'/'full' widgets span the row."""

    def __init__(self, parent, pal: dict, card_w: int = 300):
        super().__init__(parent, style="Card.TFrame")
        self.pal, self.card_w = pal, card_w
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(self, bg=pal["bg"], highlightthickness=0)
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.vsb.grid(row=0, column=1, sticky="ns")
        self.inner = tk.Frame(self.canvas, bg=pal["bg"])
        self.win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self._resized)
        self.items: list[tuple[str, tk.Widget]] = []
        self._ncols = 0
        self._maxcols = 0
        for ev in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.bind_all(ev, self._wheel, add="+")

    def frac(self) -> float:
        return self.canvas.yview()[0]

    def restore(self, frac: float) -> None:
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(frac)

    def clear(self) -> None:
        for w in self.inner.winfo_children():
            w.destroy()
        self.items = []

    def add(self, kind: str, widget: tk.Widget) -> None:
        self.items.append((kind, widget))

    def label(self, text: str, **kw) -> tk.Label:
        return tk.Label(self.inner, text=text, bg=self.pal["bg"], fg=kw.pop("fg", self.pal["muted"]), **kw)

    def layout(self) -> None:
        width = max(self.canvas.winfo_width(), 320)
        ncols = max(1, (width - 12) // self.card_w)
        self._ncols = ncols
        for c in range(max(self._maxcols, ncols)):
            self.inner.columnconfigure(c, weight=1 if c < ncols else 0, uniform="c" if c < ncols else "")
        self._maxcols = max(self._maxcols, ncols)
        row = col = 0
        for kind, w in self.items:
            if kind == "card":
                w.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
                col += 1
                if col >= ncols:
                    col, row = 0, row + 1
            else:
                if col:
                    col, row = 0, row + 1
                head = kind == "head"
                w.grid(row=row, column=0, columnspan=ncols, sticky="ew" if head else "",
                       padx=6, pady=(14, 2) if head else 12)
                row += 1

    def _resized(self, event) -> None:
        self.canvas.itemconfigure(self.win, width=event.width)
        if max(1, (max(event.width, 320) - 12) // self.card_w) != self._ncols:
            self.layout()

    def _wheel(self, event) -> None:
        try:
            if not self.winfo_viewable():
                return
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
# Inventory
# --------------------------------------------------------------------------
class ItemCard(tk.Frame):
    def __init__(self, parent, view: "InventoryView", item: sections.Item):
        self.view, self.app, self.item = view, view.app, item
        pal = self.pal = view.app.pal
        super().__init__(parent, bg=pal["card"], highlightthickness=1, highlightbackground=pal["border"],
                         highlightcolor=pal["accent"], padx=12, pady=10)
        self.steppers: list[NumberStepper] = []
        self.minis: list[MiniField] = []
        self.checks: list[tuple[tuple, tk.BooleanVar]] = []
        head = tk.Frame(self, bg=pal["card"])
        head.pack(fill="x")
        symbol, color = icon_for((item.name,), "number")
        if symbol == "#":
            symbol, color = "▣", "#0e8f9e"
        icon = tk.Canvas(head, width=40, height=40, bg=pal["card"], highlightthickness=0)
        icon.create_oval(2, 2, 38, 38, fill=color, outline="")
        icon.create_text(20, 20, text=symbol, fill="#ffffff", font="SSEIcon")
        icon.pack(side="left")
        tk.Label(head, text=item.name, bg=pal["card"], fg=pal["text"], font="SSEBold", anchor="w", justify="left",
                 wraplength=150).pack(side="left", fill="x", expand=True, padx=(10, 0))
        del_btn = ttk.Button(head, text="✕", width=3, style="Quick.TButton", command=self._delete)
        del_btn.pack(side="right", padx=(4, 0))
        Tooltip(del_btn, tr("inv_delete"), pal)
        if view.ref and view.ref.shape == "list":
            dup = ttk.Button(head, text="⧉", width=3, style="Quick.TButton", command=self._duplicate)
            dup.pack(side="right")
            Tooltip(dup, tr("inv_dup"), pal)
        body = tk.Frame(self, bg=pal["card"])
        body.pack(fill="x", pady=(10, 0))
        if item.count_path:
            st = NumberStepper(body, self.app, item.count_path, pal["card"])
            st.pack(fill="x")
            self.steppers.append(st)
        if isinstance(item.value, dict):
            self._build_fields(body)
        self.refresh()

    def _build_fields(self, body: tk.Frame) -> None:
        pal = self.pal
        item = self.item
        skip = {sections.pick_name_key(item.value), sections.pick_count_key(item.value)}
        scalar_keys = [k for k, v in item.value.items() if k not in skip and core.is_leaf(v) and v is not None]
        bools = [k for k in scalar_keys if isinstance(item.value[k], bool)]
        others = [k for k in scalar_keys if k not in bools
                  and (not isinstance(item.value[k], str) or len(item.value[k]) <= 24)][:4]
        if bools:
            row = tk.Frame(body, bg=pal["card"])
            row.pack(fill="x", pady=(10, 0))
            for k in bools[:4]:
                p = item.path + (k,)
                var = tk.BooleanVar(value=bool(item.value[k]))
                ttk.Checkbutton(row, text=core.humanize(k), variable=var, style="Card.TCheckbutton",
                                command=lambda p=p, var=var: self.app.apply_set([p], lambda _o: var.get())
                                ).pack(side="left", padx=(0, 10))
                self.checks.append((p, var))
        if others:
            grid = tk.Frame(body, bg=pal["card"])
            grid.pack(fill="x", pady=(8, 0))
            for i, k in enumerate(others):
                mf = MiniField(grid, self.app, item.path + (k,), pal["card"], pal["text"], pal["muted"])
                mf.grid(row=i // 2, column=i % 2, sticky="ew", padx=(0, 8), pady=2)
                grid.columnconfigure(i % 2, weight=1)
                self.minis.append(mf)
        ttk.Button(body, text=tr("inv_fields"), style="Quick.TButton", command=self._all_fields).pack(anchor="w",
                                                                                                    pady=(8, 0))

    def refresh(self) -> None:
        for st in self.steppers:
            st.refresh()
        for mf in self.minis:
            mf.refresh()
        slot = self.app.current_slot
        profile = self.app.root_data[slot]
        for p, var in self.checks:
            try:
                var.set(bool(core.get_at(profile, p)))
            except (KeyError, IndexError):
                pass
        n = len(self.item.path)
        changed = any(p[:n] == self.item.path for p in self.app.changed_paths(slot))
        self.configure(highlightbackground=self.pal["accent"] if changed else self.pal["border"])

    def _all_fields(self) -> None:
        dlg = ValueDialog(self.app, f"{tr('inv_fields')} — {self.item.name}", self.pal, self.item.value,
                          allow_kind_change=False, hint=tr("json_hint"))
        self.app.wait_window(dlg)
        if dlg.accepted:
            self.app.apply_set([self.item.path], lambda _o: dlg.result)

    def _duplicate(self) -> None:
        self.view.duplicate(self.item)

    def _delete(self) -> None:
        self.app.delete_path(self.item.path)


class AddItemDialog(BaseDialog):
    def __init__(self, parent, pal: dict, items: list[sections.Item], shape: str):
        super().__init__(parent, tr("inv_add_title"), pal, "560x430")
        self.accepted = False
        self.name = ""
        self.count = 1
        self.template: str | None = None
        self._items = items
        ttk.Label(self, text=tr("inv_add_title"), style="Title.TLabel").pack(anchor="w", padx=18, pady=(16, 4))
        ttk.Label(self, text=tr("inv_add_hint") if items else tr("inv_no_template"), style="Muted.TLabel",
                  wraplength=520, justify="left").pack(anchor="w", padx=18)
        ttk.Label(self, text=tr("inv_item_name")).pack(anchor="w", padx=18, pady=(14, 2))
        self.name_var = tk.StringVar()
        e = ttk.Entry(self, textvariable=self.name_var, font="SSEEntry")
        e.pack(fill="x", padx=18)
        e.focus_set()
        ttk.Label(self, text=tr("inv_item_count")).pack(anchor="w", padx=18, pady=(12, 2))
        self.count_var = tk.StringVar(value="1")
        ttk.Entry(self, textvariable=self.count_var, width=12, font="SSEEntry").pack(anchor="w", padx=18)
        self.tbox = None
        if items and shape != "map_num":
            ttk.Label(self, text=tr("inv_template")).pack(anchor="w", padx=18, pady=(12, 2))
            self.tbox = ttk.Combobox(self, state="readonly", values=[i.name for i in items])
            self.tbox.current(0)
            self.tbox.pack(fill="x", padx=18)
        btns = ttk.Frame(self)
        btns.pack(side="bottom", fill="x", padx=18, pady=16)
        ttk.Button(btns, text=tr("cancel"), command=self.destroy).pack(side="right")
        ttk.Button(btns, text=tr("apply"), style="Accent.TButton", command=self._ok).pack(side="right", padx=8)
        self.bind("<Return>", lambda _e: self._ok())
        self.present()

    def _ok(self) -> None:
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror(tr("err_bad_value"), tr("err_empty_name"), parent=self)
            return
        try:
            count = core.parse_typed("number", self.count_var.get())
        except ValueError:
            messagebox.showerror(tr("err_bad_value"), tr("err_bad_for_kind", kind=tr("kind_number")), parent=self)
            return
        self.name, self.count = name, int(count) if float(count).is_integer() else count
        self.template = self.tbox.get() if self.tbox is not None else None
        self.accepted = True
        self.destroy()


SUB_SYMBOLS = {"sword": "⚔", "shield": "◈", "crossbow": "⇗", "wand": "✦", "staff": "│", "hammer": "▮",
               "rune": "◆", "polearm": "↟", "talisman": "☼", "mask": "☻", "arm": "✋", "tool": "⚒",
               "stone": "●", "resource": "◇", "event": "★", "enchant": "✿"}
CAT_COLORS = {"basic": "#3b6cf6", "craft": "#0e8f9e", "lost": "#c2571a", "other": "#7a5cf0", "tools": "#6b7488",
              "stones": "#8a5a9e", "misc": "#d99a00"}


def is_real_item(value: Any) -> bool:
    return isinstance(value, dict) and isinstance(value.get("da"), dict) and "id" in value


def set_da(app, item_path: tuple, key: str, value: Any) -> None:
    """Set da[key] of an item, creating the key when the item does not have it yet."""
    p = item_path + ("da", key)
    if core.exists_at(app.root_data[app.current_slot], p):
        app.apply_set([p], lambda _o: value, preview=False)
    else:
        app.history.add_item(app.current_slot, item_path + ("da",), key, value)
        app.after_structural_edit()


class EnchantDialog(BaseDialog):
    """Edit or create the enchantment (da.ra) of an item: level, quality, seed."""

    def __init__(self, app, item: sections.Item):
        super().__init__(app, tr("ench_title"), app.pal, "560x600")
        self.app, self.item = app, item
        self.ra = item.value.get("da", {}).get("ra")
        cur = self.ra if isinstance(self.ra, dict) else {}
        ttk.Label(self, text=tr("ench_title") + " — " + catalog.display_name(str(item.value.get("id"))),
                  style="Title.TLabel", wraplength=520).pack(anchor="w", padx=18, pady=(14, 2))
        ttk.Label(self, text=knowledge.hint_for(item.path + ("da", "ra")) or "", style="Muted.TLabel",
                  wraplength=520, justify="left").pack(anchor="w", padx=18)
        self.vars = {k: tk.StringVar(value=str(cur.get(k, ""))) for k in ("lv", "ql", "sSS")}
        self.tier = ttk.Label(self, text="", font="SSEBold")
        self.tier.pack(anchor="w", padx=18, pady=(10, 0))
        presets = [tr("ench_manual"), tr("ench_max", lv=knowledge.ENCHANT_MAX)]
        self._preset_vals: list[dict | None] = [None, dict(catalog.MAX_ENCHANT_EXAMPLE)]
        for ex in catalog.enchanted_examples(inventory_list(app)):
            ra = ex["da"]["ra"]
            presets.append(tr("ench_from", name=catalog.display_name(str(ex.get("id"))), lv=ra.get("lv", "?")))
            self._preset_vals.append(dict(ra))
        row = ttk.Frame(self)
        row.pack(fill="x", padx=18, pady=(10, 0))
        ttk.Label(row, text=tr("ench_preset"), width=18).pack(side="left")
        self.preset = ttk.Combobox(row, state="readonly", values=presets, width=34)
        self.preset.current(0)
        self.preset.pack(side="left")
        self.preset.bind("<<ComboboxSelected>>", lambda _e: self._use_preset())
        for key, label_key, hint_path in (("lv", "ench_lv", "lv"), ("ql", "ench_ql", "ql"), ("sSS", "ench_seed", "sSS")):
            row = ttk.Frame(self)
            row.pack(fill="x", padx=18, pady=(10, 0))
            ttk.Label(row, text=tr(label_key), width=18).pack(side="left", anchor="n")
            col = ttk.Frame(row)
            col.pack(side="left", fill="x", expand=True)
            e = ttk.Entry(col, textvariable=self.vars[key], width=14)
            e.pack(anchor="w")
            ttk.Label(col, text=knowledge.hint_for(item.path + ("da", "ra", hint_path)) or "",
                      style="Muted.TLabel", wraplength=330, justify="left").pack(anchor="w")
            self.vars[key].trace_add("write", lambda *_a: self._update_tier())
        btns = ttk.Frame(self)
        btns.pack(side="bottom", fill="x", padx=18, pady=14)
        ttk.Button(btns, text=tr("cancel"), command=self.destroy).pack(side="right")
        ttk.Button(btns, text=tr("apply"), style="Accent.TButton", command=self._apply).pack(side="right", padx=8)
        if isinstance(self.ra, dict):
            ttk.Button(btns, text=tr("ench_remove"), style="Danger.TButton", command=self._remove).pack(side="left")
        self._update_tier()
        self.present()

    def _use_preset(self) -> None:
        vals = self._preset_vals[self.preset.current()]
        if vals:
            for k in ("lv", "ql", "sSS"):
                self.vars[k].set(str(vals.get(k, "")))

    def _update_tier(self) -> None:
        try:
            lv = int(core.parse_typed("number", self.vars["lv"].get()))
            tier = knowledge.enchant_tier(lv)
        except (ValueError, OverflowError):
            tier = None
        self.tier.configure(text=f"+{self.vars['lv'].get()}  ·  {tier[0]} ({tier[1]})" if tier
                            else tr("ench_out_of_range", mx=knowledge.ENCHANT_MAX),
                            foreground=tier[2] if tier else self.pal["muted"])

    def _apply(self) -> None:
        try:
            ra = {k: int(core.parse_typed("number", self.vars[k].get())) for k in ("lv", "ql", "sSS")}
        except (ValueError, OverflowError):
            messagebox.showerror(tr("err_bad_value"), tr("ench_need_numbers"), parent=self)
            return
        if not guard_range(self.app, ra["lv"], (1, knowledge.ENCHANT_MAX)):
            return
        self.destroy()
        set_da(self.app, self.item.path, "ra", ra)

    def _remove(self) -> None:
        if messagebox.askyesno(tr("ench_remove"), tr("ench_remove_ask"), parent=self):
            self.destroy()
            self.app.history.delete_item(self.app.current_slot, self.item.path + ("da", "ra"))
            self.app.after_structural_edit()


def inventory_list(app) -> list:
    try:
        node = core.get_at(app.root_data[app.current_slot], sections.INVENTORY_PATH)
        return node if isinstance(node, list) else []
    except (KeyError, IndexError, TypeError):
        return []


class RealItemCard(tk.Frame):
    """Item card for the game's real item layout {id, co, da}: separate type / element / stars / enchantment."""

    def __init__(self, parent, view: "InventoryView", item: sections.Item):
        self.view, self.app, self.item = view, view.app, item
        pal = self.pal = view.app.pal
        super().__init__(parent, bg=pal["card"], highlightthickness=1, highlightbackground=pal["border"],
                         highlightcolor=pal["accent"], padx=12, pady=10)
        self.cat = catalog.lookup_id(str(item.value.get("id")))
        self.steppers: list[NumberStepper] = []
        self.checks: list[tuple[tuple, tk.BooleanVar]] = []
        self.minis: list[MiniField] = []
        symbol = SUB_SYMBOLS.get(self.cat.sub, "▣") if self.cat else "?"
        color = CAT_COLORS.get(self.cat.category, "#6b7488") if self.cat else "#6b7488"
        head = tk.Frame(self, bg=pal["card"])
        head.pack(fill="x")
        cv = tk.Canvas(head, width=40, height=40, bg=pal["card"], highlightthickness=0)
        cv.create_oval(2, 2, 38, 38, fill=color, outline="")
        cv.create_text(20, 20, text=symbol, fill="#ffffff", font="SSEIcon")
        cv.pack(side="left")
        texts = tk.Frame(head, bg=pal["card"])
        texts.pack(side="left", fill="x", expand=True, padx=(10, 0))
        name = self.cat.name if self.cat else str(item.value.get("id"))
        tk.Label(texts, text=name, bg=pal["card"], fg=pal["text"], font="SSEBold", anchor="w", justify="left",
                 wraplength=150).pack(anchor="w", fill="x")
        sub = f"ID: {item.value.get('id')}" + ("" if self.cat else "  ·  " + tr("not_in_catalog"))
        tk.Label(texts, text=sub, bg=pal["card"], fg=pal["muted"], font="SSESmall", anchor="w", justify="left",
                 wraplength=150).pack(anchor="w", fill="x")
        ttk.Button(head, text="✕", width=3, style="Quick.TButton", command=lambda: self.app.delete_path(item.path)
                   ).pack(side="right", padx=(4, 0))
        dup = ttk.Button(head, text="⧉", width=3, style="Quick.TButton", command=lambda: view.duplicate(item))
        dup.pack(side="right")
        Tooltip(dup, tr("inv_dup"), pal)
        self.chips = tk.Frame(self, bg=pal["card"])
        self.chips.pack(fill="x", pady=(8, 0))
        body = tk.Frame(self, bg=pal["card"])
        body.pack(fill="x", pady=(6, 0))
        self._build(body)
        self.refresh()

    def _lbl(self, parent, text, hint=None, muted=True) -> tk.Label:
        lb = tk.Label(parent, text=text, bg=self.pal["card"], fg=self.pal["muted"] if muted else self.pal["text"],
                      font="SSESmall", anchor="w")
        if hint:
            Tooltip(lb, hint, self.pal)
        return lb

    def _build(self, body: tk.Frame) -> None:
        item, pal, app = self.item, self.pal, self.app
        co = item.path + ("co",)
        self._lbl(body, tr("inv_item_count"), knowledge.hint_for(co)).pack(anchor="w")
        if core.exists_at(app.root_data[app.current_slot], co):
            st = NumberStepper(body, app, co, pal["card"])
            st.pack(fill="x")
            self.steppers.append(st)
        da_path = item.path + ("da",)
        lv = da_path + ("lv",)
        show_stars = (self.cat.can_stars if self.cat else False) or "lv" in item.value["da"]
        if show_stars:
            self._lbl(body, tr("stars_label"), knowledge.hint_for(lv)).pack(anchor="w", pady=(8, 0))

            def get_lv():
                try:
                    return core.get_at(app.root_data[app.current_slot], lv)
                except (KeyError, IndexError):
                    return 0
            st = NumberStepper(body, app, None, pal["card"], chips=False, get=get_lv,
                               put=lambda n: set_da(app, item.path, "lv", n), limits=(0, knowledge.STAR_MAX))
            st.pack(fill="x")
            self.steppers.append(st)
        row = tk.Frame(body, bg=pal["card"])
        row.pack(fill="x", pady=(8, 0))
        for key, label_key in (("sh", "shiny_label"), ("hI", "hi_label")):
            if key in item.value["da"] or (key == "sh" and self.cat and self.cat.can_stars):
                p = da_path + (key,)
                var = tk.BooleanVar(value=bool(item.value["da"].get(key)))
                cb = ttk.Checkbutton(row, text=tr(label_key), variable=var, style="Card.TCheckbutton",
                                     command=lambda k=key, var=var: set_da(app, item.path, k, var.get()))
                cb.pack(side="left", padx=(0, 10))
                Tooltip(cb, knowledge.hint_for(p) or "", pal)
                self.checks.append((p, var))
        if "el" in item.value["da"] or (self.cat and self.cat.element == "varies"):
            el = da_path + ("el",)
            if core.exists_at(app.root_data[app.current_slot], el):
                mf = MiniField(body, app, el, pal["card"], pal["text"], pal["muted"], label=tr("element_label"),
                               hint=knowledge.hint_for(el))
                mf.pack(fill="x", pady=(8, 0))
                self.minis.append(mf)
        self.ench_lbl = self._lbl(body, "", knowledge.hint_for(da_path + ("ra",)), muted=False)
        self.ench_lbl.pack(anchor="w", pady=(8, 0))
        btns = tk.Frame(body, bg=pal["card"])
        btns.pack(fill="x", pady=(6, 0))
        if (self.cat.can_enchant if self.cat else False) or "ra" in item.value["da"]:
            ttk.Button(btns, text=tr("ench_btn"), style="Quick.TButton", command=self._enchant).pack(side="left")
        ttk.Button(btns, text=tr("inv_fields"), style="Quick.TButton", command=self._all_fields).pack(side="left",
                                                                                                    padx=(6, 0))

    def _chip(self, text: str, bg: str, fg: str = "#ffffff") -> None:
        tk.Label(self.chips, text=text, bg=bg, fg=fg, font="SSESmall", padx=6, pady=1).pack(side="left", padx=(0, 4))

    def refresh(self) -> None:
        pal, app = self.pal, self.app
        for st in self.steppers:
            st.refresh()
        for mf in self.minis:
            mf.refresh()
        slot = app.current_slot
        profile = app.root_data[slot]
        try:
            value = core.get_at(profile, self.item.path)
        except (KeyError, IndexError):
            return
        da = value.get("da", {}) if isinstance(value, dict) else {}
        for p, var in self.checks:
            try:
                var.set(bool(core.get_at(profile, p)))
            except (KeyError, IndexError):
                pass
        for w in self.chips.winfo_children():
            w.destroy()
        if self.cat:                       # type, element and rarity are separate characteristics
            self._chip(catalog.sub_name(self.cat.sub), pal["soft"], pal["text"])
        if da.get("el"):
            self._chip(f"{tr('element_label')}: {da['el']}", pal["soft"], pal["text"])
        elif self.cat and self.cat.element == "stone":
            self._chip(self.cat.tr_text(catalog.ELEMENT_TEXT, "stone"), pal["soft"], pal["text"])
        if isinstance(da.get("lv"), int):
            self._chip(f"★ {da['lv']}", "#d99a00")
        ra = da.get("ra")
        tier = knowledge.enchant_tier(ra["lv"]) if isinstance(ra, dict) and isinstance(ra.get("lv"), int) else None
        if tier:
            self._chip(f"+{ra['lv']}", tier[2])
        self.ench_lbl.configure(text=(f"{tr('enchant_label')}: +{ra.get('lv', '?')}"
                                      + (f" · {tier[0]} ({tier[1]})" if tier else "")) if isinstance(ra, dict)
                                else f"{tr('enchant_label')}: {tr('ench_none_short')}")
        n = len(self.item.path)
        changed = any(p[:n] == self.item.path for p in app.changed_paths(slot))
        self.configure(highlightbackground=pal["accent"] if changed else pal["border"])

    def _enchant(self) -> None:
        dlg = EnchantDialog(self.app, self.item)
        self.app.wait_window(dlg)

    def _all_fields(self) -> None:
        dlg = ValueDialog(self.app, f"{tr('inv_fields')} — {self.cat.name if self.cat else self.item.name}",
                          self.pal, self.item.value, allow_kind_change=False, hint=tr("json_hint"))
        self.app.wait_window(dlg)
        if dlg.accepted:
            self.app.apply_set([self.item.path], lambda _o: dlg.result)


class InventoryView(ttk.Frame):
    PAGE = 48
    ANY = "__any__"

    def __init__(self, parent, app, content):
        super().__init__(parent)
        self.app, self.content = app, content
        self.pal = pal = app.pal
        self.ref: sections.InventoryRef | None = None
        self.filtered: list[sections.Item] = []
        self.cards: dict[tuple, Any] = {}
        self.limit = self.PAGE
        self.type_key, self.el_key, self.sort_key = self.ANY, self.ANY, "order"
        bar = ttk.Frame(self, style="Card.TFrame", padding=(14, 10))
        bar.pack(fill="x", pady=(0, 8))
        r1 = ttk.Frame(bar, style="Inner.TFrame")
        r1.pack(fill="x")
        ttk.Label(r1, text="▣  " + tr("inv_title"), style="H1.TLabel").pack(side="left")
        self.count_lbl = ttk.Label(r1, text="", style="CardMuted.TLabel")
        self.count_lbl.pack(side="left", padx=14)
        ttk.Button(r1, text=tr("use_generic"), command=lambda: content.set_special(False)).pack(side="right")
        self.where_lbl = ttk.Label(r1, text="", style="CardMuted.TLabel")
        self.where_lbl.pack(side="left")
        r2 = ttk.Frame(bar, style="Inner.TFrame")
        r2.pack(fill="x", pady=(8, 0))
        ttk.Button(r2, text="+  " + tr("add_from_catalog"), style="Accent.TButton", command=self._add
                   ).pack(side="left")
        ttk.Separator(r2, orient="vertical").pack(side="left", fill="y", padx=10)
        ttk.Label(r2, text=tr("inv_bulk_label"), style="CardMuted.TLabel").pack(side="left")
        self.bulk_var = tk.StringVar(value="10")
        ttk.Entry(r2, textvariable=self.bulk_var, width=6, justify="center").pack(side="left", padx=6)
        ttk.Button(r2, text=tr("inv_set_all"), command=lambda: self._bulk("set")).pack(side="left", padx=2)
        ttk.Button(r2, text=tr("inv_add_all"), command=lambda: self._bulk("add")).pack(side="left", padx=2)
        ttk.Button(r2, text=tr("inv_clear"), style="Danger.TButton", command=self._clear).pack(side="right")
        r4 = ttk.Frame(bar, style="Inner.TFrame")
        r4.pack(fill="x", pady=(8, 0))
        ttk.Label(r4, text=tr("type_label") + ":", style="CardMuted.TLabel").pack(side="left")
        self.type_box = ttk.Combobox(r4, state="readonly", width=18)
        self.type_box.pack(side="left", padx=(6, 12))
        ttk.Label(r4, text=tr("element_label") + ":", style="CardMuted.TLabel").pack(side="left")
        self.el_box = ttk.Combobox(r4, state="readonly", width=14)
        self.el_box.pack(side="left", padx=(6, 12))
        ttk.Label(r4, text=tr("sort_label") + ":", style="CardMuted.TLabel").pack(side="left")
        self.sort_box = ttk.Combobox(r4, state="readonly", width=14,
                                     values=[tr("sort_order"), tr("sort_name"), tr("sort_count")])
        self.sort_box.current(0)
        self.sort_box.pack(side="left", padx=6)
        for box in (self.type_box, self.el_box, self.sort_box):
            box.bind("<<ComboboxSelected>>", lambda _e: self._filters_changed())
        self._type_keys: list[str] = [self.ANY]
        self._el_keys: list[str] = [self.ANY]
        self.grid_ = ScrollGrid(self, pal)
        self.grid_.pack(fill="both", expand=True)

    # ---- helpers ----
    def _meta(self, it: sections.Item) -> tuple[str, str]:
        """(type key, element text) of an item - separate characteristics used by the filters."""
        value = it.value if isinstance(it.value, dict) else {}
        cat = catalog.lookup_id(str(value.get("id"))) if "id" in value else None
        da = value.get("da") if isinstance(value.get("da"), dict) else {}
        return (cat.sub if cat else "unknown"), (str(da["el"]) if da.get("el") not in (None, "") else "")

    def _filters_changed(self) -> None:
        self.type_key = self._type_keys[self.type_box.current()] if self.type_box.current() >= 0 else self.ANY
        self.el_key = self._el_keys[self.el_box.current()] if self.el_box.current() >= 0 else self.ANY
        self.sort_key = ("order", "name", "count")[max(self.sort_box.current(), 0)]
        self.limit = self.PAGE
        self.rebuild()

    def _fill_filter_boxes(self, items: list[sections.Item]) -> None:
        types, els = [], []
        for it in items:
            t, e = self._meta(it)
            if t not in types:
                types.append(t)
            if e and e not in els:
                els.append(e)
        self._type_keys = [self.ANY] + types
        self._el_keys = [self.ANY] + els
        self.type_box.configure(values=[tr("type_filter_all")] + [
            tr("not_in_catalog") if t == "unknown" else catalog.sub_name(t) for t in types])
        self.el_box.configure(values=[tr("type_filter_all")] + els)
        self.type_box.current(self._type_keys.index(self.type_key) if self.type_key in self._type_keys else 0)
        self.el_box.current(self._el_keys.index(self.el_key) if self.el_key in self._el_keys else 0)
        if self.type_key not in self._type_keys:
            self.type_key = self.ANY
        if self.el_key not in self._el_keys:
            self.el_key = self.ANY

    # ---- building ----
    def rebuild(self) -> None:
        app, g = self.app, self.grid_
        frac = g.frac()
        g.clear()
        self.cards.clear()
        profile = app.root_data[app.current_slot]
        self.ref = sections.find_inventory(profile)
        if self.ref is None:
            g.add("full", g.label(tr("inv_not_found"), wraplength=560, pady=30))
            self.count_lbl.configure(text="")
            self.where_lbl.configure(text="")
            self.filtered = []
            g.layout()
            return
        items = sections.list_items(profile, self.ref)
        self._fill_filter_boxes(items)
        words = self.content.search_var.get().strip().casefold().split()
        out = []
        for it in items:
            t, e = self._meta(it)
            if self.type_key != self.ANY and t != self.type_key:
                continue
            if self.el_key != self.ANY and e != self.el_key:
                continue
            if words:
                cat = catalog.lookup_id(it.name)
                hay = f"{it.name} {cat.name_en if cat else ''} {cat.name_ru or '' if cat else ''}".casefold()
                if not all(w in hay for w in words):
                    continue
            out.append(it)
        if self.sort_key == "name":
            out.sort(key=lambda i: catalog.display_name(i.name).casefold())
        elif self.sort_key == "count":
            def cnt(i):
                try:
                    return -float(core.get_at(profile, i.count_path)) if i.count_path else 0
                except (KeyError, IndexError, TypeError, ValueError):
                    return 0
            out.sort(key=cnt)
        self.filtered = out
        self.count_lbl.configure(text=tr("inv_count", n=len(items)))
        self.where_lbl.configure(text=tr("inv_where", path=core.path_str(self.ref.path)))
        for it in out[:self.limit]:
            card = RealItemCard(g.inner, self, it) if is_real_item(it.value) else ItemCard(g.inner, self, it)
            self.cards[it.path] = card
            g.add("card", card)
        if len(out) > self.limit:
            g.add("full", ttk.Button(g.inner, text=tr("card_more", n=len(out) - self.limit),
                                     style="Tool.TButton", command=self._more))
        if not out:
            g.add("full", g.label(tr("inv_empty"), pady=30))
        g.layout()
        g.restore(frac)

    def _more(self) -> None:
        self.limit += self.PAGE
        self.rebuild()

    def update_values(self, paths: list[tuple]) -> None:
        done = set()
        for p in paths:
            for ip, card in self.cards.items():
                if p[:len(ip)] == ip and ip not in done:
                    done.add(ip)
                    card.refresh()

    # ---- actions ----
    def _bulk(self, mode: str) -> None:
        try:
            v = core.parse_typed("number", self.bulk_var.get())
        except ValueError:
            messagebox.showerror(tr("err_bad_value"), tr("err_bad_for_kind", kind=tr("kind_number")), parent=self.app)
            return
        paths = [i.count_path for i in self.filtered if i.count_path]
        if not paths:
            return
        self.app.apply_set(paths, lambda old: self.app.coerce_number(old, v if mode == "set" else old + v),
                           title=tr("inv_bulk_title"))

    def _clear(self) -> None:
        if not self.ref:
            return
        profile = self.app.root_data[self.app.current_slot]
        rows = [(catalog.display_name(i.name), tr("inv_remove_row"), "—") for i in
                sections.list_items(profile, self.ref)]
        dlg = PreviewDialog(self.app, tr("inv_clear"), self.pal, rows, note=tr("inv_clear_note"),
                            ok_text=tr("inv_clear"))
        self.app.wait_window(dlg)
        if dlg.accepted:
            self.app.apply_set([self.ref.path], lambda old: [] if isinstance(old, list) else {}, preview=False)

    def duplicate(self, item: sections.Item) -> None:
        app = self.app
        app.history.add_item(app.current_slot, self.ref.path, None, copy.deepcopy(item.value))
        app.after_structural_edit()
        app.say(tr("inv_added", name=catalog.display_name(item.name)))

    def _add(self) -> None:
        app = self.app
        profile = app.root_data[app.current_slot]
        if self.ref is None:
            messagebox.showinfo(tr("inv_add_title"), tr("inv_not_found"), parent=app)
            return
        if self.ref.shape == "list" and self.ref.path == sections.INVENTORY_PATH:
            dlg = ItemWizard(app)
            app.wait_window(dlg)
            return
        items = sections.list_items(profile, self.ref)
        dlg = AddItemDialog(app, self.pal, items, self.ref.shape)
        app.wait_window(dlg)
        if not dlg.accepted:
            return
        name, count = dlg.name, dlg.count
        existing = next((i for i in items if i.name == name), None)
        if existing is not None and existing.count_path:
            app.apply_set([existing.count_path], lambda old: app.coerce_number(old, old + count))
            return
        slot, ref = app.current_slot, self.ref
        try:
            if ref.shape == "map_num":
                app.history.add_item(slot, ref.path, name, count)
            else:
                tmpl_item = next((i for i in items if i.name == dlg.template), items[0] if items else None)
                tmpl = copy.deepcopy(tmpl_item.value) if tmpl_item else {"name": name, "count": count}
                nk, ck = sections.pick_name_key(tmpl), sections.pick_count_key(tmpl)
                if ref.shape == "list":
                    if nk:
                        tmpl[nk] = name
                    if ck:
                        tmpl[ck] = count
                    app.history.add_item(slot, ref.path, None, tmpl)
                else:
                    if ck:
                        tmpl[ck] = count
                    app.history.add_item(slot, ref.path, name, tmpl)
        except KeyError:
            messagebox.showerror(tr("err_bad_value"), tr("err_key_exists"), parent=app)
            return
        app.after_structural_edit()
        app.say(tr("inv_added", name=name))


# --------------------------------------------------------------------------
# Events / premium pass
# --------------------------------------------------------------------------
class EventsView(ttk.Frame):
    MAX_OTHER = 60

    def __init__(self, parent, app, content):
        super().__init__(parent)
        self.app, self.content = app, content
        self.pal = pal = app.pal
        self.cards: dict[tuple, ValueCard] = {}
        self.pass_paths: list[tuple] = []
        self.point_paths: list[tuple] = []
        self.expanded: set[tuple] = set()
        bar = ttk.Frame(self, style="Card.TFrame", padding=(14, 10))
        bar.pack(fill="x", pady=(0, 8))
        r1 = ttk.Frame(bar, style="Inner.TFrame")
        r1.pack(fill="x")
        ttk.Label(r1, text="★  " + tr("ev_title"), style="H1.TLabel").pack(side="left")
        self.summary = ttk.Label(r1, text="", style="CardMuted.TLabel")
        self.summary.pack(side="left", padx=14)
        ttk.Button(r1, text=tr("use_generic"), command=lambda: content.set_special(False)).pack(side="right")
        ttk.Label(bar, text=tr("ev_hint"), style="CardMuted.TLabel", wraplength=900, justify="left"
                  ).pack(anchor="w", pady=(4, 8))
        r2 = ttk.Frame(bar, style="Inner.TFrame")
        r2.pack(fill="x")
        ttk.Button(r2, text="★  " + tr("ev_give_pass"), style="Accent.TButton", command=lambda: self._pass(True)
                   ).pack(side="left")
        ttk.Button(r2, text=tr("ev_remove_pass"), command=lambda: self._pass(False)).pack(side="left", padx=6)
        r3 = ttk.Frame(bar, style="Inner.TFrame")
        r3.pack(fill="x", pady=(8, 0))
        ttk.Label(r3, text=tr("ev_points_label"), style="CardMuted.TLabel").pack(side="left")
        self.points_var = tk.StringVar(value="35")
        ttk.Entry(r3, textvariable=self.points_var, width=7, justify="center").pack(side="left", padx=6)
        ttk.Button(r3, text=tr("ev_set_points"), command=self._points).pack(side="left")
        self.grid_ = ScrollGrid(self, pal)
        self.grid_.pack(fill="both", expand=True)

    # ---- building ----
    def _title(self, profile: dict, group: tuple) -> str:
        title = " › ".join(core.humanize(x) for x in group if x != "progress_data") or tr("whole_profile")
        try:
            node = core.get_at(profile, group)
            if isinstance(node, dict):
                nk = sections.pick_name_key(node)
                if nk and isinstance(node[nk], str):
                    title += f" — {node[nk]}"
        except (KeyError, IndexError):
            pass
        return title

    def rebuild(self) -> None:
        app, g = self.app, self.grid_
        frac = g.frac()
        g.clear()
        self.cards.clear()
        profile = app.root_data[app.current_slot]
        groups = sections.event_groups(profile)
        self.pass_paths = [p for lv in groups.values() for p, v in lv
                           if isinstance(v, bool) and sections.is_pass_key(p[-1])]
        self.point_paths = [p for lv in groups.values() for p, v in lv
                            if core.kind_of(v) == "number" and sections.is_points_key(p[-1])
                            and not any(isinstance(c, int) for c in p)]
        self._update_summary()
        if not groups:
            g.add("full", g.label(tr("ev_none"), pady=30))
            g.layout()
            return
        for group in sorted(groups, key=lambda x: [str(c) for c in x]):
            leaves = groups[group]
            head = g.label(self._title(profile, group), font="SSEBold", anchor="w", fg=self.pal["text"])
            g.add("head", head)
            pass_l = [(p, v) for p, v in leaves if isinstance(v, bool) and sections.is_pass_key(p[-1])]
            def is_task(p):
                return p[-1] == "p" and len(p) >= 2 and p[-2] != "objs"
            prog_l = [(p, v) for p, v in leaves if (p, v) not in pass_l and core.kind_of(v) == "number"
                      and (sections.is_progress_key(p[-1]) or is_task(p))]
            others = [(p, v) for p, v in leaves if (p, v) not in pass_l and (p, v) not in prog_l
                      and not (len(p) >= 2 and p[-2] == "ids")]
            for p, v in pass_l:
                self._card(group, p, v, tr("ev_pass_name"))
            for p, v in prog_l:
                self._card(group, p, v, None)
            if others:
                opened = group in self.expanded
                text = tr("ev_hide_fields") if opened else tr("ev_more_fields", n=len(others))
                g.add("full", ttk.Button(g.inner, text=text, style="Tool.TButton",
                                         command=lambda grp=group: self._toggle(grp)))
                if opened:
                    for p, v in others[:self.MAX_OTHER]:
                        self._card(group, p, v, None)
        g.layout()
        g.restore(frac)

    def _card(self, group: tuple, path: tuple, value: Any, name: str | None) -> None:
        rel = " › ".join(core.humanize(x) for x in path[len(group):-1])
        if name is None and path[-1] == "p" and len(path) >= 2:
            name = tr("ev_task", id=path[-2])
            rel = ""
        card = ValueCard(self.grid_.inner, self, path, name or knowledge.label(path) or core.humanize(path[-1]),
                         rel, value, hint=knowledge.hint_for(path))
        self.cards[path] = card
        self.grid_.add("card", card)

    def _toggle(self, group: tuple) -> None:
        self.expanded ^= {group}
        self.rebuild()

    def _update_summary(self) -> None:
        profile = self.app.root_data[self.app.current_slot]
        on = sum(1 for p in self.pass_paths if core.get_at(profile, p) is True)
        self.summary.configure(text=tr("ev_summary", on=on, total=len(self.pass_paths)) if self.pass_paths
                               else tr("ev_no_pass"))

    def update_values(self, paths: list[tuple]) -> None:
        for p in paths:
            card = self.cards.get(p)
            if card is not None:
                card.refresh()
        self._update_summary()

    # ---- actions ----
    def _pass(self, on: bool) -> None:
        if not self.pass_paths:
            messagebox.showinfo(tr("ev_title"), tr("ev_no_pass"), parent=self.app)
            return
        self.app.apply_set(self.pass_paths, lambda _o: on)

    def _points(self) -> None:
        try:
            v = core.parse_typed("number", self.points_var.get())
        except ValueError:
            messagebox.showerror(tr("err_bad_value"), tr("err_bad_for_kind", kind=tr("kind_number")), parent=self.app)
            return
        if not self.point_paths:
            messagebox.showinfo(tr("ev_title"), tr("ev_no_points"), parent=self.app)
            return
        self.app.apply_set(self.point_paths, lambda old: self.app.coerce_number(old, v))
