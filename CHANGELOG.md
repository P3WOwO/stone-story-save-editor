# Changelog

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
