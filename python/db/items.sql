CREATE TABLE IF NOT EXISTS categories (
    id  INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
);

CREATE TABLE IF NOT EXISTS items (
    id  INTEGER PRIMARY KEY AUTO_INCREMENT,
    name TEXT NOT NULL,
    category_id INTEGER,
    image_name TEXT,
    FOREIGN KEY (category_id) REFERENCES categories (category_id)
);

INSERT INTO items(id, name, category_id, image_name) VALUES (1, "jacket", 1, "510824dfd4caed183a7a7cc2be80f24a5f5048e15b3b5338556d5bbd3f7bc267.jpg")
INSERT INTO categories(id, name) VALUES (1, "fashion")

