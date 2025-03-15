import os
import logging
import pathlib
from fastapi import FastAPI, Form, HTTPException, Depends, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from pydantic import BaseModel
from contextlib import asynccontextmanager
import hashlib


images = pathlib.Path(__file__).parent.resolve() / "images"
db = pathlib.Path(__file__).parent.resolve() / "db" / "mercari.sqlite3"
sql_file = pathlib.Path(__file__).parent.resolve() / "db" / "items.sql"

def get_db():
    if not db.exists():
        yield

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row 
    try:
        yield conn
    finally:
        conn.close()


def setup_database():
    conn = sqlite3.connect(db) 
    cursor = conn.cursor()

    if sql_file.exists():
        with open(sql_file, "r", encoding="utf-8") as file:
            sql_script = file.read()
            cursor.executescript(sql_script)  
    
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


class HelloResponse(BaseModel):
    message: str


@app.get("/", response_model=HelloResponse)
def hello():
    return HelloResponse(**{"message": "Hello, world!"})


class AddItemResponse(BaseModel):
    message: str

class Item(BaseModel):
    id: int
    name: str
    category: str
    image_name: str


IMAGES_DIR ="images"
os.makedirs(IMAGES_DIR, exist_ok =True)


@app.post("/items", response_model=AddItemResponse)
def add_item(
    name: str = Form(...),
    category: str = Form(...),
    image: UploadFile =File(...), 
    db: sqlite3.Connection = Depends(get_db),
):
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    
    if not category:
        raise HTTPException(status_code=400, detail="category is required")
    
    image_bytes =image.file.read()
    image.file.seek(0)
    hashed_filename = hashlib.sha256(image_bytes).hexdigest() +".jpg"

    image_path = os.path.join(IMAGES_DIR, hashed_filename)
    with open(image_path, "wb") as buffer:
        buffer.write(image_bytes)

    cursor=db.cursor() 
    
    cursor.execute("SELECT id FROM categories WHERE name = ?", (category,))
    category_row = cursor.fetchone()

    if category_row:
        category_id = category_row["id"]

    else:
        cursor.execute("INSERT INTO categories (name) VALUES (?)", (category,))
        category_id = cursor.lastrowid

    cursor.execute(
        "INSERT INTO items (name, category_id, image_name) VALUES (?, ?, ?)",
        (name, category_id, hashed_filename),
    )
    db.commit()
    return AddItemResponse(**{"message": f"item received: {name}, {category}, {hashed_filename}"})


@app.get("/items")
def get_items(db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM items")
    cursor.execute(
        """SELECT items.id, items.name, categories.name as category, items.image_name
           FROM items
           JOIN categories ON items.category_id = categories.id"""
    )
    rows = cursor.fetchall()
    items_list = [{"id": id, "name": name, "category": category, "image_name": image_name} for id, name, category, image_name in rows]
    
    
    return {"items": items_list}
    
    
@app.get("/search")
def search_items(query: str, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute(
        """SELECT items.id, items.name, categories.name as category, items.image_name
           FROM items
           JOIN categories ON items.category_id = categories.id
           WHERE items.name LIKE ? OR categories.name LIKE ?""",
        (f"%{query}%", f"%{query}%"),
    )

    items = [
        {"id": row["id"], "name": row["name"], "category": row["category"], "image_name": row["image_name"]}
        for row in cursor.fetchall()
    ]

    if not items:
        raise HTTPException(status_code=404, detail="No items found with the given query")

    return {"items": items}
    
    
@app.get("/items/{item_id}")

def get_item(item_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute(
        """SELECT items.id, items.name, categories.name as category, items.image_name
           FROM items
           JOIN categories ON items.category_id = categories.id
           WHERE items.id = ?""",
        (item_id,),
    )

    row = cursor.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Item not found")

    return {"id": row["id"], "name": row["name"], "category": row["category"], "image_name": row["image_name"]}
    

@app.get("/image/{image_name}")
async def get_image(image_name: str):
    image = os.path.join(IMAGES_DIR, image_name)

    if not image_name.endswith(".jpg"):
        raise HTTPException(status_code=400, detail="Image path must end with .jpg")

    if not os.path.exists(image):
        logger.debug(f"Image not found: {image}")
        image = os.path.join(IMAGES_DIR, "default.jpg")


    return FileResponse(image)