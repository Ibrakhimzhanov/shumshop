import asyncio
import logging
import math

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.hero_sms import (
    get_number,
    get_status,
    set_status,
    get_services_list,
    get_countries,
    get_prices,
    HeroSMSError,
)
from bot.keyboards import (
    VerifyCB,
    VerifyServiceCB,
    VerifyCountryCB,
    verify_services_kb,
    verify_countries_kb,
    verify_number_kb,
)
from bot.models import get_setting, create_order, update_order_status

router = Router()
logger = logging.getLogger(__name__)

# ---------- FSM ----------

class VerifyPayState(StatesGroup):
    waiting_receipt = State()


# ---------- Callback Data для подтверждения заказа ----------

class VerifyOrderCB(CallbackData, prefix="vorder"):
    action: str = "approve"
    order_id: int = 0


# ---------- In-memory хранилище данных верификации ----------

_verify_data: dict[int, dict] = {}  # order_id -> {service, country, user_id, price}


# ---------- Клавиатура подтверждения ----------

def verify_confirm_kb(order_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Подтвердить",
        callback_data=VerifyOrderCB(action="approve", order_id=order_id),
    )
    builder.button(
        text="❌ Отклонить",
        callback_data=VerifyOrderCB(action="reject", order_id=order_id),
    )
    builder.adjust(2)
    return builder.as_markup()


# ---------- 1. Выбор сервиса ----------

@router.callback_query(VerifyCB.filter(F.action == "start"))
async def start_verify(callback: CallbackQuery, config):
    if not config.hero_sms_api_key:
        await callback.answer(
            "Верификация временно недоступна", show_alert=True
        )
        return

    try:
        services = await get_services_list(config.hero_sms_api_key)
    except HeroSMSError as e:
        logger.warning("Hero-SMS getServicesList error: %s", e)
        await callback.answer(
            "Ошибка загрузки сервисов. Попробуйте позже.",
            show_alert=True,
        )
        return

    await callback.message.edit_text(
        "📱 <b>Верификация по номеру</b>\n\n"
        "Выберите сервис:",
        reply_markup=verify_services_kb(services),
        parse_mode="HTML",
    )
    await callback.answer()


# ---------- 2. Выбор страны ----------

@router.callback_query(VerifyServiceCB.filter())
async def select_service(callback: CallbackQuery, callback_data: VerifyServiceCB, config):
    service_code = callback_data.code

    try:
        prices_data = await get_prices(config.hero_sms_api_key, service=service_code)
        countries_map = await get_countries(config.hero_sms_api_key)
    except HeroSMSError as e:
        logger.warning("Hero-SMS getPrices/getCountries error: %s", e)
        await callback.answer(
            "Ошибка загрузки цен. Попробуйте позже.",
            show_alert=True,
        )
        return

    countries_with_prices = []
    for country_id_str, info in prices_data.items():
        try:
            country_id = int(country_id_str)
        except (ValueError, TypeError):
            continue

        if isinstance(info, dict):
            service_info = info.get(service_code, info)
            if isinstance(service_info, dict):
                cost_usd = service_info.get("cost", 0)
                count = service_info.get("count", 0)
            else:
                continue
        else:
            continue

        if count <= 0:
            continue

        cost_usd = float(cost_usd)
        price_sum = math.ceil(cost_usd * config.usd_rate * 1.6)

        # Получаем название страны из countries_map
        country_info = countries_map.get(str(country_id), {})
        if isinstance(country_info, dict):
            country_name = country_info.get("eng", country_info.get("rus", str(country_id)))
        else:
            country_name = str(country_id)

        countries_with_prices.append({
            "id": country_id,
            "name": country_name,
            "price": price_sum,
        })

    if not countries_with_prices:
        await callback.answer(
            "Нет доступных стран для этого сервиса.",
            show_alert=True,
        )
        return

    await callback.message.edit_text(
        "🌍 <b>Выберите страну:</b>",
        reply_markup=verify_countries_kb(countries_with_prices, service_code),
        parse_mode="HTML",
    )
    await callback.answer()


# ---------- 3. Показ цены и реквизитов ----------

@router.callback_query(VerifyCountryCB.filter())
async def select_country(
    callback: CallbackQuery,
    callback_data: VerifyCountryCB,
    state: FSMContext,
    config,
    db_pool,
):
    service_code = callback_data.service
    country_id = callback_data.country

    # Получаем цену заново
    try:
        prices_data = await get_prices(config.hero_sms_api_key, service=service_code)
    except HeroSMSError as e:
        logger.warning("Hero-SMS getPrices error: %s", e)
        await callback.answer("Ошибка загрузки цен.", show_alert=True)
        return

    country_info = prices_data.get(str(country_id), {})
    if isinstance(country_info, dict):
        service_info = country_info.get(service_code, country_info)
        cost_usd = float(service_info.get("cost", 0)) if isinstance(service_info, dict) else 0
    else:
        cost_usd = 0

    price_sum = math.ceil(cost_usd * config.usd_rate * 1.6)

    card_number = await get_setting(db_pool, "card_number") or "не указан"
    card_holder = await get_setting(db_pool, "card_holder") or "не указан"

    text = (
        f"📱 <b>Верификация</b>\n\n"
        f"💰 Сумма: <b>{price_sum:,} сум</b>\n\n"
        f"Переведите на карту:\n"
        f"💳 <code>{card_number}</code>\n"
        f"👤 {card_holder}\n\n"
        f"❗ После оплаты отправьте скриншот чека сюда."
    )

    await callback.message.edit_text(text, parse_mode="HTML")
    await state.set_state(VerifyPayState.waiting_receipt)
    await state.update_data(service=service_code, country=country_id, price=price_sum)
    await callback.answer()


# ---------- 4. Получение чека ----------

@router.message(VerifyPayState.waiting_receipt, F.photo)
async def receive_verify_receipt(message: Message, state: FSMContext, db_pool, config):
    data = await state.get_data()
    service_code = data["service"]
    country_id = data["country"]
    price = data["price"]

    receipt_file_id = message.photo[-1].file_id

    order = await create_order(
        db_pool,
        user_id=message.from_user.id,
        username=message.from_user.username,
        product_id=None,
        receipt_file_id=receipt_file_id,
    )

    order_id = order["id"]

    # Сохраняем данные верификации
    _verify_data[order_id] = {
        "service": service_code,
        "country": country_id,
        "user_id": message.from_user.id,
        "price": price,
    }

    await message.answer(
        "✅ Чек принят! Ожидайте подтверждения.\n\n"
        "🕐 Мы доступны с 9:00 до 23:00, без выходных.\n"
        "📞 Поддержка: @shumbolaaisupport"
    )

    username = message.from_user.username or "N/A"
    admin_text = (
        f"📱 Верификация #{order_id}\n"
        f"👤 @{username} (ID: {message.from_user.id})\n"
        f"💰 {price:,} сум\n"
        f"🔧 Сервис: {service_code} | Страна: {country_id}"
    )
    await message.bot.send_photo(
        chat_id=config.admin_id,
        photo=receipt_file_id,
        caption=admin_text,
        reply_markup=verify_confirm_kb(order_id),
    )

    await state.clear()


# ---------- 5. Админ подтверждает ----------

@router.callback_query(VerifyOrderCB.filter(F.action == "approve"))
async def approve_verify_order(
    callback: CallbackQuery, callback_data: VerifyOrderCB, db_pool, config
):
    order_id = callback_data.order_id
    await update_order_status(db_pool, order_id, "approved")

    vdata = _verify_data.get(order_id)
    if not vdata:
        await callback.answer("Данные верификации не найдены", show_alert=True)
        return

    service_code = vdata["service"]
    country_id = vdata["country"]
    user_id = vdata["user_id"]

    try:
        activation_id, phone = await get_number(
            config.hero_sms_api_key, service=service_code, country=country_id
        )
    except HeroSMSError as e:
        error = str(e)
        logger.warning("Hero-SMS getNumber error: %s", error)
        if "NO_NUMBERS" in error:
            msg = "Номера временно недоступны."
        elif "NO_BALANCE" in error:
            msg = "Ошибка сервиса. Обратитесь в поддержку."
        else:
            msg = "Ошибка получения номера."
        await callback.bot.send_message(
            user_id,
            f"❌ {msg}\n📞 Поддержка: @shumbolaaisupport",
        )
        await callback.message.edit_caption(
            caption=f"❌ Заказ #{order_id} — ошибка получения номера: {error}"
        )
        await callback.answer("Ошибка получения номера", show_alert=True)
        return

    # Сообщаем о готовности принимать SMS
    try:
        await set_status(config.hero_sms_api_key, activation_id, 1)
    except HeroSMSError as e:
        logger.warning("Hero-SMS setStatus(1) error: %s", e)

    await callback.bot.send_message(
        user_id,
        f"📱 <b>Номер для верификации</b>\n\n"
        f"📞 <code>{phone}</code>\n\n"
        f"❗ Введите этот номер в сервисе и ожидайте SMS-код.\n"
        f"Код придёт автоматически.",
        parse_mode="HTML",
        reply_markup=verify_number_kb(activation_id),
    )

    await callback.message.edit_caption(
        caption=f"✅ Заказ #{order_id} подтверждён. Номер: {phone}"
    )
    await callback.answer("Подтверждено")

    # Запускаем фоновый polling
    asyncio.create_task(
        _poll_code(
            bot=callback.bot,
            api_key=config.hero_sms_api_key,
            activation_id=activation_id,
            user_id=user_id,
            order_id=order_id,
        )
    )


# ---------- 6. Фоновый polling ----------

async def _poll_code(bot, api_key, activation_id, user_id, order_id, timeout=1200):
    """Polling каждые 5 сек, таймаут 20 минут."""
    start = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start < timeout:
        try:
            status, code = await get_status(api_key, activation_id)
        except HeroSMSError as e:
            logger.warning("Poll getStatus error (order %s): %s", order_id, e)
            await asyncio.sleep(5)
            continue

        if status == "ok" and code:
            try:
                await set_status(api_key, activation_id, 6)  # complete
            except HeroSMSError as e:
                logger.warning("Poll setStatus(6) error: %s", e)

            await bot.send_message(
                user_id,
                f"✅ <b>Код получен!</b>\n\n🔑 Ваш код: <code>{code}</code>\n\n"
                "Введите его для завершения верификации.",
                parse_mode="HTML",
            )
            return

        await asyncio.sleep(5)

    # Таймаут — отменяем
    try:
        await set_status(api_key, activation_id, 8)  # cancel
    except HeroSMSError as e:
        logger.warning("Poll setStatus(8) cancel error: %s", e)

    await bot.send_message(
        user_id,
        "⏰ Время ожидания истекло (20 минут). Номер отменён.\n"
        "📞 Поддержка: @shumbolaaisupport",
    )


# ---------- 7. Возврат номера ----------

@router.callback_query(VerifyCB.filter(F.action == "cancel"))
async def cancel_verify(callback: CallbackQuery, callback_data: VerifyCB, config):
    activation_id = callback_data.activation_id

    try:
        await set_status(config.hero_sms_api_key, activation_id, 8)
    except HeroSMSError as e:
        logger.warning("Hero-SMS setStatus cancel error: %s", e)

    await callback.message.edit_text("🔄 Номер возвращён.")
    await callback.answer()


# ---------- 8. Отклонение админом ----------

@router.callback_query(VerifyOrderCB.filter(F.action == "reject"))
async def reject_verify_order(
    callback: CallbackQuery, callback_data: VerifyOrderCB, db_pool
):
    order_id = callback_data.order_id
    await update_order_status(db_pool, order_id, "rejected")

    vdata = _verify_data.pop(order_id, None)
    user_id = vdata["user_id"] if vdata else None

    if user_id:
        await callback.bot.send_message(
            user_id,
            "❌ К сожалению, оплата не подтверждена.\n"
            "Если вы уверены что оплатили, свяжитесь с поддержкой.\n"
            "📞 @shumbolaaisupport",
        )

    await callback.message.edit_caption(
        caption=f"❌ Заказ #{order_id} отклонён"
    )
    await callback.answer("Отклонено")
