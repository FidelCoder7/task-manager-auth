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
    assert len(data) == 1
    assert data[0]["id"] == alice_task["id"]


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
    assert response.json() == []


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
