"""Light / dark colour palettes and ttk styling."""
from __future__ import annotations

import sys
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

PALETTES = {
    "light": dict(
        bg="#f4f6fa", card="#ffffff", border="#dde3ee", text="#1d2433", muted="#6b7488",
        accent="#3b6cf6", accent_fg="#ffffff", accent_hover="#2f58cf",
        soft="#e8eefe", ok="#1f9d57", warn="#c77d00", danger="#d64545",
        row_alt="#f8faff", changed="#fff3cd", select="#cfdcff", select_fg="#10204d",
        input="#ffffff", header="#eef2f9",
    ),
    "dark": dict(
        bg="#171a21", card="#20242e", border="#323847", text="#e6e9f0", muted="#8f98ad",
        accent="#5b8cff", accent_fg="#0c1020", accent_hover="#7aa0ff",
        soft="#27304a", ok="#48c78e", warn="#f0b441", danger="#ff6b6b",
        row_alt="#232835", changed="#4a3d12", select="#33457a", select_fg="#ffffff",
        input="#171a21", header="#262b38",
    ),
}


_FONTS: dict = {}   # keep references: a garbage-collected Font deletes the named font


def _named_font(root: tk.Misc, name: str, **kw) -> None:
    font = _FONTS.get(name)
    try:
        if font is None:
            raise KeyError(name)
        font.configure(**kw)
    except (KeyError, tk.TclError):
        _FONTS[name] = tkfont.Font(root=root, name=name, **kw)


def ui_font_family(root: tk.Misc) -> str:
    available = set(tkfont.families(root))
    for name in ("Segoe UI", "SF Pro Text", "Helvetica Neue", "Ubuntu", "Noto Sans", "DejaVu Sans"):
        if name in available:
            return name
    return "TkDefaultFont"


def apply(root: tk.Tk, mode: str) -> dict:
    """Configure ttk styles for the given mode and return the palette."""
    p = PALETTES[mode]
    family = ui_font_family(root)
    base = 10 if sys.platform != "darwin" else 12
    for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
        try:
            tkfont.nametofont(name).configure(family=family, size=base)
        except tk.TclError:
            pass
    for fname, size, weight in (("SSEEntry", base + 3, "normal"), ("SSEHero", base + 14, "bold"),
                                ("SSEBold", base + 1, "bold"), ("SSESmall", base - 1, "normal"),
                                ("SSEIcon", base + 4, "bold")):
        _named_font(root, fname, family=family, size=size, weight=weight)
    root.configure(bg=p["bg"])
    root.option_add("*TCombobox*Listbox.background", p["input"])
    root.option_add("*TCombobox*Listbox.foreground", p["text"])
    root.option_add("*TCombobox*Listbox.selectBackground", p["select"])
    root.option_add("*TCombobox*Listbox.selectForeground", p["select_fg"])

    st = ttk.Style(root)
    try:
        st.theme_use("clam")
    except tk.TclError:
        pass
    st.configure(".", background=p["bg"], foreground=p["text"], fieldbackground=p["input"],
                 bordercolor=p["border"], lightcolor=p["bg"], darkcolor=p["bg"],
                 troughcolor=p["header"], focuscolor=p["accent"], font=(family, base))
    st.configure("TFrame", background=p["bg"])
    st.configure("Card.TFrame", background=p["card"], bordercolor=p["border"], relief="solid", borderwidth=1)
    st.configure("Soft.TFrame", background=p["soft"])
    st.configure("Inner.TFrame", background=p["card"])
    st.configure("TLabel", background=p["bg"], foreground=p["text"])
    st.configure("Card.TLabel", background=p["card"], foreground=p["text"])
    st.configure("Soft.TLabel", background=p["soft"], foreground=p["text"])
    st.configure("Muted.TLabel", background=p["bg"], foreground=p["muted"])
    st.configure("CardMuted.TLabel", background=p["card"], foreground=p["muted"])
    st.configure("Title.TLabel", background=p["bg"], foreground=p["text"], font=(family, base + 10, "bold"))
    st.configure("H1.TLabel", background=p["card"], foreground=p["text"], font=(family, base + 3, "bold"))
    st.configure("H2.TLabel", background=p["card"], foreground=p["text"], font=(family, base + 1, "bold"))
    st.configure("Big.TLabel", background=p["card"], foreground=p["text"], font=(family, base + 8, "bold"))
    st.configure("Step.TLabel", background=p["accent"], foreground=p["accent_fg"], font=(family, base + 2, "bold"),
                 anchor="center")
    st.configure("Ok.TLabel", background=p["bg"], foreground=p["ok"])
    st.configure("Warn.TLabel", background=p["bg"], foreground=p["warn"])
    st.configure("Status.TLabel", background=p["header"], foreground=p["text"], padding=(10, 6))

    st.configure("TButton", background=p["card"], foreground=p["text"], bordercolor=p["border"],
                 padding=(12, 7), focusthickness=0, relief="flat", borderwidth=1)
    st.map("TButton", background=[("disabled", p["bg"]), ("active", p["soft"])],
           foreground=[("disabled", p["muted"])])
    st.configure("Accent.TButton", background=p["accent"], foreground=p["accent_fg"], bordercolor=p["accent"],
                 padding=(16, 9), font=(family, base, "bold"))
    st.map("Accent.TButton", background=[("disabled", p["border"]), ("active", p["accent_hover"])],
           foreground=[("disabled", p["muted"])], bordercolor=[("active", p["accent_hover"])])
    st.configure("Danger.TButton", background=p["card"], foreground=p["danger"], bordercolor=p["danger"])
    st.map("Danger.TButton", background=[("active", p["soft"])])
    st.configure("Quick.TButton", padding=(6, 5), background=p["soft"], foreground=p["text"],
                 bordercolor=p["soft"])
    st.map("Quick.TButton", background=[("active", p["select"])])
    st.configure("Tool.TButton", padding=(10, 6))
    st.configure("Big.Accent.TButton", background=p["accent"], foreground=p["accent_fg"], bordercolor=p["accent"],
                 padding=(26, 14), font=(family, base + 2, "bold"))
    st.map("Big.Accent.TButton", background=[("active", p["accent_hover"])])
    st.configure("Big.TButton", padding=(22, 12), font=(family, base + 1))

    st.configure("Chip.TRadiobutton", background=p["bg"], foreground=p["text"], padding=(12, 5),
                 indicatorsize=0, indicatormargin=0, relief="flat", borderwidth=1, bordercolor=p["border"])
    st.layout("Chip.TRadiobutton", [("Radiobutton.padding", {"sticky": "nswe", "children": [
        ("Radiobutton.label", {"sticky": "nswe"})]})])
    st.map("Chip.TRadiobutton", background=[("selected", p["accent"]), ("active", p["soft"])],
           foreground=[("selected", p["accent_fg"])])

    st.configure("Cat.TRadiobutton", background=p["card"], foreground=p["text"], padding=(12, 9),
                 indicatorsize=0, indicatormargin=0, relief="flat", anchor="w", width=24)
    st.layout("Cat.TRadiobutton", [("Radiobutton.padding", {"sticky": "nswe", "children": [
        ("Radiobutton.label", {"sticky": "nswe"})]})])
    st.map("Cat.TRadiobutton", background=[("selected", p["soft"]), ("active", p["header"])],
           foreground=[("selected", p["accent"])])

    st.configure("TEntry", fieldbackground=p["input"], foreground=p["text"], bordercolor=p["border"],
                 padding=6, insertcolor=p["text"])
    st.map("TEntry", bordercolor=[("focus", p["accent"])])
    st.configure("TCombobox", fieldbackground=p["input"], foreground=p["text"], bordercolor=p["border"],
                 arrowcolor=p["text"], padding=5, background=p["card"])
    st.map("TCombobox", fieldbackground=[("readonly", p["input"])], bordercolor=[("focus", p["accent"])])

    st.configure("Treeview", background=p["card"], fieldbackground=p["card"], foreground=p["text"],
                 rowheight=int(base * 2.6), bordercolor=p["border"], borderwidth=0)
    st.map("Treeview", background=[("selected", p["select"])], foreground=[("selected", p["select_fg"])])
    st.configure("Treeview.Heading", background=p["header"], foreground=p["muted"], relief="flat",
                 padding=(8, 7), font=(family, base, "bold"))
    st.map("Treeview.Heading", background=[("active", p["soft"])])

    st.configure("TNotebook", background=p["bg"], bordercolor=p["border"], tabmargins=(0, 4, 0, 0))
    st.configure("TNotebook.Tab", background=p["header"], foreground=p["muted"], padding=(18, 9),
                 font=(family, base, "bold"))
    st.map("TNotebook.Tab", background=[("selected", p["card"])], foreground=[("selected", p["accent"])])
    st.configure("Vertical.TScrollbar", background=p["header"], troughcolor=p["card"], bordercolor=p["card"],
                 arrowcolor=p["muted"])
    st.configure("Horizontal.TScrollbar", background=p["header"], troughcolor=p["card"], bordercolor=p["card"],
                 arrowcolor=p["muted"])
    st.configure("TSeparator", background=p["border"])
    st.configure("TCheckbutton", background=p["bg"], foreground=p["text"])
    st.configure("Card.TCheckbutton", background=p["card"], foreground=p["text"])
    return p
