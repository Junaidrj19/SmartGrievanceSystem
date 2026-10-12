"""Landing page and role-aware dashboard dispatch."""

from flask import redirect, render_template, url_for
from flask_login import current_user, login_required

from ..utils import utcnow
from . import main_bp


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return landing()


@main_bp.route("/about")
def landing():
    """Keep the product page available even when a workspace session is active."""
    can_submit = not current_user.is_authenticated or current_user.role == "student"
    return render_template(
        "landing.html",
        landing_page=True,
        raise_url=url_for("student.new_grievance" if can_submit else "main.dashboard"),
        raise_label="Raise a grievance" if can_submit else "Open your workspace",
        track_url=url_for("main.dashboard"),
        current_year=utcnow().year,
    )


@main_bp.route("/dashboard")
@login_required
def dashboard():
    endpoints = {
        "student": "student.dashboard",
        "staff": "staff.dashboard",
        "admin": "admin.dashboard",
    }
    endpoint = endpoints.get(current_user.role)
    if endpoint is None:
        return redirect(url_for("auth.logout"))
    return redirect(url_for(endpoint))
