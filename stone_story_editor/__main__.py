"""Run with:  python -m stone_story_editor [path-to-save.txt]"""
import sys

from .gui import run

if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else None)
