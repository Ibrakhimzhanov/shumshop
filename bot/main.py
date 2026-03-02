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
    from bot.handlers import start, catalog, payment, admin

    dp.include_router(start.router)
    dp.include_router(catalog.router)
    dp.include_router(payment.router)
    dp.include_router(admin.router)

    pool = await create_pool(config)
    bot["db_pool"] = pool
    logger.info("Database pool created")

    try:
        logger.info("Bot starting...")
        await dp.start_polling(bot)
    finally:
        await close_pool(pool)
        logger.info("Database pool closed")


if __name__ == "__main__":
    asyncio.run(main())
