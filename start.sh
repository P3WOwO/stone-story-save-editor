#!/usr/bin/env bash
# Linux / macOS launcher.  Needs Python 3.10+ with tkinter (Linux: sudo apt install python3-tk)
cd "$(dirname "$0")" || exit 1
if [ ! -d .venv ]; then
  python3 -m venv .venv || exit 1
fi
.venv/bin/python -m pip install -q -r requirements.txt || exit 1
exec .venv/bin/python -m stone_story_editor "$@"
