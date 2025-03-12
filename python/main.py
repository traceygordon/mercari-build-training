import os
import logging
import pathlib
import sqlite3
import hashlib
import json
from fastapi import FastAPI, UploadFile, HTTPException, Query, Depends, Form, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List
from contextlib import asynccontextmanager

# cmd to start server uvicorn main:app --reload --port 9000

# Define the path to the images & sqlite3 database
images = pathlib.Path(__file__).parent.resolve() / "images"
db = pathlib.Path(__file__).parent.resolve() / "db" / "mercari.sqlite3"
# sql_file = pathlib.Path(__file__).parent.resolve() / "db" / "items.sql"

def get_db():
    if not db.exists():
        raise HTTPException(status_code=404, detail="Database not found")

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# STEP 5-1: set up the database connection
def setup_database():
    conn = sqlite3.connect('db/mercari.sqlite3')
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL
);
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        category_id INTEGER,
        image_name TEXT,
        FOREIGN KEY (category_id) REFERENCES categories (category_id)
);
    """)
    conn.commit()
    conn.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_database()
    yield


app = FastAPI(lifespan=lifespan)

logger = logging.getLogger("uvicorn")
logger.level = logging.INFO
images = pathlib.Path(__file__).parent.resolve() / "images"
origins = [os.environ.get("FRONT_URL", "http://localhost:3000")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

class Item(BaseModel):
    name: str
    category: str
    image_name: str
    category_id: int

class HelloResponse(BaseModel):
    message: str

class AddItemResponse(BaseModel):
    message: str

def get_items(category_id, db: sqlite3.Connection):
    try:
        cursor = db.cursor()
        query = """
        SELECT items.name, categories.name AS category, items.image_name FROM items
        JOIN categories ON items.category_id = categories.id
        WHERE items.category_id = ?
        """
        cursor.execute(query, (category_id,))
        rows = cursor.fetchall()
        items = [{"name": name, "category": category, "image_name": image_name} for name, category, image_name in rows]
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
    finally:
        cursor.close()


# def get_items_from_database_by_id(id: int)-> Dict[str, List[Dict[str, str]]]:
#     try:
#         conn = sqlite3.connect(db)
#         cursor = conn.cursor()
#         query = """
#         SELECT items.name, categories.name AS category, image_name
#         FROM items
#         JOIN categories
#         ON category_id = categories.id
#         WHERE items.id = ?
#         """
#         cursor.execute(query, (id,))
#         rows = cursor.fetchall()
#         items_list = [{"name": name, "category":category, "image_name": image_name} for name, category, image_name in rows]
#         result = {"items": items_list}
#         conn.commit()

#         return result

#     except Exception as e:
#         return {f"An unexpected error occurred: {e}"}
    
#     finally:
#         cursor.close()


def insert_item_db(item: Item, category_id, db: sqlite3.Connection):
    try:
        
        cursor = db.cursor()
        cursor.execute(
        "INSERT INTO items (name, category_id, image_name) VALUES (?, ?, ?)",
        (item.name, item.category_id, item.image_name)
    )
        db.commit()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

    finally:
        cursor.close()

def hash_image(image_file: UploadFile):
    try:
        image = image_file.file.read()
        hash_value = hashlib.sha256(image).hexdigest()
        hashed_image_name = f"{hash_value}.jpeg"      
        
        hashed_image_path = images / hashed_image_name

        with open(hashed_image_path, 'wb') as f:
            f.write(image)


        return hashed_image_name
    
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred: {e}")


@app.get("/", response_model=HelloResponse)
def hello():
    return HelloResponse(**{"message": "Hello, world!"})


# add_item is a handler to add a new item for POST /items .
@app.post("/items", response_model=AddItemResponse)
def add_item(
    name: str = Form(...),
    category: str = Form(...),
    image: UploadFile = File(...),
    db: sqlite3.Connection = Depends(get_db),
):
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    if not category:
        raise HTTPException(status_code=400, detail="category is required")
    if not image:
        raise HTTPException(status_code=400, detail="image is required")
    
    try:
        cursor = db.cursor()
        cursor.execute("SELECT id FROM categories WHERE name = ?", (category,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Category not found")
        
        category_id = row["id"]

        hashed_image = hash_image(image)
        insert_item_db(Item(name=name, category=category, image_name=hashed_image, category_id=category_id), category_id, db)

        return AddItemResponse(message=f"Item received: {name}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.get("/items")
def get_items():
    all_data = get_items(db)
    return all_data

# @app.get("items/{item_id}")
# def get_item_by_id(item_id):
#     item_id_int = int(item_id)
#     all_data = get_items_from_database_by_id()
#     item = all_data["items"] [item_id_int -1]
#     return item


# get_image is a handler to return an image for GET /images/{filename} .
@app.get("/image/{image_name}")
async def get_image(image_name):
    # Create image path
    image = images / image_name

    if not image_name.endswith(".jpg"):
        raise HTTPException(status_code=400, detail="Image path does not end with .jpg")

    if not image.exists():
        logger.debug(f"Image not found: {image}")
        image = images / "default.jpg"

    return FileResponse(image)

# @app.get("/search")
# def search_keyword(keyword: str = Query(...), db: sqlite3.Connection = Depends(get_db)):
#     try:
#         cursor = db.cursor()
#         query = """
#         SELECT items.name, categories.name AS category, image_name
#         FROM items
#         JOIN categories
#         ON category_id = categories.id
#         WHERE items.name LIKE ?
#         """
#         pattern = f"%{keyword}%"
#         cursor.execute(query, (pattern,))
#         rows = cursor.fetchall()
#         items_list = [{"name": name, "category":category, "image_name": image_name} for name, category, image_name in rows]
#         result = {"items": items_list}

#         return result
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error: {e}")
    
#     finally:
#         cursor.close()