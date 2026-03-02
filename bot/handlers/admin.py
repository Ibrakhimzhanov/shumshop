from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards import (
    AdminCB,
    admin_menu_kb,
    admin_categories_kb,
    admin_products_kb,
    admin_product_actions_kb,
)
from bot.models import (
    get_categories,
    get_category,
    create_category,
    update_category,
    delete_category,
    get_products_by_category,
    get_product,
    create_product,
    update_product,
    delete_product,
    get_recent_orders,
    get_setting,
    set_setting,
)

router = Router()


# --- FSM States ---


class AddCategoryState(StatesGroup):
    name = State()


class RenameCategoryState(StatesGroup):
    category_id = State()
    name = State()


class AddProductState(StatesGroup):
    category_id = State()
    name = State()
    price = State()
    description = State()
    post_purchase_info = State()


class EditProductState(StatesGroup):
    product_id = State()
    field = State()
    value = State()


class EditSettingState(StatesGroup):
    key = State()
    value = State()


# --- Helper ---


def _pool(event: Message | CallbackQuery):
    return event.bot["db_pool"]


# --- /admin command ---


@router.message(Command("admin"))
async def cmd_admin(message: Message, config, state: FSMContext):
    if message.from_user.id != config.admin_id:
        return
    await state.clear()
    await message.answer("Админ-панель:", reply_markup=admin_menu_kb())


# --- Categories ---


@router.callback_query(AdminCB.filter(F.action == "categories"))
async def cb_categories(callback: CallbackQuery, callback_data: AdminCB, config):
    if callback.from_user.id != config.admin_id:
        return
    pool = _pool(callback)
    categories = await get_categories(pool)
    await callback.message.edit_text(
        "Категории:", reply_markup=admin_categories_kb(categories)
    )
    await callback.answer()


@router.callback_query(AdminCB.filter(F.action == "add_cat"))
async def cb_add_category(callback: CallbackQuery, callback_data: AdminCB, config, state: FSMContext):
    if callback.from_user.id != config.admin_id:
        return
    await state.set_state(AddCategoryState.name)
    await callback.message.edit_text("Введите название новой категории:")
    await callback.answer()


@router.message(AddCategoryState.name)
async def process_add_category_name(message: Message, config, state: FSMContext):
    if message.from_user.id != config.admin_id:
        return
    pool = _pool(message)
    cat = await create_category(pool, message.text.strip())
    await state.clear()
    categories = await get_categories(pool)
    await message.answer(
        f"Категория \"{cat['name']}\" создана!",
        reply_markup=admin_categories_kb(categories),
    )


@router.callback_query(AdminCB.filter(F.action == "edit_cat"))
async def cb_edit_category(callback: CallbackQuery, callback_data: AdminCB, config):
    if callback.from_user.id != config.admin_id:
        return
    pool = _pool(callback)
    cat = await get_category(pool, callback_data.id)
    if not cat:
        await callback.answer("Категория не найдена", show_alert=True)
        return
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Переименовать",
        callback_data=AdminCB(action="rename_cat", id=callback_data.id),
    )
    builder.button(
        text="Удалить",
        callback_data=AdminCB(action="del_cat", id=callback_data.id),
    )
    builder.button(
        text="Товары категории",
        callback_data=AdminCB(action="cat_prods", id=callback_data.id),
    )
    builder.button(
        text="\u2b05\ufe0f Назад",
        callback_data=AdminCB(action="categories"),
    )
    builder.adjust(2, 1, 1)
    await callback.message.edit_text(
        f"Категория: {cat['name']}", reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(AdminCB.filter(F.action == "rename_cat"))
async def cb_rename_category(callback: CallbackQuery, callback_data: AdminCB, config, state: FSMContext):
    if callback.from_user.id != config.admin_id:
        return
    await state.set_state(RenameCategoryState.name)
    await state.update_data(category_id=callback_data.id)
    await callback.message.edit_text("Введите новое название категории:")
    await callback.answer()


@router.message(RenameCategoryState.name)
async def process_rename_category(message: Message, config, state: FSMContext):
    if message.from_user.id != config.admin_id:
        return
    pool = _pool(message)
    data = await state.get_data()
    cat_id = data["category_id"]
    await update_category(pool, cat_id, message.text.strip())
    await state.clear()
    categories = await get_categories(pool)
    await message.answer(
        "Категория переименована!",
        reply_markup=admin_categories_kb(categories),
    )


@router.callback_query(AdminCB.filter(F.action == "del_cat"))
async def cb_delete_category(callback: CallbackQuery, callback_data: AdminCB, config):
    if callback.from_user.id != config.admin_id:
        return
    pool = _pool(callback)
    await delete_category(pool, callback_data.id)
    categories = await get_categories(pool)
    await callback.message.edit_text(
        "Категория удалена!\n\nКатегории:",
        reply_markup=admin_categories_kb(categories),
    )
    await callback.answer()


# --- Products ---


@router.callback_query(AdminCB.filter(F.action == "products"))
async def cb_products(callback: CallbackQuery, callback_data: AdminCB, config):
    if callback.from_user.id != config.admin_id:
        return
    pool = _pool(callback)
    categories = await get_categories(pool)
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(
            text=cat["name"],
            callback_data=AdminCB(action="cat_prods", id=cat["id"]),
        )
    builder.button(
        text="\u2b05\ufe0f Назад",
        callback_data=AdminCB(action="admin_back"),
    )
    builder.adjust(1)
    await callback.message.edit_text(
        "Выберите категорию:", reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(AdminCB.filter(F.action == "cat_prods"))
async def cb_category_products(callback: CallbackQuery, callback_data: AdminCB, config):
    if callback.from_user.id != config.admin_id:
        return
    pool = _pool(callback)
    products = await get_products_by_category(pool, callback_data.id)
    await callback.message.edit_text(
        "Товары:",
        reply_markup=admin_products_kb(products, callback_data.id),
    )
    await callback.answer()


@router.callback_query(AdminCB.filter(F.action == "add_prod"))
async def cb_add_product(callback: CallbackQuery, callback_data: AdminCB, config, state: FSMContext):
    if callback.from_user.id != config.admin_id:
        return
    await state.set_state(AddProductState.name)
    await state.update_data(category_id=callback_data.id)
    await callback.message.edit_text("Введите название товара:")
    await callback.answer()


@router.message(AddProductState.name)
async def process_add_product_name(message: Message, config, state: FSMContext):
    if message.from_user.id != config.admin_id:
        return
    await state.update_data(name=message.text.strip())
    await state.set_state(AddProductState.price)
    await message.answer("Введите цену (в сумах):")


@router.message(AddProductState.price)
async def process_add_product_price(message: Message, config, state: FSMContext):
    if message.from_user.id != config.admin_id:
        return
    try:
        price = int(message.text.strip().replace(" ", "").replace(",", ""))
    except ValueError:
        await message.answer("Введите корректную цену (число):")
        return
    await state.update_data(price=price)
    await state.set_state(AddProductState.description)
    await message.answer("Введите описание товара:")


@router.message(AddProductState.description)
async def process_add_product_desc(message: Message, config, state: FSMContext):
    if message.from_user.id != config.admin_id:
        return
    await state.update_data(description=message.text.strip())
    await state.set_state(AddProductState.post_purchase_info)
    await message.answer("Введите инструкцию после покупки:")


@router.message(AddProductState.post_purchase_info)
async def process_add_product_post_info(message: Message, config, state: FSMContext):
    if message.from_user.id != config.admin_id:
        return
    pool = _pool(message)
    data = await state.get_data()
    product = await create_product(
        pool,
        category_id=data["category_id"],
        name=data["name"],
        price=data["price"],
        description=data["description"],
        post_purchase_info=message.text.strip(),
    )
    await state.clear()
    products = await get_products_by_category(pool, data["category_id"])
    await message.answer(
        f"Товар \"{product['name']}\" добавлен!",
        reply_markup=admin_products_kb(products, data["category_id"]),
    )


# --- Product View / Edit / Delete ---


@router.callback_query(AdminCB.filter(F.action == "edit_prod"))
async def cb_view_product(callback: CallbackQuery, callback_data: AdminCB, config):
    if callback.from_user.id != config.admin_id:
        return
    pool = _pool(callback)
    product = await get_product(pool, callback_data.id)
    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return
    text = (
        f"<b>{product['name']}</b>\n\n"
        f"Цена: {product['price']:,} сум\n"
        f"Описание: {product['description'] or '—'}\n"
        f"Инструкция: {product['post_purchase_info'] or '—'}"
    )
    await callback.message.edit_text(
        text,
        reply_markup=admin_product_actions_kb(callback_data.id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(AdminCB.filter(F.action == "edit_product"))
async def cb_edit_product(callback: CallbackQuery, callback_data: AdminCB, config):
    if callback.from_user.id != config.admin_id:
        return
    builder = InlineKeyboardBuilder()
    fields = [
        ("Название", "name"),
        ("Цена", "price"),
        ("Описание", "description"),
        ("Инструкция", "post_purchase_info"),
    ]
    for label, field in fields:
        builder.button(
            text=label,
            callback_data=f"adm_edit:{callback_data.id}:{field}",
        )
    builder.button(
        text="\u2b05\ufe0f Назад",
        callback_data=AdminCB(action="edit_prod", id=callback_data.id),
    )
    builder.adjust(2, 2, 1)
    await callback.message.edit_text(
        "Что редактировать?", reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm_edit:"))
async def cb_edit_product_field(callback: CallbackQuery, config, state: FSMContext):
    if callback.from_user.id != config.admin_id:
        return
    parts = callback.data.split(":")
    product_id = int(parts[1])
    field = parts[2]
    field_labels = {
        "name": "название",
        "price": "цену (в сумах)",
        "description": "описание",
        "post_purchase_info": "инструкцию после покупки",
    }
    await state.set_state(EditProductState.value)
    await state.update_data(product_id=product_id, field=field)
    await callback.message.edit_text(f"Введите новое {field_labels[field]}:")
    await callback.answer()


@router.message(EditProductState.value)
async def process_edit_product_value(message: Message, config, state: FSMContext):
    if message.from_user.id != config.admin_id:
        return
    pool = _pool(message)
    data = await state.get_data()
    product_id = data["product_id"]
    field = data["field"]
    value = message.text.strip()
    if field == "price":
        try:
            value = int(value.replace(" ", "").replace(",", ""))
        except ValueError:
            await message.answer("Введите корректную цену (число):")
            return
    await update_product(pool, product_id, **{field: value})
    await state.clear()
    product = await get_product(pool, product_id)
    text = (
        f"<b>{product['name']}</b>\n\n"
        f"Цена: {product['price']:,} сум\n"
        f"Описание: {product['description'] or '—'}\n"
        f"Инструкция: {product['post_purchase_info'] or '—'}"
    )
    await message.answer(
        f"Обновлено!\n\n{text}",
        reply_markup=admin_product_actions_kb(product_id),
        parse_mode="HTML",
    )


@router.callback_query(AdminCB.filter(F.action == "del_prod"))
async def cb_delete_product(callback: CallbackQuery, callback_data: AdminCB, config):
    if callback.from_user.id != config.admin_id:
        return
    pool = _pool(callback)
    product = await get_product(pool, callback_data.id)
    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return
    category_id = product["category_id"]
    await delete_product(pool, callback_data.id)
    products = await get_products_by_category(pool, category_id)
    await callback.message.edit_text(
        "Товар удалён!\n\nТовары:",
        reply_markup=admin_products_kb(products, category_id),
    )
    await callback.answer()


@router.callback_query(AdminCB.filter(F.action == "back_to_prods"))
async def cb_back_to_products(callback: CallbackQuery, callback_data: AdminCB, config):
    if callback.from_user.id != config.admin_id:
        return
    pool = _pool(callback)
    product = await get_product(pool, callback_data.id)
    if not product:
        await callback.answer()
        return
    category_id = product["category_id"]
    products = await get_products_by_category(pool, category_id)
    await callback.message.edit_text(
        "Товары:",
        reply_markup=admin_products_kb(products, category_id),
    )
    await callback.answer()


# --- Settings (Реквизиты) ---


@router.callback_query(AdminCB.filter(F.action == "requisites"))
async def cb_settings(callback: CallbackQuery, callback_data: AdminCB, config):
    if callback.from_user.id != config.admin_id:
        return
    pool = _pool(callback)
    card_number = await get_setting(pool, "card_number") or "не задан"
    card_holder = await get_setting(pool, "card_holder") or "не задан"
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Изменить номер карты",
        callback_data=f"adm_set:card_number",
    )
    builder.button(
        text="Изменить ФИО",
        callback_data=f"adm_set:card_holder",
    )
    builder.button(
        text="\u2b05\ufe0f Назад",
        callback_data=AdminCB(action="admin_back"),
    )
    builder.adjust(1)
    await callback.message.edit_text(
        f"Реквизиты:\n\n"
        f"Номер карты: <b>{card_number}</b>\n"
        f"ФИО: <b>{card_holder}</b>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm_set:"))
async def cb_edit_setting(callback: CallbackQuery, config, state: FSMContext):
    if callback.from_user.id != config.admin_id:
        return
    key = callback.data.split(":")[1]
    labels = {
        "card_number": "номер карты",
        "card_holder": "ФИО владельца карты",
    }
    await state.set_state(EditSettingState.value)
    await state.update_data(key=key)
    await callback.message.edit_text(f"Введите новый {labels[key]}:")
    await callback.answer()


@router.message(EditSettingState.value)
async def process_edit_setting(message: Message, config, state: FSMContext):
    if message.from_user.id != config.admin_id:
        return
    pool = _pool(message)
    data = await state.get_data()
    key = data["key"]
    await set_setting(pool, key, message.text.strip())
    await state.clear()
    card_number = await get_setting(pool, "card_number") or "не задан"
    card_holder = await get_setting(pool, "card_holder") or "не задан"
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Изменить номер карты",
        callback_data=f"adm_set:card_number",
    )
    builder.button(
        text="Изменить ФИО",
        callback_data=f"adm_set:card_holder",
    )
    builder.button(
        text="\u2b05\ufe0f Назад",
        callback_data=AdminCB(action="admin_back"),
    )
    builder.adjust(1)
    await message.answer(
        f"Обновлено!\n\nРеквизиты:\n\n"
        f"Номер карты: <b>{card_number}</b>\n"
        f"ФИО: <b>{card_holder}</b>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )


# --- Orders ---


@router.callback_query(AdminCB.filter(F.action == "orders"))
async def cb_orders(callback: CallbackQuery, callback_data: AdminCB, config):
    if callback.from_user.id != config.admin_id:
        return
    pool = _pool(callback)
    orders = await get_recent_orders(pool, limit=10)
    if not orders:
        builder = InlineKeyboardBuilder()
        builder.button(
            text="\u2b05\ufe0f Назад",
            callback_data=AdminCB(action="admin_back"),
        )
        await callback.message.edit_text(
            "Заказов пока нет.", reply_markup=builder.as_markup()
        )
        await callback.answer()
        return
    status_map = {
        "pending": "Ожидает",
        "approved": "Подтверждён",
        "rejected": "Отклонён",
    }
    lines = []
    for o in orders:
        status_label = status_map.get(o["status"], o["status"])
        lines.append(
            f"#{o['id']} | {o['product_name']} | "
            f"@{o['username'] or '—'} | {status_label}"
        )
    text = "Последние заказы:\n\n" + "\n".join(lines)
    builder = InlineKeyboardBuilder()
    builder.button(
        text="\u2b05\ufe0f Назад",
        callback_data=AdminCB(action="admin_back"),
    )
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


# --- Back to Admin Menu ---


@router.callback_query(AdminCB.filter(F.action == "admin_back"))
async def cb_admin_back(callback: CallbackQuery, callback_data: AdminCB, config):
    if callback.from_user.id != config.admin_id:
        return
    await callback.message.edit_text(
        "Админ-панель:", reply_markup=admin_menu_kb()
    )
    await callback.answer()
