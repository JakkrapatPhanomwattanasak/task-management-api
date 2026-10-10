"""Validation and parameterized persistence, separate from HTTP routing."""

from werkzeug.exceptions import BadRequest, NotFound

from .db import get_db

STATUSES = {"todo", "in_progress", "done"}


def validate(payload, partial=False):
    if not isinstance(payload, dict) or not payload:
        raise BadRequest("A non-empty JSON object is required")
    if payload.keys() - {"title", "description", "status"}:
        raise BadRequest("Unknown task fields")
    if not partial and "title" not in payload:
        raise BadRequest("title is required")
    result = {}
    for key, value in payload.items():
        if not isinstance(value, str):
            raise BadRequest(f"{key} must be a string")
        value = value.strip()
        if key == "title" and not 1 <= len(value) <= 120:
            raise BadRequest("title must contain 1 to 120 characters")
        if key == "description" and len(value) > 2000:
            raise BadRequest("description must contain at most 2000 characters")
        if key == "status" and value not in STATUSES:
            raise BadRequest("status must be todo, in_progress, or done")
        result[key] = value
    return result


def get_task(task_id):
    row = get_db().execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        raise NotFound("Task not found")
    return dict(row)


def create_task(payload):
    values = validate(payload)
    connection = get_db()
    with connection:
        cursor = connection.execute(
            "INSERT INTO tasks (title, description, status) VALUES (?, ?, ?)",
            (values["title"], values.get("description", ""), values.get("status", "todo")),
        )
    return get_task(cursor.lastrowid)


def update_task(task_id, payload):
    values = validate(payload, partial=True)
    # Identifiers come only from the allowlist in validate; values stay parameterized.
    assignments = ", ".join(f"{key} = ?" for key in values)
    connection = get_db()
    with connection:
        cursor = connection.execute(
            f"UPDATE tasks SET {assignments}, "
            "updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE id = ?",
            (*values.values(), task_id),
        )
        if cursor.rowcount == 0:
            raise NotFound("Task not found")
    return get_task(task_id)


def delete_task(task_id):
    connection = get_db()
    with connection:
        cursor = connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        if cursor.rowcount == 0:
            raise NotFound("Task not found")


def list_tasks(page, per_page, status=None):
    connection = get_db()
    where = " WHERE status = ?" if status else ""
    params = (status,) if status else ()
    total = connection.execute(f"SELECT count(*) FROM tasks{where}", params).fetchone()[0]
    rows = connection.execute(
        f"SELECT * FROM tasks{where} ORDER BY id DESC LIMIT ? OFFSET ?",
        (*params, per_page, (page - 1) * per_page),
    ).fetchall()
    return {
        "items": [dict(row) for row in rows],
        "page": page,
        "per_page": per_page,
        "total": total,
    }
