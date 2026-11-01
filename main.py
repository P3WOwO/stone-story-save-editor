#!/usr/bin/env python3
"""Convenience launcher:  python main.py [save.txt]"""
import sys

from stone_story_editor.gui import run

if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else None)
