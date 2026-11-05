# Changelog

## 2.2.0
- **Home screen** with tiles for Inventory, Resources, Cosmetics, Player, Quests, Events, Progress, Locations, Catalogue.
- **Item catalogue** (58 real items): search, categories, subcategories, IDs with their source, descriptions, recipes.
- **Add-item wizard**: find by name, amount, stars, shiny, element, enchantment; structure copied from your own items; no JSON/IDs needed.
- **Inventory** rewritten for the real item layout (`id` / `co` / `da`): type, element, stars and enchantment tier are separate chips and filters.
- **Section pages** for Player, Resources, Cosmetics (golden / glitch / prismatic + colours), Quests, Progress (locations, workbench, projects, legends), Locations (stars) and Events (premium pass `pp`, track points, tasks).
- **Explanations ("?")** for known fields; unknown fields are never guessed. Value-range warnings (level 0-60, stars 0-10, enchantment +1...+21).
- **Change preview** before bulk edits: old / new values and affected count.
- Undo groups for add / delete, new `ops.py`, `catalog.py`, `knowledge.py`; GUI smoke tests run in CI under xvfb.
- Auto-search also finds the game's official save folders.

## 2.1.0
- **Sections sidebar** (Inventory, Events & pass, Player, Resources, Quests, Progress, Locations, Cosmetics, Time, Other).
- **Inventory manager**: item cards with +/- amount, tick boxes, stars/enchant fields, add / duplicate / delete, bulk change, clear.
- **Events & premium pass**: premium (`pp`) switch per event, "give premium everywhere", points/levels for all events.
- Auto-search now checks the game's official save folders first (`Martian Rex, Inc_/Stone Story`), also finds `backup.txt` / `historical_#`.
- Fixed headings/fonts, icon matching is word-based.

## 2.0.0
- Completely new interface: welcome screen, light/dark theme, Russian/English.
- **Cards view**: every value is a card with an icon, `-` / `+` buttons, quick-add chips and Yes/No switches.
- Classic **list view** kept, with an edit panel, search, filters and multi-select bulk edit.
- Undo / redo (Ctrl+Z / Ctrl+Y), "Changes" tab with per-change restore.
- "Find my save automatically", recent files, restore from backup.
- Code split into modules (`core`, `gui`, `i18n`, ...) and unit tests added.

## 1.0.0
- First version: generic tree editor for decrypted saves.
