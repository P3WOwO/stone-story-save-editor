"""Catalogue of real Stone Story RPG items (no GUI).

Names, categories, recipes and descriptions come from the community wiki and the game's FAQ. The `id` is
filled only when a source states it:
  "W"  - the wiki's "Stonescript ID" field of the item
  "S"  - the key used for the item in SSRPGS' cosmetics list (same identifiers as in the save)
  "WS" - both sources agree
Items without a confirmed id have `id = None`: they are listed for reference but cannot be added blindly.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from .i18n import current_language

CATEGORIES = {
    "basic": ("Basic items", "Базовые предметы"),
    "craft": ("Craftable items", "Создаваемые предметы"),
    "lost": ("Lost items", "Потерянные предметы (Lost)"),
    "other": ("Other equipment", "Другая экипировка"),
    "tools": ("Tools", "Инструменты"),
    "stones": ("Stones", "Камни"),
    "misc": ("Resources & event items", "Ресурсы и предметы событий"),
}
SUBCATEGORIES = {
    "sword": ("Swords", "Мечи"), "shield": ("Shields", "Щиты"), "crossbow": ("Crossbows", "Арбалеты"),
    "wand": ("Wands", "Жезлы"), "staff": ("Staffs", "Посохи"), "hammer": ("Hammers", "Молоты"),
    "rune": ("Runestones", "Рунные камни"), "polearm": ("Polearms", "Древковое оружие"),
    "talisman": ("Talismans", "Талисманы"), "mask": ("Masks", "Маски"), "arm": ("Arms", "Руки"),
    "tool": ("Tools", "Инструменты"), "stone": ("Stones", "Камни"), "resource": ("Resources", "Ресурсы"),
    "event": ("Event items", "Предметы событий"), "enchant": ("Enchanting", "Зачарование"),
}
SOURCE_TEXT = {
    "W": ("wiki (Stonescript ID)", "вики (Stonescript ID)"),
    "S": ("SSRPGS cosmetics list", "список косметики SSRPGS"),
    "WS": ("wiki and SSRPGS agree", "вики и SSRPGS совпадают"),
    "": ("not found in the sources", "в источниках не найден"),
}
HAND_TEXT = {"1": ("One-handed", "Одноручный"), "2": ("Two-handed", "Двуручный"),
             "R": ("Right-handed", "Правая рука"), "": ("", "")}
ELEMENT_TEXT = {"stone": ("Stone", "Камень"), "varies": ("Varies (rune)", "Зависит от рун"), "": ("", "")}


@dataclass(frozen=True)
class CatalogItem:
    key: str
    name_en: str
    name_ru: str | None
    category: str
    sub: str
    id: str | None
    id_source: str
    hand: str
    element: str
    desc_en: str
    desc_ru: str
    recipe: str
    can_stars: bool
    can_enchant: bool

    @property
    def addable(self) -> bool:
        return self.id is not None

    @property
    def name(self) -> str:
        return (self.name_ru or self.name_en) if current_language() == "ru" else self.name_en

    @property
    def description(self) -> str:
        text = self.desc_ru if current_language() == "ru" else self.desc_en
        return text

    def tr_text(self, table: dict, key: str) -> str:
        pair = table.get(key, ("", ""))
        return pair[1] if current_language() == "ru" else pair[0]


def _e(key, en, ru, cat, sub, iid=None, src="", hand="", elem="", d_en="", d_ru="", recipe="",
       stars=None, ench=None):
    equip = cat in ("basic", "craft", "lost", "other") and key != "runestone"
    return CatalogItem(key, en, ru, cat, sub, iid, src if iid else "", hand, elem, d_en, d_ru, recipe,
                       equip if stars is None else stars, equip if ench is None else ench)


ITEMS: list[CatalogItem] = [
    # ---- basic items (the six starting items) ----
    _e("sword", "Sword", "Меч", "basic", "sword", "sword", "WS", "1", "stone",
       "The main melee weapon of the game; one of the first items the player gets.",
       "Основное оружие ближнего боя; один из первых предметов игрока."),
    _e("shield", "Shield", "Щит", "basic", "shield", "shield", "WS", "R", "stone",
       "The main way to gain armor. Can be found in chests or bought at the Mushroom Shop.",
       "Главный источник брони. Находится в сундуках или покупается в Грибной лавке."),
    _e("crossbow", "Crossbow", "Арбалет", "basic", "crossbow", "crossbow", "WS", "1", "stone",
       "The ranged single-target weapon. Enchantments: damage, attack speed, crit chance / multiplier, pierce.",
       "Дальнобойное оружие по одной цели. Зачарования: урон, скорость атаки, шанс и множитель крита, пробивание."),
    _e("stone_wand", "Stone Wand", None, "basic", "wand", "wand_stone", "W", "1", "stone",
       "The ranged area-damage weapon. Used to add a socket to items (to rune them).",
       "Дальнобойное оружие с уроном по области. Нужен, чтобы добавить гнездо в предметы (для рун)."),
    _e("quarterstaff", "Quarterstaff", "Квотерстафф", "basic", "staff", "quarterstaff", "WS", "2", "stone",
       "Deals damage and gives armor. Ability: a mini-dash attack that stuns foes.",
       "Наносит урон и даёт броню. Способность: короткий рывок-атака, оглушающий врагов."),
    _e("runestone", "Runestone", None, "basic", "rune", "runestone", "W", "1", "varies",
       "Makes your weapons elemental; combined with a Stone item it makes the Rune version.",
       "Делает оружие стихийным; в сочетании с «каменным» предметом даёт рунную версию."),
    # ---- craftable: swords ----
    _e("stone_sword", "Stone Sword", None, "craft", "sword", None, "", "1", "stone",
       "Crafted from a Sword and a Stone Wand. Also found in chests in Deadwood Canyon 11-15 stars or bought at "
       "the Mushroom Shop.",
       "Создаётся из Меча и Каменного жезла. Также выпадает в сундуках Каньона Дедвуд 11-15★ и продаётся в "
       "Грибной лавке.", "Sword + Stone Wand"),
    _e("rune_sword", "Rune Sword", None, "craft", "sword", "socketed_sword", "WS", "1", "varies",
       "The runed version of the sword; the highest single-target DPS against enemies without armor.",
       "Рунная версия меча; самый высокий урон по одной цели без брони.",
       "Sword + Rune Wand  /  Stone Sword + Runestone"),
    _e("big_sword", "Big Sword", None, "craft", "sword", None, "", "1", "stone",
       "A big sword, crafted from a Sword and a Quarterstaff.",
       "Большой меч; создаётся из Меча и Квотерстаффа.", "Sword + Quarterstaff"),
    _e("big_stone_sword", "Big Stone Sword", None, "craft", "sword", "socketed_long_sword", "W", "1", "stone",
       "A big sword which has a socket. Enchantments: damage, attack speed, splash chance, +health.",
       "Большой меч с гнездом. Зачарования: урон, скорость атаки, шанс сплэша, +здоровье.",
       "Big Sword + Stone Wand"),
    _e("big_rune_sword", "Big Rune Sword", None, "craft", "sword", "socketed_long_sword", "S", "1", "varies",
       "The runed version of the Big Sword (an elemental big sword).",
       "Рунная версия большого меча (стихийный большой меч).", "Big Stone Sword + Runestone"),
    # ---- crossbows ----
    _e("heavy_crossbow", "Heavy Crossbow", None, "craft", "crossbow", None, "", "2", "stone",
       "A crafted two-handed crossbow.", "Создаваемый двуручный арбалет.", "Sword + Crossbow"),
    _e("stone_crossbow", "Stone Crossbow", None, "craft", "crossbow", None, "", "2", "stone",
       "A crafted crossbow with a socket.", "Создаваемый арбалет с гнездом.",
       "Heavy Crossbow + Stone Wand  /  Crossbow + Stone Sword"),
    _e("rune_crossbow", "Rune Crossbow", None, "craft", "crossbow", "socketed_crossbow", "WS", "2", "varies",
       "The runed version of the heavy crossbow; useful for dealing elemental damage from afar.",
       "Рунная версия тяжёлого арбалета; удобна для стихийного урона издалека.",
       "Stone Crossbow + Runestone  /  Heavy Crossbow + Rune Wand"),
    _e("repeating_crossbow", "Repeating Crossbow", "Многозарядный арбалет", "craft", "crossbow",
       "repeating_crossbow", "WS", "2", "stone",
       "Has a very fast fire rate: 10 attacks per second at max level.",
       "Очень высокая скорострельность: 10 выстрелов в секунду на максимальном уровне.",
       "Crossbow + Heavy Crossbow"),
    # ---- wands / staffs ----
    _e("rune_wand", "Rune Wand", None, "craft", "wand", "wand", "W", "1", "varies",
       "A crafted wand (Stone Wand + Runestone); ranged elemental weapon.",
       "Создаваемый жезл (Каменный жезл + Рунный камень); дальнобойное стихийное оружие.",
       "Stone Wand + Runestone"),
    _e("stone_staff", "Stone Staff", "Посох камня", "craft", "staff", "socketed_staff", "S", "2", "stone",
       "A staff with a socket.", "Посох с гнездом.", "Quarterstaff + Stone Wand"),
    _e("rune_staff", "Rune Staff", None, "craft", "staff", "socketed_staff", "S", "2", "varies",
       "The runed version of the staff.", "Рунная версия посоха.", "Quarterstaff + Rune Wand"),
    # ---- hammers ----
    _e("war_hammer", "War Hammer", None, "craft", "hammer", None, "", "1", "stone",
       "A crafted hammer.", "Создаваемый молот.", "Sword + Shield"),
    _e("stone_hammer", "Stone Hammer", None, "craft", "hammer", None, "", "1", "stone",
       "A hammer with a socket.", "Молот с гнездом.", "War Hammer + Stone Wand  /  Sword + Stone Shield"),
    _e("rune_hammer", "Rune Hammer", None, "craft", "hammer", "socketed_hammer", "S", "1", "varies",
       "The runed version of the hammer.", "Рунная версия молота.", "Sword + Rune Shield  /  Shield + Rune Sword"),
    _e("heavy_hammer", "Heavy Hammer", "Тяжёлый молот", "craft", "hammer", "heavy_hammer", "WS", "2", "stone",
       "An upgrade of the War Hammer; it stuns with each attack. Ability: a powerful attack that applies armor "
       "fatigue.",
       "Улучшение Боевого молота; каждая атака оглушает. Способность: мощная атака, накладывающая усталость брони.",
       "War Hammer + Quarterstaff"),
    # ---- shields ----
    _e("stone_shield", "Stone Shield", None, "craft", "shield", None, "", "R", "stone",
       "A shield with a socket.", "Щит с гнездом.", "Shield + Stone Wand"),
    _e("rune_shield", "Rune Shield", None, "craft", "shield", "socketed_shield", "S", "R", "varies",
       "The runed version of the shield.", "Рунная версия щита.", "Stone Shield + Runestone  /  Shield + Rune Wand"),
    _e("dashing_shield", "Dashing Shield", "Стремительный щит", "craft", "shield", "dashing_shield", "WS", "R",
       "stone",
       "Dashes straight to a nearby foe (distance 16-11), cooldown 1.5 s. Used in speedruns to skip walking.",
       "Рывком подскакивает к ближнему врагу (дистанция 16-11), перезарядка 1,5 с. Нужен в спидранах.",
       "Shield + Crossbow"),
    _e("compound_shield", "Compound Shield", "Композитный щит", "craft", "shield", "compound_shield", "WS", "R",
       "stone",
       "A better version of the normal shield; it also stuns attackers. The best shield for non-elemental "
       "locations.",
       "Улучшенный щит, который ещё и оглушает атакующих. Лучший щит для нестихийных локаций.",
       "Shield + Dashing Shield"),
    _e("tower_shield", "Towering Shield", "Ростовой щит", "craft", "shield", "tower_shield", "S", "R", "stone",
       "Crafted from a Shield and a Quarterstaff. It does not drop from chests.",
       "Создаётся из Щита и Квотерстаффа. Из сундуков не выпадает.", "Shield + Quarterstaff"),
    _e("bardiche", "Bardiche", "Бердыш", "craft", "polearm", "bardiche", "S", "", "stone",
       "A crafted polearm with an ability.", "Создаваемое древковое оружие со способностью.",
       "Shield + Big Sword  /  Sword + Towering Shield"),
    # ---- lost items ----
    _e("bashing_shield", "Bashing Shield", "Таранный щит", "lost", "shield", "bashing_shield", "S", "R", "stone",
       "The first Lost item. Lost items are found one copy at a time and upgraded as you collect copies.",
       "Первый Lost-предмет. Lost-предметы находят по одной копии и улучшают по мере сбора."),
    _e("blade_of_god", "Blade of the Fallen God", "Клинок павшего бога", "lost", "sword", "blade_of_god", "S", "",
       "stone",
       "A Lost item: from the Titanic Accord legend (once), delta and lost chests, or the Hotspring Shop. Like all "
       "Lost items it starts at level 5.",
       "Lost-предмет: из легенды «Титанический договор» (один раз), дельта- и lost-сундуков или Лавки «Горячий "
       "ключ». Как и все Lost-предметы, начинается с 5 уровня."),
    _e("skeleton_arm", "Skeleton Arm", "Рука скелета", "lost", "arm", "skeleton_arm", "S", "", "stone",
       "A Lost item.", "Lost-предмет."),
    _e("cult_mask", "Cultist Mask", "Маска культиста", "lost", "mask", "cult_mask", "S", "", "stone",
       "A Lost item.", "Lost-предмет."),
    _e("fire_talisman", "Fire Talisman", "Талисман огня", "lost", "talisman", "fire_talisman", "S", "", "stone",
       "A Lost item (talisman).", "Lost-предмет (талисман)."),
    _e("aether_talisman", "Æther Talisman", "Талисман эфира", "lost", "talisman", "aether_talisman", "S", "",
       "stone", "A Lost item (talisman).", "Lost-предмет (талисман)."),
    # ---- other equipment ----
    _e("crusader_shield", "Crusader's Shield", "Щит крестоносца", "other", "shield", "crusader_shield", "S", "R",
       "stone", "Listed in the wiki's item category and in SSRPGS' cosmetics list.",
       "Есть в категории предметов вики и в списке косметики SSRPGS."),
    _e("ice_talisman", "Ice Talisman", None, "other", "talisman", None, "", "", "stone",
       "Listed in the wiki's item category.", "Есть в категории предметов вики."),
    # ---- tools ----
    _e("hatchet", "Hatchet", None, "tools", "tool", "hatchet_lv1", "W", "R", "stone",
       "Harvests wood from trees. Crafted at the workbench for 3 stone and 5 wood. Ability: swings twice quickly.",
       "Добывает дерево из деревьев. Создаётся на верстаке за 3 камня и 5 дерева. Способность: быстро бьёт дважды.",
       "3 Stone + 5 Wood", stars=False, ench=False),
    _e("shovel", "Shovel", None, "tools", "tool", None, "", "", "",
       "A tool for harvesting stone (equipped at Rocky Plateau).", "Инструмент для добычи камня (Каменистое плато).",
       stars=False, ench=False),
    _e("grappling_hook", "Grappling Hook", None, "tools", "tool", None, "", "", "",
       "A craftable tool (the wiki lists it among equippable items).",
       "Создаваемый инструмент (в вики входит в список экипируемых предметов).", stars=False, ench=False),
    # ---- stones ----
    _e("mind_stone", "Mind Stone", None, "stones", "stone", None, "", "", "",
       "Used to automate equipment choices with Stonescript.",
       "Нужен, чтобы автоматизировать выбор экипировки с помощью Stonescript.", stars=False, ench=False),
    _e("star_stone", "Star Stone", None, "stones", "stone", None, "", "", "",
       "Its level limits the maximum star level of locations (level x allows up to 5 x stars).",
       "Его уровень ограничивает максимальные звёзды локаций (уровень x — до 5 × x звёзд).",
       stars=False, ench=False),
    _e("sight_stone", "Sight Stone", None, "stones", "stone", None, "", "", "", "", "", stars=False, ench=False),
    _e("quest_stone", "Quest Stone", None, "stones", "stone", None, "", "", "", "", "", stars=False, ench=False),
    _e("fissure_stone", "Fissure Stone", None, "stones", "stone", None, "", "", "",
       "Enchantments can be removed from an item on the Fissure station.",
       "На станции Fissure можно снять зачарование с предмета.", stars=False, ench=False),
    _e("ouroboros_stone", "Ouroboros Stone", None, "stones", "stone", None, "", "", "", "", "",
       stars=False, ench=False),
    _e("triskelion_stone", "Triskelion Stone", None, "stones", "stone", None, "", "", "",
       "Unlocks the \"Fuse Enchantments\" menu.", "Открывает меню «Выковать чары» (Fuse Enchantments).",
       stars=False, ench=False),
    _e("experience_stone", "Experience Stone", None, "stones", "stone", None, "", "", "", "", "",
       stars=False, ench=False),
    _e("ki_stone", "Ki Stone", None, "stones", "stone", None, "", "", "", "", "", stars=False, ench=False),
    # ---- resources and event items ----
    _e("event_ticket", "Event Ticket", None, "misc", "event", None, "", "", "",
       "A pseudo-resource obtained in several ways. 30 tickets unlock the premium track of an event.",
       "Псевдо-ресурс, который получают разными способами. 30 билетов открывают премиум-дорожку события.",
       stars=False, ench=False),
    _e("ki_crystal", "Ki Crystal", None, "misc", "resource", None, "", "", "",
       "A pseudo-resource obtained in several ways.", "Псевдо-ресурс, который получают разными способами.",
       stars=False, ench=False),
    _e("crystal_powder", "Crystal Powder", None, "misc", "resource", None, "", "", "",
       "Obtained by breaking down Ki Crystals from treasures.",
       "Получается при разборе Ki-кристаллов из сокровищ.", stars=False, ench=False),
    _e("moonbloom", "Moonbloom", None, "misc", "enchant", None, "", "", "",
       "Needed to create a double enchantment (from a transcendent +16 or higher enchantment).",
       "Нужен, чтобы создать двойное зачарование (из трансцендентного зачарования +16 и выше).",
       stars=False, ench=False),
    _e("moonbloom_petal", "Moonbloom Petal", None, "misc", "enchant", None, "", "", "",
       "Used instead of Ki to upgrade the second enchantment of a double enchantment.",
       "Тратится вместо Ки на улучшение второго зачарования у двойного зачарования.", stars=False, ench=False),
    _e("warm_stone", "Warm Stone", None, "misc", "event", None, "", "", "",
       "Event resource: digging boulders and enemies during Summer.",
       "Ресурс события: копание валунов и враги во время Лета.", stars=False, ench=False),
    _e("balloon", "Balloon", None, "misc", "event", None, "", "", "",
       "Event resource: defeating enemies with an item of range higher than 11 during Spring.",
       "Ресурс события: победы над врагами предметом с дальностью больше 11 во время Весны.",
       stars=False, ench=False),
    _e("torch", "Torch", None, "misc", "event", None, "", "", "",
       "Event resource: defeating cultists during the Caves event.",
       "Ресурс события: победы над культистами во время события «Пещеры».", stars=False, ench=False),
    _e("candy", "Candy", None, "misc", "event", None, "", "", "",
       "Event resource: defeating enemies during Halloween.",
       "Ресурс события: победы над врагами во время Хэллоуина.", stars=False, ench=False),
    _e("hot_beverage", "Hot Beverage", None, "misc", "event", None, "", "", "",
       "Event resource: defeating enemies with ice weapons during Winter.",
       "Ресурс события: победы над врагами ледяным оружием во время Зимы.", stars=False, ench=False),
]

BY_KEY = {it.key: it for it in ITEMS}
BY_ID: dict[str, list[CatalogItem]] = {}
for _it in ITEMS:
    if _it.id:
        BY_ID.setdefault(_it.id, []).append(_it)


def category_name(cat: str) -> str:
    en, ru = CATEGORIES[cat]
    return ru if current_language() == "ru" else en


def sub_name(sub: str) -> str:
    en, ru = SUBCATEGORIES[sub]
    return ru if current_language() == "ru" else en


def lookup_id(item_id: str) -> CatalogItem | None:
    """Catalogue entry for a save item id (the first one if several entries share an id)."""
    rows = BY_ID.get(item_id)
    return rows[0] if rows else None


def display_name(item_id: str) -> str:
    """Readable name for an item id; unknown ids are shown as they are."""
    rows = BY_ID.get(item_id)
    if not rows:
        return item_id
    if len(rows) == 1:
        return rows[0].name
    return " / ".join(r.name for r in rows)


def search(query: str = "", category: str | None = None, sub: str | None = None,
           only_addable: bool = False) -> list[CatalogItem]:
    words = query.casefold().split()
    out = []
    for it in ITEMS:
        if category and it.category != category:
            continue
        if sub and it.sub != sub:
            continue
        if only_addable and not it.addable:
            continue
        if words:
            hay = " ".join([it.name_en, it.name_ru or "", it.id or "", it.desc_en, it.desc_ru,
                            category_name(it.category), sub_name(it.sub)]).casefold()
            if not all(w in hay for w in words):
                continue
        out.append(it)
    return out


# --------------------------------------------------------------------------
# building a new inventory entry from a template
# --------------------------------------------------------------------------
# per-item personal state: never inherited from the template item
PERSONAL_DA_KEYS = {"hI", "lv", "sh", "el", "ra", "sra", "sig", "tag", "c", "abs", "lC", "lBU", "time", "rng", "rS"}
MIN_DA = {"hI": False}          # the minimal item data SSRPGS itself uses for a new item
MAX_ENCHANT_EXAMPLE = {"lv": 21, "ql": 12049, "sSS": 0}   # the +21 example used by SSRPGS


def find_templates(items: list[dict], item_id: str) -> list[dict]:
    return [it for it in items if isinstance(it, dict) and it.get("id") == item_id]


def known_values(items: list[dict], key: str, item_id: str | None = None) -> list[Any]:
    """Distinct values of da[key] found in the player's own items (optionally for one item id)."""
    seen: list[Any] = []
    for it in items:
        if not isinstance(it, dict) or (item_id and it.get("id") != item_id):
            continue
        da = it.get("da")
        if isinstance(da, dict) and key in da and da[key] not in seen and not isinstance(da[key], (dict, list)):
            seen.append(da[key])
    return seen


def enchanted_examples(items: list[dict]) -> list[dict]:
    return [it for it in items if isinstance(it, dict) and isinstance(it.get("da"), dict)
            and isinstance(it["da"].get("ra"), dict)]


def build_item(items: list[dict], item_id: str, count: int, *, stars: int | None = None,
               shiny: bool = False, element: Any = None, enchant: dict | None = None) -> tuple[dict, str]:
    """Create a new inventory entry. Returns (item, template_note).

    The structure is taken from an existing item with the same id when there is one (so unknown but required
    keys stay as the game wrote them); personal state (stars, enchantments, signature ...) is never inherited.
    """
    templates = find_templates(items, item_id)
    da: dict[str, Any] = dict(MIN_DA)
    note = "minimal"
    if templates:
        src_da = templates[0].get("da") if isinstance(templates[0].get("da"), dict) else {}
        for k, v in src_da.items():
            if k not in PERSONAL_DA_KEYS:
                da[k] = copy.deepcopy(v)
        note = "template"
    if stars is not None:
        da["lv"] = int(stars)
    if shiny:
        da["sh"] = True
    if element not in (None, ""):
        da["el"] = element
    if enchant:
        da["ra"] = copy.deepcopy(enchant)
    return {"id": item_id, "co": int(count), "da": da}, note
