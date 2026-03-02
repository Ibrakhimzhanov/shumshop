import asyncpg

from bot.config import Config


async def create_pool(config: Config) -> asyncpg.Pool:
    pool = await asyncpg.create_pool(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
        min_size=2,
        max_size=10,
    )
    return pool


async def close_pool(pool: asyncpg.Pool) -> None:
    await pool.close()
