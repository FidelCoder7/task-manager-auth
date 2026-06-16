"""
CRUD operations for tasks — all database logic lives here.

Every function requires a user_id and filters/scopes by it.
This is the core of ownership enforcement: a user can only
ever read, update, or delete rows where Task.user_id == their own id.

CRUD = Create, Read, Update, Delete
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.models import Priority, Status, Task, User
from app.schemas import TaskCreate, TaskUpdate


def create_task(db: Session, task_in: TaskCreate, user_id: int) -> Task:
    """
    Insert a new task into the database, owned by user_id.

    Args:
        db: Database session.
        task_in: Validated TaskCreate schema from the request.
        user_id: ID of the authenticated user (from get_current_user).

    Returns:
        The newly created Task ORM object.
    """
    task = Task(**task_in.model_dump(), user_id=user_id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_task(db: Session, task_id: int, user_id: int) -> Optional[Task]:
    """
    Fetch a single task by id, but ONLY if it belongs to user_id.

    Returns:
        Task object, or None if it doesn't exist OR belongs to
        another user. The caller (router) turns None into a 404,
        which means "task not found" and "not yours" look identical
        to the client — no information leakage.
    """
    return (
        db.query(Task)
        .filter(Task.id == task_id, Task.user_id == user_id)
        .first()
    )

def get_tasks_paginated(
    db: Session,
    user_id: int,
    page: int = 1,
    page_size: int = 20,
    status: Optional[Status] = None,
    priority: Optional[Priority] = None,
    search: Optional[str] = None,
) -> tuple[int, list[Task]]:
    """
    Fetch a page of tasks belonging to user_id, with optional filtering.

    Returns:
        (total, items) — total is the full count matching filters
        (before pagination), items is just this page's rows.
    """
    query = db.query(Task).filter(Task.user_id == user_id)

    if status:
        query = query.filter(Task.status == status)

    if priority:
        query = query.filter(Task.priority == priority)

    if search:
        query = query.filter(Task.title.ilike(f"%{search}%"))

    total = query.count()

    items = (
        query.order_by(Task.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return total, items

def update_task(db: Session, task: Task, updates: TaskUpdate) -> Task:
    """
    Apply partial updates to an existing task.

    The router is responsible for fetching `task` via get_task()
    (which already enforces ownership) before calling this.
    """
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task: Task) -> None:
    """
    Permanently delete a task.

    The router is responsible for fetching `task` via get_task()
    (which already enforces ownership) before calling this.
    """
    db.delete(task)
    db.commit()


def get_task_count(db: Session, user_id: int) -> dict:
    """
    Return task counts grouped by status, scoped to user_id.
    """
    base = db.query(Task).filter(Task.user_id == user_id)

    return {
        "total": base.count(),
        "pending": base.filter(Task.status == Status.pending).count(),
        "in_progress": base.filter(Task.status == Status.in_progress).count(),
        "done": base.filter(Task.status == Status.done).count(),
    }


def get_all_tasks_paginated(
    db: Session,
    page: int = 1,
    page_size: int = 20,
) -> tuple[int, list[Task]]:
    """
    Admin only — fetch a page of ALL tasks across ALL users.
    No user_id filter, unlike get_tasks_paginated.
    """
    query = db.query(Task)
    total = query.count()

    items = (
        query.order_by(Task.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return total, items


def get_all_users(db: Session) -> list[User]:
    """Admin only — fetch every user account."""
    return db.query(User).all()