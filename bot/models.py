import asyncpg


# --- Categories ---


async def get_categories(pool: asyncpg.Pool) -> list[asyncpg.Record]:
    return await pool.fetch(
        "SELECT * FROM categories WHERE is_active = true ORDER BY sort_order, id"
    )


async def get_category(pool: asyncpg.Pool, cat_id: int) -> asyncpg.Record | None:
    return await pool.fetchrow(
        "SELECT * FROM categories WHERE id = $1", cat_id
    )


async def create_category(pool: asyncpg.Pool, name: str) -> asyncpg.Record:
    return await pool.fetchrow(
        "INSERT INTO categories (name) VALUES ($1) RETURNING *", name
    )


async def update_category(pool: asyncpg.Pool, cat_id: int, name: str) -> None:
    await pool.execute(
        "UPDATE categories SET name = $1 WHERE id = $2", name, cat_id
    )


async def delete_category(pool: asyncpg.Pool, cat_id: int) -> None:
    await pool.execute("DELETE FROM categories WHERE id = $1", cat_id)


# --- Products ---


async def get_products_by_category(
    pool: asyncpg.Pool, category_id: int
) -> list[asyncpg.Record]:
    return await pool.fetch(
        "SELECT * FROM products WHERE category_id = $1 AND is_active = true "
        "ORDER BY sort_order, id",
        category_id,
    )


async def get_product(
    pool: asyncpg.Pool, product_id: int
) -> asyncpg.Record | None:
    return await pool.fetchrow(
        "SELECT * FROM products WHERE id = $1", product_id
    )


async def create_product(
    pool: asyncpg.Pool,
    category_id: int,
    name: str,
    price: int,
    description: str,
    post_purchase_info: str,
) -> asyncpg.Record:
    return await pool.fetchrow(
        "INSERT INTO products (category_id, name, price, description, post_purchase_info) "
        "VALUES ($1, $2, $3, $4, $5) RETURNING *",
        category_id,
        name,
        price,
        description,
        post_purchase_info,
    )


async def update_product(
    pool: asyncpg.Pool, product_id: int, **kwargs
) -> None:
    if not kwargs:
        return
    fields = []
    values = []
    for i, (key, value) in enumerate(kwargs.items(), start=1):
        fields.append(f"{key} = ${i}")
        values.append(value)
    values.append(product_id)
    query = (
        f"UPDATE products SET {', '.join(fields)} "
        f"WHERE id = ${len(values)}"
    )
    await pool.execute(query, *values)


async def delete_product(pool: asyncpg.Pool, product_id: int) -> None:
    await pool.execute("DELETE FROM products WHERE id = $1", product_id)


async def get_category_by_name(pool: asyncpg.Pool, name: str) -> asyncpg.Record | None:
    return await pool.fetchrow(
        "SELECT * FROM categories WHERE name = $1", name
    )


# --- Orders ---


async def create_order(
    pool: asyncpg.Pool,
    user_id: int,
    username: str | None,
    product_id: int | None,
    receipt_file_id: str,
) -> asyncpg.Record:
    return await pool.fetchrow(
        "INSERT INTO orders (user_id, username, product_id, receipt_file_id) "
        "VALUES ($1, $2, $3, $4) RETURNING *",
        user_id,
        username,
        product_id,
        receipt_file_id,
    )


async def get_order(pool: asyncpg.Pool, order_id: int) -> asyncpg.Record | None:
    return await pool.fetchrow(
        "SELECT o.*, p.name AS product_name, p.price AS product_price, "
        "p.post_purchase_info "
        "FROM orders o JOIN products p ON o.product_id = p.id "
        "WHERE o.id = $1",
        order_id,
    )


async def update_order_status(
    pool: asyncpg.Pool, order_id: int, status: str
) -> None:
    await pool.execute(
        "UPDATE orders SET status = $1 WHERE id = $2", status, order_id
    )


async def get_recent_orders(
    pool: asyncpg.Pool, limit: int = 10
) -> list[asyncpg.Record]:
    return await pool.fetch(
        "SELECT o.*, p.name AS product_name "
        "FROM orders o JOIN products p ON o.product_id = p.id "
        "ORDER BY o.created_at DESC LIMIT $1",
        limit,
    )


# --- Users ---


async def save_user(pool: asyncpg.Pool, user_id: int, username: str | None, full_name: str | None) -> None:
    await pool.execute(
        "INSERT INTO users (id, username, full_name) VALUES ($1, $2, $3) "
        "ON CONFLICT (id) DO UPDATE SET username = $2, full_name = $3",
        user_id,
        username,
        full_name,
    )


async def get_users_count(pool: asyncpg.Pool) -> int:
    row = await pool.fetchrow("SELECT COUNT(*) AS cnt FROM users")
    return row["cnt"]


async def get_today_users_count(pool: asyncpg.Pool) -> int:
    row = await pool.fetchrow(
        "SELECT COUNT(*) AS cnt FROM users WHERE started_at::date = CURRENT_DATE"
    )
    return row["cnt"]


# --- Settings ---


async def get_setting(pool: asyncpg.Pool, key: str) -> str | None:
    row = await pool.fetchrow(
        "SELECT value FROM settings WHERE key = $1", key
    )
    return row["value"] if row else None


async def set_setting(pool: asyncpg.Pool, key: str, value: str) -> None:
    await pool.execute(
        "INSERT INTO settings (key, value) VALUES ($1, $2) "
        "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
        key,
        value,
    )
