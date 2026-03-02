from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.keyboards import (
    CategoryCB,
    ProductCB,
    category_products_kb,
    product_card_kb,
)
from bot.models import get_products_by_category, get_product

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
