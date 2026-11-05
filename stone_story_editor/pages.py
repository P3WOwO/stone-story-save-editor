"""Section pages built on the real save layout: player, resources, cosmetics, quests, progress, locations."""
from __future__ import annotations

import tkinter as tk
from tkinter import colorchooser, messagebox, ttk
from typing import Any, Callable

from . import core, knowledge, ops
from . import knowledge_data as kd
from .cards import MemberCard, NumberStepper, ValueCard, icon_for
from .common import display_value
from .i18n import tr
from .views import ScrollGrid

PD = "progress_data"


class PageBase(ttk.Frame):
    """Header (title, explanation, actions) + scrolling grid of cards. Subclasses fill `build`."""

    TITLE = "page_player"
    ICON = "☺"
    HINT = "hint_player"

    def __init__(self, parent, app, content):
        super().__init__(parent)
        self.app, self.content = app, content
        self.pal = app.pal
        self.cards: dict[tuple, ValueCard] = {}
        self.live: list[Any] = []          # members / steppers that refresh after every edit
        bar = ttk.Frame(self, style="Card.TFrame", padding=(14, 10))
        bar.pack(fill="x", pady=(0, 8))
        r1 = ttk.Frame(bar, style="Inner.TFrame")
        r1.pack(fill="x")
        ttk.Label(r1, text=f"{self.ICON}  " + tr(self.TITLE), style="H1.TLabel").pack(side="left")
        self.summary = ttk.Label(r1, text="", style="CardMuted.TLabel")
        self.summary.pack(side="left", padx=14)
        ttk.Button(r1, text=tr("use_generic"), command=lambda: content.set_special(False)).pack(side="right")
        ttk.Label(bar, text=tr(self.HINT), style="CardMuted.TLabel", wraplength=900, justify="left"
                  ).pack(anchor="w", pady=(4, 6))
        self.actions = ttk.Frame(bar, style="Inner.TFrame")
        self.actions.pack(fill="x")
        self.grid_ = ScrollGrid(self, self.pal)
        self.grid_.pack(fill="both", expand=True)
        self.make_actions()

    # ---- to override ----
    def make_actions(self) -> None: ...

    def build(self, g: ScrollGrid, profile: dict) -> None: ...

    def empty_text(self) -> str:
        return tr("page_empty")

    # ---- helpers ----
    def profile(self) -> dict:
        return self.app.root_data[self.app.current_slot]

    def has(self, path: tuple) -> bool:
        return core.exists_at(self.profile(), path)

    def button(self, text: str, cmd: Callable, style: str = "TButton") -> ttk.Button:
        b = ttk.Button(self.actions, text=text, style=style, command=cmd)
        b.pack(side="left", padx=(0, 6))
        return b

    def header(self, text: str, buttons: list[tuple[str, Callable]] | None = None) -> None:
        g = self.grid_
        row = tk.Frame(g.inner, bg=self.pal["bg"])
        tk.Label(row, text=text, bg=self.pal["bg"], fg=self.pal["text"], font="SSEBold").pack(side="left")
        for label, cmd in buttons or []:
            ttk.Button(row, text=label, style="Quick.TButton", command=cmd).pack(side="left", padx=(10, 0))
        g.add("head", row)

    def value_card(self, path: tuple, name: str | None = None, section: str = "", hint: str | None = None,
                   icon: tuple[str, str] | None = None, limits: tuple | None = None,
                   cls: type = ValueCard, **kw) -> ValueCard | None:
        if not self.has(path):
            return None
        value = core.get_at(self.profile(), path)
        card = cls(self.grid_.inner, self, path, name or knowledge.label(path) or core.humanize(path[-1]),
                   section, value, hint=hint if hint is not None else knowledge.hint_for(path), icon=icon,
                   limits=limits, **kw)
        self.cards[path] = card
        self.grid_.add("card", card)
        return card

    def live_add(self, widget: Any) -> Any:
        self.live.append(widget)
        return widget

    # ---- lifecycle ----
    def rebuild(self) -> None:
        g = self.grid_
        frac = g.frac()
        g.clear()
        self.cards.clear()
        self.live.clear()
        self.build(g, self.profile())
        if not g.items:
            g.add("full", g.label(self.empty_text(), wraplength=560, pady=30))
        g.layout()
        g.restore(frac)

    def update_values(self, paths: list[tuple]) -> None:
        for p in paths:
            card = self.cards.get(p)
            if card is not None:
                card.refresh()
        for w in self.live:
            w.refresh()


# --------------------------------------------------------------------------
class NameCard(ValueCard):
    """The player name is stored twice in the save; this card changes both places."""

    def __init__(self, *a, extra_paths: tuple = (), **kw):
        self.extra = list(extra_paths)
        super().__init__(*a, **kw)

    def _commit_text(self) -> None:
        try:
            cur = self._current()
        except (KeyError, IndexError):
            return
        raw = self.var.get()
        if raw != cur and raw.strip():
            targets = [self.path] + [p for p in self.extra if core.exists_at(self.app.root_data[self.app.current_slot], p)]
            self.app.apply_set(targets, lambda _o: raw, preview=False)
        self.var.set(self._as_text(self._current()))


class PlayerPage(PageBase):
    TITLE, ICON, HINT = "page_player", "☺", "hint_player"
    LEVEL = (PD, "xp", "currentLevel")

    def make_actions(self) -> None:
        self.button(tr("max_level_btn", n=knowledge.LEVEL_MAX), self._max_level, "Accent.TButton")

    def _max_level(self) -> None:
        if self.has(self.LEVEL):
            self.app.apply_set([self.LEVEL], lambda _o: knowledge.LEVEL_MAX)

    def build(self, g: ScrollGrid, profile: dict) -> None:
        name_path = (PD, "hero_settings", "playerName")
        if self.has(name_path):
            self.value_card(name_path, icon=("A", "#8a5a9e"), cls=NameCard, extra_paths=(("player_name",),))
        elif self.has(("player_name",)):
            self.value_card(("player_name",), tr("name_label"), icon=("A", "#8a5a9e"),
                            hint=knowledge.hint_for(name_path))
        self.value_card(self.LEVEL, icon=("▲", "#1f9d57"), limits=(0, knowledge.LEVEL_MAX))
        self.value_card((PD, "xp", "currentXP"), icon=("✦", "#7a5cf0"))
        if self.has(self.LEVEL):
            lvl = core.get_at(profile, self.LEVEL)
            if isinstance(lvl, int):
                self.summary.configure(text=tr("player_summary", lvl=lvl, hp=lvl, chests=100 + 5 * lvl))


class ResourcesPage(PageBase):
    TITLE, ICON, HINT = "page_resources", "$", "hint_resources"

    def make_actions(self) -> None:
        self.n_var = tk.StringVar(value="1000")
        ttk.Entry(self.actions, textvariable=self.n_var, width=9, justify="center").pack(side="left", padx=(0, 6))
        self.button(tr("res_all_add"), lambda: self._bulk("add"))
        self.button(tr("res_all_set"), lambda: self._bulk("set"))

    def _paths(self) -> list[tuple]:
        return [(PD, "inventory_data", k) for k, *_ in knowledge.RESOURCES
                if self.has((PD, "inventory_data", k)) and isinstance(self.profile()[PD]["inventory_data"][k], (int, float))]

    def _bulk(self, mode: str) -> None:
        try:
            n = core.parse_typed("number", self.n_var.get())
        except ValueError:
            messagebox.showerror(tr("err_bad_value"), tr("err_bad_for_kind", kind=tr("kind_number")), parent=self.app)
            return
        paths = self._paths()
        if paths:
            self.app.apply_set(paths, lambda old: self.app.coerce_number(old, old + n if mode == "add" else n),
                               title=tr("res_bulk_title"))

    def _add_missing(self, key: str) -> None:
        self.app.run_ops(lambda h, s, g: bool(ops.ensure(h, s, (PD, "inventory_data", key), 0, g) is not None))

    def build(self, g: ScrollGrid, profile: dict) -> None:
        for key, en, ru, sym, where_en, where_ru in knowledge.RESOURCES:
            path = (PD, "inventory_data", key)
            where = tr("res_where", where=knowledge.pick(where_en, where_ru))
            if self.has(path):
                self.value_card(path, section=where, icon=(sym, "#d99a00"))
            else:
                card = tk.Frame(g.inner, bg=self.pal["card"], highlightthickness=1,
                                highlightbackground=self.pal["border"], padx=12, pady=10)
                tk.Label(card, text=knowledge.pick(en, ru), bg=self.pal["card"], fg=self.pal["text"],
                         font="SSEBold").pack(anchor="w")
                tk.Label(card, text=tr("res_missing"), bg=self.pal["card"], fg=self.pal["muted"],
                         font="SSESmall").pack(anchor="w")
                ttk.Button(card, text=tr("res_add"), style="Quick.TButton",
                           command=lambda k=key: self._add_missing(k)).pack(anchor="w", pady=(10, 0))
                g.add("card", card)


# --------------------------------------------------------------------------
class CosmeticCard(tk.Frame):
    KIND_LABELS = {"golden": "cos_golden", "glitch": "cos_glitch", "prismatic": "cos_prismatic"}

    def __init__(self, parent, page: "CosmeticsPage", key: str, name: str):
        self.page, self.app, self.key = page, page.app, key
        pal = self.pal = page.pal
        super().__init__(parent, bg=pal["card"], highlightthickness=1, highlightbackground=pal["border"], padx=12,
                         pady=10)
        head = tk.Frame(self, bg=pal["card"])
        head.pack(fill="x")
        cv = tk.Canvas(head, width=40, height=40, bg=pal["card"], highlightthickness=0)
        cv.create_oval(2, 2, 38, 38, fill="#a855f7", outline="")
        cv.create_text(20, 20, text="✦", fill="#ffffff", font="SSEIcon")
        cv.pack(side="left")
        texts = tk.Frame(head, bg=pal["card"])
        texts.pack(side="left", fill="x", expand=True, padx=(10, 0))
        tk.Label(texts, text=name, bg=pal["card"], fg=pal["text"], font="SSEBold", anchor="w", justify="left",
                 wraplength=170).pack(anchor="w", fill="x")
        tk.Label(texts, text=key, bg=pal["card"], fg=pal["muted"], font="SSESmall", anchor="w").pack(anchor="w")
        self.vars: dict[str, tk.BooleanVar] = {}
        for kind in ops.COSMETIC_KINDS:
            var = tk.BooleanVar(value=False)
            self.vars[kind] = var
            ttk.Checkbutton(self, text=tr(self.KIND_LABELS[kind]), variable=var, style="Card.TCheckbutton",
                            command=lambda k=kind, v=var: self._toggle(k, v)).pack(anchor="w", pady=(6, 0))
        self.color = tk.Button(self, text=tr("cos_color"), relief="flat", padx=8, pady=2, command=self._pick_color)
        self.refresh()

    def _toggle(self, kind: str, var: tk.BooleanVar) -> None:
        on = var.get()
        self.app.run_ops(lambda h, s, g: ops.set_cosmetic(h, s, kind, self.key, on, g))

    def _pick_color(self) -> None:
        h, s = self.app.history, self.app.current_slot
        cur = ops.prismatic_color(h, s, self.key) or "#000000"
        rgb, hexv = colorchooser.askcolor(color=cur, parent=self.app, title=tr("cos_color"))
        if hexv:
            self.app.run_ops(lambda h, s, g: ops.set_prismatic_color(h, s, self.key, hexv, g))

    def refresh(self) -> None:
        h, s = self.app.history, self.app.current_slot
        for kind, var in self.vars.items():
            var.set(ops.cosmetic_owned(h, s, kind, self.key))
        col = ops.prismatic_color(h, s, self.key) if self.vars["prismatic"].get() else None
        if col:
            try:
                self.color.configure(bg=col, activebackground=col)
            except tk.TclError:
                pass
            self.color.pack(anchor="w", pady=(6, 0))
        else:
            self.color.pack_forget()


class CosmeticsPage(PageBase):
    TITLE, ICON, HINT = "page_cosmetics", "✦", "hint_cosmetics"

    def make_actions(self) -> None:
        for kind in ops.COSMETIC_KINDS:
            label = tr(CosmeticCard.KIND_LABELS[kind])
            self.button(tr("cos_all_on", kind=label), lambda k=kind: self._bulk(k, True))
            self.button(tr("cos_all_off", kind=label), lambda k=kind: self._bulk(k, False))

    def _entries(self) -> list[tuple[str, str]]:
        words = self.content.search_var.get().strip().casefold().split()
        out = []
        for ck, _tk, en, ru in kd.COSMETICS:
            name = knowledge.pick(en, ru)
            if words and not all(w in f"{en} {ru} {ck}".casefold() for w in words):
                continue
            out.append((ck, name))
        return out

    def _bulk(self, kind: str, on: bool) -> None:
        h, s = self.app.history, self.app.current_slot
        todo = [(ck, n) for ck, n in self._entries() if ops.cosmetic_owned(h, s, kind, ck) != on]
        if not todo:
            self.app.say(tr("nothing_to_change"))
            return
        label = tr(CosmeticCard.KIND_LABELS[kind])
        rows = [(n, tr("no") if on else tr("yes"), tr("yes") if on else tr("no")) for _ck, n in todo]
        self.app.run_ops(lambda hh, ss, gg: sum(ops.set_cosmetic(hh, ss, kind, ck, on, gg) for ck, _n in todo),
                         rows=rows, title=f"{tr('page_cosmetics')}: {label}")

    def build(self, g: ScrollGrid, profile: dict) -> None:
        h, s = self.app.history, self.app.current_slot
        total = len(kd.COSMETICS)
        counts = [sum(1 for ck, *_ in kd.COSMETICS if ops.cosmetic_owned(h, s, k, ck)) for k in ops.COSMETIC_KINDS]
        self.summary.configure(text=tr("cos_summary", a=counts[0], b=counts[1], c=counts[2], n=total))
        for ck, name in self._entries():
            card = CosmeticCard(g.inner, self, ck, name)
            self.live.append(card)
            g.add("card", card)

    def update_values(self, paths: list[tuple]) -> None:
        pass          # cosmetics change lists, so every edit rebuilds the page


# --------------------------------------------------------------------------
class QuestsPage(PageBase):
    TITLE, ICON, HINT = "page_quests", "⚑", "hint_quests"

    def make_actions(self) -> None:
        self.button(tr("quests_all_done"), self._all_done, "Accent.TButton")

    def _completed_paths(self) -> list[tuple]:
        out = []
        active = (PD, "custom_quests", "active")
        if self.has(active):
            for i, q in enumerate(core.get_at(self.profile(), active)):
                if isinstance(q, dict) and isinstance(q.get("completed"), bool):
                    out.append(active + (i, "completed"))
        weekly = (PD, "weekly_quest", "activeQuest", "completed")
        if self.has(weekly):
            out.append(weekly)
        return out

    def _all_done(self) -> None:
        paths = self._completed_paths()
        if paths:
            self.app.apply_set(paths, lambda _o: True, title=tr("quests_all_done"))

    def build(self, g: ScrollGrid, profile: dict) -> None:
        active = (PD, "custom_quests", "active")
        if self.has(active):
            self.header(tr("quests_active"))
            for i, q in enumerate(core.get_at(profile, active)):
                if isinstance(q, dict) and isinstance(q.get("completed"), bool):
                    self.value_card(active + (i, "completed"), tr("quest_n", id=q.get("customQuestId", i + 1)),
                                    tr("quest_done_label"), icon=("⚑", "#c2571a"),
                                    hint=tr("quest_name_unknown"))
        weekly = (PD, "weekly_quest", "activeQuest")
        if self.has(weekly + ("completed",)):
            self.header(tr("quests_weekly"))
            q = core.get_at(profile, weekly)
            self.value_card(weekly + ("completed",), tr("quest_weekly_n", id=q.get("type", "?")),
                            tr("quest_done_label"), icon=("⚑", "#7a5cf0"))
        timers = [(PD, "custom_quests", k) for k in ("nextSpawnDate", "epicSpawnPending", "basicQuestDate")
                  if self.has((PD, "custom_quests", k))]
        if timers:
            self.header(tr("quests_timers"))
            for p in timers:
                self.value_card(p, icon=icon_for(p, "text") if isinstance(core.get_at(profile, p), str)
                                else ("◷", "#7a5cf0"))


class ProgressPage(PageBase):
    TITLE, ICON, HINT = "page_progress", "✔", "hint_progress"
    GROUPS = [("progress_locations", kd.LOCATIONS, "⌂", "#3b6cf6", "avail"),
              ("progress_workbench", kd.WORKBENCH, "⚒", "#0e8f9e", "avail"),
              ("progress_projects", kd.PROJECTS, "✎", "#d99a00", "avail"),
              ("progress_legends", kd.LEGENDS, "★", "#7a5cf0", "legend")]

    def _is_on(self, kind: str, gid: str) -> bool:
        h, s = self.app.history, self.app.current_slot
        return ops.legend_open(h, s, gid) if kind == "legend" else ops.has_member(h, s, ops.AVAILABLE, gid)

    def _set(self, kind: str, gid: str, on: bool, g: int | None = None) -> bool:
        h, s = self.app.history, self.app.current_slot
        return ops.set_legend(h, s, gid, on, g) if kind == "legend" else ops.set_member(h, s, ops.AVAILABLE, gid, on, g)

    def _bulk(self, title_key: str, table, kind: str, on: bool) -> None:
        todo = [(gid, knowledge.pick(en, ru)) for gid, en, ru in table if self._is_on(kind, gid) != on]
        if not todo:
            self.app.say(tr("nothing_to_change"))
            return
        rows = [(n, tr("no") if on else tr("yes"), tr("yes") if on else tr("no")) for _g, n in todo]
        self.app.run_ops(lambda h, s, grp: sum(self._set(kind, gid, on, grp) for gid, _n in todo), rows=rows,
                         title=f"{tr('page_progress')}: {tr(title_key)}")

    def build(self, g: ScrollGrid, profile: dict) -> None:
        total_on = total = 0
        for title_key, table, sym, color, kind in self.GROUPS:
            on_n = sum(1 for gid, *_ in table if self._is_on(kind, gid))
            total_on, total = total_on + on_n, total + len(table)
            self.header(f"{tr(title_key)}  ({on_n}/{len(table)})",
                        [(tr("open_all"), lambda t=title_key, tb=table, k=kind: self._bulk(t, tb, k, True)),
                         (tr("close_all"), lambda t=title_key, tb=table, k=kind: self._bulk(t, tb, k, False))])
            for gid, en, ru in table:
                card = MemberCard(g.inner, self.app, knowledge.pick(en, ru), gid,
                                  get=lambda k=kind, i=gid: self._is_on(k, i),
                                  put=lambda on, k=kind, i=gid: self.app.run_ops(
                                      lambda h, s, grp: self._set(k, i, on, grp)),
                                  icon=(sym, color))
                self.live.append(card)
                g.add("card", card)
        self.summary.configure(text=tr("progress_summary", a=total_on, n=total))

    def update_values(self, paths: list[tuple]) -> None:
        pass


class LocationsPage(PageBase):
    TITLE, ICON, HINT = "page_locations", "⌂", "hint_locations"

    def make_actions(self) -> None:
        self.n_var = tk.StringVar(value="5")
        ttk.Entry(self.actions, textvariable=self.n_var, width=7, justify="center").pack(side="left", padx=(0, 6))
        self.button(tr("loc_all_set"), self._all_set, "Accent.TButton")

    def _all_set(self) -> None:
        try:
            n = int(core.parse_typed("number", self.n_var.get()))
        except (ValueError, OverflowError):
            messagebox.showerror(tr("err_bad_value"), tr("err_bad_for_kind", kind=tr("kind_number")), parent=self.app)
            return
        h, s = self.app.history, self.app.current_slot
        rows = []
        for loc in knowledge.FARM_LOCATIONS:
            cur = self._stars(loc)
            if cur != n:
                rows.append((knowledge.id_name(loc) or loc, str(cur), str(n)))
        if not rows:
            self.app.say(tr("nothing_to_change"))
            return
        self.app.run_ops(lambda hh, ss, g: sum(ops.set_star_level(hh, ss, loc, n, g)
                                                for loc in knowledge.FARM_LOCATIONS if self._stars(loc) != n),
                         rows=rows, title=tr("loc_all_set"))

    def _stars(self, loc: str) -> int:
        try:
            v = core.get_at(self.profile(), ops.STAR_LEVELS + (loc,))
            return v if isinstance(v, int) else 0
        except (KeyError, IndexError, TypeError):
            return 0

    def build(self, g: ScrollGrid, profile: dict) -> None:
        pal, app = self.pal, self.app
        hint = knowledge.hint_for(ops.STAR_LEVELS)
        for loc in knowledge.FARM_LOCATIONS:
            card = tk.Frame(g.inner, bg=pal["card"], highlightthickness=1, highlightbackground=pal["border"],
                            padx=12, pady=10)
            head = tk.Frame(card, bg=pal["card"])
            head.pack(fill="x")
            cv = tk.Canvas(head, width=40, height=40, bg=pal["card"], highlightthickness=0)
            cv.create_oval(2, 2, 38, 38, fill="#3b6cf6", outline="")
            cv.create_text(20, 20, text="★", fill="#ffffff", font="SSEIcon")
            cv.pack(side="left")
            tk.Label(head, text=knowledge.id_name(loc) or loc, bg=pal["card"], fg=pal["text"], font="SSEBold",
                     anchor="w", justify="left", wraplength=170).pack(side="left", padx=(10, 0), fill="x", expand=True)
            if hint:
                b = ttk.Button(head, text="?", width=2, style="Quick.TButton",
                               command=lambda: messagebox.showinfo(tr("page_locations"), hint, parent=app))
                b.pack(side="right", anchor="n")
            tk.Label(card, text=tr("loc_stars"), bg=pal["card"], fg=pal["muted"], font="SSESmall").pack(anchor="w",
                                                                                                    pady=(8, 0))
            st = NumberStepper(card, app, None, pal["card"], chips=False, get=lambda l=loc: self._stars(l),
                               put=lambda n, l=loc: app.run_ops(lambda h, s, grp: ops.set_star_level(h, s, l, n, grp)),
                               limits=(0, 20))
            st.pack(fill="x")
            self.live.append(st)
            g.add("card", card)
        if not self.has(ops.STAR_LEVELS[:-1]):
            self.summary.configure(text=tr("loc_no_data"))

    def update_values(self, paths: list[tuple]) -> None:
        pass
