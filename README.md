---
title: Learning FastAPI with Note App
emoji: 📝
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---


# FastAPI Learning — Notes App

A complete learning journal covering everything built and discussed during this session — from Python concepts to a fully working FastAPI Notes API with SQLite database.

---

## Table of Contents

1. [Python Concepts](#python-concepts)
2. [Project Structure](#project-structure)
3. [FastAPI Basics](#fastapi-basics)
4. [Pydantic & BaseModel](#pydantic--basemodel)
5. [Path Parameters vs Query Parameters vs Request Body](#path-parameters-vs-query-parameters-vs-request-body)
6. [HTTP Methods & Status Codes](#http-methods--status-codes)
7. [In-Memory CRUD](#in-memory-crud)
8. [Database Integration](#database-integration)
9. [SQLAlchemy Concepts](#sqlalchemy-concepts)
10. [Full App Code](#full-app-code)
11. [Running the Project](#running-the-project)
12. [Git & Deployment](#git--deployment)

---

## Python Concepts

### Generators

A generator stores the **recipe**, not the **results**. Instead of computing and storing all values upfront, it produces one value at a time — on demand.

```python
def double_numbers(n):
    for x in range(n):
        yield x * 2  # pause here, give value, resume later

gen = double_numbers(5)
print(next(gen))  # 0
print(next(gen))  # 2
print(next(gen))  # 4
```

**Key points:**
- `yield` produces a value, pauses the function, and resumes from that exact point next time
- Generator stores constant, tiny memory regardless of how many values
- Once exhausted, it cannot be rewound
- Values are **temporary** — they exist just long enough to be used, then discarded

**Memory comparison:**
```python
import sys

nums_list = [x * 2 for x in range(1_000_000)]
nums_gen  = (x * 2 for x in range(1_000_000))

print(sys.getsizeof(nums_list))  # ~8MB
print(sys.getsizeof(nums_gen))   # ~200 bytes
```

**When to use generators:**
- When values are just a means to an end (summing, filtering, processing)
- Reading huge files line by line
- Streaming database rows without loading the full table
- FastAPI streaming responses

**Conveyor belt analogy:** Items come out one by one, you inspect each one, it moves off and disappears. The belt never piles up items.

---

## Project Structure

```
FASTAPI--LEARNING/
    .venv/                  ← virtual environment (not pushed to git)
    app/
        __init__.py         ← makes app/ a Python package (enables relative imports)
        app.py              ← FastAPI routes, all endpoints
        database.py         ← engine, SessionLocal, Base, get_db
        models.py           ← Notes(Base) SQLAlchemy table definition
    .gitignore
    .python-version
    main.py                 ← uvicorn entry point
    pyproject.toml          ← project dependencies (managed by uv)
    uv.lock
    README.md
```

**Why `__init__.py`?**
Python needs this empty file to treat `app/` as a package — without it, relative imports (`.database`, `.models`) won't work.

**Setup commands with uv:**
```
uv init .               # scaffold project
uv venv                 # create virtual environment
.venv\Scripts\activate  # activate it (Windows)
uv add fastapi uvicorn sqlalchemy  # install dependencies
```

---

## FastAPI Basics

### Creating the app

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Hello World"}
```

- `FastAPI()` — creates the application instance
- `@app.get("/")` — decorator that registers a GET route at "/"
- Returning a dict → FastAPI automatically converts it to JSON

### Running the server

```
uvicorn app.app:app --reload
```

- `app.app` — the module path (app folder → app.py file)
- `app` — the FastAPI instance inside that file
- `--reload` — auto-restarts on file changes (development only)

### Auto-generated docs

FastAPI generates interactive API documentation automatically:
- `http://localhost:8000/docs` — Swagger UI (try out endpoints)
- `http://localhost:8000/redoc` — ReDoc UI

---

## Pydantic & BaseModel

Pydantic is a Python library for **data validation**. FastAPI uses it under the hood for everything.

### Defining a model

```python
from pydantic import BaseModel

class NoteCreate(BaseModel):
    title: str
    content: str
```

- Inherit from `BaseModel`
- Fields with type hints = automatic validation
- No default = **required**
- Has default = **optional**

### What Pydantic does automatically

```python
# Auto coercion — "22" becomes 22
u = User(name="Mohammed", age="22")

# Validation error — "abc" can't become int
u = User(name="Mohammed", age="abc")  # raises ValidationError
```

### Optional fields

```python
from typing import Optional

class Note(BaseModel):
    title: str                      # required
    content: str                    # required
    is_published: bool = False      # optional, default False
    tags: Optional[str] = None      # optional, default None
```

### Field() wrapper

Used when a field needs extra configuration beyond just a type hint:

```python
from pydantic import BaseModel, Field
import uuid

class Note(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
```

**Why `default_factory` and not `default`?**
```python
# WRONG — runs once at class definition, every Note gets the SAME id
id: str = str(uuid.uuid4())

# CORRECT — runs fresh for every new Note object
id: str = Field(default_factory=lambda: str(uuid.uuid4()))
```

**Why lambda?**
`default_factory` expects a callable (a function). `uuid.uuid4` alone gives a UUID object (not JSON serializable). Wrapping in `lambda: str(uuid.uuid4())` gives a fresh string UUID every time.

### Useful methods

```python
note = Note(id="1", title="My Note", content="Hello")

note.model_dump()       # {"id": "1", "title": "My Note", "content": "Hello"}
note.model_dump_json()  # '{"id":"1","title":"My Note","content":"Hello"}'
```

### Two schemas pattern

Always separate input schema from stored schema:

```python
# What the USER sends — no ID
class NoteCreate(BaseModel):
    title: str
    content: str

# What gets STORED — has ID
class Note(BaseModel):
    id: str
    title: str
    content: str
```

User should never decide their own ID — the system assigns it automatically.

---

## Path Parameters vs Query Parameters vs Request Body

### Path Parameters

Part of the URL itself. Used to identify a **specific resource**.

```python
@app.get("/notes/{note_id}")
def get_note(note_id: str):
    ...
# URL: /notes/abc-123
```

### Query Parameters

Come after `?` in the URL. Used for **filtering, searching, pagination**.

```python
@app.get("/notes")
def get_notes(limit: int = 10, search: str = ""):
    ...
# URL: /notes?limit=5&search=python
```

### Request Body

Sent as JSON in the request body. Used for **structured data** (POST, PUT).

```python
@app.post("/notes")
def create_note(note: NoteCreate):  # Pydantic model = request body
    ...
```

### How FastAPI decides what something is

| Parameter type | FastAPI treats it as |
|---|---|
| Variable in `{}` in route | Path parameter |
| Plain type (`int`, `str`) not in route | Query parameter |
| Pydantic `BaseModel` | Request body |
| Pydantic `BaseModel` with `Depends()` | Grouped query parameters |

### Path vs Query — when to use which

```
/notes/abc-123          → "I want THIS specific note" (path param)
/notes?limit=5          → "I want any 5 notes" (query param)
/notes?search=python    → "I want notes matching python" (query param)
```

Path params should always be **unique identifiers** (like `id`) — because they're expected to return exactly one resource.

---

## HTTP Methods & Status Codes

### Methods

| Method | Purpose |
|---|---|
| `GET` | Fetch data |
| `POST` | Create new data |
| `PUT` | Replace/update entire resource |
| `DELETE` | Remove data |
| `PATCH` | Partially update (only changed fields) |

**PUT vs PATCH:** PUT replaces the entire resource (you send all fields). PATCH only updates the fields you send.

### Status Codes

| Code | Meaning | When to use |
|---|---|---|
| `200` | OK | Default success |
| `201` | Created | After POST (resource created) |
| `204` | No Content | After DELETE (no body returned) |
| `404` | Not Found | Resource doesn't exist |
| `422` | Validation Error | FastAPI sends automatically for bad input |
| `500` | Internal Server Error | Something crashed on the server |

### HTTPException

```python
from fastapi import HTTPException

raise HTTPException(status_code=404, detail="Note not found")
```

Always use `raise` — just creating the object does nothing.

---

## In-Memory CRUD

Before adding a database, notes were stored in a Python list. This disappears when the server restarts — but great for learning the concepts.

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uuid

app = FastAPI()

class NoteCreate(BaseModel):
    title: str
    content: str

class Note(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str

notes = []  # in-memory "database"

# CREATE
@app.post("/post_note", status_code=201)
def post_note(note: NoteCreate):
    new_note = Note(title=note.title, content=note.content)
    notes.append(new_note)
    return new_note

# READ ALL
@app.get("/get_all_notes")
def get_all_notes():
    return notes

# UPDATE
@app.put("/update_note/{note_id}")
def update_note(note_id: str, note_changes: NoteCreate):
    for i, note in enumerate(notes):
        if note.id == note_id:
            notes[i].title = note_changes.title
            notes[i].content = note_changes.content
            return notes[i]
    raise HTTPException(status_code=404, detail="Note not found")

# DELETE
@app.delete("/delete_note/{note_id}")
def delete_note(note_id: str):
    for i, note in enumerate(notes):
        if note.id == note_id:
            del notes[i]
            return {"message": f"Note with id: {note_id} deleted"}
    raise HTTPException(status_code=404, detail="Note not found")
```

**Why `enumerate()`?** When deleting from a list you need the **index** (`i`) to use `del notes[i]`. `enumerate()` gives both the index and the object in one loop.

**Important:** Always put `raise HTTPException` **outside and after** the loop — raise 404 only after checking ALL items and finding nothing. Raising inside the loop with `else` raises on the very first non-match.

---

## Database Integration

### Why a database?

In-memory list disappears on server restart. SQLite persists data in a `.db` file on disk.

```
Before: Request → FastAPI → notes = []  (dies on restart)
After:  Request → FastAPI → SQLAlchemy → notes.db (persists forever)
```

### database.py

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./notes.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### models.py

```python
from sqlalchemy import Column, String
from .database import Base
import uuid

class Notes(Base):
    __tablename__ = "notes"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
```

---

## SQLAlchemy Concepts

### The three layers

```
Your Python code
      ↓
  Engine (the connection to the database)
      ↓
  Session (a single conversation/transaction)
      ↓
  Database file (notes.db)
```

### Engine

The core connection object — knows what database type and where it lives. Created **once per application**.

```python
engine = create_engine("sqlite:///./notes.db")
```

Think of it as the **phone line installed** between your app and the database.

### Why `check_same_thread=False`?

SQLite was designed assuming **one connection = one thread**. FastAPI handles multiple requests concurrently across different threads. Without this setting, SQLite would throw an error when a different thread tries to use the connection.

```
Thread 1 creates connection → belongs to Thread 1
Request on Thread 2 tries to use it → SQLite: ❌ ERROR!
```

`check_same_thread=False` tells SQLite to drop that restriction. SQLAlchemy's session system manages thread safety instead — each thread gets its own session via `SessionLocal()`.

### SessionLocal

A **factory** that produces new sessions. Each session is an independent conversation with the database.

```python
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

- `bind=engine` — which engine/database to use
- `autocommit=False` — changes are NOT saved until you explicitly call `db.commit()`
- `autoflush=False` — pending changes are NOT sent to db until commit

**Why `autocommit=False`?** Gives you control to group multiple operations and either commit them all or roll them all back:

```python
db.add(note1)
db.add(note2)
db.add(note3)
# none saved yet

db.commit()    # save ALL three together — atomic
# OR
db.rollback()  # undo all three if something went wrong
```

### Session as a meeting room

```
Engine = the building's phone line (always installed, shared)

Session = booking a meeting room that uses that phone line temporarily

Room opens   → SessionLocal() called
             → borrows a connection from engine's pool
Work happens → db.add(), db.query(), db.commit()
Room closes  → db.close()
             → connection returned to pool for next session
```

### Base

```python
Base = declarative_base()
```

Special parent class. Every table you define inherits from this — it's how SQLAlchemy knows "this Python class represents a database table".

### Column types and options

```python
id    = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
title = Column(String, nullable=False)
```

- `primary_key=True` — unique identifier, no two rows can have the same value
- `index=True` — faster lookups on this column
- `nullable=False` — this field cannot be empty/NULL
- `default=` — SQLAlchemy's equivalent of Pydantic's `default_factory`

### Pydantic Field() vs SQLAlchemy default=

| Layer | Auto-generate default |
|---|---|
| Pydantic `BaseModel` | `Field(default_factory=lambda: ...)` |
| SQLAlchemy `Column` | `default=lambda: ...` |

They're separate systems — Pydantic's `default_factory` does NOT apply to SQLAlchemy objects.

### Two separate "Note" classes

| File | Class | Purpose |
|---|---|---|
| `app.py` | `Note(BaseModel)` | Pydantic — validates request/response JSON |
| `models.py` | `Notes(Base)` | SQLAlchemy — defines database table structure |

They look similar but serve completely different jobs.

### Creating tables

```python
from .database import engine, Base
from .models import Notes  # import so Base knows about it

Base.metadata.create_all(bind=engine)
```

Must be called when the app starts — runs `CREATE TABLE IF NOT EXISTS` SQL behind the scenes. Safe to call every time since it only creates tables that don't exist yet.

### get_db — dependency with yield

```python
def get_db():
    db = SessionLocal()  # open session
    try:
        yield db          # hand session to endpoint
    finally:
        db.close()        # ALWAYS runs — whether success or error
```

This is a **generator function** using `yield`. The `finally` block runs no matter what — success, error, committed or not. It's a guaranteed cleanup to prevent session leaks.

### Depends()

FastAPI's dependency injection system. Tells FastAPI to call a function and inject its result:

```python
from fastapi import Depends
from sqlalchemy.orm import Session
from .database import get_db

@app.post("/notes")
def create_note(note: NoteCreate, db: Session = Depends(get_db)):
    # db is a ready-to-use session injected automatically
    ...
```

FastAPI sees `Depends(get_db)`, calls `get_db()`, gets the session, injects it as `db`.

### Database operations

```python
# CREATE
db_note = Notes(title=note.title, content=note.content)
db.add(db_note)      # stage the object
db.commit()          # permanently save to database
db.refresh(db_note)  # reload from db into Python object
return db_note

# READ ALL
notes = db.query(Notes).all()

# READ ONE
note = db.query(Notes).filter(Notes.id == note_id).first()

# UPDATE
note.title = note_changes.title      # modify directly
note.content = note_changes.content
db.commit()
db.refresh(note)

# DELETE
db.delete(note)
db.commit()
```

### Why db.refresh()?

After `db.commit()`, SQLAlchemy **expires** the Python object — clears its attribute values from memory. The data is safe in the database, but your Python object is wiped clean.

```python
db.commit()
print(new_note.title)  # ❌ might throw DetachedInstanceError

db.refresh(new_note)
print(new_note.title)  # ✅ reloaded from database
```

### The full flow

```
db.add()      → stage the object (tell session about it)
db.commit()   → permanently save to database → Python object expires
db.refresh()  → reload from database back into Python object
return        → send fresh, accurate data to client
```

---

## Full App Code

### app/database.py

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./notes.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### app/models.py

```python
from sqlalchemy import Column, String
from .database import Base
import uuid

class Notes(Base):
    __tablename__ = "notes"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
```

### app/app.py

```python
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .database import engine, Base, get_db
from .models import Notes

Base.metadata.create_all(bind=engine)

app = FastAPI()

class NoteCreate(BaseModel):
    title: str
    content: str

class Note(BaseModel):
    id: str
    title: str
    content: str

@app.get("/")
def home():
    return {"message": "Hello, world"}

@app.post("/post_note", status_code=201)
def post_note(note: NoteCreate, db: Session = Depends(get_db)):
    new_note = Notes(title=note.title, content=note.content)
    db.add(new_note)
    db.commit()
    db.refresh(new_note)
    return new_note

@app.get("/get_all_notes")
def get_all_notes(db: Session = Depends(get_db)):
    notes = db.query(Notes).all()
    return notes

@app.put("/update_note/{note_id}")
def update_note(note_id: str, note_changes: NoteCreate, db: Session = Depends(get_db)):
    note = db.query(Notes).filter(Notes.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    note.title = note_changes.title
    note.content = note_changes.content
    db.commit()
    db.refresh(note)
    return note

@app.delete("/delete_note/{note_id}")
def delete_note(note_id: str, db: Session = Depends(get_db)):
    note = db.query(Notes).filter(Notes.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()
    return {"message": f"Note with id: {note_id} deleted successfully"}
```

### main.py

```python
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.app:app", host="0.0.0.0", port=8000, reload=True)
```

---

## Running the Project

```bash
# Install dependencies
uv sync

# Run the server
uv run main.py

# Or directly with uvicorn
uvicorn app.app:app --reload
```

Visit `http://localhost:8000/docs` for the interactive API documentation.

---

## Git & Deployment

### .gitignore essentials

```
__pycache__/
*.py[oc]
.venv
notes.db        ← database file, local only
```

### Git workflow

```bash
git init
git add .
git commit -m "first commit"
git remote add origin https://github.com/username/repo.git
git branch -M main
git push -u origin main

# Future commits
git add .
git commit -m "your message"
git push
```

### Remove a file from git tracking (without deleting it locally)

```bash
git rm --cached notes.db
git commit -m "remove notes.db from tracking"
```

### Deploying to Hugging Face Spaces (Docker)

Create a `Dockerfile` in the project root:

```dockerfile
FROM python:3.11-slim

WORKDIR /code

COPY pyproject.toml .
COPY uv.lock .

RUN pip install uv && uv sync

COPY . .

EXPOSE 7860

CMD ["uv", "run", "uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "7860"]
```

**Note:** Hugging Face Spaces requires port `7860`. SQLite data will reset on Space restart since the filesystem is ephemeral — use a hosted database like Neon (PostgreSQL) for persistent data in production.

---

*Built during a FastAPI learning session — from Hello World to a fully working Notes API with SQLite database.*
