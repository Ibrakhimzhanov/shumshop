from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from bot.keyboards import (
    main_menu_reply_kb,
    category_products_kb,
    admin_menu_kb,
    BUTTON_YOUTUBE,
    BUTTON_AI,
    BUTTON_SUPPORT,
    BUTTON_ADMIN,
)
from bot.models import get_categories, get_products_by_category, save_user

router = Router()

WELCOME = "\U0001f44b \u0414\u043e\u0431\u0440\u043e \u043f\u043e\u0436\u0430\u043b\u043e\u0432\u0430\u0442\u044c \u0432 Shum Bola AI!\n\n\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0440\u0430\u0437\u0434\u0435\u043b \u0432\u043d\u0438\u0437\u0443 \U0001f447"


@router.message(CommandStart())
async def cmd_start(message: Message, db_pool, config):
    # Сохраняем пользователя для статистики
    await save_user(
        db_pool,
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
    )
    is_admin = message.from_user.id == config.admin_id
    await message.answer(WELCOME, reply_markup=main_menu_reply_kb(is_admin))


@router.message(F.text == BUTTON_YOUTUBE)
async def btn_youtube(message: Message, db_pool):
    categories = await get_categories(db_pool)
    cat = next((c for c in categories if c["name"].lower().find("youtube") >= 0), None)
    if not cat:
        await message.answer("\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f YouTube \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u0430.")
        return
    products = await get_products_by_category(db_pool, cat["id"])
    await message.answer(
        "\U0001f3ac <b>YouTube</b>\n\n\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0442\u043e\u0432\u0430\u0440:",
        reply_markup=category_products_kb(products, cat["id"]),
        parse_mode="HTML",
    )


@router.message(F.text == BUTTON_AI)
async def btn_ai(message: Message, db_pool):
    categories = await get_categories(db_pool)
    cat = next((c for c in categories if c["name"].lower().find("ai") >= 0), None)
    if not cat:
        await message.answer("\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f AI \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u0430.")
        return
    products = await get_products_by_category(db_pool, cat["id"])
    await message.answer(
        "\U0001f916 <b>AI \u0441\u0435\u0440\u0432\u0438\u0441\u044b</b>\n\n\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0442\u043e\u0432\u0430\u0440:",
        reply_markup=category_products_kb(products, cat["id"]),
        parse_mode="HTML",
    )


@router.message(F.text == BUTTON_SUPPORT)
async def btn_support(message: Message):
    await message.answer(
        "\U0001f4de <b>\u041f\u043e\u0434\u0434\u0435\u0440\u0436\u043a\u0430</b>\n\n"
        "\U0001f550 \u041c\u044b \u0434\u043e\u0441\u0442\u0443\u043f\u043d\u044b \u0441 9:00 \u0434\u043e 23:00, \u0431\u0435\u0437 \u0432\u044b\u0445\u043e\u0434\u043d\u044b\u0445.\n"
        "\U0001f4ac \u041d\u0430\u043f\u0438\u0448\u0438\u0442\u0435 \u043d\u0430\u043c: @shumbolaaisupport",
        parse_mode="HTML",
    )


@router.message(F.text == BUTTON_ADMIN)
async def btn_admin(message: Message, config):
    if message.from_user.id != config.admin_id:
        return
    await message.answer("\u2699\ufe0f \u0410\u0434\u043c\u0438\u043d-\u043f\u0430\u043d\u0435\u043b\u044c:", reply_markup=admin_menu_kb())
