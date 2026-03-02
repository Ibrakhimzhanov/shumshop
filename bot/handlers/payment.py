from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.keyboards import PaymentCB, OrderCB, confirm_order_kb
from bot.models import (
    get_product,
    get_setting,
    create_order,
    get_order,
    update_order_status,
)

router = Router()


class PaymentState(StatesGroup):
    waiting_receipt = State()


@router.callback_query(PaymentCB.filter(F.action == "pay"))
async def start_payment(callback: CallbackQuery, callback_data: PaymentCB, state: FSMContext, config):
    pool = callback.bot["db_pool"]
    product = await get_product(pool, callback_data.product_id)
    if not product:
        await callback.answer("\u0422\u043e\u0432\u0430\u0440 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d", show_alert=True)
        return

    card_number = await get_setting(pool, "card_number") or "\u043d\u0435 \u0443\u043a\u0430\u0437\u0430\u043d"
    card_holder = await get_setting(pool, "card_holder") or "\u043d\u0435 \u0443\u043a\u0430\u0437\u0430\u043d"
    price = f"{product['price']:,} \u0441\u0443\u043c"

    text = (
        f"\U0001f4b3 \u041e\u043f\u043b\u0430\u0442\u0430: {product['name']}\n\n"
        f"\u0421\u0443\u043c\u043c\u0430: {price}\n\n"
        f"\u041f\u0435\u0440\u0435\u0432\u0435\u0434\u0438\u0442\u0435 \u043d\u0430 \u043a\u0430\u0440\u0442\u0443:\n"
        f"\U0001f4b3 {card_number}\n"
        f"\U0001f464 {card_holder}\n\n"
        f"\u041f\u043e\u0441\u043b\u0435 \u043e\u043f\u043b\u0430\u0442\u044b \u043e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 \u0441\u043a\u0440\u0438\u043d\u0448\u043e\u0442 \u0447\u0435\u043a\u0430 \u0441\u044e\u0434\u0430."
    )

    await callback.message.answer(text)
    await state.set_state(PaymentState.waiting_receipt)
    await state.update_data(product_id=callback_data.product_id)
    await callback.answer()


@router.message(PaymentState.waiting_receipt, F.photo)
async def receive_receipt(message: Message, state: FSMContext, config):
    pool = message.bot["db_pool"]
    data = await state.get_data()
    product_id = data["product_id"]

    product = await get_product(pool, product_id)
    if not product:
        await message.answer("\u041e\u0448\u0438\u0431\u043a\u0430: \u0442\u043e\u0432\u0430\u0440 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d.")
        await state.clear()
        return

    receipt_file_id = message.photo[-1].file_id
    order = await create_order(
        pool,
        user_id=message.from_user.id,
        username=message.from_user.username,
        product_id=product_id,
        receipt_file_id=receipt_file_id,
    )

    await message.answer(
        "\u2705 \u0427\u0435\u043a \u043f\u0440\u0438\u043d\u044f\u0442! \u041e\u0436\u0438\u0434\u0430\u0439\u0442\u0435 \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0438\u044f.\n\n"
        "\U0001f550 \u041c\u044b \u0434\u043e\u0441\u0442\u0443\u043f\u043d\u044b \u0441 9:00 \u0434\u043e 23:00, \u0431\u0435\u0437 \u0432\u044b\u0445\u043e\u0434\u043d\u044b\u0445.\n"
        "\U0001f4de \u041f\u043e\u0434\u0434\u0435\u0440\u0436\u043a\u0430: @shumbolaaisupport"
    )

    price = f"{product['price']:,} \u0441\u0443\u043c"
    username = message.from_user.username or "N/A"
    admin_text = (
        f"\U0001f4e6 \u041d\u043e\u0432\u044b\u0439 \u0437\u0430\u043a\u0430\u0437 #{order['id']}\n"
        f"\U0001f464 @{username} (ID: {message.from_user.id})\n"
        f"\U0001f6d2 {product['name']} \u2014 {price}"
    )
    await message.bot.send_photo(
        chat_id=config.admin_id,
        photo=receipt_file_id,
        caption=admin_text,
        reply_markup=confirm_order_kb(order["id"]),
    )

    await state.clear()


@router.callback_query(OrderCB.filter(F.action == "approve"))
async def approve_order(callback: CallbackQuery, callback_data: OrderCB):
    pool = callback.bot["db_pool"]
    order_id = callback_data.order_id

    await update_order_status(pool, order_id, "approved")
    order = await get_order(pool, order_id)
    if not order:
        await callback.answer("\u0417\u0430\u043a\u0430\u0437 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d", show_alert=True)
        return

    buyer_text = (
        f"\u2705 \u041e\u043f\u043b\u0430\u0442\u0430 \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0430!\n\n"
        f"\u0412 \u0442\u0435\u0447\u0435\u043d\u0438\u0435 10-15 \u043c\u0438\u043d\u0443\u0442 \u043c\u044b \u0432\u044b\u0434\u0430\u0434\u0438\u043c \u0432\u0430\u043c \u0434\u043e\u0441\u0442\u0443\u043f\u044b.\n\n"
        f"\U0001f4d6 \u0418\u043d\u0441\u0442\u0440\u0443\u043a\u0446\u0438\u044f:\n{order['post_purchase_info'] or ''}\n\n"
        f"\U0001f4de \u041f\u043e\u0434\u0434\u0435\u0440\u0436\u043a\u0430: @shumbolaaisupport"
    )
    await callback.bot.send_message(chat_id=order["user_id"], text=buyer_text)

    await callback.message.edit_caption(
        caption=f"\u2705 \u0417\u0430\u043a\u0430\u0437 #{order_id} \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0451\u043d"
    )
    await callback.answer("\u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u043e")


@router.callback_query(OrderCB.filter(F.action == "reject"))
async def reject_order(callback: CallbackQuery, callback_data: OrderCB):
    pool = callback.bot["db_pool"]
    order_id = callback_data.order_id

    await update_order_status(pool, order_id, "rejected")
    order = await get_order(pool, order_id)
    if not order:
        await callback.answer("\u0417\u0430\u043a\u0430\u0437 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d", show_alert=True)
        return

    buyer_text = (
        "\u274c \u041a \u0441\u043e\u0436\u0430\u043b\u0435\u043d\u0438\u044e, \u043e\u043f\u043b\u0430\u0442\u0430 \u043d\u0435 \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0430.\n"
        "\u0415\u0441\u043b\u0438 \u0432\u044b \u0443\u0432\u0435\u0440\u0435\u043d\u044b \u0447\u0442\u043e \u043e\u043f\u043b\u0430\u0442\u0438\u043b\u0438, \u0441\u0432\u044f\u0436\u0438\u0442\u0435\u0441\u044c \u0441 \u043f\u043e\u0434\u0434\u0435\u0440\u0436\u043a\u043e\u0439.\n"
        "\U0001f4de @shumbolaaisupport"
    )
    await callback.bot.send_message(chat_id=order["user_id"], text=buyer_text)

    await callback.message.edit_caption(
        caption=f"\u274c \u0417\u0430\u043a\u0430\u0437 #{order_id} \u043e\u0442\u043a\u043b\u043e\u043d\u0451\u043d"
    )
    await callback.answer("\u041e\u0442\u043a\u043b\u043e\u043d\u0435\u043d\u043e")
