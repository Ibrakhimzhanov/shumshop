from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class CategoryCB(CallbackData, prefix="cat"):
    action: str = "select"
    id: int = 0


class ProductCB(CallbackData, prefix="prod"):
    action: str = "view"
    id: int = 0


class PaymentCB(CallbackData, prefix="pay"):
    action: str = "pay"
    product_id: int = 0


class OrderCB(CallbackData, prefix="order"):
    action: str = "approve"
    order_id: int = 0


class AdminCB(CallbackData, prefix="adm"):
    action: str = ""
    id: int = 0


BUTTON_YOUTUBE = "\U0001f3ac YouTube"
BUTTON_AI = "\U0001f916 AI"
BUTTON_SUPPORT = "\U0001f4de \u041f\u043e\u0434\u0434\u0435\u0440\u0436\u043a\u0430"
BUTTON_ADMIN = "\u2699\ufe0f \u0410\u0434\u043c\u0438\u043d"


def main_menu_reply_kb(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Reply-клавиатура которая всегда видна внизу."""
    keyboard = [
        [KeyboardButton(text=BUTTON_YOUTUBE), KeyboardButton(text=BUTTON_AI)],
        [KeyboardButton(text=BUTTON_SUPPORT)],
    ]
    if is_admin:
        keyboard.append([KeyboardButton(text=BUTTON_ADMIN)])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def category_products_kb(
    products: list, category_id: int
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for p in products:
        builder.button(
            text=p["name"],
            callback_data=ProductCB(action="view", id=p["id"]),
        )
    builder.adjust(1)
    builder.button(
        text="\u2b05\ufe0f \u041d\u0430\u0437\u0430\u0434",
        callback_data=CategoryCB(action="back"),
    )
    builder.adjust(1)
    return builder.as_markup()


def product_card_kb(product_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="\U0001f4b3 \u041e\u043f\u043b\u0430\u0442\u0438\u0442\u044c",
        callback_data=PaymentCB(action="pay", product_id=product_id),
    )
    builder.button(
        text="\u2b05\ufe0f \u041d\u0430\u0437\u0430\u0434",
        callback_data=ProductCB(action="back", id=product_id),
    )
    builder.adjust(1)
    return builder.as_markup()


def confirm_order_kb(order_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="\u2705 \u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0434\u0438\u0442\u044c",
        callback_data=OrderCB(action="approve", order_id=order_id),
    )
    builder.button(
        text="\u274c \u041e\u0442\u043a\u043b\u043e\u043d\u0438\u0442\u044c",
        callback_data=OrderCB(action="reject", order_id=order_id),
    )
    builder.adjust(2)
    return builder.as_markup()


def admin_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="\U0001f4e6 \u0422\u043e\u0432\u0430\u0440\u044b",
        callback_data=AdminCB(action="products"),
    )
    builder.button(
        text="\U0001f4c2 \u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u0438",
        callback_data=AdminCB(action="categories"),
    )
    builder.button(
        text="\U0001f4b3 \u0420\u0435\u043a\u0432\u0438\u0437\u0438\u0442\u044b",
        callback_data=AdminCB(action="requisites"),
    )
    builder.button(
        text="\U0001f4ca \u0417\u0430\u043a\u0430\u0437\u044b",
        callback_data=AdminCB(action="orders"),
    )
    builder.button(
        text="\U0001f4c8 \u0421\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043a\u0430",
        callback_data=AdminCB(action="stats"),
    )
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def admin_categories_kb(categories: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(
            text=cat["name"],
            callback_data=AdminCB(action="edit_cat", id=cat["id"]),
        )
    builder.adjust(1)
    builder.button(
        text="\u2795 \u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c",
        callback_data=AdminCB(action="add_cat"),
    )
    builder.adjust(1)
    return builder.as_markup()


def admin_products_kb(
    products: list, category_id: int
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for p in products:
        builder.button(
            text=p["name"],
            callback_data=AdminCB(action="edit_prod", id=p["id"]),
        )
    builder.adjust(1)
    builder.button(
        text="\u2795 \u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c",
        callback_data=AdminCB(action="add_prod", id=category_id),
    )
    builder.button(
        text="\u2b05\ufe0f \u041d\u0430\u0437\u0430\u0434",
        callback_data=AdminCB(action="products"),
    )
    builder.adjust(1)
    return builder.as_markup()


def admin_product_actions_kb(product_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="\u270f\ufe0f \u0420\u0435\u0434\u0430\u043a\u0442\u0438\u0440\u043e\u0432\u0430\u0442\u044c",
        callback_data=AdminCB(action="edit_product", id=product_id),
    )
    builder.button(
        text="\U0001f5d1 \u0423\u0434\u0430\u043b\u0438\u0442\u044c",
        callback_data=AdminCB(action="del_prod", id=product_id),
    )
    builder.button(
        text="\u2b05\ufe0f \u041d\u0430\u0437\u0430\u0434",
        callback_data=AdminCB(action="back_to_prods", id=product_id),
    )
    builder.adjust(2, 1)
    return builder.as_markup()


def back_to_main_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="\u2b05\ufe0f \u0413\u043b\u0430\u0432\u043d\u043e\u0435 \u043c\u0435\u043d\u044e",
        callback_data=CategoryCB(action="back"),
    )
    return builder.as_markup()
