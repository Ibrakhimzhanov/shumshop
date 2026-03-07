import logging
import math

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.smm_raja import get_youtube_services, add_order, order_status, SMMRajaError
from bot.keyboards import (
    SmmTypeCB,
    SmmServiceCB,
    SmmOrderCB,
    smm_types_kb,
    smm_services_kb,
)
from bot.models import get_setting, create_order, update_order_status

router = Router()
logger = logging.getLogger(__name__)

# ---------- FSM ----------


class SmmState(StatesGroup):
    waiting_link = State()
    waiting_quantity = State()
    waiting_receipt = State()


# ---------- In-memory storage ----------

_smm_data: dict[int, dict] = {}  # order_id -> {service_id, service_name, link, quantity, user_id, price}

# ---------- Cached services ----------

_services_cache: dict[str, list[dict]] = {}


# ---------- Back to SMM menu keyboard ----------


def _back_to_smm_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="\u2b05\ufe0f \u041d\u0430\u0437\u0430\u0434",
        callback_data=SmmTypeCB(type="menu"),
    )
    return builder.as_markup()


# ---------- Admin confirm / reject keyboard ----------


def smm_confirm_kb(order_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="\u2705 \u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0434\u0438\u0442\u044c",
        callback_data=SmmOrderCB(action="approve", order_id=order_id),
    )
    builder.button(
        text="\u274c \u041e\u0442\u043a\u043b\u043e\u043d\u0438\u0442\u044c",
        callback_data=SmmOrderCB(action="reject", order_id=order_id),
    )
    builder.adjust(2)
    return builder.as_markup()


# ---------- 1. Menu of boost types ----------


@router.callback_query(SmmTypeCB.filter(F.type == "menu"))
async def smm_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "\U0001f680 <b>\u041d\u0430\u043a\u0440\u0443\u0442\u043a\u0430 YouTube</b>\n\n"
        "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0442\u0438\u043f:",
        reply_markup=smm_types_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


# ---------- 2. List services by type ----------


@router.callback_query(SmmTypeCB.filter(F.type != "menu"))
async def smm_select_type(callback: CallbackQuery, callback_data: SmmTypeCB, config):
    global _services_cache

    smm_type = callback_data.type

    if not config.smm_raja_api_key:
        await callback.answer(
            "\u041d\u0430\u043a\u0440\u0443\u0442\u043a\u0430 \u0432\u0440\u0435\u043c\u0435\u043d\u043d\u043e \u043d\u0435\u0434\u043e\u0441\u0442\u0443\u043f\u043d\u0430",
            show_alert=True,
        )
        return

    try:
        all_services = await get_youtube_services(config.smm_raja_api_key)
    except SMMRajaError as e:
        logger.warning("SMMRaja get_youtube_services error: %s", e)
        await callback.answer(
            "\u041e\u0448\u0438\u0431\u043a\u0430 \u0437\u0430\u0433\u0440\u0443\u0437\u043a\u0438 \u0441\u0435\u0440\u0432\u0438\u0441\u043e\u0432. \u041f\u043e\u043f\u0440\u043e\u0431\u0443\u0439\u0442\u0435 \u043f\u043e\u0437\u0436\u0435.",
            show_alert=True,
        )
        return

    _services_cache = all_services
    services = all_services.get(smm_type, [])

    if not services:
        await callback.answer(
            "\u041d\u0435\u0442 \u0434\u043e\u0441\u0442\u0443\u043f\u043d\u044b\u0445 \u0441\u0435\u0440\u0432\u0438\u0441\u043e\u0432 \u0434\u043b\u044f \u044d\u0442\u043e\u0433\u043e \u0442\u0438\u043f\u0430.",
            show_alert=True,
        )
        return

    # Pre-calculate prices and cap max at 5000
    for s in services:
        rate_usd = float(s.get("rate", 0))
        s["price_sum"] = math.ceil(rate_usd * config.usd_rate * 1.5)
        s["max"] = min(int(s.get("max", 0)), 5000)

    type_labels = {
        "views": "\U0001f441 \u041f\u0440\u043e\u0441\u043c\u043e\u0442\u0440\u044b",
        "likes": "\u2764\ufe0f \u041b\u0430\u0439\u043a\u0438",
        "subscribers": "\U0001f465 \u041f\u043e\u0434\u043f\u0438\u0441\u0447\u0438\u043a\u0438",
        "comments": "\U0001f4ac \u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0438",
        "shorts": "\U0001f3ac Shorts",
        "shares": "\U0001f517 \u0420\u0435\u043f\u043e\u0441\u0442\u044b",
    }
    label = type_labels.get(smm_type, smm_type)

    await callback.message.edit_text(
        f"\U0001f680 <b>{label}</b>\n\n"
        f"\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0441\u0435\u0440\u0432\u0438\u0441:",
        reply_markup=smm_services_kb(services, smm_type),
        parse_mode="HTML",
    )
    await callback.answer()


# ---------- 3. Service card — ask for link ----------


@router.callback_query(SmmServiceCB.filter())
async def smm_select_service(
    callback: CallbackQuery, callback_data: SmmServiceCB, state: FSMContext, config
):
    service_id = callback_data.service_id

    # Find the service in cache
    service = None
    for services_list in _services_cache.values():
        for s in services_list:
            if int(s.get("service", 0)) == service_id:
                service = s
                break
        if service:
            break

    if not service:
        await callback.answer(
            "\u0421\u0435\u0440\u0432\u0438\u0441 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d. \u041f\u043e\u043f\u0440\u043e\u0431\u0443\u0439\u0442\u0435 \u0441\u043d\u043e\u0432\u0430.",
            show_alert=True,
        )
        return

    rate_usd = float(service.get("rate", 0))
    min_qty = int(service.get("min", 0))
    max_qty = min(int(service.get("max", 0)), 5000)
    name = service.get("name", "Service")

    price_per_1000 = math.ceil(rate_usd * config.usd_rate * 1.5)

    text = (
        f"\U0001f4e6 <b>{name}</b>\n"
        f"\U0001f4b0 \u0426\u0435\u043d\u0430: <b>{price_per_1000:,} \u0441\u0443\u043c</b> \u0437\u0430 1000\n"
        f"\U0001f4ca \u041c\u0438\u043d: {min_qty} | \u041c\u0430\u043a\u0441: {max_qty}\n\n"
        f"\u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 \u0441\u0441\u044b\u043b\u043a\u0443 \u043d\u0430 \u0432\u0438\u0434\u0435\u043e YouTube:"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=_back_to_smm_menu_kb(),
    )
    await state.set_state(SmmState.waiting_link)
    await state.update_data(
        service_id=service_id,
        service_name=name,
        rate=rate_usd,
        min=min_qty,
        max=max_qty,
    )
    await callback.answer()


# ---------- 3.5. Back from FSM to SMM menu ----------


@router.callback_query(SmmTypeCB.filter(F.type == "menu"), SmmState.waiting_link)
@router.callback_query(SmmTypeCB.filter(F.type == "menu"), SmmState.waiting_quantity)
@router.callback_query(SmmTypeCB.filter(F.type == "menu"), SmmState.waiting_receipt)
async def smm_back_from_fsm(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "\U0001f680 <b>\u041d\u0430\u043a\u0440\u0443\u0442\u043a\u0430 YouTube</b>\n\n"
        "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0442\u0438\u043f:",
        reply_markup=smm_types_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


# ---------- 4. Receive link — ask for quantity ----------


@router.message(SmmState.waiting_link, F.text)
async def smm_receive_link(message: Message, state: FSMContext):
    link = message.text.strip()

    if "youtu" not in link.lower():
        await message.answer(
            "\u274c \u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 \u043a\u043e\u0440\u0440\u0435\u043a\u0442\u043d\u0443\u044e \u0441\u0441\u044b\u043b\u043a\u0443 YouTube."
        )
        return

    data = await state.get_data()
    min_qty = data["min"]
    max_qty = data["max"]

    await state.update_data(link=link)
    await state.set_state(SmmState.waiting_quantity)
    await message.answer(
        f"\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043a\u043e\u043b\u0438\u0447\u0435\u0441\u0442\u0432\u043e (\u043e\u0442 {min_qty} \u0434\u043e {max_qty}):",
        reply_markup=_back_to_smm_menu_kb(),
    )


# ---------- 5. Receive quantity — show price & payment details ----------


@router.message(SmmState.waiting_quantity, F.text)
async def smm_receive_quantity(message: Message, state: FSMContext, db_pool, config):
    text = message.text.strip()

    if not text.isdigit():
        await message.answer("\u274c \u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0447\u0438\u0441\u043b\u043e.")
        return

    quantity = int(text)
    data = await state.get_data()
    min_qty = data["min"]
    max_qty = data["max"]

    if quantity < min_qty or quantity > max_qty:
        await message.answer(
            f"\u274c \u041a\u043e\u043b\u0438\u0447\u0435\u0441\u0442\u0432\u043e \u0434\u043e\u043b\u0436\u043d\u043e \u0431\u044b\u0442\u044c \u043e\u0442 {min_qty} \u0434\u043e {max_qty}."
        )
        return

    rate_usd = data["rate"]
    service_name = data["service_name"]
    total_price = math.ceil(quantity / 1000 * rate_usd * config.usd_rate * 1.5)

    card_number = await get_setting(db_pool, "card_number") or "\u043d\u0435 \u0443\u043a\u0430\u0437\u0430\u043d"
    card_holder = await get_setting(db_pool, "card_holder") or "\u043d\u0435 \u0443\u043a\u0430\u0437\u0430\u043d"

    pay_text = (
        f"\U0001f680 <b>\u041d\u0430\u043a\u0440\u0443\u0442\u043a\u0430 YouTube</b>\n\n"
        f"\U0001f4e6 {service_name}\n"
        f"\U0001f522 \u041a\u043e\u043b\u0438\u0447\u0435\u0441\u0442\u0432\u043e: <b>{quantity}</b>\n"
        f"\U0001f4b0 \u0421\u0443\u043c\u043c\u0430: <b>{total_price:,} \u0441\u0443\u043c</b>\n\n"
        f"\u041f\u0435\u0440\u0435\u0432\u0435\u0434\u0438\u0442\u0435 \u043d\u0430 \u043a\u0430\u0440\u0442\u0443:\n"
        f"\U0001f4b3 <code>{card_number}</code>\n"
        f"\U0001f464 {card_holder}\n\n"
        f"\u2757 \u041f\u043e\u0441\u043b\u0435 \u043e\u043f\u043b\u0430\u0442\u044b \u043e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 \u0441\u043a\u0440\u0438\u043d\u0448\u043e\u0442 \u0447\u0435\u043a\u0430 \u0441\u044e\u0434\u0430."
    )

    await message.answer(pay_text, parse_mode="HTML")
    await state.update_data(quantity=quantity, total_price=total_price)
    await state.set_state(SmmState.waiting_receipt)


# ---------- 6. Receive receipt — notify admin ----------


@router.message(SmmState.waiting_receipt, F.photo)
async def smm_receive_receipt(message: Message, state: FSMContext, db_pool, config):
    data = await state.get_data()
    receipt_file_id = message.photo[-1].file_id

    order = await create_order(
        db_pool,
        user_id=message.from_user.id,
        username=message.from_user.username,
        product_id=None,
        receipt_file_id=receipt_file_id,
    )

    order_id = order["id"]

    _smm_data[order_id] = {
        "service_id": data["service_id"],
        "service_name": data["service_name"],
        "link": data["link"],
        "quantity": data["quantity"],
        "user_id": message.from_user.id,
        "price": data["total_price"],
    }

    await message.answer(
        "\u2705 \u0427\u0435\u043a \u043f\u0440\u0438\u043d\u044f\u0442! \u041e\u0436\u0438\u0434\u0430\u0439\u0442\u0435 \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0438\u044f.\n\n"
        "\U0001f550 \u041c\u044b \u0434\u043e\u0441\u0442\u0443\u043f\u043d\u044b \u0441 9:00 \u0434\u043e 23:00, \u0431\u0435\u0437 \u0432\u044b\u0445\u043e\u0434\u043d\u044b\u0445.\n"
        "\U0001f4de \u041f\u043e\u0434\u0434\u0435\u0440\u0436\u043a\u0430: @shumbolaaisupport"
    )

    username = message.from_user.username or "N/A"
    admin_text = (
        f"\U0001f680 \u041d\u0430\u043a\u0440\u0443\u0442\u043a\u0430 #{order_id}\n"
        f"\U0001f464 @{username} (ID: {message.from_user.id})\n"
        f"\U0001f4e6 {data['service_name']}\n"
        f"\U0001f522 \u041a\u043e\u043b\u0438\u0447\u0435\u0441\u0442\u0432\u043e: {data['quantity']}\n"
        f"\U0001f4b0 {data['total_price']:,} \u0441\u0443\u043c\n"
        f"\U0001f517 {data['link']}"
    )

    await message.bot.send_photo(
        chat_id=config.admin_id,
        photo=receipt_file_id,
        caption=admin_text,
        reply_markup=smm_confirm_kb(order_id),
    )

    await state.clear()


# ---------- 7. Admin approves ----------


@router.callback_query(SmmOrderCB.filter(F.action == "approve"))
async def smm_approve_order(
    callback: CallbackQuery, callback_data: SmmOrderCB, db_pool, config
):
    order_id = callback_data.order_id
    await update_order_status(db_pool, order_id, "approved")

    sdata = _smm_data.get(order_id)
    if not sdata:
        await callback.answer(
            "\u0414\u0430\u043d\u043d\u044b\u0435 \u0437\u0430\u043a\u0430\u0437\u0430 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u044b",
            show_alert=True,
        )
        return

    service_id = sdata["service_id"]
    link = sdata["link"]
    quantity = sdata["quantity"]
    service_name = sdata["service_name"]
    user_id = sdata["user_id"]

    try:
        result = await add_order(config.smm_raja_api_key, service_id, link, quantity)
        logger.info("SMMRaja add_order result for order #%s: %s", order_id, result)
    except SMMRajaError as e:
        error_msg = str(e)
        logger.warning("SMMRaja add_order error for order #%s: %s", order_id, error_msg)

        await callback.bot.send_message(
            user_id,
            f"\u274c \u041e\u0448\u0438\u0431\u043a\u0430 \u043e\u0444\u043e\u0440\u043c\u043b\u0435\u043d\u0438\u044f \u0437\u0430\u043a\u0430\u0437\u0430. \u041c\u044b \u0440\u0430\u0437\u0431\u0435\u0440\u0451\u043c\u0441\u044f \u0432 \u0431\u043b\u0438\u0436\u0430\u0439\u0448\u0435\u0435 \u0432\u0440\u0435\u043c\u044f.\n"
            f"\U0001f4de \u041f\u043e\u0434\u0434\u0435\u0440\u0436\u043a\u0430: @shumbolaaisupport",
        )
        await callback.message.edit_caption(
            caption=f"\u274c \u0417\u0430\u043a\u0430\u0437 #{order_id} \u2014 \u043e\u0448\u0438\u0431\u043a\u0430 API: {error_msg}"
        )
        await callback.answer("\u041e\u0448\u0438\u0431\u043a\u0430 API", show_alert=True)
        return

    await callback.bot.send_message(
        user_id,
        f"\u2705 <b>\u0417\u0430\u043a\u0430\u0437 \u043e\u0444\u043e\u0440\u043c\u043b\u0435\u043d!</b>\n"
        f"\U0001f4e6 {service_name}\n"
        f"\U0001f522 \u041a\u043e\u043b\u0438\u0447\u0435\u0441\u0442\u0432\u043e: {quantity}\n\n"
        f"\u23f3 \u0412\u044b\u043f\u043e\u043b\u043d\u0435\u043d\u0438\u0435 \u043c\u043e\u0436\u0435\u0442 \u0437\u0430\u043d\u044f\u0442\u044c \u043e\u0442 \u043d\u0435\u0441\u043a\u043e\u043b\u044c\u043a\u0438\u0445 \u043c\u0438\u043d\u0443\u0442 \u0434\u043e 24 \u0447\u0430\u0441\u043e\u0432.\n"
        f"\U0001f4de \u041f\u043e\u0434\u0434\u0435\u0440\u0436\u043a\u0430: @shumbolaaisupport",
        parse_mode="HTML",
    )

    await callback.message.edit_caption(
        caption=f"\u2705 \u0417\u0430\u043a\u0430\u0437 #{order_id} \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0451\u043d \u0438 \u043e\u0442\u043f\u0440\u0430\u0432\u043b\u0435\u043d \u0432 SMM"
    )
    await callback.answer("\u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u043e")

    _smm_data.pop(order_id, None)


# ---------- 8. Admin rejects ----------


@router.callback_query(SmmOrderCB.filter(F.action == "reject"))
async def smm_reject_order(
    callback: CallbackQuery, callback_data: SmmOrderCB, db_pool
):
    order_id = callback_data.order_id
    await update_order_status(db_pool, order_id, "rejected")

    sdata = _smm_data.pop(order_id, None)
    user_id = sdata["user_id"] if sdata else None

    if user_id:
        await callback.bot.send_message(
            user_id,
            "\u274c \u041a \u0441\u043e\u0436\u0430\u043b\u0435\u043d\u0438\u044e, \u043e\u043f\u043b\u0430\u0442\u0430 \u043d\u0435 \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0430.\n"
            "\u0415\u0441\u043b\u0438 \u0432\u044b \u0443\u0432\u0435\u0440\u0435\u043d\u044b \u0447\u0442\u043e \u043e\u043f\u043b\u0430\u0442\u0438\u043b\u0438, \u0441\u0432\u044f\u0436\u0438\u0442\u0435\u0441\u044c \u0441 \u043f\u043e\u0434\u0434\u0435\u0440\u0436\u043a\u043e\u0439.\n"
            "\U0001f4de @shumbolaaisupport",
        )

    await callback.message.edit_caption(
        caption=f"\u274c \u0417\u0430\u043a\u0430\u0437 #{order_id} \u043e\u0442\u043a\u043b\u043e\u043d\u0451\u043d"
    )
    await callback.answer("\u041e\u0442\u043a\u043b\u043e\u043d\u0435\u043d\u043e")
