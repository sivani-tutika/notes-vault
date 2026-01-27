import pytest
from sqlalchemy import text
from app.db.database import engine, SessionLocal

@pytest.fixture
def db_session():
    """Provide a SQLAlchemy session for testing."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_database_connection():
    """Test if the engine can connect and execute a simple query."""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1

def test_session_local(db_session):
    """Test if the session works for executing queries."""
    result = db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1
