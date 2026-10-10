"""Task API application factory."""

import os
from pathlib import Path

from flask import Flask, jsonify, render_template
from werkzeug.exceptions import HTTPException

from . import db
from .routes import tasks


def create_app(config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        DATABASE=os.environ.get("TASK_DATABASE", str(Path(app.instance_path) / "tasks.db")),
        MAX_CONTENT_LENGTH=16 * 1024,
    )
    if config:
        app.config.update(config)
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    with app.app_context():
        db.init_db()
    app.register_blueprint(tasks, url_prefix="/api/tasks")

    @app.get("/")
    def dashboard():
        return render_template("index.html")

    @app.get("/health")
    def health():
        db.get_db().execute("SELECT 1").fetchone()
        return {"status": "ok"}

    @app.errorhandler(HTTPException)
    def http_error(error):
        response = error.get_response()
        response.data = jsonify(error={"code": error.code, "message": error.description}).data
        response.content_type = "application/json"
        return response

    @app.errorhandler(500)
    def server_error(error):
        return {"error": {"code": 500, "message": "Internal server error"}}, 500

    return app
