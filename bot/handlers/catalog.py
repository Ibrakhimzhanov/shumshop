from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.keyboards import (
    CategoryCB,
    ProductCB,
    main_menu_kb,
    category_products_kb,
    product_card_kb,
)
from bot.models import get_products_by_category, get_product, get_categories

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
        f"\U0001f4cc {product['name']}\n\n"
        f"\U0001f4b0 \u0426\u0435\u043d\u0430: {price}\n\n"
        f"{product['description'] or ''}"
    )
    await callback.message.edit_text(
        text, reply_markup=product_card_kb(product["id"])
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
async def back_to_categories(callback: CallbackQuery, db_pool):
    categories = await get_categories(db_pool)
    await callback.message.edit_text(
        "\U0001f44b \u0414\u043e\u0431\u0440\u043e \u043f\u043e\u0436\u0430\u043b\u043e\u0432\u0430\u0442\u044c \u0432 Shum Bola AI!\n\n\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0440\u0430\u0437\u0434\u0435\u043b:",
        reply_markup=main_menu_kb(categories),
    )
    await callback.answer()
