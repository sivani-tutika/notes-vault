from datetime import timedelta
from typing import Optional
from sqlalchemy.orm import Session

from app.repositories.user_repository import get_user_by_username, create_user as repo_create_user
from app.core import security
from app.schemas.user_schema import UserCreate


def create_user(db: Session, user_in: UserCreate):
    existing = get_user_by_username(db, user_in.username)
    if existing:
        raise ValueError("Username already registered")
    hashed = security.get_password_hash(user_in.password)
    return repo_create_user(db, username=user_in.username, hashed_password=hashed)


def authenticate_user(db: Session, username: str, password: str) -> Optional[object]:
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not security.verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token_for_user(user, expires_delta: Optional[timedelta] = None) -> str:
    data = {"sub": user.username}
    return security.create_access_token(data=data, expires_delta=expires_delta)
