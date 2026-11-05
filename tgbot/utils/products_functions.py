# - *- coding: utf- 8 - *-
from collections import defaultdict
from typing import DefaultDict, List, Optional, Tuple

from tgbot.database import Categoryx, Itemx, Settingsx, Positionx, ModelCategory, ModelPosition

SYMBOLS_LIMIT = 4_000  # Кол-во макс символов в сообщение


# Наличие товаров
async def get_items_available(remover: int) -> Tuple[str, int, int]:
    get_categories = await Categoryx().get_all()
    get_positions = await Positionx().get_all()

    item_counts = await Positionx().item_counts()

    positions_by_category: DefaultDict[int, List[Tuple[str, float, int]]] = defaultdict(list)
    for position in get_positions:
        in_stock = item_counts.get(position.position_id, 0)

        if in_stock > 0:
            positions_by_category[position.category_id].append(
                (position.position_name, position.position_price, in_stock)
            )

    category_sections: List[Tuple[str, List[Tuple[str, float, int]]]] = []
    for category in get_categories:
        category_positions = positions_by_category.get(category.category_id, [])

        if len(category_positions) == 0:
            continue

        category_sections.append((category.category_name, category_positions))

    pages = parse_items_available(category_sections)
    max_page = len(pages)

    if max_page == 0:
        return "", 0, 0

    remover = max(0, min(remover, max_page - 1))

    return pages[remover], max_page, remover


# Форматирование товаров для вывода наличия
def _format_position_line(
        position_name: str,
        position_price: float,
        in_stock: int,
        max_len: Optional[int] = None,
) -> str:
    prefix = "• "
    suffix = f" - {position_price}₽ - {in_stock} шт"
    full_line = f"{prefix}{position_name}{suffix}"

    if max_len is None or len(full_line) <= max_len:
        return full_line

    max_name_len = max(1, max_len - len(prefix) - len(suffix) - 1)
    short_name = f"{position_name[:max_name_len]}..."

    return f"{prefix}{short_name}{suffix}"


# Перебор товаров в списке для вывода
def parse_items_available(category_sections: List[Tuple[str, List[Tuple[str, float, int]]]]) -> List[str]:
    current_page = ""
    pages: List[str] = []

    for category_name, positions in category_sections:
        header_category = f"<b>➖➖➖ {category_name} ➖➖➖</b>"

        header_block = header_category if current_page == "" else f"\n\n{header_category}"
        candidate_with_header = current_page + header_block

        if len(candidate_with_header) > SYMBOLS_LIMIT:
            if current_page != "":
                pages.append(current_page)
            current_page = header_category
        else:
            current_page = candidate_with_header

        for position_name, position_price, in_stock in positions:
            line = _format_position_line(position_name, position_price, in_stock)
            candidate_with_line = current_page + f"\n{line}"

            if len(candidate_with_line) > SYMBOLS_LIMIT:
                if current_page != "":
                    pages.append(current_page)

                current_page = header_category

                remain_len = SYMBOLS_LIMIT - len(current_page) - 1
                line = _format_position_line(position_name, position_price, in_stock, max_len=remain_len)
                current_page += f"\n{line}"
            else:
                current_page = candidate_with_line

    if current_page != "":
        pages.append(current_page)

    return pages


# Получение категорий с товарами
async def get_categories_items() -> List[ModelCategory]:
    get_settings = await Settingsx().get()

    get_categories = await Categoryx().get_all()

    save_categories = []

    if get_settings.misc_hide_category == "True":
        for category in get_categories:
            get_positions = await get_positions_items(category.category_id)

            if len(get_positions) >= 1:
                save_categories.append(category)
    else:
        save_categories = get_categories

    return save_categories


# Получение позиций с товарами
async def get_positions_items(category_id: int) -> List[ModelPosition]:
    get_settings = await Settingsx().get()

    get_positions = await Positionx().gets(category_id=category_id)

    save_positions = []

    if get_settings.misc_hide_position == "True":
        for position in get_positions:
            get_items = await Itemx().gets(position_id=position.position_id)

            if len(get_items) >= 1:
                save_positions.append(position)
    else:
        save_positions = get_positions

    return save_positions
