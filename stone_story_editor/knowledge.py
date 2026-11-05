"""What is known about Stone Story RPG save fields.

Everything here comes from published sources (the game's FAQ and Stonescript manual, the community wiki,
and the structure documented by the SSRPGS project). Where the sources say nothing about a field the
editor shows "not described" instead of guessing.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from . import knowledge_data as kd
from .i18n import current_language

# --------------------------------------------------------------------------
# fixed facts (wiki / FAQ / Glossary)
# --------------------------------------------------------------------------
STAR_MAX = 10          # star level 0-10 (or MAX)                         [FAQ, wiki Glossary]
ENCHANT_MAX = 21       # enchantment +1 ... +21                           [FAQ, wiki Enchantments]
LEVEL_MAX = 60         # character level 0-60                             [wiki Glossary]

# (from level, to level, English name, Russian name, English colour, Russian colour)     [wiki Enchantments]
ENCHANT_TIERS = [
    (1, 1, "Common", "Обычное", "Cyan", "Бирюзовый"),
    (2, 3, "Rare", "Редкое", "Yellow", "Жёлтый"),
    (4, 6, "Heroic", "Героическое", "Green", "Зелёный"),
    (7, 10, "Epic", "Эпическое", "Blue", "Синий"),
    (11, 15, "Legendary", "Легендарное", "Red", "Красный"),
    (16, 21, "Transcendent", "Трансцендентное", "Rainbow", "Радужный"),
]
ENCHANT_COLORS = {"Cyan": "#18b8c9", "Yellow": "#e0b000", "Green": "#2fa84f", "Blue": "#3b6cf6",
                  "Red": "#d64545", "Rainbow": "#a855f7"}

# resources stored in progress_data.inventory_data: key -> (en, ru, symbol, where found en, where found ru)
RESOURCES = [
    ("Stone", "Stone", "Камни", "o", "Rocky Plateau", "Каменистое плато"),
    ("Wood", "Wood", "Дерево", "_/`", "Deadwood Canyon", "Каньон Дедвуд"),
    ("Tar", "Tar", "Смола", "≈", "Caves of Fear", "Пещеры страха"),
    ("Xi", "Ki", "Ки", "@", "Enemy kills", "Победы над врагами"),
    ("Bronze", "Bronze", "Бронза", ":.", "Boiling Mine", "Бурлящая шахта"),
]

# locations whose star level can be edited (SSRPGS) -> star colours  [en.json locations_list_info]
FARM_LOCATIONS = ["rocky_plateau", "deadwood_valley", "caustic_caves", "fungus_forest", "undead_crypt",
                  "bronze_mine", "icy_ridge", "temple"]


def lang() -> str:
    return current_language()


def pick(en: str, ru: str) -> str:
    return ru if lang() == "ru" else en


def enchant_tier(level: int) -> tuple[str, str, str] | None:
    """(tier name, colour name, colour hex) for an enchantment level, or None when out of range."""
    for lo, hi, en, ru, cen, cru in ENCHANT_TIERS:
        if lo <= level <= hi:
            return pick(en, ru), pick(cen, cru), ENCHANT_COLORS[cen]
    return None


# --------------------------------------------------------------------------
# id -> name tables
# --------------------------------------------------------------------------
def _names(table) -> dict[str, tuple[str, str]]:
    return {row[0]: (row[-2], row[-1]) for row in table}


_LOC = _names(kd.LOCATIONS)
_LEG = _names(kd.LEGENDS)
_WB = _names(kd.WORKBENCH)
_PRJ = _names(kd.PROJECTS)
_COS = {ck: (en, ru) for ck, _tk, en, ru in kd.COSMETICS}
_RES = {k: (en, ru) for k, en, ru, *_ in RESOURCES}
_ALL_IDS = {**_LOC, **_LEG, **_WB, **_PRJ}


def id_name(game_id: str) -> str | None:
    """Readable name of a location / legend / project / workbench id, or None if unknown."""
    pair = _ALL_IDS.get(game_id)
    return pick(*pair) if pair else None


def cosmetic_name(cosmetic_key: str) -> str | None:
    pair = _COS.get(cosmetic_key)
    return pick(*pair) if pair else None


def resource_name(key: str) -> str | None:
    pair = _RES.get(key)
    return pick(*pair) if pair else None


# --------------------------------------------------------------------------
# field explanations
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Info:
    name_en: str
    name_ru: str
    hint_en: str
    hint_ru: str

    @property
    def name(self) -> str:
        return pick(self.name_en, self.name_ru)

    @property
    def hint(self) -> str:
        return pick(self.hint_en, self.hint_ru)


NOT_DESCRIBED_EN = "The meaning of this field is not described in the public sources, so the editor does not guess."
NOT_DESCRIBED_RU = "Значение этого поля не описано в открытых источниках, поэтому редактор его не угадывает."


def not_described() -> str:
    return pick(NOT_DESCRIBED_EN, NOT_DESCRIBED_RU)


def _I(name_en, name_ru, hint_en, hint_ru) -> Info:
    return Info(name_en, name_ru, hint_en, hint_ru)


# patterns are written relative to progress_data; "*" matches any key / list index
_ITEM = ("inventory_data", "itms", "*")
KEY_INFO: list[tuple[tuple, Info]] = [
    (("hero_settings", "playerName"), _I(
        "Player name", "Имя игрока",
        "The hero's name. It is stored in two places in the save; the editor changes both.",
        "Имя героя. В сейве оно хранится в двух местах; редактор меняет оба.")),
    (("xp", "currentLevel"), _I(
        "Player level", "Уровень игрока",
        "Character level, 0-60. Each level adds 1 maximum health and raises the treasure chest limit by 5 "
        "(limit = 100 + 5 x level).",
        "Уровень персонажа, 0-60. Каждый уровень даёт +1 к максимуму здоровья и +5 к лимиту сундуков "
        "(лимит = 100 + 5 × уровень).")),
    (("xp", "currentXP"), _I(
        "Experience (XP)", "Опыт (XP)",
        "Reward for defeating foes; it raises the character level. Which XP value matches which level is not "
        "described in the sources.",
        "Награда за победу над врагами, повышает уровень персонажа. Какое число XP соответствует какому уровню "
        "— в источниках не описано.")),
    (("inventory_data", "Stone"), _I("Stone", "Камни", "Resource found in Rocky Plateau. Used to craft items and "
                                    "for story projects.",
                                    "Ресурс из Каменистого плато. Идёт на создание предметов и проекты истории.")),
    (("inventory_data", "Wood"), _I("Wood", "Дерево", "Resource found in Deadwood Canyon.",
                                    "Ресурс из Каньона Дедвуд.")),
    (("inventory_data", "Tar"), _I("Tar", "Смола", "Resource found in the Caves of Fear.",
                                   "Ресурс из Пещер страха.")),
    (("inventory_data", "Xi"), _I("Ki", "Ки", "Resource gained from enemy kills. (Stored under the key \"Xi\".)",
                                  "Ресурс, который выпадает за победы над врагами. (В сейве хранится под ключом "
                                  "«Xi».)")),
    (("inventory_data", "Bronze"), _I("Bronze", "Бронза", "Resource found in the Boiling Mine.",
                                      "Ресурс из Бурлящей шахты.")),
    (("inventory_data", "itms"), _I("Items", "Предметы", "The list of every item in your inventory.",
                                    "Список всех предметов вашего инвентаря.")),
    (_ITEM + ("id",), _I("Item ID", "ID предмета", "The internal identifier of the item (Stonescript ID).",
                         "Внутренний идентификатор предмета (Stonescript ID).")),
    (_ITEM + ("co",), _I("Count", "Количество", "How many copies of this exact item you have.",
                         "Сколько копий именно этого предмета у вас есть.")),
    (_ITEM + ("da",), _I("Item data", "Данные предмета", "Parameters of the item: level, enchantments, element...",
                         "Параметры предмета: уровень, зачарования, стихия...")),
    (_ITEM + ("da", "hI"), _I(
        "Has interacted", "Просмотрен игроком",
        "Flag \"has interacted\". SSRPGS' \"Mark all\" button sets it to True for every item; what exactly it "
        "changes in the game is not described.",
        "Флаг «взаимодействовал» (has interacted). Кнопка «Mark all» в SSRPGS ставит его всем предметам; что "
        "именно он меняет в игре — не описано.")),
    (_ITEM + ("da", "sh"), _I(
        "Shiny", "Блёстки (Shiny)",
        "Marks the item as shiny. Stonescript can search items by the word \"shiny\". What exactly it changes is "
        "not described in the sources.",
        "Отметка «shiny». Stonescript умеет искать предметы по слову shiny. Что именно она меняет — в источниках "
        "не описано.")),
    (_ITEM + ("da", "lv"), _I(
        "Star level", "Уровень (звёзды)",
        "Item level (stars). Equipment goes from 0 to 10 stars (MAX). Enchantments add on top of stars.",
        "Уровень предмета (звёзды). У экипировки от 0 до 10 звёзд (MAX). Зачарования добавляются сверх звёзд.")),
    (_ITEM + ("da", "el"), _I(
        "Element", "Стихия",
        "Element of the item. The editor offers the values it finds in your own items; the full list of values is "
        "not given in the sources.",
        "Стихия предмета. Редактор предлагает значения, которые нашёл у ваших предметов; полный список значений "
        "в источниках не приведён.")),
    (_ITEM + ("da", "ra"), _I(
        "Enchantment", "Зачарование",
        "An enchantment boosts one stat of the item. Level +1...+21; colours: cyan +1, yellow +2-3, green +4-6, "
        "blue +7-10, red +11-15, rainbow +16-21.",
        "Зачарование усиливает одну характеристику предмета. Уровень +1…+21; цвета: бирюзовый +1, жёлтый +2-3, "
        "зелёный +4-6, синий +7-10, красный +11-15, радужный +16-21.")),
    (_ITEM + ("da", "ra", "lv"), _I("Enchantment level", "Уровень зачарования",
                                    "From +1 to +21. A higher value means a bigger stat boost.",
                                    "От +1 до +21. Чем выше, тем сильнее прибавка к характеристике.")),
    (_ITEM + ("da", "ra", "ql"), _I(
        "Enchantment quality", "Качество зачарования",
        "An internal value; the FAQ says the colour reflects the enchantment's \"quality\". The exact link to the "
        "level is not described. (SSRPGS uses 12049 for a +21 enchantment.)",
        "Внутренняя величина; по FAQ цвет зачарования отражает его «качество». Точная связь с уровнем не описана. "
        "(SSRPGS для зачарования +21 использует 12049.)")),
    (_ITEM + ("da", "ra", "sSS"), _I(
        "Enchantment seed", "Сид зачарования",
        "The seed decides which stat the enchantment boosts (wiki).",
        "Сид определяет, какую именно характеристику усиливает зачарование (вики).")),
    (_ITEM + ("da", "sra"), _I(
        "Second enchantment", "Второе зачарование",
        "Double enchantments boost two stats. The wiki says the first must be at least +16 (transcendent) and a "
        "Moonbloom is needed to create one.",
        "Двойные зачарования усиливают две характеристики. По вики первое зачарование должно быть не ниже +16 "
        "(трансцендентное), а для создания нужен Moonbloom.")),
    (_ITEM + ("da", "lC"), _I(
        "Lost items: elements", "Lost-предметы: стихии (lC)",
        "Lost items (Bashing Shield, Blade of the Fallen God, Skeleton Arm, Cultist Mask, talismans) are found one "
        "copy at a time; a counter such as [4/8] grows as you collect copies. The sources only name this field "
        "\"Lost elements\".",
        "Lost-предметы (Bashing Shield, Blade of the Fallen God, Skeleton Arm, Cultist Mask, талисманы) "
        "находят по одной копии; счётчик вида [4/8] растёт по мере сбора. Это поле в источниках названо лишь "
        "«Lost elements».")),
    (_ITEM + ("da", "lBU"), _I(
        "Lost items: upgrades", "Lost-предметы: улучшения (lBU)",
        "Related to the upgrades of Lost items (see Lost items). The sources only name this field \"Upgrades\".",
        "Связано с улучшениями Lost-предметов. В источниках это поле названо лишь «Upgrades».")),
    (_ITEM + ("da", "tag"), _I("Tag", "Тег", "A text tag of the item. " + NOT_DESCRIBED_EN,
                               "Текстовая метка предмета. " + NOT_DESCRIBED_RU)),
    (_ITEM + ("da", "sig"), _I("Signature", "Сигнатура", "A text signature of the item. " + NOT_DESCRIBED_EN,
                               "Текстовая подпись предмета. " + NOT_DESCRIBED_RU)),
    (_ITEM + ("da", "c"), _I("Item cosmetics", "Косметика предмета", "Cosmetic look of the item. " + NOT_DESCRIBED_EN,
                             "Внешний вид предмета. " + NOT_DESCRIBED_RU)),
    (_ITEM + ("da", "abs"), _I("Effects", "Эффекты", "A list of effect names. " + NOT_DESCRIBED_EN,
                               "Список названий эффектов. " + NOT_DESCRIBED_RU)),
    (_ITEM + ("da", "rng"), _I("Random seed", "Случайный сид", "Seed used by the game's random generator for this "
                               "item. " + NOT_DESCRIBED_EN, "Сид генератора случайных чисел для предмета. "
                               + NOT_DESCRIBED_RU)),
    (("events", "*", "pp"), _I(
        "Premium pass", "Премиум-пропуск (pp)",
        "Unlocks the premium reward track of the event. In the game it is granted by a subscription or for 30 "
        "Event Tickets.",
        "Открывает премиум-дорожку наград события. В игре её дают за подписку или за 30 Event Tickets.")),
    (("events", "*", "rwds", "rp"), _I(
        "Track points (rp)", "Очки дорожки (rp)",
        "Reward points of the event track. SSRPGS labels this field \"Tasks completed\". Most events need 35 points "
        "for the whole track (50 in Green Part 1 and 2).",
        "Очки дорожки наград события. В SSRPGS поле подписано «Tasks completed». Для всей дорожки обычно нужно "
        "35 очков (в Green Part 1 и 2 — 50).")),
    (("events", "*", "objs", "*", "p"), _I("Task progress", "Прогресс задания", "Progress of one event task.",
                                           "Прогресс одного задания события.")),
    (("events", "sIds"), _I("Event ids", "ID событий", "The ids of the events found in the save.",
                            "Идентификаторы событий, которые есть в сейве.")),
    (("custom_quests", "nextSpawnDate"), _I("Next legend date", "Дата следующей легенды",
                                            "When the next Legend quest appears (a date string as stored in the "
                                            "save). Change it carefully.",
                                            "Когда появится следующая легенда (дата в том виде, как она лежит в "
                                            "сейве). Меняйте аккуратно.")),
    (("custom_quests", "epicSpawnPending"), _I("Legend spawn pending", "Появление легенды отложено",
                                               "Flag \"legend spawn pending\".", "Флаг «появление легенды отложено».")),
    (("custom_quests", "basicQuestDate"), _I("Basic quest date", "Дата базового квеста",
                                             "Date of the basic quest (a date string as stored in the save).",
                                             "Дата базового квеста (строка с датой, как в сейве).")),
    (("custom_quests", "active"), _I("Daily quests", "Ежедневные квесты", "The currently active custom quests.",
                                     "Сейчас активные квесты.")),
    (("custom_quests", "revealed"), _I("Opened legends", "Открытые легенды", "Legends that are unlocked.",
                                       "Легенды, которые открыты.")),
    (("weekly_quest", "activeQuest", "completed"), _I("Weekly quest done", "Еженедельный квест выполнен",
                                                      "Marks the weekly quest as completed.",
                                                      "Отмечает еженедельный квест выполненным.")),
    (("quest_data", "available"), _I("Unlocked locations, workbench and projects", "Открытые локации, верстак и проекты",
                                     "Ids of the locations, workbench functions and projects that are unlocked.",
                                     "Идентификаторы открытых локаций, функций верстака и проектов.")),
    (("quest_data", "star_levels"), _I(
        "Location stars", "Звёзды локаций",
        "Stars of each location: 1-5 white, 6-10 cyan, 11-15 yellow, 16-20 green. The maximum available level "
        "depends on the level of the Star Stone.",
        "Звёзды локаций: 1-5 белый, 6-10 бирюзовый, 11-15 жёлтый, 16-20 зелёный. Максимальный доступный уровень "
        "зависит от уровня Камня Звезды.")),
    (("quest_data", "lastRewardTime"), _I(
        "Last reward time", "Время последней награды",
        "If an offline farm started before this time, the player does not receive any chests (SSRPGS note).",
        "Если офлайн-ферма началась раньше этого времени, игрок не получит сундуков (примечание SSRPGS).")),
    (("treasure_factory", "*"), _I("Treasure factory date", "Дата фабрики сокровищ",
                                   "A date of the treasure factory (unique / crystal / gold). A date string as "
                                   "stored in the save.",
                                   "Дата фабрики сокровищ (unique / crystal / gold), строка с датой как в сейве.")),
    (("cosmetics", "golden"), _I("Golden skins", "Золотые скины", "Golden skins you own.", "Золотые скины, которые у вас есть.")),
    (("cosmetics", "glitch"), _I("Glitch skins", "Glitch-скины", "Glitch skins you own.", "Glitch-скины, которые у вас есть.")),
    (("cosmetics", "prismatic"), _I("Prismatic skins", "Призматические скины",
                                    "Prismatic skins you own; each has its own colour.",
                                    "Призматические скины, которые у вас есть; у каждого свой цвет.")),
]


def _strip(path: tuple) -> tuple:
    return path[1:] if path and path[0] == "progress_data" else path


def _match(pattern: tuple, path: tuple) -> bool:
    if len(pattern) != len(path):
        return False
    return all(p == "*" or p == q for p, q in zip(pattern, path))


def info(path: tuple) -> Info | None:
    """Explanation for a save path, or None when nothing is known about it."""
    rel = _strip(tuple(path))
    for pattern, inf in KEY_INFO:
        if _match(pattern, rel):
            return inf
    return None


def label(path: tuple) -> str | None:
    """Friendly name for a path (known fields, resources, location/legend ids), else None."""
    inf = info(path)
    if inf:
        return inf.name
    if path:
        last = path[-1]
        if isinstance(last, str):
            return id_name(last)
    return None


def hint_for(path: tuple) -> str | None:
    inf = info(path)
    return inf.hint if inf else None
