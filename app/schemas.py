"""
Pydantic schemas — define what the API accepts and returns.

Organized in two groups:
  Auth schemas  — registration, login, tokens
  Task schemas  — create/update/response 
                   
                   
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models import Priority, Status


# ── Auth Schemas ─────────────────────────────────────────────────

class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str
    is_active: bool
    is_verified: bool
    oauth_provider: Optional[str]
    role: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    message: str


# ── Task Schemas ─────────────────────────────────────────────────

class TaskCreate(BaseModel):
    """Payload required to create a new task. user_id is NOT included —
    it's derived from the authenticated user (current_user.id)."""
    title: str = Field(..., min_length=1, max_length=200,
                        description="Short task description")
    description: Optional[str] = Field(None, description="Optional longer notes")
    status: Status = Field(Status.pending, description="Task status")
    priority: Priority = Field(Priority.medium, description="Task priority")


class TaskUpdate(BaseModel):
    """Payload for updating an existing task. All fields optional —
    client only sends what they want to change."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[Status] = None
    priority: Optional[Priority] = None


class TaskResponse(BaseModel):
    """What the API returns — includes ownership (user_id) so the
    client can confirm whose task this is."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str]
    status: Status
    priority: Priority
    created_at: datetime
    updated_at: datetime
    user_id: int


class PaginatedTaskResponse(BaseModel):
    """Paginated wrapper for task list responses."""
    total: int
    page: int
    page_size: int
    items: list[TaskResponse]
    