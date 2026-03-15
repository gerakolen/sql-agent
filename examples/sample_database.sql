-- Пример базы данных для Text-to-SQL AI Assistant
-- Это пример схемы базы данных для тестирования

-- Таблица клиентов
CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    phone TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица продуктов
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    stock INTEGER DEFAULT 0
);

-- Таблица заказов
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10, 2) NOT NULL,
    status TEXT DEFAULT 'pending',
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

-- Таблица позиций заказа
CREATE TABLE order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Вставка тестовых данных
INSERT INTO customers (name, email, phone) VALUES
    ('Иван Иванов', 'ivan@example.com', '+7-900-123-4567'),
    ('Мария Петрова', 'maria@example.com', '+7-900-234-5678'),
    ('Алексей Сидоров', 'alex@example.com', '+7-900-345-6789'),
    ('Елена Козлова', 'elena@example.com', '+7-900-456-7890'),
    ('Дмитрий Новиков', 'dmitry@example.com', '+7-900-567-8901');

INSERT INTO products (name, category, price, stock) VALUES
    ('Ноутбук', 'Электроника', 59999.00, 10),
    ('Смартфон', 'Электроника', 29999.00, 25),
    ('Наушники', 'Электроника', 3999.00, 50),
    ('Книга Python', 'Книги', 1999.00, 100),
    ('Книга SQL', 'Книги', 1799.00, 80),
    ('Рюкзак', 'Аксессуары', 2499.00, 30),
    ('Чехол для телефона', 'Аксессуары', 999.00, 200),
    ('Клавиатура', 'Электроника', 4999.00, 40);

INSERT INTO orders (customer_id, order_date, total_amount, status) VALUES
    (1, '2024-01-15', 63998.00, 'completed'),
    (2, '2024-01-16', 29999.00, 'completed'),
    (3, '2024-01-17', 1999.00, 'completed'),
    (1, '2024-01-18', 4999.00, 'pending'),
    (4, '2024-01-19', 1799.00, 'completed'),
    (5, '2024-01-20', 3998.00, 'shipped');

INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
    (1, 1, 1, 59999.00),
    (1, 3, 1, 3999.00),
    (2, 2, 1, 29999.00),
    (3, 4, 1, 1999.00),
    (4, 7, 1, 4999.00),
    (5, 5, 1, 1799.00),
    (6, 3, 1, 3999.00),
    (6, 6, 1, 2499.00);
