from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_tasks():
    response = client.get("/tasks")
    assert response.status_code == 200
    assert len(response.json()) >= 2


def test_create_task():
    response = client.post("/tasks", json={"title": "  New task  "})

    assert response.status_code == 201
    assert response.json()["title"] == "New task"


def test_get_missing_task():
    response = client.get("/tasks/99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


def test_delete_task():
    # TODO (Copilot Agent demo):
    # This test should pass after the DELETE endpoint is implemented.
    response = client.delete("/tasks/2")

    assert response.status_code == 204


def test_delete_missing_task():
    # TODO (Copilot Agent demo):
    # Verify the endpoint returns 404 for a task that does not exist.
    response = client.delete("/tasks/99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"
