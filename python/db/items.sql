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
    image_name TEXT NOT NULL,
    FOREIGN KEY (category) REFERENCES categories(id)
);

INSERT INTO categories (id, name) VALUES (1, 'fashion');
INSERT INTO items (id, name, category, image_name) VALUES (1, 'jacket', 'fashion', '510824dfd4caed183a7a7cc2be80f24a5f5048e15b3b5338556d5bbd3f7bc267.jpg');

SELECT * FROM categories;
SELECT * FROM items;