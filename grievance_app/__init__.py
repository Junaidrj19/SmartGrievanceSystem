"""Application factory for the Smart Grievance Redressal System."""

from __future__ import annotations

import os

import click
from flask import Flask, render_template

from .config import Config
from .extensions import csrf, db, login_manager
from .models import User


def create_app(test_config: dict | None = None) -> Flask:
    """Create and configure a Flask application instance.

    The factory creates the SQLite schema when the application starts.  Demo
    data is deliberately kept in a separate, explicit seed command so a
    normal startup never overwrites local data.
    """

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"

    from .admin import admin_bp
    from .auth import auth_bp
    from .main import main_bp
    from .staff import staff_bp
    from .student import student_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(admin_bp)

    @login_manager.user_loader
    def load_user(user_id: str) -> User | None:
        try:
            return db.session.get(User, int(user_id))
        except (TypeError, ValueError):
            return None

    @app.context_processor
    def inject_ui_helpers() -> dict:
        from .forms import LogoutForm
        from .utils import ROLE_LABELS, STATUS_LABELS, format_datetime

        return {
            "role_labels": ROLE_LABELS,
            "status_labels": STATUS_LABELS,
            "format_datetime": format_datetime,
            "logout_form": LogoutForm(),
        }

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(400)
    def bad_request(_error):
        return render_template("errors/400.html"), 400

    @app.errorhandler(500)
    def internal_error(_error):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    register_cli_commands(app)

    with app.app_context():
        # Importing models above registers every table with SQLAlchemy.
        db.create_all()

    return app


def register_cli_commands(app: Flask) -> None:
    """Register database and workflow commands on the Flask CLI."""

    @app.cli.command("init-db")
    def init_db_command() -> None:
        """Create all application tables without changing existing data."""

        db.create_all()
        click.echo("Database tables are ready.")

    @app.cli.command("check-escalations")
    def check_escalations_command() -> None:
        """Run the idempotent overdue grievance checker once."""

        from .services.escalation_service import run_escalation_check

        summary = run_escalation_check()
        click.echo(
            "Escalation check complete: "
            f"examined={summary['examined']} "
            f"escalated={summary['escalated']} "
            f"skipped={summary['skipped']} "
            f"failed={summary['failed']}"
        )
