"""Reusable widgets and dialogs."""
from __future__ import annotations

import json
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox
from typing import Any, Callable

from . import core, finder
from .i18n import tr


class Tooltip:
    """Small hover hint. `text` may be a string or a zero-arg callable."""

    def __init__(self, widget: tk.Misc, text, palette: dict):
        self.widget, self.text, self.p = widget, text, palette
        self.tip: tk.Toplevel | None = None
        self.job = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, _e=None):
        self._hide()
        self.job = self.widget.after(450, self._show)

    def _show(self):
        text = self.text() if callable(self.text) else self.text
        if not text:
            return
        x = self.widget.winfo_rootx() + 8
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self.tip = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tk.Label(tw, text=text, justify="left", bg=self.p["text"], fg=self.p["card"],
                 padx=9, pady=5, wraplength=320).pack()

    def _hide(self, _e=None):
        if self.job:
            self.widget.after_cancel(self.job)
            self.job = None
        if self.tip:
            self.tip.destroy()
            self.tip = None


def center_on(win: tk.Toplevel, parent: tk.Misc) -> None:
    win.update_idletasks()
    w, h = win.winfo_width(), win.winfo_height()
    x = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
    y = parent.winfo_rooty() + (parent.winfo_height() - h) // 3
    win.geometry(f"+{max(0, x)}+{max(0, y)}")


class BaseDialog(tk.Toplevel):
    def __init__(self, parent: tk.Misc, title: str, palette: dict, size: str | None = None):
        super().__init__(parent)
        self.p = palette
        self.title(title)
        self.configure(bg=palette["bg"])
        self.transient(parent)
        self.parent = parent
        if size:
            self.geometry(size)
        self.bind("<Escape>", lambda _e: self.destroy())

    def present(self) -> None:
        center_on(self, self.parent)
        self.grab_set()
        self.focus_set()


# --------------------------------------------------------------------------
class ValueDialog(BaseDialog):
    """Add / edit any value. For objects with `ask_name` the key name is requested too."""

    KINDS = ["text", "number", "bool", "null", "object", "array"]

    def __init__(self, parent, title: str, palette: dict, value: Any = "", ask_name: bool = False,
                 allow_kind_change: bool = True, hint: str = ""):
        super().__init__(parent, title, palette, "640x500")
        self.minsize(520, 400)
        self.accepted = False
        self.name: str | None = None
        self.result: Any = None
        self._ask_name = ask_name
        pad = dict(padx=18)
        ttk.Label(self, text=title, style="Title.TLabel").pack(anchor="w", padx=18, pady=(16, 4))
        if hint:
            ttk.Label(self, text=hint, style="Muted.TLabel", wraplength=580, justify="left").pack(anchor="w", **pad)
        if ask_name:
            ttk.Label(self, text=tr("dlg_field_name")).pack(anchor="w", padx=18, pady=(12, 2))
            self.name_var = tk.StringVar()
            e = ttk.Entry(self, textvariable=self.name_var)
            e.pack(fill="x", **pad)
            e.focus_set()
        self.kind_var = tk.StringVar(value=core.kind_of(value) if value != "" else "text")
        row = ttk.Frame(self)
        row.pack(fill="x", padx=18, pady=(12, 2))
        ttk.Label(row, text=tr("dlg_type")).pack(side="left")
        self.kind_box = ttk.Combobox(row, state="readonly" if allow_kind_change else "disabled", width=22,
                                     values=[tr("kind_" + k) for k in self.KINDS])
        self.kind_box.current(self.KINDS.index(self.kind_var.get()))
        self.kind_box.pack(side="left", padx=10)
        ttk.Label(self, text=tr("dlg_value_help"), style="Muted.TLabel").pack(anchor="w", padx=18, pady=(8, 2))
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True, padx=18, pady=(0, 8))
        self.text = tk.Text(frame, wrap="none", height=10, undo=True, bg=palette["input"], fg=palette["text"],
                            insertbackground=palette["text"], relief="solid", bd=1, highlightthickness=0,
                            font="TkFixedFont")
        ys = ttk.Scrollbar(frame, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=ys.set)
        self.text.pack(side="left", fill="both", expand=True)
        ys.pack(side="right", fill="y")
        if isinstance(value, (dict, list)):
            initial = json.dumps(value, ensure_ascii=False, indent=2)
        elif isinstance(value, bool):
            initial = "true" if value else "false"
        elif value is None:
            initial = "null"
        else:
            initial = str(value)
        self.text.insert("1.0", initial)
        btns = ttk.Frame(self)
        btns.pack(fill="x", padx=18, pady=(0, 16))
        ttk.Button(btns, text=tr("cancel"), command=self.destroy).pack(side="right")
        ttk.Button(btns, text=tr("apply"), style="Accent.TButton", command=self._apply).pack(side="right", padx=(0, 8))
        self.bind("<Control-Return>", lambda _e: self._apply())
        if not ask_name:
            self.text.focus_set()
        self.present()

    def _apply(self) -> None:
        kind = self.KINDS[self.kind_box.current()]
        raw = self.text.get("1.0", "end-1c")
        try:
            if kind == "null":
                result = None
            else:
                result = core.parse_typed(kind, raw)
        except json.JSONDecodeError as exc:
            messagebox.showerror(tr("err_bad_value"), tr("err_bad_json", err=str(exc)), parent=self)
            return
        except ValueError:
            messagebox.showerror(tr("err_bad_value"), tr("err_bad_for_kind", kind=tr("kind_" + kind)), parent=self)
            return
        if self._ask_name:
            name = self.name_var.get().strip()
            if not name:
                messagebox.showerror(tr("err_bad_value"), tr("err_empty_name"), parent=self)
                return
            self.name = name
        self.result = result
        self.accepted = True
        self.destroy()


# --------------------------------------------------------------------------
class TextDialog(BaseDialog):
    """Scrollable read-only text with simple headings (used for the help window)."""

    def __init__(self, parent, title: str, palette: dict, sections: list[tuple[str, str]]):
        super().__init__(parent, title, palette, "720x640")
        self.minsize(520, 420)
        frame = ttk.Frame(self, padding=(18, 14, 18, 0))
        frame.pack(fill="both", expand=True)
        txt = tk.Text(frame, wrap="word", bg=palette["bg"], fg=palette["text"], relief="flat", bd=0,
                      highlightthickness=0, padx=4, pady=4, cursor="arrow", spacing3=4)
        ys = ttk.Scrollbar(frame, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=ys.set)
        txt.pack(side="left", fill="both", expand=True)
        ys.pack(side="right", fill="y")
        txt.tag_configure("h", font=("TkDefaultFont", 13, "bold"), foreground=palette["accent"],
                          spacing1=14, spacing3=4)
        for head, body in sections:
            txt.insert("end", head + "\n", "h")
            txt.insert("end", body.strip() + "\n")
        txt.configure(state="disabled")
        ttk.Button(self, text=tr("close"), style="Accent.TButton", command=self.destroy).pack(pady=12)
        self.present()


# --------------------------------------------------------------------------
class PickDialog(BaseDialog):
    """Pick one item from a list. `result` holds the chosen value or None."""

    def __init__(self, parent, title: str, message: str, palette: dict, items: list[tuple[str, Any]],
                 ok_text: str | None = None):
        super().__init__(parent, title, palette, "680x420")
        self.minsize(480, 300)
        self.items = items
        self.result: Any = None
        ttk.Label(self, text=message, wraplength=620, justify="left").pack(anchor="w", padx=18, pady=(16, 8))
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True, padx=18)
        self.lb = tk.Listbox(frame, activestyle="none", bg=palette["card"], fg=palette["text"], relief="solid", bd=1,
                             highlightthickness=0, selectbackground=palette["select"],
                             selectforeground=palette["select_fg"], height=8)
        ys = ttk.Scrollbar(frame, orient="vertical", command=self.lb.yview)
        self.lb.configure(yscrollcommand=ys.set)
        self.lb.pack(side="left", fill="both", expand=True)
        ys.pack(side="right", fill="y")
        for label, _v in items:
            self.lb.insert("end", "  " + label)
        if items:
            self.lb.selection_set(0)
        self.lb.bind("<Double-1>", lambda _e: self._ok())
        btns = ttk.Frame(self)
        btns.pack(fill="x", padx=18, pady=14)
        ttk.Button(btns, text=tr("cancel"), command=self.destroy).pack(side="right")
        ttk.Button(btns, text=ok_text or tr("open"), style="Accent.TButton", command=self._ok).pack(side="right", padx=8)
        self.bind("<Return>", lambda _e: self._ok())
        self.present()

    def _ok(self) -> None:
        sel = self.lb.curselection()
        if sel:
            self.result = self.items[sel[0]][1]
        self.destroy()


# --------------------------------------------------------------------------
class FinderDialog(BaseDialog):
    """Searches the computer for save files in a background thread."""

    def __init__(self, parent, palette: dict):
        super().__init__(parent, tr("find_title"), palette, "700x460")
        self.minsize(520, 340)
        self.result: Path | None = None
        self.found: list[Path] = []
        self.q: "queue.Queue[tuple[str, Any]]" = queue.Queue()
        self.stop = threading.Event()
        self.protocol("WM_DELETE_WINDOW", self._close)

        ttk.Label(self, text=tr("find_title"), style="Title.TLabel").pack(anchor="w", padx=18, pady=(16, 2))
        ttk.Label(self, text=tr("find_intro"), style="Muted.TLabel", wraplength=640,
                  justify="left").pack(anchor="w", padx=18)
        self.status = tk.StringVar(value=tr("find_searching"))
        ttk.Label(self, textvariable=self.status, style="Muted.TLabel").pack(anchor="w", padx=18, pady=(8, 4))
        self.bar = ttk.Progressbar(self, mode="indeterminate")
        self.bar.pack(fill="x", padx=18)
        self.bar.start(12)
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True, padx=18, pady=10)
        self.lb = tk.Listbox(frame, activestyle="none", bg=palette["card"], fg=palette["text"], relief="solid", bd=1,
                             highlightthickness=0, selectbackground=palette["select"],
                             selectforeground=palette["select_fg"])
        ys = ttk.Scrollbar(frame, orient="vertical", command=self.lb.yview)
        self.lb.configure(yscrollcommand=ys.set)
        self.lb.pack(side="left", fill="both", expand=True)
        ys.pack(side="right", fill="y")
        self.lb.bind("<Double-1>", lambda _e: self._ok())
        btns = ttk.Frame(self)
        btns.pack(fill="x", padx=18, pady=(0, 16))
        ttk.Button(btns, text=tr("cancel"), command=self._close).pack(side="right")
        self.ok_btn = ttk.Button(btns, text=tr("open"), style="Accent.TButton", command=self._ok)
        self.ok_btn.pack(side="right", padx=8)
        ttk.Button(btns, text=tr("find_pick_folder"), command=self._pick_folder).pack(side="left")
        self.thread: threading.Thread | None = None
        self._start([])
        self.after(120, self._poll)
        self.present()

    def _start(self, extra_roots: list[Path]) -> None:
        self.stop.set()
        self.stop = threading.Event()
        stop = self.stop

        def work():
            try:
                finder.find_saves(stop, lambda p: self.q.put(("found", p)),
                                  lambda d: self.q.put(("progress", d)), extra_roots)
            finally:
                self.q.put(("done", None))

        self.thread = threading.Thread(target=work, daemon=True)
        self.thread.start()

    def _poll(self) -> None:
        if not self.winfo_exists():
            return
        try:
            while True:
                kind, val = self.q.get_nowait()
                if kind == "found":
                    if val not in self.found:
                        self.found.append(val)
                        self.lb.insert("end", "  " + str(val))
                        if self.lb.size() == 1:
                            self.lb.selection_set(0)
                elif kind == "progress":
                    short = str(val)
                    self.status.set(tr("find_scanning", path=short if len(short) < 70 else "…" + short[-68:]))
                elif kind == "done":
                    self.bar.stop()
                    self.bar.configure(mode="determinate", value=100)
                    self.status.set(tr("find_done", n=len(self.found)) if self.found else tr("find_none"))
        except queue.Empty:
            pass
        self.after(120, self._poll)

    def _pick_folder(self) -> None:
        from tkinter import filedialog
        folder = filedialog.askdirectory(parent=self, title=tr("find_pick_folder"))
        if folder:
            self.bar.configure(mode="indeterminate")
            self.bar.start(12)
            self.status.set(tr("find_searching"))
            self._start([Path(folder)])

    def _ok(self) -> None:
        sel = self.lb.curselection()
        if sel:
            self.result = self.found[sel[0]]
            self._close()

    def _close(self) -> None:
        self.stop.set()
        self.destroy()


# --------------------------------------------------------------------------
class PreviewDialog(BaseDialog):
    """Shows old and new values (and how many parameters are affected) before a bulk change."""

    MAX_ROWS = 400

    def __init__(self, parent, title: str, palette: dict, rows: list[tuple[str, str, str]], unchanged: int = 0,
                 note: str = "", ok_text: str | None = None):
        super().__init__(parent, title, palette, "760x560")
        self.minsize(560, 380)
        self.accepted = False
        ttk.Label(self, text=title, style="Title.TLabel").pack(anchor="w", padx=18, pady=(16, 2))
        summary = tr("preview_summary", n=len(rows), same=unchanged)
        ttk.Label(self, text=summary, font="SSEBold").pack(anchor="w", padx=18)
        if note:
            ttk.Label(self, text=note, style="Muted.TLabel", wraplength=700, justify="left"
                      ).pack(anchor="w", padx=18, pady=(2, 0))
        frame = ttk.Frame(self, style="Card.TFrame")
        frame.pack(fill="both", expand=True, padx=18, pady=12)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        tree = ttk.Treeview(frame, columns=("what", "old", "new"), show="headings", selectmode="none")
        for col, w in (("what", 330), ("old", 170), ("new", 170)):
            tree.heading(col, text=tr("chg_" + col))
            tree.column(col, width=w, minwidth=80, anchor="w")
        ys = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=ys.set)
        tree.grid(row=0, column=0, sticky="nsew")
        ys.grid(row=0, column=1, sticky="ns")
        for what, old, new in rows[:self.MAX_ROWS]:
            tree.insert("", "end", values=(what, old, new))
        if len(rows) > self.MAX_ROWS:
            tree.insert("", "end", values=(tr("preview_more", n=len(rows) - self.MAX_ROWS), "", ""))
        btns = ttk.Frame(self)
        btns.pack(fill="x", padx=18, pady=(0, 16))
        ttk.Button(btns, text=tr("cancel"), command=self.destroy).pack(side="right")
        ok = ttk.Button(btns, text=ok_text or tr("preview_apply"), style="Accent.TButton", command=self._ok)
        ok.pack(side="right", padx=8)
        ok.focus_set()
        self.bind("<Return>", lambda _e: self._ok())
        self.present()

    def _ok(self) -> None:
        self.accepted = True
        self.destroy()
