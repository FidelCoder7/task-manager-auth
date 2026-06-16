"""
Admin-only routes.

All endpoints here require role == admin via get_current_admin.

Route pattern:
  GET /admin/tasks  → all tasks, across all users, paginated
  GET /admin/users  → all user accounts
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import crud
from app.auth.dependencies import get_current_admin
from app.database import get_db
from app.models import User
from app.schemas import PaginatedTaskResponse, UserResponse

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/tasks", response_model=PaginatedTaskResponse)
def list_all_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Retrieve all tasks, from all users, paginated. Admin only."""
    total, items = crud.get_all_tasks_paginated(db, page=page, page_size=page_size)
    return PaginatedTaskResponse(total=total, page=page, page_size=page_size, items=items)


@router.get("/users", response_model=list[UserResponse])
def list_all_users(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Retrieve all user accounts. Admin only."""
    return crud.get_all_users(db)