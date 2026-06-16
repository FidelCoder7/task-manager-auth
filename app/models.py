"""
SQLAlchemy ORM models — defines the database tables.

Tables:
  users           — authentication + profile data
  tasks           — owned by a user via user_id FK
  token_blacklist — invalidated refresh tokens (logout)

Relationship:
  User.tasks  <--->  Task.owner   (one-to-many, cascade delete)
"""

import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Boolean,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


# ── Enums (from task-api) ──────────────────────────────────────────

class Priority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Status(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    done = "done"

class RoleEnum(str, enum.Enum):
    user = "user"
    admin = "admin"

# ── User (from auth-system) ────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    oauth_provider = Column(String, nullable=True)
    oauth_id = Column(String, nullable=True)
    role = Column(Enum(RoleEnum), default=RoleEnum.user, nullable=False) 
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # One user → many tasks. Deleting a user deletes their tasks.
    tasks = relationship(
        "Task",
        back_populates="owner",
        cascade="all, delete-orphan",
    )


# ── Task (from task-api, now with ownership) ────────────────────────

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(Enum(Status), default=Status.pending, nullable=False)
    priority = Column(Enum(Priority), default=Priority.medium, nullable=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    # NEW — ownership
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    owner = relationship("User", back_populates="tasks")


# ── Token Blacklist (from auth-system) ──────────────────────────────

class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True)
    blacklisted_at = Column(DateTime(timezone=True), server_default=func.now())
