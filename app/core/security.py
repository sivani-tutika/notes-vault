from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from app.db.database import get_db
from app.repositories.user_repository import get_user_by_username
from app.schemas.user_schema import TokenData

# Use pbkdf2_sha256 as the primary hashing scheme to avoid requiring the bcrypt C-extension.
# This is a secure, widely used KDF and works without native dependencies.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/token")


# bcrypt has a 72-byte password input limit. To avoid errors when users enter
# longer passwords, truncate the UTF-8 encoded bytes to 72 bytes in a
# character-safe way (decode ignoring partial character at the end).
BCRYPT_MAX_BYTES = 72


def _truncate_password(password: str) -> str:
    """Return a string whose UTF-8 encoding is at most BCRYPT_MAX_BYTES.

    If the original UTF-8 bytes exceed the limit, the bytes are truncated and
    then decoded with 'ignore' to drop any partial trailing character.
    """
    if not isinstance(password, str):
        password = str(password)
    b = password.encode("utf-8")
    if len(b) <= BCRYPT_MAX_BYTES:
        return password
    truncated = b[:BCRYPT_MAX_BYTES]
    return truncated.decode("utf-8", errors="ignore")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Truncate plain password before verification to match how it was hashed
    truncated = _truncate_password(plain_password)
    return pwd_context.verify(truncated, hashed_password)


def get_password_hash(password: str) -> str:
    # Safely truncate before hashing to avoid bcrypt's 72-byte limit error
    safe = _truncate_password(password)
    return pwd_context.hash(safe)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user
