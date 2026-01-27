import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure model modules are imported so they register with Base.metadata
import app.models.user_model  # noqa: F401
import app.models.notes_model  # noqa: F401

from app.db.database import get_db
from main import app
from app.db.database import Base


# Create an in-memory SQLite engine for tests
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def prepare_database():
    # Create tables in the in-memory database
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# Override the get_db dependency to use the testing session
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def client(prepare_database):
    # ensure dependency override is set before creating the TestClient
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c


def test_signup_and_token(client):
    # Signup
    resp = client.post("/users/", json={"username": "testuser", "password": "testpass"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "testuser"
    assert "id" in data

    # Obtain token
    resp = client.post("/users/token", data={"username": "testuser", "password": "testpass"})
    assert resp.status_code == 200
    token_data = resp.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"


def test_notes_crud_flow(client):
    # Signup and login a user
    resp = client.post("/users/", json={"username": "noteuser", "password": "notepass"})
    assert resp.status_code == 200

    resp = client.post("/users/token", data={"username": "noteuser", "password": "notepass"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create a note
    note_payload = {"title": "First Note", "content": "This is a note."}
    resp = client.post("/notes/", json=note_payload, headers=headers)
    assert resp.status_code == 200
    note = resp.json()
    assert note["title"] == note_payload["title"]
    note_id = note["id"]

    # List notes (should include the created note)
    resp = client.get("/notes/", headers=headers)
    assert resp.status_code == 200
    notes = resp.json()
    assert isinstance(notes, list)
    assert any(n["id"] == note_id for n in notes)

    # Get the specific note
    resp = client.get(f"/notes/{note_id}", headers=headers)
    assert resp.status_code == 200
    note_get = resp.json()
    assert note_get["id"] == note_id

    # Update the note
    update_payload = {"title": "Updated Title", "content": "Updated content."}
    resp = client.put(f"/notes/{note_id}", json=update_payload, headers=headers)
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["title"] == update_payload["title"]

    # Delete the note
    resp = client.delete(f"/notes/{note_id}", headers=headers)
    assert resp.status_code == 200
    resp = client.get(f"/notes/{note_id}", headers=headers)
    assert resp.status_code == 404
