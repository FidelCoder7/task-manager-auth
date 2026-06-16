"""
FastAPI application factory.

Responsibilities:
- Create the FastAPI app instance
- Register auth and task routers
- Create database tables on startup (users, tasks, token_blacklist)
- Add a root health-check endpoint
"""

from fastapi import FastAPI

from app.database import Base, engine
from app.routers import admin, auth_routes, tasks

# Create all tables defined in models.py (users, tasks, token_blacklist)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Task Manager API (with Auth + RBAC)",
    description=(
        "A REST API for managing personal tasks. "
        "Every task is owned by an authenticated user — "
        "JWT access tokens required for all /tasks endpoints."
        "Admins can access /admin endpoints to view all users and tasks."
    
    ),
    version="1.1.0",
)

# Register routers
app.include_router(auth_routes.router)
app.include_router(tasks.router)
app.include_router(admin.router)


@app.get("/", tags=["Health"])
def root():
    """Health check — confirms the API is running."""
    return {"status": "ok", "message": "Task Manager API (with Auth + RBAC) is running."}