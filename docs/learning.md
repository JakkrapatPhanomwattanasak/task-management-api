# Understanding Task Management API

- Entry point: `task_api.create_app`; follow request → routes → service → db.
- Explain POST 201 + Location, PATCH partial updates, DELETE 204, 404, 415, and 413.
- Why parameterized SQL? User input stays a value instead of becoming SQL syntax.
- Why a connection per request? Avoid sharing a connection across request threads; teardown releases it.
- Why validate before a write? Reject ambiguous inputs and keep the database consistent.
- Explain pagination, filtering, database transactions, and last-write-wins updates.

Practice: run a full create/read/update/delete lifecycle, restart the server to show persistence, submit an invalid status, and read the tests. Add a due date with a migration as a follow-up exercise.

Resume wording after you can reproduce and explain the implementation:
"Developed a Flask task-management API with SQLite persistence, validated CRUD endpoints, pagination, and automated integration tests."

Keep claims specific to this local demo; it does not implement authentication or production deployment.
