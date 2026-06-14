"""
Task routes — defines all HTTP endpoints for /tasks.

All endpoints require a valid JWT access token (via get_current_user).
Every operation is scoped to the authenticated user — tasks belonging
to other users are invisible and return 404, not 403 (see Phase 2
architecture decision: 404 hides existence of other users' data).

Route pattern:
  GET    /tasks          → list current user's tasks (with filters)
  POST   /tasks          → create a new task for current user
  GET    /tasks/summary  → count current user's tasks by status
  GET    /tasks/{id}     → get one task (must belong to current user)
  PUT    /tasks/{id}     → update a task (must belong to current user)
  DELETE /tasks/{id}     → delete a task (must belong to current user)

HTTP status codes used:
  200 OK           — successful GET / PUT
  201 Created      — successful POST
  204 No Content   — successful DELETE (no body returned)
  401 Unauthorized — missing/invalid/expired token
  404 Not Found    — task id doesn't exist OR belongs to another user
  422 Unprocessable — invalid request data (Pydantic handles this automatically)
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud
from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models import Priority, Status, User
from app.schemas import TaskCreate, TaskResponse, TaskUpdate

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
)


def _get_task_or_404(task_id: int, user_id: int, db: Session) -> crud.Task:
    """
    Helper: fetch task (scoped to user_id) or raise 404.

    Because crud.get_task() already filters by user_id, a task that
    exists but belongs to someone else returns None here — identical
    to a task that doesn't exist at all. The client can't distinguish
    the two, which is the intended security behavior.
    """
    task = crud.get_task(db, task_id, user_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found.",
        )
    return task


# ── GET /tasks ────────────────────────────────────────────────────

@router.get("/", response_model=list[TaskResponse])
def list_tasks(
    task_status: Optional[Status] = Query(None, alias="status"),
    priority: Optional[Priority] = Query(None),
    search: Optional[str] = Query(None, min_length=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve the current user's tasks.

    Optional query parameters:
    - **status**: filter by pending | in_progress | done
    - **priority**: filter by low | medium | high
    - **search**: search by title keyword
    - **skip** / **limit**: pagination
    """
    return crud.get_tasks(
        db,
        user_id=current_user.id,
        status=task_status,
        priority=priority,
        search=search,
        skip=skip,
        limit=limit,
    )


# ── GET /tasks/summary ────────────────────────────────────────────

@router.get("/summary")
def task_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the current user's task counts grouped by status."""
    return crud.get_task_count(db, user_id=current_user.id)


# ── POST /tasks ───────────────────────────────────────────────────

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_in: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new task, owned by the current user."""
    return crud.create_task(db, task_in, user_id=current_user.id)


# ── GET /tasks/{id} ───────────────────────────────────────────────

@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve a single task by ID — must belong to current user."""
    return _get_task_or_404(task_id, current_user.id, db)


# ── PUT /tasks/{id} ───────────────────────────────────────────────

@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    updates: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update a task. Only include fields you want to change —
    omitted fields are left unchanged. Must belong to current user.
    """
    task = _get_task_or_404(task_id, current_user.id, db)
    return crud.update_task(db, task, updates)


# ── DELETE /tasks/{id} ────────────────────────────────────────────

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Permanently delete a task. Must belong to current user."""
    task = _get_task_or_404(task_id, current_user.id, db)
    crud.delete_task(db, task)
