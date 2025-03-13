import pathlib
import sqlite3
from fastapi import FastAPI, Depends, HTTPException, Form, UploadFile
from pydantic import BaseModel
from typing import List

db_path = pathlib.Path(__file__).parent.resolve() / "db" / "mercari.db"
app = FastAPI(debug=True)

# Proper Dependency Injection for DB
def get_db():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# Setup database function (run separately, not on every app run)
def setup_database():
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        cursor.execute("DROP TABLE IF EXISTS items;")
        cursor.execute("DROP TABLE IF EXISTS categories;")

        cursor.execute("""
            CREATE TABLE categories (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            );
        """)

        cursor.execute("""
            CREATE TABLE items (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                category_id INTEGER,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            );
        """)

        cursor.execute("INSERT INTO categories VALUES (?, ?)", (1, 'fashion'))
        cursor.execute("INSERT INTO items VALUES (?, ?, ?)", (1, 'jacket', 1))

        conn.commit()

def seed_database():
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO categories VALUES (?, ?)", (1, 'fashion'))
        cursor.execute("INSERT INTO items VALUES (?, ?, ?)", (1, 'jacket', 1))

        conn.commit()

# Models
class Item(BaseModel):
    id: int
    name: str
    category_id: int

class AddItemResponse(BaseModel):
    message: str

# Endpoint to get items
@app.get("/items", response_model=List[Item], )
def get_items(db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    try:
        cursor.execute("SELECT * FROM items;")
        rows = cursor.fetchall()
        items = [Item(**row) for row in map(dict, rows)]
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

#POST Item
def insert_item(item: Item, db: sqlite3.Connection):
    try:
        cursor = db.cursor()
        cursor.execute(
        "INSERT INTO items (name) VALUES (?)",
        (item.name)
    )
        db.commit()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
    
    finally:
        cursor.close()
    


@app.post("/items", response_model=AddItemResponse)
def add_item(
    name: str = Form(...),
    category: str = Form(...),
    image_name: UploadFile = Form(...),
    db: sqlite3.Connection = Depends(get_db),
):
    if not name:
        raise HTTPException(status_code=400, detail="name is required")

    insert_item(Item(name=name, category=category, image=image_name))
    return AddItemResponse(**{"message": f"item received: {name}"})


# @app.on_event("startup")
# def startup_event():
#     seed_database()