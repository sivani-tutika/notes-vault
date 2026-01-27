from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.schemas.notes_schema import NoteCreate, NoteOut, NoteUpdate
from app.db.database import get_db
from app.services import notes_service
from app.core.security import get_current_user

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("/", response_model=NoteOut)
def create_note(note_in: NoteCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    note = notes_service.create_note(db, note_in, owner_id=current_user.id)
    return note


@router.get("/", response_model=List[NoteOut])
def list_notes(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    notes = notes_service.get_notes_for_user(db, owner_id=current_user.id)
    return notes


@router.get("/{note_id}", response_model=NoteOut)
def read_note(note_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    note = notes_service.get_note(db, note_id)
    if not note or note.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return note


@router.put("/{note_id}", response_model=NoteOut)
def update_note(note_id: int, note_in: NoteUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    note = notes_service.get_note(db, note_id)
    if not note or note.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    updated = notes_service.update_note(db, note_id, note_in)
    return updated


@router.delete("/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    note = notes_service.get_note(db, note_id)
    if not note or note.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    success = notes_service.delete_note(db, note_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to delete note")
    return {"ok": True}
