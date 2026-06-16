"""
Tests for /tasks endpoints — authentication enforcement, CRUD behavior,
and ownership isolation between users.
"""


# ── Authentication enforcement ──────────────────────────────────────

def test_list_tasks_requires_auth(client):
    response = client.get("/tasks/")
    assert response.status_code == 401


def test_create_task_requires_auth(client):
    response = client.post("/tasks/", json={"title": "No auth"})
    assert response.status_code == 401


def test_invalid_token_rejected(client):
    response = client.get("/tasks/", headers={"Authorization": "Bearer not.a.real.token"})
    assert response.status_code == 401


# ── Basic CRUD (single user) ────────────────────────────────────────

def test_create_task(client, auth_headers):
    response = client.post("/tasks/", json={
        "title": "Write tests",
        "description": "Cover ownership logic",
        "priority": "high",
    }, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Write tests"
    assert data["status"] == "pending"
    assert "user_id" in data


def test_list_tasks_returns_only_own(client, auth_headers, alice_task):
    response = client.get("/tasks/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == alice_task["id"]


def test_get_task_by_id(client, auth_headers, alice_task):
    response = client.get(f"/tasks/{alice_task['id']}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == alice_task["id"]


def test_update_task(client, auth_headers, alice_task):
    response = client.put(f"/tasks/{alice_task['id']}", json={
        "status": "done",
    }, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "done"


def test_delete_task(client, auth_headers, alice_task):
    response = client.delete(f"/tasks/{alice_task['id']}", headers=auth_headers)
    assert response.status_code == 204

    # Confirm it's gone
    response = client.get(f"/tasks/{alice_task['id']}", headers=auth_headers)
    assert response.status_code == 404


def test_get_nonexistent_task(client, auth_headers):
    response = client.get("/tasks/9999", headers=auth_headers)
    assert response.status_code == 404


def test_task_summary(client, auth_headers, alice_task):
    response = client.get("/tasks/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["pending"] == 1


# ── Ownership isolation (two users) ─────────────────────────────────

def test_user_cannot_see_others_task_in_list(client, second_user_headers, alice_task):
    """Bob's task list must not include Alice's task."""
    response = client.get("/tasks/", headers=second_user_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_user_cannot_get_others_task_by_id(client, second_user_headers, alice_task):
    """Bob fetching Alice's task by id returns 404 — not 403."""
    response = client.get(f"/tasks/{alice_task['id']}", headers=second_user_headers)
    assert response.status_code == 404


def test_user_cannot_update_others_task(client, second_user_headers, alice_task):
    """Bob cannot modify Alice's task."""
    response = client.put(f"/tasks/{alice_task['id']}", json={
        "status": "done",
    }, headers=second_user_headers)
    assert response.status_code == 404


def test_user_cannot_delete_others_task(client, second_user_headers, alice_task):
    """Bob cannot delete Alice's task — and it must still exist for Alice."""
    response = client.delete(f"/tasks/{alice_task['id']}", headers=second_user_headers)
    assert response.status_code == 404


def test_others_task_unaffected_after_failed_delete(client, auth_headers, second_user_headers, alice_task):
    """After Bob's failed delete attempt, Alice can still access her task."""
    client.delete(f"/tasks/{alice_task['id']}", headers=second_user_headers)

    response = client.get(f"/tasks/{alice_task['id']}", headers=auth_headers)
    assert response.status_code == 200


def test_task_summary_isolated_per_user(client, auth_headers, second_user_headers, alice_task):
    """Bob's summary shows zero tasks even though Alice has one."""
    response = client.get("/tasks/summary", headers=second_user_headers)
    data = response.json()
    assert data["total"] == 0


def test_pagination_metadata_accuracy(client, auth_headers):
    """Creates 3 tasks, requests page_size=2, verifies pagination math."""
    for i in range(3):
        client.post("/tasks/", json={"title": f"Task {i}"}, headers=auth_headers)

    response = client.get("/tasks/?page=1&page_size=2", headers=auth_headers)
    data = response.json()
    assert data["total"] == 3
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert len(data["items"]) == 2

    response_page2 = client.get("/tasks/?page=2&page_size=2", headers=auth_headers)
    data2 = response_page2.json()
    assert len(data2["items"]) == 1  # remaining 1 task
    


# ── RBAC: Admin access ──────────────────────────────────────────────

def test_regular_user_cannot_access_admin_tasks(client, auth_headers):
    """A regular user hitting /admin/tasks gets 403, not 404."""
    response = client.get("/admin/tasks", headers=auth_headers)
    assert response.status_code == 403


def test_regular_user_cannot_access_admin_users(client, auth_headers):
    """A regular user hitting /admin/users gets 403."""
    response = client.get("/admin/users", headers=auth_headers)
    assert response.status_code == 403


def test_admin_can_access_admin_tasks(client, admin_headers):
    """An admin can successfully hit /admin/tasks."""
    response = client.get("/admin/tasks", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data


def test_admin_can_access_admin_users(client, admin_headers):
    """An admin can successfully hit /admin/users."""
    response = client.get("/admin/users", headers=admin_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_admin_sees_all_users_tasks(client, auth_headers, admin_headers, alice_task):
    """Admin's /admin/tasks includes Alice's task, even though
    the admin didn't create it."""
    response = client.get("/admin/tasks", headers=admin_headers)
    data = response.json()
    task_ids = [t["id"] for t in data["items"]]
    assert alice_task["id"] in task_ids


def test_admin_user_list_includes_regular_users(client, auth_headers, admin_headers):
    """Admin's /admin/users includes Alice, not just the admin account."""
    response = client.get("/admin/users", headers=admin_headers)
    emails = [u["email"] for u in response.json()]
    assert "alice@example.com" in emails
    assert "admin@example.com" in emails


def test_admin_routes_require_auth(client):
    """No token at all on /admin/tasks → 401, not 403."""
    response = client.get("/admin/tasks")
    assert response.status_code == 401


def test_invalid_token_on_admin_route_returns_401(client):
    """Invalid token → 401 (auth failure), checked before role (403)."""
    response = client.get(
        "/admin/tasks",
        headers={"Authorization": "Bearer not.a.real.token"},
    )
    assert response.status_code == 401
    