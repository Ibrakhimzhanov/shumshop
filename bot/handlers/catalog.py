from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.keyboards import (
    CategoryCB,
    ProductCB,
    category_products_kb,
    product_card_kb,
)
from bot.models import get_products_by_category, get_product, get_category_by_name

router = Router()


@router.callback_query(CategoryCB.filter(F.action == "select"))
async def show_category(callback: CallbackQuery, callback_data: CategoryCB, db_pool):
    products = await get_products_by_category(db_pool, callback_data.id)
    await callback.message.edit_text(
        "\U0001f4e6 \u0422\u043e\u0432\u0430\u0440\u044b:",
        reply_markup=category_products_kb(products, callback_data.id),
    )
    await callback.answer()


@router.callback_query(ProductCB.filter(F.action == "view"))
async def show_product(callback: CallbackQuery, callback_data: ProductCB, db_pool):
    product = await get_product(db_pool, callback_data.id)
    if not product:
        await callback.answer("\u0422\u043e\u0432\u0430\u0440 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d", show_alert=True)
        return

    # "Старореги" — показываем подпродукты из скрытой категории
    if product["name"] == "\u0421\u0442\u0430\u0440\u043e\u0440\u0435\u0433\u0438":
        sub_cat = await get_category_by_name(db_pool, "\u0421\u0442\u0430\u0440\u043e\u0440\u0435\u0433\u0438 YouTube")
        if sub_cat:
            sub_products = await get_products_by_category(db_pool, sub_cat["id"])
            if sub_products:
                await callback.message.edit_text(
                    "\U0001f4e6 <b>\u0421\u0442\u0430\u0440\u043e\u0440\u0435\u0433\u0438</b>\n\n\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0442\u043e\u0432\u0430\u0440:",
                    reply_markup=category_products_kb(sub_products, sub_cat["id"]),
                    parse_mode="HTML",
                )
                await callback.answer()
                return
        await callback.answer("\u0422\u043e\u0432\u0430\u0440\u044b \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u044b", show_alert=True)
        return

    price = f"{product['price']:,} \u0441\u0443\u043c"
    text = (
        f"\U0001f4cc <b>{product['name']}</b>\n\n"
        f"\U0001f4b0 \u0426\u0435\u043d\u0430: <b>{price}</b>\n\n"
        f"{product['description'] or ''}"
    )
    await callback.message.edit_text(
        text, reply_markup=product_card_kb(product["id"]), parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(ProductCB.filter(F.action == "back"))
async def product_back(callback: CallbackQuery, callback_data: ProductCB, db_pool):
    product = await get_product(db_pool, callback_data.id)
    if product:
        products = await get_products_by_category(db_pool, product["category_id"])
        await callback.message.edit_text(
            "\U0001f4e6 \u0422\u043e\u0432\u0430\u0440\u044b:",
            reply_markup=category_products_kb(products, product["category_id"]),
        )
    await callback.answer()


@router.callback_query(CategoryCB.filter(F.action == "back"))
async def back_to_categories(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer()
