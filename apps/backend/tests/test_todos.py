import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_list_todo(client: AsyncClient):
    response = await client.post("/api/v1/todos", json={"title": "Buy milk"})
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Buy milk"
    assert body["completed"] is False
    assert "id" in body

    response = await client.get("/api/v1/todos")
    assert response.status_code == 200
    todos = response.json()
    assert len(todos) == 1
    assert todos[0]["title"] == "Buy milk"


@pytest.mark.asyncio
async def test_create_todo_rejects_empty_title(client: AsyncClient):
    response = await client.post("/api/v1/todos", json={"title": ""})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_toggle_todo(client: AsyncClient):
    create_resp = await client.post("/api/v1/todos", json={"title": "Walk the dog"})
    todo_id = create_resp.json()["id"]

    toggle_resp = await client.patch(f"/api/v1/todos/{todo_id}/toggle")
    assert toggle_resp.status_code == 200
    assert toggle_resp.json()["completed"] is True

    toggle_again = await client.patch(f"/api/v1/todos/{todo_id}/toggle")
    assert toggle_again.json()["completed"] is False


@pytest.mark.asyncio
async def test_delete_todo(client: AsyncClient):
    create_resp = await client.post("/api/v1/todos", json={"title": "Temp"})
    todo_id = create_resp.json()["id"]

    delete_resp = await client.delete(f"/api/v1/todos/{todo_id}")
    assert delete_resp.status_code == 204

    list_resp = await client.get("/api/v1/todos")
    assert list_resp.json() == []


@pytest.mark.asyncio
async def test_toggle_nonexistent_todo_returns_404(client: AsyncClient):
    response = await client.patch("/api/v1/todos/00000000-0000-0000-0000-000000000000/toggle")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_ownership_isolation(client: AsyncClient, other_user_override):
    create_resp = await client.post("/api/v1/todos", json={"title": "User1 secret"})
    todo_id = create_resp.json()["id"]

    # Switch the authenticated identity to a different user.
    other_user_override()

    list_resp = await client.get("/api/v1/todos")
    assert list_resp.json() == []

    toggle_resp = await client.patch(f"/api/v1/todos/{todo_id}/toggle")
    assert toggle_resp.status_code == 404

    delete_resp = await client.delete(f"/api/v1/todos/{todo_id}")
    assert delete_resp.status_code == 404
