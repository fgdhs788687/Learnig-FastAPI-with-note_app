from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import uuid
from .database import get_db, engine, Base
from sqlalchemy.orm import Session
from .models import Notes
# This line will create the database tables based on the models defined in models.py
# If they dont exist
Base.metadata.create_all(bind=engine) # 

# Creating instance of the FastAPI APP:
app = FastAPI()


@app.get("/")
def home():
    return {"message": "Hello, world"}


# Creating a class called Note which inherits from the BaseModel:
# Schemas for the request and response bodies of the API endpoints.
class NoteCreate(BaseModel):
    title: str
    content: str

class Note(BaseModel):
    id: str
    title: str
    content: str


# Creating as well storing the notes:
@app.post("/post_note")
def post_note(note: NoteCreate, db: Session = Depends(get_db)):
    new_note = Notes(title = note.title, content = note.content)
    db.add(new_note) 
    db.commit()
    db.refresh(new_note) 
    return new_note



# Seeing all the notes which are availble
@app.get("/get_all_notes")
def get_all_notes(
    db: Session = Depends(get_db)
):
    notes = db.query(Notes).all()
    return notes



# Deletion of notes by id
@app.delete("/delete_note/{note_id}")
def delete_note(
    note_id: str,
    db: Session = Depends(get_db)
):
    notes = db.query(Notes).all()
    for note in notes:
        if note.id == note_id:
            db.delete(note)
            db.commit()
            return {
                "message": f"Note with id {note_id} has been deleted successfully."
            }
    raise HTTPException(status_code=404, detail="Note Not Found")

       

# Updating the notes by id
@app.put("/update_note/{note_id}")
def update_note(
    note_id: str,
    NoteChanges: NoteCreate,
    db: Session = Depends(get_db)
):
    notes = db.query(Notes).all()

    for note in notes:
        if note.id == note_id:
            note.title = NoteChanges.title
            note.content = NoteChanges.content
            db.commit()
            db.refresh(note)
            return note
    raise HTTPException(status_code=404, detail="Note not Found") 


