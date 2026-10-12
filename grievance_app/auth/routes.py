"""Login and logout routes."""

from __future__ import annotations

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from ..forms import LoginForm, LogoutForm
from ..models import User
from . import auth_bp


def _login_destination(user):
    """Allow only known, role-appropriate landing actions as return paths."""
    target = request.args.get("next", "")
    allowed = {url_for("main.dashboard")}
    if user.role == "student":
        allowed.update({url_for("student.new_grievance"), url_for("student.dashboard")})
    return target if target in allowed else url_for("main.dashboard")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(_login_destination(current_user))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()
        if user is None or not user.check_password(form.password.data):
            flash("The email or password is incorrect.", "danger")
        else:
            login_user(user, remember=form.remember.data)
            flash(f"Welcome back, {user.name}.", "success")
            return redirect(_login_destination(user))
    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout", methods=["POST"])
def logout():
    form = LogoutForm()
    if not form.validate_on_submit():
        flash("Your sign-out request could not be verified.", "danger")
        return redirect(url_for("main.dashboard"))
    logout_user()
    flash("You have been signed out.", "success")
    return redirect(url_for("auth.login"))
