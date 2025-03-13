DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS items;

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL COLLATE NOCASE UNIQUE
);

CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL COLLATE NOCASE,
    category TEXT NOT NULL,
    FOREIGN KEY (category) REFERENCES categories(id)
);

INSERT INTO categories (id, name) VALUES (1, 'fashion');
INSERT INTO items (id, name, category) VALUES (1, 'jacket', 'fashion');

SELECT * FROM categories;
SELECT * FROM items;