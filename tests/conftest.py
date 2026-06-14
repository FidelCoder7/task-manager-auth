"""
Shared pytest fixtures.

- Uses a separate SQLite file for tests (test_app.db)
- Overrides get_db to use the test database
- Provides two pre-registered users (alice, bob) with tokens,
  used throughout test_tasks.py for ownership isolation tests
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

TEST_DATABASE_URL = "sqlite:///./test_app.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    """Create all tables before each test, drop after — clean slate every time."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


# ── Single-user fixtures ───────────────────────────────────────────

@pytest.fixture
def registered_user(client):
    """A pre-registered user (alice)."""
    client.post("/auth/register", json={
        "email": "alice@example.com",
        "username": "alice",
        "password": "Pass123!",
    })
    return {"email": "alice@example.com", "password": "Pass123!"}


@pytest.fixture
def auth_tokens(client, registered_user):
    """Access + refresh tokens for alice."""
    response = client.post("/auth/login", json=registered_user)
    return response.json()


@pytest.fixture
def auth_headers(auth_tokens):
    """Authorization header for alice."""
    return {"Authorization": f"Bearer {auth_tokens['access_token']}"}


# ── Two-user fixtures (for ownership tests) ────────────────────────

@pytest.fixture
def second_user_headers(client):
    """Registers bob, logs in, returns his Authorization header."""
    client.post("/auth/register", json={
        "email": "bob@example.com",
        "username": "bob",
        "password": "Pass123!",
    })
    login = client.post("/auth/login", json={
        "email": "bob@example.com",
        "password": "Pass123!",
    })
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def alice_task(client, auth_headers):
    """Creates a task owned by alice, returns the response JSON."""
    response = client.post("/tasks/", json={
        "title": "Alice's Task",
        "priority": "high",
    }, headers=auth_headers)
    return response.json()
