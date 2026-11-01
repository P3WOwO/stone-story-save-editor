"""Value cards: one friendly card per value (icon, name, +/- buttons, Yes/No switch)."""
from __future__ import annotations

from typing import Any
import tkinter as tk
from tkinter import ttk

from . import core, sections
from .common import fmt_num
from .i18n import tr
from .widgets import Tooltip, ValueDialog


ICON_RULES = [
    (("gold", "coin", "money", "cash", "gem", "crystal", "currency", "price"), "$", "#d99a00"),
    (("health", "hp", "life", "heal", "vital"), "♥", "#d64545"),
    (("damage", "attack", "weapon", "sword", "strength", "power"), "⚔", "#c2571a"),
    (("armor", "armour", "defen", "shield", "protect", "resist"), "◈", "#3b6cf6"),
    (("time", "second", "minute", "hour", "clock"), "◷", "#7a5cf0"),
    (("kill", "death", "died", "enem", "monster", "boss"), "☠", "#6b7488"),
    (("level", "depth", "floor", "stage", "rank", "xp", "exp", "score", "best"), "▲", "#1f9d57"),
    (("item", "inventory", "count", "amount", "quantity", "stack", "bag"), "▣", "#0e8f9e"),
    (("premium", "pp", "pass", "ticket"), "★", "#d99a00"),
    (("name", "title", "note", "description"), "A", "#8a5a9e"),
]
DEFAULT_ICONS = {"number": ("#", "#5b6b8c"), "bool": ("✔", "#1f9d57"), "text": ("A", "#8a5a9e"),
                 "null": ("·", "#8f98ad")}


def icon_for(path: tuple, kind: str) -> tuple[str, str]:
    key = path[-1] if path else ""
    toks = sections.tokens(key) | sections.tokens(core.humanize(key))
    hay = f"{key} {core.humanize(key)}".casefold()
    for words, symbol, color in ICON_RULES:
        for w in words:
            if (w in toks) if len(w) <= 3 else (any(t.startswith(w) for t in toks) or (len(w) >= 6 and w in hay)):
                return symbol, color
    return DEFAULT_ICONS.get(kind, ("#", "#5b6b8c"))


def smart_step(value: Any) -> Any:
    """A sensible '+/-' step for a number: 1 for small values, 10 / 100 / 1000 ... for larger ones."""
    a = abs(value)
    if isinstance(value, float) and not float(value).is_integer() and a < 20:
        return 0.1
    if a < 20:
        return 1
    return 10 ** max(len(str(int(a))) - 2, 1)


class ValueCard(tk.Frame):
    """One value shown as a friendly card: icon, name and the right control for its type."""

    def __init__(self, parent, tab: "SimpleTab", path: tuple, name: str, section: str, value: Any):
        self.tab, self.app, self.path = tab, tab.app, path
        self.pal = pal = tab.app.pal
        self.kind = core.kind_of(value)
        self._bgw: list[tk.Widget] = []
        super().__init__(parent, bg=pal["card"], highlightthickness=1, highlightbackground=pal["border"],
                         highlightcolor=pal["border"], padx=12, pady=10)
        self._bgw.append(self)
        head = self._frame(self)
        head.pack(fill="x")
        symbol, color = icon_for(path, self.kind)
        icon = tk.Canvas(head, width=40, height=40, bg=pal["card"], highlightthickness=0)
        icon.create_oval(2, 2, 38, 38, fill=color, outline="")
        icon.create_text(20, 20, text=symbol, fill="#ffffff", font="SSEIcon")
        icon.pack(side="left")
        self._bgw.append(icon)
        texts = self._frame(head)
        texts.pack(side="left", fill="x", expand=True, padx=(10, 0))
        self._label(texts, name, font="SSEBold", fg=pal["text"], wraplength=170).pack(anchor="w", fill="x")
        if section:
            self._label(texts, section, font="SSESmall", fg=pal["muted"], wraplength=170).pack(anchor="w", fill="x")
        self.restore_btn = ttk.Button(head, text="↺", width=3, style="Quick.TButton", command=self._restore)
        Tooltip(self.restore_btn, tr("restore_original"), pal)
        self.body = self._frame(self)
        self.body.pack(fill="x", pady=(10, 0))
        self.var = tk.StringVar()
        getattr(self, "_build_" + self.kind, self._build_null)(value)
        self.refresh(value)

    # ---- small factories ----
    def _frame(self, parent) -> tk.Frame:
        f = tk.Frame(parent, bg=self.pal["card"])
        self._bgw.append(f)
        return f

    def _label(self, parent, text, fg=None, font=None, **kw) -> tk.Label:
        lb = tk.Label(parent, text=text, bg=self.pal["card"], fg=fg or self.pal["text"], font=font,
                      anchor="w", justify="left", **kw)
        self._bgw.append(lb)
        return lb

    # ---- controls ----
    def _build_number(self, value: Any) -> None:
        row = self._frame(self.body)
        row.pack(fill="x")
        minus = ttk.Button(row, text="−", width=3, style="Quick.TButton", command=lambda: self._bump(-1))
        minus.pack(side="left")
        self.entry = ttk.Entry(row, textvariable=self.var, justify="center", width=9, font="SSEEntry")
        self.entry.pack(side="left", fill="x", expand=True, padx=6, ipady=2)
        plus = ttk.Button(row, text="+", width=3, style="Quick.TButton", command=lambda: self._bump(1))
        plus.pack(side="left")
        Tooltip(minus, tr("tip_minus"), self.pal)
        Tooltip(plus, tr("tip_plus"), self.pal)
        self.entry.bind("<Return>", lambda _e: self._commit_text())
        self.entry.bind("<FocusOut>", lambda _e: self._commit_text())
        chips = self._frame(self.body)
        chips.pack(fill="x", pady=(8, 0))
        for text, op, n in (("+10", "add", 10), ("+100", "add", 100), ("+1 000", "add", 1000), ("×2", "mul", 2)):
            ttk.Button(chips, text=text, style="Quick.TButton", width=6,
                       command=lambda op=op, n=n: self._quick(op, n)).pack(side="left", padx=(0, 4))

    def _build_bool(self, value: bool) -> None:
        row = self._frame(self.body)
        row.pack(fill="x")
        self.switch = tk.Canvas(row, width=56, height=28, bg=self.pal["card"], highlightthickness=0, cursor="hand2")
        self.switch.pack(side="left")
        self._bgw.append(self.switch)
        self.switch_label = self._label(row, "", font="SSEBold")
        self.switch_label.pack(side="left", padx=10)
        self.switch_label.configure(cursor="hand2")
        for w in (self.switch, self.switch_label):
            w.bind("<Button-1>", lambda _e: self._toggle())

    def _build_text(self, value: str) -> None:
        row = self._frame(self.body)
        row.pack(fill="x")
        self.entry = ttk.Entry(row, textvariable=self.var, font="SSEEntry")
        self.entry.pack(side="left", fill="x", expand=True, ipady=2)
        ttk.Button(row, text="✓", width=3, style="Quick.TButton", command=self._commit_text).pack(side="left",
                                                                                                     padx=(6, 0))
        self.entry.bind("<Return>", lambda _e: self._commit_text())
        self.entry.bind("<FocusOut>", lambda _e: self._commit_text())

    def _build_null(self, value: Any) -> None:
        self._label(self.body, "—", fg=self.pal["muted"]).pack(side="left")
        ttk.Button(self.body, text=tr("set_value"), style="Quick.TButton",
                   command=lambda: self._advanced()).pack(side="right")

    # ---- reading current data ----
    def _current(self) -> Any:
        return core.get_at(self.app.root_data[self.app.current_slot], self.path)

    def _advanced(self) -> None:
        dlg = ValueDialog(self.app, tr("advanced_edit"), self.pal, self._current())
        self.app.wait_window(dlg)
        if dlg.accepted:
            self.app.apply_set([self.path], lambda _o: dlg.result)

    # ---- actions ----
    def _bump(self, sign: int) -> None:
        try:
            cur = self._current()
        except (KeyError, IndexError):
            return
        step = smart_step(cur)
        self.app.apply_set([self.path], lambda old: self.app.coerce_number(old, round(old + sign * step, 10)))

    def _quick(self, op: str, n: int) -> None:
        self.app.apply_set([self.path], lambda old: self.app.coerce_number(old, old + n if op == "add" else old * n))

    def _toggle(self) -> None:
        self.app.apply_set([self.path], lambda old: not old)

    def _commit_text(self) -> None:
        try:
            cur = self._current()
        except (KeyError, IndexError):
            return
        raw = self.var.get()
        if raw == self._as_text(cur):
            return
        try:
            if self.kind == "number":
                new = core.parse_typed("number", raw)
                self.app.apply_set([self.path], lambda old: self.app.coerce_number(old, new))
            else:
                self.app.apply_set([self.path], lambda _o: raw)
        except ValueError:
            pass
        finally:
            try:
                self.var.set(self._as_text(self._current()))   # always show the real stored value
            except (KeyError, IndexError, tk.TclError):
                pass

    def _restore(self) -> None:
        ok, orig = self.app.original_value(self.path)
        if ok:
            self.app.apply_set([self.path], lambda _o: orig)

    @staticmethod
    def _as_text(v: Any) -> str:
        return "" if v is None else str(v)

    # ---- appearance ----
    def refresh(self, value: Any | None = None) -> None:
        if value is None:
            try:
                value = self._current()
            except (KeyError, IndexError):
                return
        changed = self.path in self.app.changed_paths(self.app.current_slot)
        bg = self.pal["changed"] if changed else self.pal["card"]
        for w in self._bgw:
            try:
                w.configure(bg=bg)
            except tk.TclError:
                pass
        self.configure(highlightbackground=self.pal["accent"] if changed else self.pal["border"],
                       highlightcolor=self.pal["accent"])
        if changed:
            self.restore_btn.pack(side="right", anchor="n")
        else:
            self.restore_btn.pack_forget()
        if self.kind in ("number", "text"):
            if self.focus_get() is not self.entry:
                self.var.set(self._as_text(value))
        elif self.kind == "bool":
            self._draw_switch(bool(value), bg)

    def _draw_switch(self, on: bool, bg: str) -> None:
        c = self.switch
        c.delete("all")
        color = self.pal["ok"] if on else self.pal["muted"]
        c.create_oval(2, 2, 28, 26, fill=color, outline=color)
        c.create_oval(28, 2, 54, 26, fill=color, outline=color)
        c.create_rectangle(15, 2, 41, 26, fill=color, outline=color)
        x = 31 if on else 5
        c.create_oval(x, 5, x + 20, 25, fill="#ffffff", outline="")
        self.switch_label.configure(text=tr("yes") if on else tr("no"), fg=color)
