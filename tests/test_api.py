import pytest

from task_api import create_app


@pytest.fixture
def client(tmp_path):
    return create_app({"TESTING": True, "DATABASE": str(tmp_path / "tasks.db")}).test_client()


def test_crud_lifecycle_and_persistence(client):
    response = client.post("/api/tasks", json={"title": "  Prepare demo  "})
    assert response.status_code == 201
    url = response.headers["Location"]
    assert client.get(url).json["title"] == "Prepare demo"
    assert client.patch(url, json={"status": "done"}).json["status"] == "done"
    # A fresh app opens the same persisted database.
    other = create_app({"TESTING": True, "DATABASE": client.application.config["DATABASE"]})
    assert other.test_client().get(url).json["status"] == "done"
    assert client.delete(url).status_code == 204
    assert client.get(url).status_code == 404


@pytest.mark.parametrize(
    "body",
    [
        [],
        {},
        {"title": " "},
        {"title": 7},
        {"title": "x" * 121},
        {"title": "x", "status": "bad"},
        {"title": "x", "admin": True},
        {"description": "x"},
        {"title": "x", "description": "x" * 2001},
    ],
)
def test_invalid_create(client, body):
    assert client.post("/api/tasks", json=body).status_code == 400
    assert client.get("/api/tasks").json["total"] == 0


def test_pagination_filter_and_sql_literal(client):
    title = "Robert'); DROP TABLE tasks;--"
    client.post("/api/tasks", json={"title": title})
    for i in range(4):
        client.post("/api/tasks", json={"title": f"Task {i}", "status": "done"})
    page = client.get("/api/tasks?status=done&per_page=2&page=2").json
    assert page["total"] == 4 and len(page["items"]) == 2
    assert client.get("/api/tasks?status=todo").json["items"][0]["title"] == title


@pytest.mark.parametrize("query", ["page=0", "page=x", "per_page=101", "status=bad"])
def test_bad_query(client, query):
    assert client.get(f"/api/tasks?{query}").status_code == 400


def test_error_contract(client):
    for method in ("get", "patch", "delete"):
        kwargs = {"json": {"title": "x"}} if method == "patch" else {}
        response = getattr(client, method)("/api/tasks/999", **kwargs)
        assert response.status_code == 404 and response.json["error"]["code"] == 404
    assert (
        client.post("/api/tasks", data="not json", content_type="application/json").status_code
        == 400
    )
    assert client.post("/api/tasks", data="x").status_code == 415
    assert (
        client.post("/api/tasks", data="x" * 17000, content_type="application/json").status_code
        == 413
    )
    assert client.put("/health").status_code == 405
    assert client.get("/health").json == {"status": "ok"}
