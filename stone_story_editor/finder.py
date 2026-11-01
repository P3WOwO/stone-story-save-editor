"""Best-effort automatic search for Stone Story save files."""
from __future__ import annotations

import os
import sys
import time
import threading
from pathlib import Path
from typing import Callable, Iterable

from .core import looks_like_save

_SKIP_DIRS = {"node_modules", ".git", "cache", "caches", "code cache", "gpucache", "temp", "tmp",
              "crashpad", "logs", "__pycache__", "windows", "system32"}


GAME_DIR = Path("Martian Rex, Inc_") / "Stone Story"   # official save folder (per the game's FAQ)


def candidate_roots() -> list[Path]:
    home = Path.home()
    roots: list[Path] = []
    # official locations: <root>/Martian Rex, Inc_/Stone Story/<steam id>/primary_save.txt
    if sys.platform.startswith("win"):
        roots.append(home / "AppData" / "LocalLow" / GAME_DIR)
    elif sys.platform == "darwin":
        roots.append(home / "Library" / "Application Support" / GAME_DIR)
    else:
        roots.append(home / ".local" / "share" / "Steam" / "steamapps" / "common" / "Stone Story RPG" / "saves")
    if sys.platform.startswith("win"):
        for var in ("APPDATA", "LOCALAPPDATA"):
            if os.environ.get(var):
                roots.append(Path(os.environ[var]))
        roots.append(home / "AppData" / "LocalLow")
        roots.append(home / "Documents")
        roots.append(home / "Saved Games")
        for pf in (os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles")):
            if pf:
                roots.append(Path(pf) / "Steam" / "steamapps" / "common")
                roots.append(Path(pf) / "Steam" / "userdata")
    elif sys.platform == "darwin":
        roots += [home / "Library" / "Application Support", home / "Documents",
                  home / "Library" / "Containers"]
    else:
        roots += [home / ".config", home / ".local" / "share", home / "Documents",
                  home / ".steam" / "steam" / "steamapps" / "common"]
    out, seen = [], set()
    for r in roots:
        if r.exists() and str(r) not in seen:
            seen.add(str(r))
            out.append(r)
    return out


def _name_ok(name: str) -> bool:
    low = name.lower()
    return low.endswith(".txt") and any(w in low for w in ("save", "primary", "backup", "historical"))


def find_saves(stop: threading.Event, on_found: Callable[[Path], None],
               on_progress: Callable[[str], None], extra_roots: Iterable[Path] = (),
               max_depth: int = 6, time_limit: float = 45.0) -> None:
    """Walk likely folders and report every file that looks like a save."""
    started = time.monotonic()
    seen: set[str] = set()
    roots = list(extra_roots) + candidate_roots()
    for root in roots:
        base_depth = len(root.parts)
        for dirpath, dirnames, filenames in os.walk(root):
            if stop.is_set() or time.monotonic() - started > time_limit:
                return
            depth = len(Path(dirpath).parts) - base_depth
            if depth >= max_depth:
                dirnames[:] = []
            else:
                dirnames[:] = [d for d in dirnames if d.lower() not in _SKIP_DIRS]
            on_progress(dirpath)
            for fn in filenames:
                if _name_ok(fn):
                    p = Path(dirpath) / fn
                    key = str(p).lower()
                    if key not in seen and looks_like_save(p):
                        seen.add(key)
                        on_found(p)
