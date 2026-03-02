-- Categories
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    sort_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT true
);

-- Products
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    category_id INT REFERENCES categories(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price INT NOT NULL DEFAULT 0,
    post_purchase_info TEXT,
    is_active BOOLEAN DEFAULT true,
    sort_order INT DEFAULT 0
);

-- Orders
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    username VARCHAR(100),
    product_id INT REFERENCES products(id),
    status VARCHAR(20) DEFAULT 'pending',
    receipt_file_id TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Settings (key-value)
CREATE TABLE IF NOT EXISTS settings (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT
);

-- Seed categories
INSERT INTO categories (name, sort_order) VALUES
    ('YouTube', 1),
    ('AI', 2)
ON CONFLICT DO NOTHING;

-- Seed products for YouTube (category_id = 1)
INSERT INTO products (category_id, name, price, sort_order) VALUES
    (1, 'Мини курс по YouTube', 99000, 1),
    (1, 'Топ 5 ниш', 0, 2),
    (1, 'Топ 15 ниш', 0, 3),
    (1, 'Топ 20 ниш', 0, 4),
    (1, 'Старореги', 0, 5),
    (1, 'Приложение автоматизация', 0, 6),
    (1, 'Приложение сценарий', 0, 7),
    (1, 'Настройка YouTube', 0, 8),
    (1, 'Создание превью', 0, 9),
    (1, 'Озвучка видео', 0, 10)
ON CONFLICT DO NOTHING;

-- Seed products for AI (category_id = 2)
INSERT INTO products (category_id, name, price, sort_order) VALUES
    (2, 'Gemini Pro', 0, 1),
    (2, 'GPT PLUS', 0, 2),
    (2, 'Grok', 0, 3),
    (2, 'Perplexity', 0, 4)
ON CONFLICT DO NOTHING;

-- Seed settings
INSERT INTO settings (key, value) VALUES
    ('card_number', ''),
    ('card_holder', ''),
    ('work_hours', '9:00-23:00'),
    ('support_contact', '@shumbolaaisupport')
ON CONFLICT (key) DO NOTHING;
