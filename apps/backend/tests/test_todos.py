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
    body = response.json()
    assert body["total"] == 1
    assert body["limit"] == 20
    assert body["offset"] == 0
    assert len(body["items"]) == 1
    assert body["items"][0]["title"] == "Buy milk"


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
    assert list_resp.json()["items"] == []


@pytest.mark.asyncio
async def test_toggle_nonexistent_todo_returns_404(client: AsyncClient):
    response = await client.patch("/api/v1/todos/00000000-0000-0000-0000-000000000000/toggle")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_todos_cache_is_invalidated_by_writes(client: AsyncClient):
    """The list endpoint caches its result in Redis; every write must bust it,
    or a client would keep seeing a stale list until the TTL expires."""
    await client.post("/api/v1/todos", json={"title": "First"})
    first_list = await client.get("/api/v1/todos")  # populates the cache
    assert len(first_list.json()["items"]) == 1

    await client.post("/api/v1/todos", json={"title": "Second"})
    second_list = await client.get("/api/v1/todos")
    titles = {todo["title"] for todo in second_list.json()["items"]}
    assert titles == {"First", "Second"}


@pytest.mark.asyncio
async def test_list_todos_pagination(client: AsyncClient):
    for i in range(5):
        await client.post("/api/v1/todos", json={"title": f"Todo {i}"})

    page1 = await client.get("/api/v1/todos", params={"limit": 2, "offset": 0})
    assert page1.status_code == 200
    body1 = page1.json()
    assert body1["total"] == 5
    assert body1["limit"] == 2
    assert body1["offset"] == 0
    assert len(body1["items"]) == 2

    page2 = await client.get("/api/v1/todos", params={"limit": 2, "offset": 2})
    body2 = page2.json()
    assert len(body2["items"]) == 2
    assert {t["id"] for t in body1["items"]}.isdisjoint({t["id"] for t in body2["items"]})


@pytest.mark.asyncio
async def test_list_todos_rejects_out_of_range_limit(client: AsyncClient):
    response = await client.get("/api/v1/todos", params={"limit": 1000})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_ownership_isolation(client: AsyncClient, other_user_override):
    create_resp = await client.post("/api/v1/todos", json={"title": "User1 secret"})
    todo_id = create_resp.json()["id"]

    # Switch the authenticated identity to a different user.
    other_user_override()

    list_resp = await client.get("/api/v1/todos")
    assert list_resp.json()["items"] == []

    toggle_resp = await client.patch(f"/api/v1/todos/{todo_id}/toggle")
    assert toggle_resp.status_code == 404

    delete_resp = await client.delete(f"/api/v1/todos/{todo_id}")
    assert delete_resp.status_code == 404
