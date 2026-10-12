"""Student submission and own-case routes."""

from __future__ import annotations

from flask import abort, flash, redirect, render_template, url_for
from flask_login import current_user

from ..auth.decorators import roles_required
from ..forms import GrievanceForm
from ..models import Grievance
from ..services.exceptions import DomainError
from ..services.grievance_service import create_grievance
from . import student_bp


@student_bp.route("/dashboard")
@roles_required("student")
def dashboard():
    grievances = (
        Grievance.query.filter_by(student_id=current_user.id)
        .order_by(Grievance.updated_at.desc(), Grievance.id.desc())
        .all()
    )
    return render_template("student/dashboard.html", grievances=grievances)


@student_bp.route("/grievances/new", methods=["GET", "POST"])
@roles_required("student")
def new_grievance():
    form = GrievanceForm()
    if form.validate_on_submit():
        try:
            grievance = create_grievance(
                student=current_user,
                title=form.title.data,
                category=form.category.data,
                description=form.description.data,
                location=form.location.data,
            )
        except DomainError as exc:
            flash(str(exc), "danger")
        else:
            flash(
                f"Grievance submitted successfully. Reference: {grievance.reference_id}",
                "success",
            )
            return redirect(
                url_for("student.grievance_detail", grievance_id=grievance.id)
            )
    return render_template("student/new_grievance.html", form=form)


@student_bp.route("/grievances/<int:grievance_id>")
@roles_required("student")
def grievance_detail(grievance_id: int):
    grievance = Grievance.query.filter_by(
        id=grievance_id, student_id=current_user.id
    ).first()
    if grievance is None:
        abort(404)
    return render_template("grievances/detail.html", grievance=grievance)
