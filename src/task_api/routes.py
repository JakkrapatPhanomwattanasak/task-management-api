from flask import Blueprint, request, url_for
from werkzeug.exceptions import BadRequest

from . import service

tasks = Blueprint("tasks", __name__)


@tasks.get("")
def list_tasks():
    try:
        page = int(request.args.get("page", "1"))
        per_page = int(request.args.get("per_page", "20"))
    except ValueError:
        raise BadRequest("page and per_page must be integers") from None
    if not 1 <= page <= 1_000_000 or not 1 <= per_page <= 100:
        raise BadRequest("page must be 1..1000000 and per_page must be 1..100")
    status = request.args.get("status")
    if status is not None and status not in service.STATUSES:
        raise BadRequest("Invalid status filter")
    return service.list_tasks(page, per_page, status)


@tasks.post("")
def create_task():
    task = service.create_task(request.get_json())
    return task, 201, {"Location": url_for("tasks.get_task", task_id=task["id"])}


@tasks.get("/<int:task_id>")
def get_task(task_id):
    return service.get_task(task_id)


@tasks.patch("/<int:task_id>")
def update_task(task_id):
    return service.update_task(task_id, request.get_json())


@tasks.delete("/<int:task_id>")
def delete_task(task_id):
    service.delete_task(task_id)
    return "", 204
