# Contributing / Как помочь

**Most useful contribution:** real key names from the game's save (see the *Real key names* issue form), then
add them to the `RULES` table in `stone_story_editor/sections.py`.

```bash
pip install -r requirements-dev.txt
python -m pytest
python tests/sample_save.py demo_save.txt   # fake save for trying the UI
python -m stone_story_editor demo_save.txt
```

- Every user-visible text goes into `stone_story_editor/i18n.py` in **both** `ru` and `en` (a test checks this).
- Keep GUI code in `gui.py`/`views.py`/`cards.py` and logic in `core.py`/`sections.py` so it stays testable.
- Never commit real saves (`primary_save.txt`, `*.bak`) – `.gitignore` already blocks them.
