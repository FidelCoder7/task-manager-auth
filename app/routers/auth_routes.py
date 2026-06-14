"""
Authentication routes.

Endpoints:
  POST /auth/register  — create a new user account
  POST /auth/login      — authenticate, receive access + refresh tokens
  POST /auth/refresh    — exchange a valid refresh token for a new pair
  POST /auth/logout     — blacklist a refresh token
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.jwt_handler import create_access_token, create_refresh_token, decode_token
from app.auth.password import hash_password, verify_password
from app.database import get_db
from app.models import TokenBlacklist, User
from app.schemas import (
    MessageResponse,
    TokenRefreshRequest,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ── REGISTER ─────────────────────────────────────────────────

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Create a new user account."""
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hash_password(user_data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ── LOGIN ─────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate and receive access + refresh tokens."""
    user = db.query(User).filter(User.email == credentials.email).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is disabled")

    token_data = {"sub": str(user.id), "email": user.email}

    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


# ── REFRESH TOKEN ─────────────────────────────────────────────

@router.post("/refresh", response_model=TokenResponse)
def refresh_token(body: TokenRefreshRequest, db: Session = Depends(get_db)):
    """Exchange a valid, non-blacklisted refresh token for a new token pair."""
    payload = decode_token(body.refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    blacklisted = db.query(TokenBlacklist).filter(
        TokenBlacklist.token == body.refresh_token
    ).first()
    if blacklisted:
        raise HTTPException(status_code=401, detail="Token has been revoked")

    token_data = {"sub": payload["sub"], "email": payload["email"]}

    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


# ── LOGOUT ────────────────────────────────────────────────────

@router.post("/logout", response_model=MessageResponse)
def logout(body: TokenRefreshRequest, db: Session = Depends(get_db)):
    """Blacklist the refresh token so it can't be used again."""
    blacklist_entry = TokenBlacklist(token=body.refresh_token)
    db.add(blacklist_entry)
    db.commit()
    return MessageResponse(message="Successfully logged out")
