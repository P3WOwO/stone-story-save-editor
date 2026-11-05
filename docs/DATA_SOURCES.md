# Data sources & accuracy / Источники данных и точность

The editor never invents game data. Everything below comes from the sources listed here; when a source says
nothing, the editor shows "not described" or leaves the value unknown.
Редактор не выдумывает игровые данные: всё взято из перечисленных источников, а где источники молчат,
значение остаётся неизвестным.

## Where each kind of data comes from

| Data | Source |
|------|--------|
| Save layout (`progress_data.inventory_data.itms`, `events`, `cosmetics`, `quest_data` ...) | structure documented by the SSRPGS project (reference only; no code copied) |
| Names of locations, legends, projects, workbench, cosmetics (EN/RU) | the game's own localisation as published by SSRPGS |
| Item names, categories, recipes, descriptions | community wiki (Items, Basic Recipes, Runestone Crafting, Enchanting) |
| Item **IDs** | wiki "Stonescript ID" field (`W`) and SSRPGS cosmetics keys (`S`); `WS` = both agree |
| Star level 0-10, enchantment +1...+21 and colours, level 0-60, save folders | game FAQ and wiki Glossary / Enchantments |
| Premium pass (`pp`), 35 points per track (50 in Green Part 1 & 2), 30 Event Tickets | wiki Events + SSRPGS field names |

## Game version

Encryption and decryption of saves are confirmed to work with the current game release. Item and field data come from
the sources above and may lag behind new game content.

## What is deliberately unknown

* Items without a confirmed ID (shown grey in the catalogue, ID `—`) cannot be added from the catalogue.
  Add them by duplicating an item you already own, or by ID in the expert dialog.
* Meaning of `hI`, `sh`, `tag`, `sig`, `abs`, `rng`, `lC`, `lBU`, `ql` is only described as far as the sources go.
* Values of the element field (`da.el`) are offered only from your own items.
* The exact link between enchantment level and quality (`ql`) is not described; the editor copies real
  enchantments from your save or uses the +21 example SSRPGS itself uses.
* Quest names are not in the sources; their IDs are shown.

Found something wrong or have a real ID? Open an issue ("Real key names") or edit `stone_story_editor/catalog.py`.
