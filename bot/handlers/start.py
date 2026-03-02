from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from bot.keyboards import main_menu_kb
from bot.models import get_categories

router = Router()

WELCOME = "\U0001f44b \u0414\u043e\u0431\u0440\u043e \u043f\u043e\u0436\u0430\u043b\u043e\u0432\u0430\u0442\u044c \u0432 Shum Bola AI!\n\n\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0440\u0430\u0437\u0434\u0435\u043b:"


@router.message(CommandStart())
async def cmd_start(message: Message, db_pool):
    categories = await get_categories(db_pool)
    await message.answer(WELCOME, reply_markup=main_menu_kb(categories))


@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, db_pool):
    categories = await get_categories(db_pool)
    await callback.message.edit_text(WELCOME, reply_markup=main_menu_kb(categories))
    await callback.answer()
