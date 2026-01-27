from sqlalchemy.orm import Session
from typing import List, Optional, cast
from app.models.notes_model import Note


def create_note(db: Session, title: str, content: Optional[str], owner_id: int) -> Note:
    note = Note(title=title, content=content, owner_id=owner_id)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def get_note(db: Session, note_id: int) -> Optional[Note]:
    return db.query(Note).filter(Note.id == note_id).first()


def get_notes_for_user(db: Session, owner_id: int) -> List[Note]:
    result = db.query(Note).filter(Note.owner_id == owner_id).all()
    return cast(List[Note], result)


def update_note(db: Session, note: Note, title: Optional[str], content: Optional[str]) -> Note:
    if title is not None:
        note.title = title
    if content is not None:
        note.content = content
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def delete_note(db: Session, note: Note) -> None:
    db.delete(note)
    db.commit()
