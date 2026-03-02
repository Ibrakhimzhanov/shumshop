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


# --- /admin command ---


@router.message(Command("admin"))
async def cmd_admin(message: Message, config, state: FSMContext):
    if message.from_user.id != config.admin_id:
        return
    await state.clear()
    await message.answer("\u2699\ufe0f \u0410\u0434\u043c\u0438\u043d-\u043f\u0430\u043d\u0435\u043b\u044c:", reply_markup=admin_menu_kb())


# --- Categories ---


@router.callback_query(AdminCB.filter(F.action == "categories"))
async def cb_categories(callback: CallbackQuery, callback_data: AdminCB, config, db_pool):
    if callback.from_user.id != config.admin_id:
        return
    categories = await get_categories(db_pool)
    await callback.message.edit_text(
        "\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u0438:", reply_markup=admin_categories_kb(categories)
    )
    await callback.answer()


@router.callback_query(AdminCB.filter(F.action == "add_cat"))
async def cb_add_category(callback: CallbackQuery, callback_data: AdminCB, config, state: FSMContext):
    if callback.from_user.id != config.admin_id:
        return
    await state.set_state(AddCategoryState.name)
    await callback.message.edit_text("\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u043d\u043e\u0432\u043e\u0439 \u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u0438:")
    await callback.answer()


@router.message(AddCategoryState.name)
async def process_add_category_name(message: Message, config, state: FSMContext, db_pool):
    if message.from_user.id != config.admin_id:
        return
    cat = await create_category(db_pool, message.text.strip())
    await state.clear()
    categories = await get_categories(db_pool)
    await message.answer(
        f"\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f \"{cat['name']}\" \u0441\u043e\u0437\u0434\u0430\u043d\u0430!",
        reply_markup=admin_categories_kb(categories),
    )


@router.callback_query(AdminCB.filter(F.action == "edit_cat"))
async def cb_edit_category(callback: CallbackQuery, callback_data: AdminCB, config, db_pool):
    if callback.from_user.id != config.admin_id:
        return
    cat = await get_category(db_pool, callback_data.id)
    if not cat:
        await callback.answer("\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u0430", show_alert=True)
        return
    builder = InlineKeyboardBuilder()
    builder.button(
        text="\u041f\u0435\u0440\u0435\u0438\u043c\u0435\u043d\u043e\u0432\u0430\u0442\u044c",
        callback_data=AdminCB(action="rename_cat", id=callback_data.id),
    )
    builder.button(
        text="\u0423\u0434\u0430\u043b\u0438\u0442\u044c",
        callback_data=AdminCB(action="del_cat", id=callback_data.id),
    )
    builder.button(
        text="\u0422\u043e\u0432\u0430\u0440\u044b \u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u0438",
        callback_data=AdminCB(action="cat_prods", id=callback_data.id),
    )
    builder.button(
        text="\u2b05\ufe0f \u041d\u0430\u0437\u0430\u0434",
        callback_data=AdminCB(action="categories"),
    )
    builder.adjust(2, 1, 1)
    await callback.message.edit_text(
        f"\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f: {cat['name']}", reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(AdminCB.filter(F.action == "rename_cat"))
async def cb_rename_category(callback: CallbackQuery, callback_data: AdminCB, config, state: FSMContext):
    if callback.from_user.id != config.admin_id:
        return
    await state.set_state(RenameCategoryState.name)
    await state.update_data(category_id=callback_data.id)
    await callback.message.edit_text("\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043d\u043e\u0432\u043e\u0435 \u043d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u0438:")
    await callback.answer()


@router.message(RenameCategoryState.name)
async def process_rename_category(message: Message, config, state: FSMContext, db_pool):
    if message.from_user.id != config.admin_id:
        return
    data = await state.get_data()
    cat_id = data["category_id"]
    await update_category(db_pool, cat_id, message.text.strip())
    await state.clear()
    categories = await get_categories(db_pool)
    await message.answer(
        "\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f \u043f\u0435\u0440\u0435\u0438\u043c\u0435\u043d\u043e\u0432\u0430\u043d\u0430!",
        reply_markup=admin_categories_kb(categories),
    )


@router.callback_query(AdminCB.filter(F.action == "del_cat"))
async def cb_delete_category(callback: CallbackQuery, callback_data: AdminCB, config, db_pool):
    if callback.from_user.id != config.admin_id:
        return
    await delete_category(db_pool, callback_data.id)
    categories = await get_categories(db_pool)
    await callback.message.edit_text(
        "\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f \u0443\u0434\u0430\u043b\u0435\u043d\u0430!\n\n\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u0438:",
        reply_markup=admin_categories_kb(categories),
    )
    await callback.answer()


# --- Products ---


@router.callback_query(AdminCB.filter(F.action == "products"))
async def cb_products(callback: CallbackQuery, callback_data: AdminCB, config, db_pool):
    if callback.from_user.id != config.admin_id:
        return
    categories = await get_categories(db_pool)
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(
            text=cat["name"],
            callback_data=AdminCB(action="cat_prods", id=cat["id"]),
        )
    builder.button(
        text="\u2b05\ufe0f \u041d\u0430\u0437\u0430\u0434",
        callback_data=AdminCB(action="admin_back"),
    )
    builder.adjust(1)
    await callback.message.edit_text(
        "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044e:", reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(AdminCB.filter(F.action == "cat_prods"))
async def cb_category_products(callback: CallbackQuery, callback_data: AdminCB, config, db_pool):
    if callback.from_user.id != config.admin_id:
        return
    products = await get_products_by_category(db_pool, callback_data.id)
    await callback.message.edit_text(
        "\u0422\u043e\u0432\u0430\u0440\u044b:",
        reply_markup=admin_products_kb(products, callback_data.id),
    )
    await callback.answer()


@router.callback_query(AdminCB.filter(F.action == "add_prod"))
async def cb_add_product(callback: CallbackQuery, callback_data: AdminCB, config, state: FSMContext):
    if callback.from_user.id != config.admin_id:
        return
    await state.set_state(AddProductState.name)
    await state.update_data(category_id=callback_data.id)
    await callback.message.edit_text("\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u0442\u043e\u0432\u0430\u0440\u0430:")
    await callback.answer()


@router.message(AddProductState.name)
async def process_add_product_name(message: Message, config, state: FSMContext):
    if message.from_user.id != config.admin_id:
        return
    await state.update_data(name=message.text.strip())
    await state.set_state(AddProductState.price)
    await message.answer("\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0446\u0435\u043d\u0443 (\u0432 \u0441\u0443\u043c\u0430\u0445):")


@router.message(AddProductState.price)
async def process_add_product_price(message: Message, config, state: FSMContext):
    if message.from_user.id != config.admin_id:
        return
    try:
        price = int(message.text.strip().replace(" ", "").replace(",", ""))
    except ValueError:
        await message.answer("\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043a\u043e\u0440\u0440\u0435\u043a\u0442\u043d\u0443\u044e \u0446\u0435\u043d\u0443 (\u0447\u0438\u0441\u043b\u043e):")
        return
    await state.update_data(price=price)
    await state.set_state(AddProductState.description)
    await message.answer("\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043e\u043f\u0438\u0441\u0430\u043d\u0438\u0435 \u0442\u043e\u0432\u0430\u0440\u0430:")


@router.message(AddProductState.description)
async def process_add_product_desc(message: Message, config, state: FSMContext):
    if message.from_user.id != config.admin_id:
        return
    await state.update_data(description=message.text.strip())
    await state.set_state(AddProductState.post_purchase_info)
    await message.answer("\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0438\u043d\u0441\u0442\u0440\u0443\u043a\u0446\u0438\u044e \u043f\u043e\u0441\u043b\u0435 \u043f\u043e\u043a\u0443\u043f\u043a\u0438:")


@router.message(AddProductState.post_purchase_info)
async def process_add_product_post_info(message: Message, config, state: FSMContext, db_pool):
    if message.from_user.id != config.admin_id:
        return
    data = await state.get_data()
    product = await create_product(
        db_pool,
        category_id=data["category_id"],
        name=data["name"],
        price=data["price"],
        description=data["description"],
        post_purchase_info=message.text.strip(),
    )
    await state.clear()
    products = await get_products_by_category(db_pool, data["category_id"])
    await message.answer(
        f"\u0422\u043e\u0432\u0430\u0440 \"{product['name']}\" \u0434\u043e\u0431\u0430\u0432\u043b\u0435\u043d!",
        reply_markup=admin_products_kb(products, data["category_id"]),
    )


# --- Product View / Edit / Delete ---


@router.callback_query(AdminCB.filter(F.action == "edit_prod"))
async def cb_view_product(callback: CallbackQuery, callback_data: AdminCB, config, db_pool):
    if callback.from_user.id != config.admin_id:
        return
    product = await get_product(db_pool, callback_data.id)
    if not product:
        await callback.answer("\u0422\u043e\u0432\u0430\u0440 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d", show_alert=True)
        return
    text = (
        f"<b>{product['name']}</b>\n\n"
        f"\u0426\u0435\u043d\u0430: {product['price']:,} \u0441\u0443\u043c\n"
        f"\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435: {product['description'] or '\u2014'}\n"
        f"\u0418\u043d\u0441\u0442\u0440\u0443\u043a\u0446\u0438\u044f: {product['post_purchase_info'] or '\u2014'}"
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
        ("\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435", "name"),
        ("\u0426\u0435\u043d\u0430", "price"),
        ("\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435", "description"),
        ("\u0418\u043d\u0441\u0442\u0440\u0443\u043a\u0446\u0438\u044f", "post_purchase_info"),
    ]
    for label, field in fields:
        builder.button(
            text=label,
            callback_data=f"adm_edit:{callback_data.id}:{field}",
        )
    builder.button(
        text="\u2b05\ufe0f \u041d\u0430\u0437\u0430\u0434",
        callback_data=AdminCB(action="edit_prod", id=callback_data.id),
    )
    builder.adjust(2, 2, 1)
    await callback.message.edit_text(
        "\u0427\u0442\u043e \u0440\u0435\u0434\u0430\u043a\u0442\u0438\u0440\u043e\u0432\u0430\u0442\u044c?", reply_markup=builder.as_markup()
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
        "name": "\u043d\u0430\u0437\u0432\u0430\u043d\u0438\u0435",
        "price": "\u0446\u0435\u043d\u0443 (\u0432 \u0441\u0443\u043c\u0430\u0445)",
        "description": "\u043e\u043f\u0438\u0441\u0430\u043d\u0438\u0435",
        "post_purchase_info": "\u0438\u043d\u0441\u0442\u0440\u0443\u043a\u0446\u0438\u044e \u043f\u043e\u0441\u043b\u0435 \u043f\u043e\u043a\u0443\u043f\u043a\u0438",
    }
    await state.set_state(EditProductState.value)
    await state.update_data(product_id=product_id, field=field)
    await callback.message.edit_text(f"\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043d\u043e\u0432\u043e\u0435 {field_labels[field]}:")
    await callback.answer()


@router.message(EditProductState.value)
async def process_edit_product_value(message: Message, config, state: FSMContext, db_pool):
    if message.from_user.id != config.admin_id:
        return
    data = await state.get_data()
    product_id = data["product_id"]
    field = data["field"]
    value = message.text.strip()
    if field == "price":
        try:
            value = int(value.replace(" ", "").replace(",", ""))
        except ValueError:
            await message.answer("\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043a\u043e\u0440\u0440\u0435\u043a\u0442\u043d\u0443\u044e \u0446\u0435\u043d\u0443 (\u0447\u0438\u0441\u043b\u043e):")
            return
    await update_product(db_pool, product_id, **{field: value})
    await state.clear()
    product = await get_product(db_pool, product_id)
    text = (
        f"<b>{product['name']}</b>\n\n"
        f"\u0426\u0435\u043d\u0430: {product['price']:,} \u0441\u0443\u043c\n"
        f"\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435: {product['description'] or '\u2014'}\n"
        f"\u0418\u043d\u0441\u0442\u0440\u0443\u043a\u0446\u0438\u044f: {product['post_purchase_info'] or '\u2014'}"
    )
    await message.answer(
        f"\u041e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u043e!\n\n{text}",
        reply_markup=admin_product_actions_kb(product_id),
        parse_mode="HTML",
    )


@router.callback_query(AdminCB.filter(F.action == "del_prod"))
async def cb_delete_product(callback: CallbackQuery, callback_data: AdminCB, config, db_pool):
    if callback.from_user.id != config.admin_id:
        return
    product = await get_product(db_pool, callback_data.id)
    if not product:
        await callback.answer("\u0422\u043e\u0432\u0430\u0440 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d", show_alert=True)
        return
    category_id = product["category_id"]
    await delete_product(db_pool, callback_data.id)
    products = await get_products_by_category(db_pool, category_id)
    await callback.message.edit_text(
        "\u0422\u043e\u0432\u0430\u0440 \u0443\u0434\u0430\u043b\u0451\u043d!\n\n\u0422\u043e\u0432\u0430\u0440\u044b:",
        reply_markup=admin_products_kb(products, category_id),
    )
    await callback.answer()


@router.callback_query(AdminCB.filter(F.action == "back_to_prods"))
async def cb_back_to_products(callback: CallbackQuery, callback_data: AdminCB, config, db_pool):
    if callback.from_user.id != config.admin_id:
        return
    product = await get_product(db_pool, callback_data.id)
    if not product:
        await callback.answer()
        return
    category_id = product["category_id"]
    products = await get_products_by_category(db_pool, category_id)
    await callback.message.edit_text(
        "\u0422\u043e\u0432\u0430\u0440\u044b:",
        reply_markup=admin_products_kb(products, category_id),
    )
    await callback.answer()


# --- Settings ---


@router.callback_query(AdminCB.filter(F.action == "requisites"))
async def cb_settings(callback: CallbackQuery, callback_data: AdminCB, config, db_pool):
    if callback.from_user.id != config.admin_id:
        return
    card_number = await get_setting(db_pool, "card_number") or "\u043d\u0435 \u0437\u0430\u0434\u0430\u043d"
    card_holder = await get_setting(db_pool, "card_holder") or "\u043d\u0435 \u0437\u0430\u0434\u0430\u043d"
    builder = InlineKeyboardBuilder()
    builder.button(
        text="\u0418\u0437\u043c\u0435\u043d\u0438\u0442\u044c \u043d\u043e\u043c\u0435\u0440 \u043a\u0430\u0440\u0442\u044b",
        callback_data="adm_set:card_number",
    )
    builder.button(
        text="\u0418\u0437\u043c\u0435\u043d\u0438\u0442\u044c \u0424\u0418\u041e",
        callback_data="adm_set:card_holder",
    )
    builder.button(
        text="\u2b05\ufe0f \u041d\u0430\u0437\u0430\u0434",
        callback_data=AdminCB(action="admin_back"),
    )
    builder.adjust(1)
    await callback.message.edit_text(
        f"\u0420\u0435\u043a\u0432\u0438\u0437\u0438\u0442\u044b:\n\n"
        f"\u041d\u043e\u043c\u0435\u0440 \u043a\u0430\u0440\u0442\u044b: <b>{card_number}</b>\n"
        f"\u0424\u0418\u041e: <b>{card_holder}</b>",
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
        "card_number": "\u043d\u043e\u043c\u0435\u0440 \u043a\u0430\u0440\u0442\u044b",
        "card_holder": "\u0424\u0418\u041e \u0432\u043b\u0430\u0434\u0435\u043b\u044c\u0446\u0430 \u043a\u0430\u0440\u0442\u044b",
    }
    await state.set_state(EditSettingState.value)
    await state.update_data(key=key)
    await callback.message.edit_text(f"\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043d\u043e\u0432\u044b\u0439 {labels[key]}:")
    await callback.answer()


@router.message(EditSettingState.value)
async def process_edit_setting(message: Message, config, state: FSMContext, db_pool):
    if message.from_user.id != config.admin_id:
        return
    data = await state.get_data()
    key = data["key"]
    await set_setting(db_pool, key, message.text.strip())
    await state.clear()
    card_number = await get_setting(db_pool, "card_number") or "\u043d\u0435 \u0437\u0430\u0434\u0430\u043d"
    card_holder = await get_setting(db_pool, "card_holder") or "\u043d\u0435 \u0437\u0430\u0434\u0430\u043d"
    builder = InlineKeyboardBuilder()
    builder.button(
        text="\u0418\u0437\u043c\u0435\u043d\u0438\u0442\u044c \u043d\u043e\u043c\u0435\u0440 \u043a\u0430\u0440\u0442\u044b",
        callback_data="adm_set:card_number",
    )
    builder.button(
        text="\u0418\u0437\u043c\u0435\u043d\u0438\u0442\u044c \u0424\u0418\u041e",
        callback_data="adm_set:card_holder",
    )
    builder.button(
        text="\u2b05\ufe0f \u041d\u0430\u0437\u0430\u0434",
        callback_data=AdminCB(action="admin_back"),
    )
    builder.adjust(1)
    await message.answer(
        f"\u041e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u043e!\n\n\u0420\u0435\u043a\u0432\u0438\u0437\u0438\u0442\u044b:\n\n"
        f"\u041d\u043e\u043c\u0435\u0440 \u043a\u0430\u0440\u0442\u044b: <b>{card_number}</b>\n"
        f"\u0424\u0418\u041e: <b>{card_holder}</b>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )


# --- Orders ---


@router.callback_query(AdminCB.filter(F.action == "orders"))
async def cb_orders(callback: CallbackQuery, callback_data: AdminCB, config, db_pool):
    if callback.from_user.id != config.admin_id:
        return
    orders = await get_recent_orders(db_pool, limit=10)
    if not orders:
        builder = InlineKeyboardBuilder()
        builder.button(
            text="\u2b05\ufe0f \u041d\u0430\u0437\u0430\u0434",
            callback_data=AdminCB(action="admin_back"),
        )
        await callback.message.edit_text(
            "\u0417\u0430\u043a\u0430\u0437\u043e\u0432 \u043f\u043e\u043a\u0430 \u043d\u0435\u0442.", reply_markup=builder.as_markup()
        )
        await callback.answer()
        return
    status_map = {
        "pending": "\u041e\u0436\u0438\u0434\u0430\u0435\u0442",
        "approved": "\u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0451\u043d",
        "rejected": "\u041e\u0442\u043a\u043b\u043e\u043d\u0451\u043d",
    }
    lines = []
    for o in orders:
        status_label = status_map.get(o["status"], o["status"])
        lines.append(
            f"#{o['id']} | {o['product_name']} | "
            f"@{o['username'] or '\u2014'} | {status_label}"
        )
    text = "\u041f\u043e\u0441\u043b\u0435\u0434\u043d\u0438\u0435 \u0437\u0430\u043a\u0430\u0437\u044b:\n\n" + "\n".join(lines)
    builder = InlineKeyboardBuilder()
    builder.button(
        text="\u2b05\ufe0f \u041d\u0430\u0437\u0430\u0434",
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
        "\u2699\ufe0f \u0410\u0434\u043c\u0438\u043d-\u043f\u0430\u043d\u0435\u043b\u044c:", reply_markup=admin_menu_kb()
    )
    await callback.answer()
