"""Specialised views: Inventory manager and Events / premium pass manager."""
from __future__ import annotations

import copy
from typing import Any
import tkinter as tk
from tkinter import ttk, messagebox

from . import core, sections
from .cards import ValueCard, icon_for, smart_step
from .common import display_value, fmt_num
from .i18n import tr
from .widgets import BaseDialog, Tooltip, ValueDialog


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
# small editors used inside item cards
# --------------------------------------------------------------------------
class NumberStepper(tk.Frame):
    """[-] [ number ] [+] with quick-add chips, bound to one number in the save."""

    def __init__(self, parent, app, path: tuple, bg: str, chips: bool = True):
        super().__init__(parent, bg=bg)
        self.app, self.path = app, path
        self.var = tk.StringVar()
        row = tk.Frame(self, bg=bg)
        row.pack(fill="x")
        ttk.Button(row, text="−", width=3, style="Quick.TButton", command=lambda: self._bump(-1)).pack(side="left")
        self.entry = ttk.Entry(row, textvariable=self.var, justify="center", width=8, font="SSEEntry")
        self.entry.pack(side="left", fill="x", expand=True, padx=6, ipady=2)
        ttk.Button(row, text="+", width=3, style="Quick.TButton", command=lambda: self._bump(1)).pack(side="left")
        self.entry.bind("<Return>", lambda _e: self._commit())
        self.entry.bind("<FocusOut>", lambda _e: self._commit())
        if chips:
            crow = tk.Frame(self, bg=bg)
            crow.pack(fill="x", pady=(8, 0))
            for text, op, n in (("+10", "add", 10), ("+100", "add", 100), ("×2", "mul", 2), ("= 0", "set", 0)):
                ttk.Button(crow, text=text, style="Quick.TButton", width=5,
                           command=lambda op=op, n=n: self._quick(op, n)).pack(side="left", padx=(0, 4))
        self.refresh()

    def _cur(self) -> Any:
        return core.get_at(self.app.root_data[self.app.current_slot], self.path)

    def refresh(self) -> None:
        try:
            if self.focus_get() is not self.entry:
                self.var.set(str(self._cur()))
        except (KeyError, IndexError, tk.TclError):
            pass

    def _bump(self, sign: int) -> None:
        try:
            step = smart_step(self._cur())
        except (KeyError, IndexError):
            return
        self.app.apply_set([self.path], lambda old: self.app.coerce_number(old, round(old + sign * step, 10)))

    def _quick(self, op: str, n: int) -> None:
        def fn(old):
            return n if op == "set" else (old + n if op == "add" else old * n)
        self.app.apply_set([self.path], lambda old: self.app.coerce_number(old, fn(old)))

    def _commit(self) -> None:
        try:
            cur = self._cur()
        except (KeyError, IndexError):
            return
        raw = self.var.get()
        if raw != str(cur):
            try:
                new = core.parse_typed("number", raw)
                self.app.apply_set([self.path], lambda old: self.app.coerce_number(old, new))
            except ValueError:
                pass
        try:
            self.var.set(str(self._cur()))
        except (KeyError, IndexError, tk.TclError):
            pass


class MiniField(tk.Frame):
    """A small labelled entry for a number/short text field of an item (stars, enchant level ...)."""

    def __init__(self, parent, app, path: tuple, bg: str, fg: str, muted: str):
        super().__init__(parent, bg=bg)
        self.app, self.path = app, path
        tk.Label(self, text=core.humanize(path[-1]), bg=bg, fg=muted, font="SSESmall").pack(anchor="w")
        self.var = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.var, width=9)
        self.entry.pack(fill="x")
        self.entry.bind("<Return>", lambda _e: self._commit())
        self.entry.bind("<FocusOut>", lambda _e: self._commit())
        self.refresh()

    def _cur(self) -> Any:
        return core.get_at(self.app.root_data[self.app.current_slot], self.path)

    def refresh(self) -> None:
        try:
            if self.focus_get() is not self.entry:
                self.var.set("" if self._cur() is None else str(self._cur()))
        except (KeyError, IndexError, tk.TclError):
            pass

    def _commit(self) -> None:
        try:
            cur = self._cur()
        except (KeyError, IndexError):
            return
        raw = self.var.get()
        if raw != str(cur):
            try:
                if core.kind_of(cur) == "number":
                    new = core.parse_typed("number", raw)
                    self.app.apply_set([self.path], lambda old: self.app.coerce_number(old, new))
                else:
                    self.app.apply_set([self.path], lambda _o: raw)
            except ValueError:
                pass
        try:
            self.var.set(str(self._cur()))
        except (KeyError, IndexError, tk.TclError):
            pass


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


class InventoryView(ttk.Frame):
    PAGE = 48

    def __init__(self, parent, app, content):
        super().__init__(parent)
        self.app, self.content = app, content
        self.pal = pal = app.pal
        self.ref: sections.InventoryRef | None = None
        self.filtered: list[sections.Item] = []
        self.cards: dict[tuple, ItemCard] = {}
        self.limit = self.PAGE
        bar = ttk.Frame(self, style="Card.TFrame", padding=(14, 10))
        bar.pack(fill="x", pady=(0, 8))
        r1 = ttk.Frame(bar, style="Inner.TFrame")
        r1.pack(fill="x")
        ttk.Label(r1, text="▣  " + tr("inv_title"), style="H1.TLabel").pack(side="left")
        self.count_lbl = ttk.Label(r1, text="", style="CardMuted.TLabel")
        self.count_lbl.pack(side="left", padx=14)
        ttk.Button(r1, text=tr("use_generic"), command=lambda: content.set_special(False)).pack(side="right")
        self.where_lbl = ttk.Label(bar, text="", style="CardMuted.TLabel")
        self.where_lbl.pack(anchor="w", pady=(2, 8))
        r2 = ttk.Frame(bar, style="Inner.TFrame")
        r2.pack(fill="x")
        ttk.Button(r2, text="+  " + tr("inv_add"), style="Accent.TButton", command=self._add).pack(side="left")
        ttk.Button(r2, text=tr("inv_clear"), style="Danger.TButton", command=self._clear).pack(side="right")
        r3 = ttk.Frame(bar, style="Inner.TFrame")
        r3.pack(fill="x", pady=(8, 0))
        ttk.Label(r3, text=tr("inv_bulk_label"), style="CardMuted.TLabel").pack(side="left")
        self.bulk_var = tk.StringVar(value="10")
        ttk.Entry(r3, textvariable=self.bulk_var, width=8, justify="center").pack(side="left", padx=6)
        ttk.Button(r3, text=tr("inv_set_all"), command=lambda: self._bulk("set")).pack(side="left", padx=2)
        ttk.Button(r3, text=tr("inv_add_all"), command=lambda: self._bulk("add")).pack(side="left", padx=2)
        self.grid_ = ScrollGrid(self, pal)
        self.grid_.pack(fill="both", expand=True)

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
        words = self.content.search_var.get().strip().casefold().split()
        self.filtered = [i for i in items if all(w in i.name.casefold() for w in words)] if words else items
        self.count_lbl.configure(text=tr("inv_count", n=len(items)))
        self.where_lbl.configure(text=tr("inv_where", path=core.path_str(self.ref.path)))
        for it in self.filtered[:self.limit]:
            card = ItemCard(g.inner, self, it)
            self.cards[it.path] = card
            g.add("card", card)
        if len(self.filtered) > self.limit:
            g.add("full", ttk.Button(g.inner, text=tr("card_more", n=len(self.filtered) - self.limit),
                                     style="Tool.TButton", command=self._more))
        if not self.filtered:
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
        self.app.apply_set(paths, lambda old: self.app.coerce_number(old, v if mode == "set" else old + v))

    def _clear(self) -> None:
        if not self.ref:
            return
        n = len(self.filtered)
        if not messagebox.askyesno(tr("inv_clear"), tr("inv_clear_ask", n=n), icon="warning", parent=self.app):
            return
        self.app.apply_set([self.ref.path], lambda old: [] if isinstance(old, list) else {})

    def duplicate(self, item: sections.Item) -> None:
        app = self.app
        app.history.add_item(app.current_slot, self.ref.path, None, copy.deepcopy(item.value))
        app.after_structural_edit()
        app.say(tr("inv_added", name=item.name))

    def _add(self) -> None:
        app = self.app
        profile = app.root_data[app.current_slot]
        if self.ref is None:
            messagebox.showinfo(tr("inv_add_title"), tr("inv_not_found"), parent=app)
            return
        items = sections.list_items(profile, self.ref)
        dlg = AddItemDialog(app, self.pal, items, self.ref.shape)
        app.wait_window(dlg)
        if not dlg.accepted:
            return
        name, count = dlg.name, dlg.count
        existing = next((i for i in items if i.name == name), None)
        if existing is not None and existing.count_path:      # same item already there: just add to its count
            app.apply_set([existing.count_path], lambda old: app.coerce_number(old, old + count))
            return
        slot, ref = app.current_slot, self.ref
        node = core.get_at(profile, ref.path)
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
        del node
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
            prog_l = [(p, v) for p, v in leaves if (p, v) not in pass_l and core.kind_of(v) == "number"
                      and sections.is_progress_key(p[-1])]
            others = [(p, v) for p, v in leaves if (p, v) not in pass_l and (p, v) not in prog_l]
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
        card = ValueCard(self.grid_.inner, self, path, name or core.humanize(path[-1]), rel, value)
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
