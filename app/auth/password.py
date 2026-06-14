"""
Password hashing utilities.

Uses bcrypt directly (not passlib — see Project 8 notes on the
passlib/bcrypt 4.x incompatibility).

Passwords are SHA-256 hashed first, then base64-encoded, so the
input to bcrypt is always well under its 72-byte limit regardless
of how long the user's original password is.
"""

import base64
import hashlib

import bcrypt


def _prepare(plain_password: str) -> bytes:
    """SHA-256 hash -> base64 -> bytes. Always <72 bytes for bcrypt."""
    digest = hashlib.sha256(plain_password.encode()).digest()
    return base64.b64encode(digest)


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password for storage."""
    hashed = bcrypt.hashpw(_prepare(plain_password), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plain-text password against a stored bcrypt hash."""
    return bcrypt.checkpw(_prepare(plain_password), hashed_password.encode("utf-8"))
