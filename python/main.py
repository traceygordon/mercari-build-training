import os
import logging
import pathlib
import sqlite3
from fastapi import FastAPI, Form, HTTPException, Depends, Query, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
import hashlib
from typing import Optional

#PATHS
images = pathlib.Path(__file__).parent.resolve() / "images"
items_file = pathlib.Path(__file__).parent.resolve() / "items.json"
db = pathlib.Path(__file__).parent.resolve() / "db" / "mercari.sqlite3"
SQL_File = pathlib.Path(__file__).parent.resolve() / "db" / "items.sql"

#MIDDLEWARE
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

#TEST
class HelloResponse(BaseModel):
    message: str


@app.get("/", response_model=HelloResponse)
def hello():
    return HelloResponse(**{"message": "Hello, world!"})


#MODELS
class Item(BaseModel):
    id: Optional[int] = None
    name: str
    category: str



class AddItemResponse(BaseModel):
    message: str


#DATABASE AND GET ITEMS
@app.get("/items")
def get_items():
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items;") 
    data = cursor.fetchall()
    conn.close()
    return AddItemResponse(**{"message": f"items: {data}"})

def get_db():
    conn = sqlite3.connect(db)
    return conn

def setup_database():
    # Ensure the db directory exists
    db_dir = pathlib.Path(__file__).parent.resolve() / "db"
    db_dir.mkdir(exist_ok=True)
    
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    if SQL_File.exists():
        with open(SQL_File, 'r') as f:
            cursor.executescript(f.read())
    conn.commit()
    conn.close()


#GET IMAGE
@app.get("/image/")
async def get_image(image_name: Optional[str] = Query(None)):
    if image_name is None:
        image_name = "default.jpg"

    image_path = images / image_name

    if not image_name.endswith(".jpg"):
        raise HTTPException(status_code=400, detail="Image must end with .jpg")

    if not image_path.exists():
        logger.debug(f"Image not found: {image_path}")
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(image_path)


#HASHED IMAGE
def hash_image(image_file: UploadFile):
    image = image_file.file.read()
    hash_value = hashlib.sha256(image).hexdigest()
    hashed_image_name = f"{hash_value}.jpg"
    hashed_image_path = images / hashed_image_name
    
    with open(hashed_image_path, 'wb') as f:
        f.write(image)
    return hashed_image_name


#POST
def insert_item(item: Item, db: sqlite3.Connection):
    cursor = None
    try:
        cursor = db.cursor()
        query_category = "SELECT id FROM categories WHERE name = ?"
        cursor.execute(query_category, (item.category,))
        rows = cursor.fetchone()
        if rows is None:
            insert_query_category = "INSERT INTO categories (name) VALUES (?)"
            cursor.execute(insert_query_category, (item.category,))
            category_id = cursor.lastrowid
        else:
            category_id = rows[0]
            
        query = """
        INSERT INTO items (name, category) VALUES (?, ?)
        """
        cursor.execute(query, (item.name, category_id))

        db.commit()
    except sqlite3.DatabaseError as e:
        db.rollback() 
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        if cursor:
            cursor.close()

@app.post("/items/json", response_model=AddItemResponse)
def add_item_json(item: Item):
    if not item.name:
        raise HTTPException(status_code=400, detail="name is required")

    if not item.category:
        raise HTTPException(status_code=400, detail="category is required")
    
    db_conn = get_db()
    try:
        insert_item(item, db_conn)
        return AddItemResponse(**{"message": f"item received: {item.name}, {item.category}"})
    finally:
        db_conn.close()

@app.post("/items", response_model=AddItemResponse)
def add_item(
    name: str = Form(...),
    category: str = Form(...),
):
    if not name:
        raise HTTPException(status_code=400, detail="name is required")

    if not category:
        raise HTTPException(status_code=400, detail="category is required")
    
    db_conn = get_db()
    try:
        insert_item(Item(name=name, category=category), db_conn)
        return AddItemResponse(**{"message": f"item received: {name}, {category}"})
    finally:
        db_conn.close()
