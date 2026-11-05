"""Interface texts in Russian and English."""
from __future__ import annotations

_lang = "en"


def set_language(lang: str) -> None:
    global _lang
    _lang = lang if lang in STRINGS else "en"


def current_language() -> str:
    return _lang


def tr(key: str, **kw) -> str:
    table = STRINGS.get(_lang, STRINGS["en"])
    text = table.get(key)
    if text is None:
        text = STRINGS["en"].get(key, key)
    try:
        return text.format(**kw) if kw else text
    except (KeyError, IndexError):
        return text


def help_sections() -> list[tuple[str, str]]:
    return HELP[_lang]


STRINGS: dict[str, dict[str, str]] = {
    # ------------------------------------------------------------------ RU
    "ru": {
        "app_title": "Stone Story RPG — редактор сохранений",
        "header_sub": "редактор сохранений",
        "help_btn": "Помощь",
        "tip_help": "Подробная инструкция (F1)",
        "tip_theme": "Светлая / тёмная тема",
        "tip_language": "Сменить язык / Switch language",
        "welcome_title": "Редактор сохранений Stone Story RPG",
        "welcome_sub": "Меняйте золото, предметы и прогресс в пару кликов — без программирования. "
                       "Файл расшифровывается автоматически, а перед записью всегда создаётся резервная копия.",
        "step1_title": "Закройте игру",
        "step1_text": "Иначе игра может перезаписать ваши изменения.",
        "step2_title": "Откройте сейв",
        "step2_text": "Нажмите кнопку ниже. Не знаете, где лежит файл? Нажмите «Найти сейв автоматически».",
        "step3_title": "Измените и сохраните",
        "step3_text": "Выберите значение в списке, введите новое и нажмите «Сохранить».",
        "open_save": "Открыть файл сейва",
        "find_save": "Найти сейв автоматически",
        "recent_files": "Недавние файлы:",
        "safe_note": "Неофициальная программа. Оригинал не теряется: перед каждой записью рядом создаётся "
                     "копия (.bak), а любое изменение можно отменить.",
        "ready": "Откройте файл сейва, чтобы начать.",
        # toolbar
        "open": "Открыть",
        "undo": "Отменить",
        "redo": "Вернуть",
        "save": "Сохранить",
        "save_as": "Сохранить как копию…",
        "restore_backup": "Восстановить из копии…",
        "export_json": "Экспорт в JSON…",
        "tip_open": "Открыть другой файл сейва (Ctrl+O)",
        "tip_undo": "Отменить последнее действие (Ctrl+Z)",
        "tip_redo": "Вернуть отменённое действие (Ctrl+Y)",
        "tip_save": "Записать изменения в файл. Сначала создаётся резервная копия. (Ctrl+S)",
        "tip_save_as": "Записать изменения в новый файл, не трогая исходный",
        "tip_restore": "Вернуть сейв из резервной копии, если что-то пошло не так",
        "tip_export": "Сохранить расшифрованные данные в читаемом виде (только для просмотра)",
        "profile": "Профиль:",
        "slot": "Слот",
        "no_name": "Без имени",
        "profile_info": "Версия игры: {ver}   ·   {slot}",
        "tab_simple": "Простой режим",
        "tab_tree": "Все данные (для опытных)",
        "tab_changes": "Изменения",
        # simple tab
        "filter_all": "Все",
        "filter_number": "Числа",
        "filter_bool": "Да / Нет",
        "filter_text": "Текст",
        "filter_changed": "Изменённые",
        "col_name": "Название",
        "col_value": "Значение",
        "col_section": "Раздел",
        "col_field": "Поле",
        "col_type": "Тип",
        "rows_shown": "Показано: {n} из {all}",
        "rows_capped": "Показаны первые {shown} из {total} — уточните поиск, чтобы увидеть остальные",
        "search_hint": "Поиск",
        # panel
        "panel_empty_title": "Ничего не выбрано",
        "panel_empty_text_simple": "Выберите строку в списке слева. Затем введите новое значение справа или "
                                   "нажмите быструю кнопку (например, +1 000).\n\nМожно выделить сразу несколько "
                                   "строк с помощью Ctrl или Shift.\n\nНужное значение не видно? Начните вводить его "
                                   "название в строке поиска (Ctrl+F).",
        "panel_empty_text_tree": "Раскройте ветку и выберите поле. Двойной клик по полю — сразу перейти к вводу.\n\n"
                                 "Правая кнопка мыши — меню действий (добавить, удалить, скопировать путь).",
        "technical_key": "Технический ключ",
        "whole_profile": "Весь профиль",
        "value_empty": "Значение пустое.",
        "set_value": "Задать значение…",
        "was": "Было",
        "did_not_exist": "(этого поля не было)",
        "restore_original": "Вернуть как было",
        "advanced_edit": "Расширенное редактирование…",
        "delete": "Удалить",
        "show_in_tree": "Показать в «Все данные»",
        "container_info_object": "Группа из {n} полей.",
        "container_info_array": "Список из {n} элементов.",
        "add_field": "Добавить поле…",
        "add_item": "Добавить элемент…",
        "edit_as_json": "Изменить как JSON…",
        "json_hint": "Правьте аккуратно: скобки, кавычки и запятые должны остаться на своих местах.",
        "new_value": "Новое значение",
        "not_a_number": "Это не число",
        "quick_add": "Быстро изменить:",
        "quick_more": "Ещё:",
        "switch": "Переключатель",
        "yes": "Да",
        "no": "Нет",
        "apply": "Применить",
        "cancel": "Отмена",
        "close": "Закрыть",
        "selected_n": "Выбрано строк: {n}",
        "bulk_numbers_only": "Чтобы менять сразу несколько значений, выберите только числа.",
        "bulk_hint": "Введите одно значение для всех выбранных строк или используйте быстрые кнопки — "
                     "они применятся к каждой строке.",
        "set_all_to": "Установить всем это значение",
        "kind_text": "Текст",
        "kind_number": "Число",
        "kind_bool": "Да/Нет",
        "kind_null": "Пусто",
        "kind_object": "Группа",
        "kind_array": "Список",
        "kind_profile": "Профиль",
        "n_fields": "группа · {n} полей",
        "n_items": "список · {n} элементов",
        # dialogs
        "dlg_field_name": "Название нового поля",
        "dlg_type": "Тип значения",
        "dlg_value_help": "Значение (для группы и списка — в формате JSON)",
        "err_bad_value": "Неверное значение",
        "err_bad_json": "Ошибка в формате JSON: {err}",
        "err_bad_for_kind": "Это значение не подходит для типа «{kind}».",
        "err_empty_name": "Название не может быть пустым.",
        "err_key_exists": "Такое поле уже существует.",
        "add_hint": "Для обычного числа выберите тип «Число», для слов — «Текст».",
        "add_pick_container": "Выберите группу или список, в который нужно добавить.",
        "big_title": "Очень большое число",
        "big_text": "Вы ставите значение {v}. Слишком большие числа могут сломать игру или сохранение. "
                    "Всё равно применить?",
        # finder
        "find_title": "Поиск сейва на компьютере",
        "find_intro": "Программа заглянет в обычные папки, где игры хранят сохранения (AppData, Документы, Steam). "
                      "Это безопасно: файлы только читаются.",
        "find_searching": "Идёт поиск…",
        "find_scanning": "Смотрю: {path}",
        "find_done": "Готово. Найдено файлов: {n}. Выберите нужный и нажмите «Открыть».",
        "find_none": "Ничего не найдено. Нажмите «Указать папку…» или откройте файл вручную.",
        "find_pick_folder": "Указать папку…",
        # tree tab
        "find_next": "Найти дальше",
        "collapse_all": "Свернуть всё",
        "copy_path": "Копировать путь",
        "copied": "Скопировано",
        "nothing_found": "Ничего не найдено: {q}",
        "match_n": "Совпадение {pos} из {n}: {path}",
        # changes tab
        "changes_intro": "Здесь всё, что вы изменили в этом профиле и ещё не сохранили. Выделите строки и нажмите "
                         "«Вернуть выбранное», чтобы отменить именно их.",
        "chg_what": "Что",
        "chg_type": "Действие",
        "chg_old": "Было",
        "chg_new": "Стало",
        "chg_type_changed": "Изменено",
        "chg_type_added": "Добавлено",
        "chg_type_removed": "Удалено",
        "no_changes": "Пока нет изменений.",
        "revert_selected": "Вернуть выбранное",
        "revert_all": "Отменить все изменения профиля",
        "select_first": "Сначала выделите строки в списке.",
        "revert_removed_hint": "Удалённые поля отсюда вернуть нельзя — нажмите «Отменить» (Ctrl+Z).",
        "revert_all_ask": "Вернуть профиль к состоянию на момент открытия или последнего сохранения? "
                          "Все несохранённые изменения этого профиля пропадут.",
        "reverted_all": "Все изменения профиля отменены",
        # status
        "opened": "Открыто: {name}. Профилей: {n}. Файл на диске пока не изменён.",
        "changed_one": "Изменено: {name} → {v}",
        "changed_many": "Изменено значений: {n}",
        "undone": "Действие отменено",
        "redone": "Действие возвращено",
        "unsaved_n": "● Несохранённых изменений: {n}",
        "all_saved": "✓ Все изменения сохранены",
        "added_ok": "Добавлено: {path}",
        "deleted_ok": "Удалено: {path}",
        "saved_ok": "Сохранено: {name}",
        "restored_ok": "Сейв восстановлен из резервной копии",
        "exported_ok": "Экспортировано: {name}",
        # open / save
        "open_title": "Открыть сохранение Stone Story RPG",
        "ft_save": "Сейв Stone Story (*.txt)",
        "ft_all": "Все файлы",
        "err_open_title": "Не удалось открыть файл",
        "err_open_text": "Не получилось прочитать этот файл.\n\nПроверьте, что это именно сейв Stone Story RPG "
                         "(обычно primary_save.txt или save.txt) и что игра сейчас закрыта.\n\nПодробности:\n{detail}",
        "unsaved_title": "Есть несохранённые изменения",
        "unsaved_ask": "Несохранённые изменения будут потеряны. Продолжить?",
        "unsaved_quit": "Есть несохранённые изменения. Закрыть программу без сохранения?",
        "save_confirm_title": "Сохранить изменения?",
        "save_confirm_text": "Файл «{name}» будет перезаписан.\n\nПеред этим рядом автоматически создаётся "
                             "резервная копия (.bak), а результат проверяется.\n\nИгра закрыта? Если она запущена, "
                             "она может затереть ваши изменения.",
        "err_save_title": "Не удалось сохранить",
        "err_save_text": "Файл НЕ был изменён.\n\n{detail}",
        "saved_title": "Готово!",
        "saved_text": "Сохранено: {name}\nРезервная копия: {backup}\n\nТеперь можно запускать игру и загружать сейв.",
        "save_as_title": "Сохранить копию сейва",
        "restore_pick": "Выберите резервную копию. Текущий файл перед заменой тоже сохранится как копия.",
        "restore": "Восстановить",
        "restore_ask": "Заменить текущий файл копией «{name}»?",
        "no_backups": "Резервных копий этого файла не найдено.",
        "export_title": "Экспорт в JSON",
        "exported_text": "Расшифрованные данные сохранены:\n{name}\n\nЭто копия для просмотра, игра её не прочитает. "
                         "Чтобы изменить сейв, используйте кнопку «Сохранить».",
        "delete_ask": "Удалить «{name}»?\nТип: {kind}\n\nЭто можно отменить кнопкой «Отменить» (Ctrl+Z).",
        "help_title": "Помощь",
        "ench_btn": "Зачарование…",
        "tab_home": "Главная",
        "tab_catalog": "Каталог предметов",
        "home_title": "Что вы хотите изменить?",
        "home_profile": "Профиль: {name}",
        "level_short": "уровень {n}",
        "home_tip": "Выберите плитку — откроется понятная страница раздела. Рядом с полями есть кнопка «?» с объяснением. Перед массовыми изменениями программа покажет старые и новые значения. Всё можно отменить (Ctrl+Z).",
        "home_count": "Параметров: {n}",
        "catalog_count_short": "Предметов в каталоге: {n}",
        "catalog_tile": "Каталог предметов",
        "home_inventory": "Предметы: найти по названию, добавить, изменить количество, звёзды, зачарования.",
        "home_resources": "Камни, дерево, смола, ки и бронза.",
        "home_cosmetics": "Золотые, glitch и призматические скины.",
        "home_player": "Имя, уровень и опыт героя.",
        "home_quests": "Ежедневные и еженедельные квесты, таймеры легенд.",
        "home_events": "Премиум-пропуск, очки дорожки и задания событий.",
        "home_progress": "Открытые локации, верстак, проекты и легенды.",
        "home_locations": "Звёзды (сложность) локаций.",
        "home_catalog": "Все предметы игры: категории, ID, описания, рецепты.",
        "page_player": "Игрок и профиль",
        "page_resources": "Ресурсы",
        "page_cosmetics": "Косметика",
        "page_quests": "Квесты",
        "page_progress": "Прогресс",
        "page_locations": "Локации",
        "hint_player": "Имя, уровень и опыт героя. Наведите курсор на «?» рядом с полем — там объяснение.",
        "hint_resources": "Ресурсы для создания предметов и проектов. Если ресурса нет в сейве, его можно добавить.",
        "hint_cosmetics": "Скины предметов. Отметьте нужные; у призматических можно выбрать цвет. Поиск работает по названию.",
        "hint_quests": "Квесты и таймеры легенд. Названий квестов в источниках нет, поэтому показаны их ID.",
        "hint_progress": "Что открыто в игре: локации, функции верстака, проекты и легенды. Кнопками можно открыть или закрыть сразу всё группой.",
        "hint_locations": "Звёзды локаций: 1-5 белый, 6-10 бирюзовый, 11-15 жёлтый, 16-20 зелёный. Максимум зависит от уровня Камня Звезды.",
        "page_empty": "В этом сейве нет данных для этого раздела. Загляните в «Все данные» или нажмите «Обычные карточки».",
        "max_level_btn": "Максимальный уровень ({n})",
        "name_label": "Имя игрока",
        "player_summary": "Уровень {lvl}: +{hp} к здоровью, лимит сундуков {chests}",
        "res_where": "Где добывается: {where}",
        "res_missing": "Нет в сейве",
        "res_add": "Добавить (0)",
        "res_all_add": "Всем +",
        "res_all_set": "Всем =",
        "res_bulk_title": "Ресурсы: массовое изменение",
        "cos_golden": "Золотой",
        "cos_glitch": "Glitch",
        "cos_prismatic": "Призматический",
        "cos_color": "Цвет",
        "cos_all_on": "Открыть все: {kind}",
        "cos_all_off": "Снять все: {kind}",
        "cos_summary": "Золотых: {a} · Glitch: {b} · Призматических: {c} (из {n})",
        "nothing_to_change": "Нечего менять: всё уже так, как вы просите.",
        "quests_active": "Активные квесты",
        "quests_weekly": "Еженедельный квест",
        "quests_timers": "Таймеры и легенды",
        "quests_all_done": "Отметить все выполненными",
        "quest_n": "Квест {id}",
        "quest_weekly_n": "Еженедельный: {id}",
        "quest_done_label": "Выполнен",
        "quest_name_unknown": "Название квеста в открытых источниках не найдено, поэтому показан его ID.",
        "progress_locations": "Локации",
        "progress_workbench": "Верстак",
        "progress_projects": "Проекты",
        "progress_legends": "Легенды",
        "open_all": "Открыть все",
        "close_all": "Закрыть все",
        "progress_summary": "Открыто: {a} из {n}",
        "loc_stars": "Звёзды",
        "loc_all_set": "Всем локациям = ",
        "loc_no_data": "В сейве нет данных о звёздах локаций.",
        "ev_task": "Задание {id}",
        "catalog_intro": "Каталог реальных предметов Stone Story RPG. Тип, хват и стихия — отдельные характеристики. ID показан только там, где он указан в источниках; у остальных предметов ID неизвестен, и вслепую их добавить нельзя.",
        "catalog_pick": "Выберите предмет в списке слева — здесь появятся его описание, рецепт и ID.",
        "catalog_count": "Найдено: {n} из {total}",
        "cat_filter_all": "Все категории",
        "type_filter_all": "Все типы",
        "only_addable": "Только с известным ID",
        "col_item": "Предмет",
        "col_item_type": "Тип",
        "col_element": "Стихия",
        "cat_label": "Категория",
        "type_label": "Тип предмета",
        "hand_label": "Хват",
        "element_label": "Стихия",
        "rarity_label": "Редкость",
        "rarity_text": "У предмета нет фиксированной «редкости»: сила задаётся звёздами (0-10) и зачарованием (+1…+21, цвет от бирюзового до радужного).",
        "no_description": "Описание в источниках не найдено.",
        "recipe_label": "Рецепт",
        "id_source": "Источник ID",
        "id_unknown": "ID этого предмета в источниках не найден, поэтому добавить его вслепую нельзя (иначе игра может не загрузить сейв).",
        "add_to_inventory": "Добавить в инвентарь…",
        "add_from_catalog": "Добавить из каталога…",
        "wizard_title": "Добавить предмет в инвентарь",
        "wizard_intro": "Найдите предмет по названию, задайте количество и характеристики — и нажмите «Добавить». Знать ID и JSON не нужно: структура берётся из ваших предметов.",
        "wizard_pick_first": "Сначала выберите предмет слева.",
        "wizard_no_id": "У этого предмета нет подтверждённого ID, поэтому добавить его нельзя. Можно сделать копию уже имеющегося предмета в инвентаре (кнопка ⧉).",
        "wizard_no_inventory": "В этом сейве не найден список предметов (progress_data.inventory_data.itms).",
        "wizard_options": "Параметры предмета",
        "stars_label": "Звёзды",
        "stars_hint": "0-{n}",
        "shiny_label": "Shiny",
        "hi_label": "Просмотрен",
        "element_hint": "Значения взяты из ваших предметов. Пусто — без стихии.",
        "element_none_known": "В ваших предметах нет значений стихии, поэтому список пуст. Стихию можно задать позже в «Все параметры».",
        "enchant_label": "Зачарование",
        "ench_none": "Без зачарования",
        "ench_none_short": "нет",
        "ench_copy": "Скопировать с моего предмета:",
        "ench_max": "Максимальное +{lv} (значения как в SSRPGS)",
        "ench_hint": "Значения качества и сида берутся из реальных зачарований вашего сейва или из примера SSRPGS — вручную их придумывать не нужно.",
        "tmpl_from": "Структура будет взята из вашего предмета «{name}»; личные параметры (звёзды, зачарования) не копируются.",
        "tmpl_minimal": "У вас нет такого предмета — используется минимальная структура (как в SSRPGS): ID, количество и данные.",
        "add_btn": "Добавить",
        "wizard_added": "Добавлено: {n} × {name}",
        "wizard_added_more": "Увеличено количество: {name} +{n}",
        "add_by_id": "Добавить по ID…",
        "add_by_id_ask": "Введите ID предмета (только если точно знаете его):",
        "add_by_id_warn": "ID «{id}» нет среди ваших предметов, и я не могу проверить, что он верный. Неверный ID может сломать загрузку сейва. Всё равно добавить?",
        "err_min_value": "Значение должно быть не меньше {lo}.",
        "not_in_catalog": "нет в каталоге",
        "sort_label": "Сортировка",
        "sort_order": "Как в сейве",
        "sort_name": "По названию",
        "sort_count": "По количеству",
        "inv_bulk_title": "Инвентарь: массовое изменение количества",
        "inv_remove_row": "будет удалён",
        "inv_clear_note": "Будут удалены ВСЕ предметы инвентаря. Это можно отменить (Ctrl+Z).",
        "ench_title": "Зачарование",
        "ench_manual": "— вручную —",
        "ench_from": "Как у «{name}» (+{lv})",
        "ench_preset": "Взять за основу",
        "ench_lv": "Уровень (+)",
        "ench_ql": "Качество",
        "ench_seed": "Сид",
        "ench_remove": "Снять зачарование",
        "ench_remove_ask": "Убрать зачарование с этого предмета?",
        "ench_need_numbers": "Уровень, качество и сид должны быть целыми числами.",
        "ench_out_of_range": "Вне диапазона +1…+{mx}",
        "range_title": "Необычное значение",
        "range_warn": "Игра документирует диапазон {lo}-{hi}, а вы ставите {v}. Применить всё равно?",
        "preview_title": "Предпросмотр изменений",
        "preview_summary": "Будет изменено параметров: {n}.  Без изменений: {same}.",
        "preview_more": "…и ещё {n}",
        "preview_apply": "Применить изменения",
        "sections_title": "Разделы",
        "cat_all": "Всё",
        "cat_inventory": "Инвентарь",
        "cat_events": "Ивенты и пропуск",
        "cat_player": "Игрок и профиль",
        "cat_resources": "Ресурсы",
        "cat_quests": "Квесты",
        "cat_progress": "Прогресс",
        "cat_locations": "Локации",
        "cat_cosmetics": "Косметика",
        "cat_time": "Время",
        "cat_other": "Прочее",
        "use_special": "Умный вид раздела",
        "use_generic": "Обычные карточки",
        "inv_title": "Инвентарь",
        "inv_count": "Предметов: {n}",
        "inv_where": "Найден в сейве: {path}",
        "inv_add": "Добавить предмет…",
        "inv_clear": "Очистить инвентарь",
        "inv_clear_ask": "Удалить ВСЕ предметы ({n})?\n\nЭто можно отменить кнопкой «Отменить» (Ctrl+Z).",
        "inv_bulk_label": "Для всех показанных:",
        "inv_set_all": "Всем =",
        "inv_add_all": "Всем +",
        "inv_dup": "Сделать копию предмета",
        "inv_delete": "Удалить предмет",
        "inv_fields": "Все параметры…",
        "inv_not_found": "Не получилось найти список предметов в этом сейве. Нажмите «Обычные карточки» — там "
                         "доступны все значения раздела, а вкладка «Все данные» покажет полную структуру.",
        "inv_empty": "Ничего не найдено. Проверьте поиск.",
        "inv_add_title": "Добавить предмет",
        "inv_item_name": "Название / ID предмета",
        "inv_item_count": "Количество",
        "inv_template": "Взять за основу предмет",
        "inv_add_hint": "Пишите название так же, как у существующих предметов. Остальные параметры (звёзды, "
                        "чары и т.д.) копируются с выбранного ниже предмета. Если такой предмет уже есть, "
                        "просто увеличится его количество.",
        "inv_no_template": "Инвентарь пуст, поэтому предмет будет простым: название + количество. Если игра его не "
                           "поймёт, сначала получите любой предмет в игре.",
        "inv_added": "Предмет добавлен: {name}",
        "ev_title": "Ивенты и пропуск",
        "ev_hint": "У каждого ивента есть дорожка наград. Премиум-часть открывается переключателем «Премиум-пропуск» "
                   "(в сейве это поле pp/premium). В игре её дают за подписку или за 30 Event Tickets. На всю дорожку "
                   "обычно нужно 35 очков (в Green Part 1 и 2 — 50).",
        "ev_give_pass": "Выдать премиум-пропуск везде",
        "ev_remove_pass": "Снять премиум везде",
        "ev_pass_name": "Премиум-пропуск",
        "ev_points_label": "Очки / уровни всех ивентов:",
        "ev_set_points": "Поставить всем",
        "ev_more_fields": "Остальные поля ({n})",
        "ev_hide_fields": "Скрыть остальные поля",
        "ev_none": "Ивенты в этом сейве не найдены. Загляните в «Все данные» — возможно, они названы иначе.",
        "ev_no_pass": "Переключатель премиума не найден — используйте карточки ниже.",
        "ev_no_points": "Поля с очками или уровнями не найдены — используйте карточки ниже.",
        "ev_summary": "Премиум включён: {on} из {total}",
        "view_cards": "▦  Карточки",
        "view_list": "☰  Список",
        "tip_view_cards": "Наглядные карточки с кнопками и переключателями",
        "tip_view_list": "Таблица значений с панелью редактирования справа",
        "card_more": "Показать ещё ({n})",
        "cards_empty": "Ничего не найдено. Попробуйте другое слово или сбросьте фильтр «Все».",
        "section_general": "Основное",
        "section_profile": "Данные профиля",
        "tip_minus": "Уменьшить",
        "tip_plus": "Увеличить",
    },
    # ------------------------------------------------------------------ EN
    "en": {
        "app_title": "Stone Story RPG Save Editor",
        "header_sub": "save editor",
        "help_btn": "Help",
        "tip_help": "Full guide (F1)",
        "tip_theme": "Light / dark theme",
        "tip_language": "Switch language / Сменить язык",
        "welcome_title": "Stone Story RPG Save Editor",
        "welcome_sub": "Change gold, items and progress in a few clicks - no programming needed. "
                       "The file is decrypted automatically and a backup is always made before saving.",
        "step1_title": "Close the game",
        "step1_text": "Otherwise the game may overwrite your changes.",
        "step2_title": "Open your save",
        "step2_text": "Press the button below. Not sure where the file is? Press \"Find my save automatically\".",
        "step3_title": "Edit and save",
        "step3_text": "Pick a value in the list, type a new one and press \"Save\".",
        "open_save": "Open save file",
        "find_save": "Find my save automatically",
        "recent_files": "Recent files:",
        "safe_note": "Unofficial tool. Your original is never lost: a backup copy (.bak) is created next to the "
                     "file before every save, and every change can be undone.",
        "ready": "Open a save file to begin.",
        "open": "Open",
        "undo": "Undo",
        "redo": "Redo",
        "save": "Save",
        "save_as": "Save as copy...",
        "restore_backup": "Restore from backup...",
        "export_json": "Export to JSON...",
        "tip_open": "Open another save file (Ctrl+O)",
        "tip_undo": "Undo the last action (Ctrl+Z)",
        "tip_redo": "Redo the undone action (Ctrl+Y)",
        "tip_save": "Write changes to the file. A backup is created first. (Ctrl+S)",
        "tip_save_as": "Write changes to a new file and leave the original untouched",
        "tip_restore": "Bring back the save from a backup if something went wrong",
        "tip_export": "Save the decrypted data in readable form (view only)",
        "profile": "Profile:",
        "slot": "Slot",
        "no_name": "No name",
        "profile_info": "Game version: {ver}   ·   {slot}",
        "tab_simple": "Simple mode",
        "tab_tree": "All data (advanced)",
        "tab_changes": "Changes",
        "filter_all": "All",
        "filter_number": "Numbers",
        "filter_bool": "Yes / No",
        "filter_text": "Text",
        "filter_changed": "Changed",
        "col_name": "Name",
        "col_value": "Value",
        "col_section": "Section",
        "col_field": "Field",
        "col_type": "Type",
        "rows_shown": "Showing {n} of {all}",
        "rows_capped": "Showing the first {shown} of {total} - refine the search to see the rest",
        "search_hint": "Search",
        "panel_empty_title": "Nothing selected",
        "panel_empty_text_simple": "Pick a row in the list on the left. Then type a new value here or press a quick "
                                   "button (for example +1 000).\n\nYou can select several rows at once with Ctrl or "
                                   "Shift.\n\nCan't see the value you need? Start typing its name in the search box "
                                   "(Ctrl+F).",
        "panel_empty_text_tree": "Expand a branch and pick a field. Double-click a field to jump straight to typing."
                                 "\n\nRight-click for more actions (add, delete, copy path).",
        "technical_key": "Technical key",
        "whole_profile": "Whole profile",
        "value_empty": "The value is empty.",
        "set_value": "Set a value...",
        "was": "Was",
        "did_not_exist": "(this field did not exist)",
        "restore_original": "Restore original",
        "advanced_edit": "Advanced edit...",
        "delete": "Delete",
        "show_in_tree": "Show in \"All data\"",
        "container_info_object": "A group of {n} fields.",
        "container_info_array": "A list of {n} items.",
        "add_field": "Add field...",
        "add_item": "Add item...",
        "edit_as_json": "Edit as JSON...",
        "json_hint": "Edit carefully: brackets, quotes and commas must stay in place.",
        "new_value": "New value",
        "not_a_number": "That is not a number",
        "quick_add": "Quick change:",
        "quick_more": "More:",
        "switch": "Switch",
        "yes": "Yes",
        "no": "No",
        "apply": "Apply",
        "cancel": "Cancel",
        "close": "Close",
        "selected_n": "Rows selected: {n}",
        "bulk_numbers_only": "To change several values at once, select numbers only.",
        "bulk_hint": "Type one value for all selected rows, or use the quick buttons - they apply to every row.",
        "set_all_to": "Set all to this value",
        "kind_text": "Text",
        "kind_number": "Number",
        "kind_bool": "Yes/No",
        "kind_null": "Empty",
        "kind_object": "Group",
        "kind_array": "List",
        "kind_profile": "Profile",
        "n_fields": "group · {n} fields",
        "n_items": "list · {n} items",
        "dlg_field_name": "Name of the new field",
        "dlg_type": "Value type",
        "dlg_value_help": "Value (for a group or list use JSON format)",
        "err_bad_value": "Invalid value",
        "err_bad_json": "JSON format error: {err}",
        "err_bad_for_kind": "This value does not fit the type \"{kind}\".",
        "err_empty_name": "The name cannot be empty.",
        "err_key_exists": "A field with this name already exists.",
        "add_hint": "For a plain number choose the type \"Number\", for words choose \"Text\".",
        "add_pick_container": "Select the group or list you want to add to.",
        "big_title": "Very large number",
        "big_text": "You are setting the value {v}. Numbers this large can break the game or the save. "
                    "Apply anyway?",
        "find_title": "Find the save on this computer",
        "find_intro": "The program will look in the usual places where games keep saves (AppData, Documents, "
                      "Steam). This is safe: files are only read.",
        "find_searching": "Searching...",
        "find_scanning": "Looking in: {path}",
        "find_done": "Done. Files found: {n}. Pick one and press \"Open\".",
        "find_none": "Nothing found. Press \"Choose folder...\" or open the file manually.",
        "find_pick_folder": "Choose folder...",
        "find_next": "Find next",
        "collapse_all": "Collapse all",
        "copy_path": "Copy path",
        "copied": "Copied",
        "nothing_found": "Nothing found: {q}",
        "match_n": "Match {pos} of {n}: {path}",
        "changes_intro": "Everything you changed in this profile and have not saved yet. Select rows and press "
                         "\"Restore selected\" to undo exactly those.",
        "chg_what": "What",
        "chg_type": "Action",
        "chg_old": "Was",
        "chg_new": "Now",
        "chg_type_changed": "Changed",
        "chg_type_added": "Added",
        "chg_type_removed": "Removed",
        "no_changes": "No changes yet.",
        "revert_selected": "Restore selected",
        "revert_all": "Discard all changes in this profile",
        "select_first": "Select rows in the list first.",
        "revert_removed_hint": "Removed fields cannot be restored here - press \"Undo\" (Ctrl+Z).",
        "revert_all_ask": "Return this profile to how it was when opened or last saved? All unsaved changes "
                          "in this profile will be lost.",
        "reverted_all": "All changes in the profile were discarded",
        "opened": "Opened: {name}. Profiles: {n}. The file on disk has not been changed yet.",
        "changed_one": "Changed: {name} → {v}",
        "changed_many": "Values changed: {n}",
        "undone": "Action undone",
        "redone": "Action redone",
        "unsaved_n": "● Unsaved changes: {n}",
        "all_saved": "✓ All changes saved",
        "added_ok": "Added: {path}",
        "deleted_ok": "Deleted: {path}",
        "saved_ok": "Saved: {name}",
        "restored_ok": "Save restored from backup",
        "exported_ok": "Exported: {name}",
        "open_title": "Open a Stone Story RPG save",
        "ft_save": "Stone Story save (*.txt)",
        "ft_all": "All files",
        "err_open_title": "Could not open the file",
        "err_open_text": "This file could not be read.\n\nMake sure it is a Stone Story RPG save (usually "
                         "primary_save.txt or save.txt) and that the game is closed.\n\nDetails:\n{detail}",
        "unsaved_title": "Unsaved changes",
        "unsaved_ask": "Unsaved changes will be lost. Continue?",
        "unsaved_quit": "You have unsaved changes. Quit without saving?",
        "save_confirm_title": "Save changes?",
        "save_confirm_text": "The file \"{name}\" will be overwritten.\n\nA backup copy (.bak) is created next to it "
                             "first, and the result is verified.\n\nIs the game closed? If it is running, it may "
                             "overwrite your changes.",
        "err_save_title": "Could not save",
        "err_save_text": "The file was NOT changed.\n\n{detail}",
        "saved_title": "Done!",
        "saved_text": "Saved: {name}\nBackup: {backup}\n\nYou can now start the game and load the save.",
        "save_as_title": "Save a copy of the save",
        "restore_pick": "Pick a backup. The current file is also backed up before it is replaced.",
        "restore": "Restore",
        "restore_ask": "Replace the current file with the backup \"{name}\"?",
        "no_backups": "No backups of this file were found.",
        "export_title": "Export to JSON",
        "exported_text": "Decrypted data saved:\n{name}\n\nThis is a view-only copy that the game cannot read. "
                         "To change your save use the \"Save\" button.",
        "delete_ask": "Delete \"{name}\"?\nType: {kind}\n\nYou can undo this with the \"Undo\" button (Ctrl+Z).",
        "help_title": "Help",
        "ench_btn": "Enchantment...",
        "tab_home": "Home",
        "tab_catalog": "Item catalogue",
        "home_title": "What do you want to change?",
        "home_profile": "Profile: {name}",
        "level_short": "level {n}",
        "home_tip": "Pick a tile to open a clear page for that area. Fields have a \"?\" button with an explanation. Before bulk changes the editor shows old and new values. Everything can be undone (Ctrl+Z).",
        "home_count": "Parameters: {n}",
        "catalog_count_short": "Items in the catalogue: {n}",
        "catalog_tile": "Item catalogue",
        "home_inventory": "Items: find by name, add, change amount, stars and enchantments.",
        "home_resources": "Stone, wood, tar, ki and bronze.",
        "home_cosmetics": "Golden, glitch and prismatic skins.",
        "home_player": "The hero's name, level and experience.",
        "home_quests": "Daily and weekly quests, legend timers.",
        "home_events": "Premium pass, track points and event tasks.",
        "home_progress": "Unlocked locations, workbench, projects and legends.",
        "home_locations": "Star levels (difficulty) of locations.",
        "home_catalog": "Every game item: categories, IDs, descriptions, recipes.",
        "page_player": "Player & profile",
        "page_resources": "Resources",
        "page_cosmetics": "Cosmetics",
        "page_quests": "Quests",
        "page_progress": "Progress",
        "page_locations": "Locations",
        "hint_player": "The hero's name, level and experience. Hover the \"?\" next to a field for an explanation.",
        "hint_resources": "Resources for crafting and projects. If a resource is missing from the save you can add it.",
        "hint_cosmetics": "Item skins. Tick the ones you want; prismatic skins have a colour. Search works by name.",
        "hint_quests": "Quests and legend timers. Quest names are not in the public sources, so their IDs are shown.",
        "hint_progress": "What is unlocked in the game: locations, workbench functions, projects and legends. The buttons open or close a whole group.",
        "hint_locations": "Location stars: 1-5 white, 6-10 cyan, 11-15 yellow, 16-20 green. The maximum depends on the Star Stone level.",
        "page_empty": "This save has no data for this section. Look in \"All data\" or press \"Plain cards\".",
        "max_level_btn": "Maximum level ({n})",
        "name_label": "Player name",
        "player_summary": "Level {lvl}: +{hp} health, chest limit {chests}",
        "res_where": "Found in: {where}",
        "res_missing": "Not in the save",
        "res_add": "Add (0)",
        "res_all_add": "Add to all +",
        "res_all_set": "Set all =",
        "res_bulk_title": "Resources: bulk change",
        "cos_golden": "Golden",
        "cos_glitch": "Glitch",
        "cos_prismatic": "Prismatic",
        "cos_color": "Colour",
        "cos_all_on": "Unlock all: {kind}",
        "cos_all_off": "Remove all: {kind}",
        "cos_summary": "Golden: {a} · Glitch: {b} · Prismatic: {c} (of {n})",
        "nothing_to_change": "Nothing to change: it is already as you ask.",
        "quests_active": "Active quests",
        "quests_weekly": "Weekly quest",
        "quests_timers": "Timers and legends",
        "quests_all_done": "Mark all as completed",
        "quest_n": "Quest {id}",
        "quest_weekly_n": "Weekly: {id}",
        "quest_done_label": "Completed",
        "quest_name_unknown": "The quest's name is not in the public sources, so its ID is shown.",
        "progress_locations": "Locations",
        "progress_workbench": "Workbench",
        "progress_projects": "Projects",
        "progress_legends": "Legends",
        "open_all": "Unlock all",
        "close_all": "Lock all",
        "progress_summary": "Unlocked: {a} of {n}",
        "loc_stars": "Stars",
        "loc_all_set": "Set all locations = ",
        "loc_no_data": "The save has no location star data.",
        "ev_task": "Task {id}",
        "catalog_intro": "A catalogue of real Stone Story RPG items. Type, hand and element are separate characteristics. An ID is shown only where the sources state it; for other items the ID is unknown and they cannot be added blindly.",
        "catalog_pick": "Pick an item in the list on the left - its description, recipe and ID appear here.",
        "catalog_count": "Found: {n} of {total}",
        "cat_filter_all": "All categories",
        "type_filter_all": "All types",
        "only_addable": "Only with a known ID",
        "col_item": "Item",
        "col_item_type": "Type",
        "col_element": "Element",
        "cat_label": "Category",
        "type_label": "Item type",
        "hand_label": "Hand",
        "element_label": "Element",
        "rarity_label": "Rarity",
        "rarity_text": "Items have no fixed \"rarity\": power comes from stars (0-10) and an enchantment (+1...+21, colour from cyan to rainbow).",
        "no_description": "No description found in the sources.",
        "recipe_label": "Recipe",
        "id_source": "ID source",
        "id_unknown": "The ID of this item is not in the sources, so it cannot be added blindly (the game might fail to load the save).",
        "add_to_inventory": "Add to inventory...",
        "add_from_catalog": "Add from catalogue...",
        "wizard_title": "Add an item to the inventory",
        "wizard_intro": "Find an item by name, set the amount and characteristics, then press \"Add\". No IDs or JSON needed: the structure is taken from your own items.",
        "wizard_pick_first": "Pick an item on the left first.",
        "wizard_no_id": "This item has no confirmed ID, so it cannot be added. You can duplicate an item you already have in the inventory (the ⧉ button).",
        "wizard_no_inventory": "No item list (progress_data.inventory_data.itms) was found in this save.",
        "wizard_options": "Item parameters",
        "stars_label": "Stars",
        "stars_hint": "0-{n}",
        "shiny_label": "Shiny",
        "hi_label": "Viewed",
        "element_hint": "Values come from your own items. Empty means no element.",
        "element_none_known": "Your items have no element values, so the list is empty. You can set an element later in \"All fields\".",
        "enchant_label": "Enchantment",
        "ench_none": "No enchantment",
        "ench_none_short": "none",
        "ench_copy": "Copy from my item:",
        "ench_max": "Maximum +{lv} (values as in SSRPGS)",
        "ench_hint": "Quality and seed come from real enchantments in your save or from the SSRPGS example - you do not have to invent them.",
        "tmpl_from": "The structure will be taken from your item \"{name}\"; personal parameters (stars, enchantments) are not copied.",
        "tmpl_minimal": "You have no such item, so the minimal structure is used (as in SSRPGS): ID, amount and data.",
        "add_btn": "Add",
        "wizard_added": "Added: {n} x {name}",
        "wizard_added_more": "Amount increased: {name} +{n}",
        "add_by_id": "Add by ID...",
        "add_by_id_ask": "Enter the item ID (only if you are sure of it):",
        "add_by_id_warn": "The ID \"{id}\" is not among your items and I cannot verify it. A wrong ID may break loading the save. Add anyway?",
        "err_min_value": "The value must be at least {lo}.",
        "not_in_catalog": "not in catalogue",
        "sort_label": "Sort",
        "sort_order": "As in save",
        "sort_name": "By name",
        "sort_count": "By amount",
        "inv_bulk_title": "Inventory: bulk amount change",
        "inv_remove_row": "will be removed",
        "inv_clear_note": "ALL inventory items will be removed. You can undo this (Ctrl+Z).",
        "ench_title": "Enchantment",
        "ench_manual": "- manual -",
        "ench_from": "Like \"{name}\" (+{lv})",
        "ench_preset": "Start from",
        "ench_lv": "Level (+)",
        "ench_ql": "Quality",
        "ench_seed": "Seed",
        "ench_remove": "Remove enchantment",
        "ench_remove_ask": "Remove the enchantment from this item?",
        "ench_need_numbers": "Level, quality and seed must be whole numbers.",
        "ench_out_of_range": "Out of range +1...+{mx}",
        "range_title": "Unusual value",
        "range_warn": "The game documents the range {lo}-{hi}, but you are setting {v}. Apply anyway?",
        "preview_title": "Preview of changes",
        "preview_summary": "Parameters to change: {n}.  Unchanged: {same}.",
        "preview_more": "…and {n} more",
        "preview_apply": "Apply changes",
        "sections_title": "Sections",
        "cat_all": "Everything",
        "cat_inventory": "Inventory",
        "cat_events": "Events & pass",
        "cat_player": "Player & profile",
        "cat_resources": "Resources",
        "cat_quests": "Quests",
        "cat_progress": "Progress",
        "cat_locations": "Locations",
        "cat_cosmetics": "Cosmetics",
        "cat_time": "Time",
        "cat_other": "Other",
        "use_special": "Smart section view",
        "use_generic": "Plain cards",
        "inv_title": "Inventory",
        "inv_count": "Items: {n}",
        "inv_where": "Found in the save at: {path}",
        "inv_add": "Add item...",
        "inv_clear": "Clear inventory",
        "inv_clear_ask": "Delete ALL items ({n})?\n\nYou can undo this with the \"Undo\" button (Ctrl+Z).",
        "inv_bulk_label": "For all shown:",
        "inv_set_all": "Set all =",
        "inv_add_all": "Add to all +",
        "inv_dup": "Duplicate this item",
        "inv_delete": "Delete item",
        "inv_fields": "All fields...",
        "inv_not_found": "The item list could not be found in this save. Press \"Plain cards\" - all values of "
                         "this section are available there, and the \"All data\" tab shows the full structure.",
        "inv_empty": "Nothing found. Check the search.",
        "inv_add_title": "Add item",
        "inv_item_name": "Item name / ID",
        "inv_item_count": "Amount",
        "inv_template": "Use this item as a template",
        "inv_add_hint": "Write the name the same way existing items are written. Other parameters (stars, "
                        "enchantments ...) are copied from the template item below. If the item already exists, "
                        "its amount simply goes up.",
        "inv_no_template": "The inventory is empty, so the item will be simple: name + amount. If the game does not "
                           "understand it, first obtain any item in the game.",
        "inv_added": "Item added: {name}",
        "ev_title": "Events & premium pass",
        "ev_hint": "Every event has a reward track. The premium part is unlocked with the \"Premium pass\" switch "
                   "(it is the pp/premium field in the save). In the game it is granted by a subscription or for "
                   "30 Event Tickets. A full track usually needs 35 points (50 in Green Part 1 and 2).",
        "ev_give_pass": "Give premium pass everywhere",
        "ev_remove_pass": "Remove premium everywhere",
        "ev_pass_name": "Premium pass",
        "ev_points_label": "Points / levels of all events:",
        "ev_set_points": "Set for all",
        "ev_more_fields": "Other fields ({n})",
        "ev_hide_fields": "Hide other fields",
        "ev_none": "No events found in this save. Look in \"All data\" - they may be named differently.",
        "ev_no_pass": "No premium switch found - use the cards below.",
        "ev_no_points": "No points or level fields found - use the cards below.",
        "ev_summary": "Premium on: {on} of {total}",
        "view_cards": "▦  Cards",
        "view_list": "☰  List",
        "tip_view_cards": "Friendly cards with buttons and switches",
        "tip_view_list": "A table of values with an edit panel on the right",
        "card_more": "Show more ({n})",
        "cards_empty": "Nothing found. Try another word or reset the filter to \"All\".",
        "section_general": "General",
        "section_profile": "Profile info",
        "tip_minus": "Decrease",
        "tip_plus": "Increase",
    },
}

HELP: dict[str, list[tuple[str, str]]] = {
    "ru": [
        ("Что это за программа?", """
Редактор открывает файл сохранения Stone Story RPG, расшифровывает его и показывает всё содержимое в виде удобного списка. Вы меняете нужные значения (например, количество золота), а программа сама зашифровывает файл обратно в формат игры.
"""),
        ("Быстрый старт", """
1. Закройте игру.
2. Нажмите «Открыть файл сейва» — или «Найти сейв автоматически», если не знаете, где он лежит.
3. Выберите профиль (персонажа) сверху, если их несколько.
4. В «Простом режиме» найдите нужное значение: прокрутите список или введите часть названия в строку поиска.
5. Нажмите на строку. Справа введите новое значение и нажмите «Применить» (или Enter). Для чисел есть быстрые кнопки: +100, ×2 и т.д.
6. Нажмите «Сохранить». Готово — запускайте игру.
"""),
        ("Где лежит файл сейва?", """
Самый простой путь — кнопка «Найти сейв автоматически». Программа проверит обычные папки (AppData, Документы, Steam).

Вручную: в Steam нажмите правой кнопкой на игру → «Управление» → «Просмотреть локальные файлы». Сохранения чаще всего называются primary_save.txt или save.txt, но могут лежать в другой папке — тогда поищите по этим именам через поиск Windows.
"""),
        ("Главная, каталог и добавление предметов", """
На вкладке «Главная» — плитки: Инвентарь, Ресурсы, Косметика, Игрок, Квесты, Ивенты, Прогресс, Локации и Каталог. Нажмите плитку, и откроется понятная страница раздела. Рядом с полями есть кнопка «?» с объяснением; если поле не описано в открытых источниках, редактор так и пишет и не угадывает.

Чтобы добавить предмет: Инвентарь → «Добавить из каталога…» → найдите предмет по названию → задайте количество, звёзды, shiny, стихию и зачарование → «Добавить». ID и JSON знать не нужно. Структура берётся из ваших предметов, а звёзды и зачарования не копируются. Предметы без известного ID (в каталоге они серые) вслепую добавить нельзя, чтобы не сломать сейв.

Тип предмета, стихия, звёзды и зачарование — отдельные характеристики; их можно фильтровать в инвентаре. Перед массовыми изменениями (все ресурсы, все предметы, весь пропуск, косметика, прогресс) показывается предпросмотр: что изменится, было и стало.
"""),
        ("Разделы: инвентарь, ивенты, профиль", """
Слева в «Простом режиме» — разделы: Инвентарь, Ивенты и пропуск, Игрок, Ресурсы, Квесты, Прогресс, Локации, Косметика, Время, Прочее. Выберите раздел, и в списке останется только его содержимое.

• Инвентарь — карточка на каждый предмет: количество (кнопки − / + и быстрые +10, +100, ×2), галочки вроде «shiny», параметры (звёзды, чары). Можно добавить предмет, сделать копию, удалить, изменить количество сразу у всех показанных предметов или очистить инвентарь.

• Ивенты и пропуск — для каждого ивента переключатель «Премиум-пропуск» (поле pp), очки и уровни дорожки. Кнопка «Выдать премиум-пропуск везде» включает его во всех ивентах, а «Поставить всем» задаёт очки (обычно нужно 35, в Green Part 1 и 2 — 50).

Названия полей в сейве нигде официально не описаны, поэтому разделы определяются по ключевым словам. Если что-то попало не в тот раздел, нажмите «Обычные карточки» или найдите значение поиском — ничего не скрывается, неопознанное лежит в «Прочее».
"""),
        ("Режимы работы", """
• Простой режим — плоский список всех значений с понятными названиями, поиском и фильтрами (числа, Да/Нет, текст, изменённые). Можно выделить несколько чисел и изменить их разом.

• Все данные (для опытных) — полное дерево сейва, как оно устроено внутри. Здесь можно добавлять и удалять поля.

• Изменения — список всего, что вы поменяли. Любое изменение можно вернуть по отдельности.
"""),
        ("Если что-то пошло не так", """
• Кнопка «Отменить» (Ctrl+Z) возвращает последнее действие. Вкладка «Изменения» показывает, что именно изменено.

• Перед каждым сохранением рядом с файлом создаётся резервная копия с датой — например primary_save.txt.20261101_120000.bak. Кнопка «Восстановить из копии…» вернёт любую из них.

• Программа не запишет файл, если проверка после шифрования не прошла — исходный файл останется нетронутым.

• Не удаляйте .bak-файлы, пока не убедитесь, что игра нормально загружает изменённый сейв.
"""),
        ("Важно знать", """
• Закрывайте игру перед сохранением, иначе она может перезаписать файл своими данными.

• Редактор меняет только локальный файл. Покупки, подписки и всё, что проверяет сервер, он не выдаёт и не гарантирует.

• Слишком большие числа (больше ~2 миллиардов) могут сломать игру — программа предупредит об этом.

• Это неофициальная программа, использовать на свой риск. Формат шифрования подогнан под версию игры 4.33.0; если игра обновит формат, редактор придётся обновить.

• Сочетания клавиш: Ctrl+O открыть · Ctrl+S сохранить · Ctrl+Z отменить · Ctrl+Y вернуть · Ctrl+F поиск · F1 помощь.
"""),
    ],
    "en": [
        ("What is this program?", """
The editor opens a Stone Story RPG save file, decrypts it and shows everything in a convenient list. You change the values you want (for example the amount of gold) and the program encrypts the file back into the game's format for you.
"""),
        ("Quick start", """
1. Close the game.
2. Press "Open save file" - or "Find my save automatically" if you don't know where it is.
3. Pick the profile (character) at the top if there are several.
4. In "Simple mode" find the value you want: scroll the list or type part of its name into the search box.
5. Click the row. On the right type a new value and press "Apply" (or Enter). Numbers have quick buttons: +100, x2 and so on.
6. Press "Save". Done - start the game.
"""),
        ("Where is the save file?", """
The easiest way is the "Find my save automatically" button. The program checks the usual folders (AppData, Documents, Steam).

Manually: in Steam right-click the game → Manage → Browse local files. Saves are most often called primary_save.txt or save.txt, but they may live in another folder - search your computer for those names.
"""),
        ("Home, catalogue and adding items", """
The "Home" tab shows tiles: Inventory, Resources, Cosmetics, Player, Quests, Events, Progress, Locations and the Catalogue. Click a tile to open a clear page for that area. Fields have a "?" button with an explanation; if a field is not described in the public sources the editor says so instead of guessing.

To add an item: Inventory → "Add from catalogue..." → find the item by name → set amount, stars, shiny, element and enchantment → "Add". No IDs or JSON needed. The structure is taken from your own items, and stars / enchantments are not copied. Items without a known ID (grey in the catalogue) cannot be added blindly, so your save is not broken.

Item type, element, stars and enchantment are separate characteristics and can be filtered in the inventory. Before bulk changes (all resources, all items, the whole pass, cosmetics, progress) a preview shows what will change: old and new values.
"""),
        ("Sections: inventory, events, profile", """
On the left of "Simple mode" are the sections: Inventory, Events & pass, Player, Resources, Quests, Progress, Locations, Cosmetics, Time, Other. Pick a section and the list shows only its contents.

• Inventory - one card per item: amount (- / + buttons and quick +10, +100, x2), tick boxes such as "shiny", parameters (stars, enchantments). You can add an item, duplicate it, delete it, change the amount of every shown item at once, or clear the inventory.

• Events & pass - for every event a "Premium pass" switch (the pp field), plus the track's points and levels. "Give premium pass everywhere" turns it on in all events, and "Set for all" sets the points (usually 35, 50 in Green Part 1 and 2).

The save's field names are not officially documented, so sections are detected from key words. If something landed in the wrong section press "Plain cards" or find it with search - nothing is hidden, unrecognised values live in "Other".
"""),
        ("Modes", """
• Simple mode - a flat list of all values with readable names, search and filters (numbers, Yes/No, text, changed). You can select several numbers and change them at once.

• All data (advanced) - the full tree of the save as it is stored. You can add and delete fields here.

• Changes - a list of everything you changed. Any change can be restored individually.
"""),
        ("If something goes wrong", """
• "Undo" (Ctrl+Z) reverts the last action. The "Changes" tab shows exactly what was modified.

• Before every save a dated backup is created next to the file - for example primary_save.txt.20261101_120000.bak. "Restore from backup..." brings any of them back.

• The program will not write the file if the post-encryption check fails - your original stays untouched.

• Don't delete .bak files until you are sure the game loads the edited save correctly.
"""),
        ("Good to know", """
• Close the game before saving, otherwise it may overwrite the file with its own data.

• The editor only changes the local file. Purchases, subscriptions and anything verified by a server are not granted and not guaranteed.

• Very large numbers (above ~2 billion) can break the game - the program will warn you.

• This is an unofficial tool, use it at your own risk. The encryption format matches game version 4.33.0; if the game changes the format the editor will need an update.

• Shortcuts: Ctrl+O open · Ctrl+S save · Ctrl+Z undo · Ctrl+Y redo · Ctrl+F search · F1 help.
"""),
    ],
}
