"""
FastAPI dependencies for authentication.

get_current_user is used by every protected route (including all
task endpoints) to:
  1. Extract the Bearer token from the Authorization header
  2. Validate it's a non-expired ACCESS token
  3. Look up the corresponding User in the database
  4. Return that User object — routes use it for ownership checks
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.jwt_handler import decode_token
from app.database import get_db
from app.models import User

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency: extracts and validates JWT from Authorization header.
    Raises 401 if token is missing, invalid, expired, or user not found.
    """
    token = credentials.credentials
    payload = decode_token(token)

    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    return user
