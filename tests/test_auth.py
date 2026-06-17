"""Tests for /auth endpoints: register, login, refresh, logout."""


def test_register_success(client):
    response = client.post("/auth/register", json={
        "email": "new@example.com",
        "username": "newuser",
        "password": "Pass123!",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new@example.com"
    assert "hashed_password" not in data


def test_register_duplicate_email(client, registered_user):
    response = client.post("/auth/register", json={
        "email": "alice@example.com",  # already registered
        "username": "different",
        "password": "Pass123!",
    })
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]


def test_register_duplicate_username(client, registered_user):
    response = client.post("/auth/register", json={
        "email": "different@example.com",
        "username": "alice",  # already taken
        "password": "Pass123!",
    })
    assert response.status_code == 400


def test_login_success(client, registered_user):
    response = client.post("/auth/login", json=registered_user)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, registered_user):
    response = client.post("/auth/login", json={
        "email": "alice@example.com",
        "password": "WrongPassword!",
    })
    assert response.status_code == 401


def test_login_nonexistent_user(client):
    response = client.post("/auth/login", json={
        "email": "ghost@example.com",
        "password": "anything",
    })
    assert response.status_code == 401


def test_refresh_token(client, auth_tokens):
    response = client.post("/auth/refresh", json={
        "refresh_token": auth_tokens["refresh_token"],
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_logout_then_refresh_fails(client, auth_tokens):
    client.post("/auth/logout", json={"refresh_token": auth_tokens["refresh_token"]})

    response = client.post("/auth/refresh", json={
        "refresh_token": auth_tokens["refresh_token"],
    })
    assert response.status_code == 401


def test_get_me_returns_user_profile(client, auth_headers):
    response = client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "alice@example.com"
    assert data["role"] == "user"


def test_get_me_requires_auth(client):
    response = client.get("/auth/me")
    assert response.status_code == 401