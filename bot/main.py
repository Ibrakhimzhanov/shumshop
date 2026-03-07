import asyncio
import logging

from aiogram import Bot, Dispatcher

from bot.config import Config
from bot.db import close_pool, create_pool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    config = Config.from_env()
    bot = Bot(token=config.bot_token)
    dp = Dispatcher()

    dp["config"] = config

    # Import and register routers
    from bot.handlers import start, catalog, payment, admin, verify

    dp.include_router(start.router)
    dp.include_router(catalog.router)
    dp.include_router(payment.router)
    dp.include_router(verify.router)
    dp.include_router(admin.router)

    pool = await create_pool(config)
    dp["db_pool"] = pool
    logger.info("Database pool created")

    # Очищаем старые команды бота и ставим новые
    from aiogram.types import BotCommand
    await bot.set_my_commands([
        BotCommand(command="start", description="\u0413\u043b\u0430\u0432\u043d\u043e\u0435 \u043c\u0435\u043d\u044e"),
    ])
    await bot.delete_my_commands()
    await bot.set_my_commands([
        BotCommand(command="start", description="\u0413\u043b\u0430\u0432\u043d\u043e\u0435 \u043c\u0435\u043d\u044e"),
    ])
    logger.info("Bot commands updated")

    try:
        logger.info("Bot starting...")
        await dp.start_polling(bot)
    finally:
        await close_pool(pool)
        logger.info("Database pool closed")


if __name__ == "__main__":
    asyncio.run(main())
