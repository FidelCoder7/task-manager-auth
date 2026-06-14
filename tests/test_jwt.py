"""Unit tests for JWT creation and validation — no HTTP layer involved."""

from datetime import timedelta

from app.auth.jwt_handler import create_access_token, create_refresh_token, decode_token


def test_access_token_creates_and_decodes():
    token = create_access_token({"sub": "1", "email": "user@example.com"})
    payload = decode_token(token)
    assert payload["sub"] == "1"
    assert payload["type"] == "access"


def test_refresh_token_type():
    token = create_refresh_token({"sub": "1", "email": "user@example.com"})
    payload = decode_token(token)
    assert payload["type"] == "refresh"


def test_expired_token_returns_none():
    token = create_access_token({"sub": "1"}, expires_delta=timedelta(seconds=-1))
    assert decode_token(token) is None


def test_invalid_token_returns_none():
    assert decode_token("not.a.valid.token") is None
    assert decode_token("") is None
