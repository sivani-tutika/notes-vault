from typing import List, Optional
from sqlalchemy.orm import Session

from app.repositories import notes_repository
from app.schemas.notes_schema import NoteCreate, NoteUpdate
from app.models.notes_model import Note


def create_note(db: Session, note_in: NoteCreate, owner_id: int) -> Note:
    return notes_repository.create_note(db, title=note_in.title, content=note_in.content, owner_id=owner_id)


def get_note(db: Session, note_id: int) -> Optional[Note]:
    return notes_repository.get_note(db, note_id)


def get_notes_for_user(db: Session, owner_id: int) -> List[Note]:
    return notes_repository.get_notes_for_user(db, owner_id)


def update_note(db: Session, note_id: int, note_in: NoteUpdate) -> Optional[Note]:
    note = notes_repository.get_note(db, note_id)
    if not note:
        return None
    return notes_repository.update_note(db, note, title=note_in.title, content=note_in.content)


def delete_note(db: Session, note_id: int) -> bool:
    note = notes_repository.get_note(db, note_id)
    if not note:
        return False
    notes_repository.delete_note(db, note)
    return True
