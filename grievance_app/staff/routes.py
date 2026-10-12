"""Staff dashboard and authorized status update routes."""

from __future__ import annotations

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from ..auth.decorators import roles_required
from ..forms import StatusUpdateForm
from ..models import Grievance
from ..services.exceptions import DomainError
from ..services.grievance_service import allowed_next_statuses, update_status
from ..services.reporting_service import filter_grievances, status_counts, visible_grievances
from ..utils import STATUS_LABELS
from . import staff_bp


def _staff_grievance(grievance_id: int) -> Grievance:
    grievance = visible_grievances(current_user).filter_by(id=grievance_id).first()
    if grievance is None:
        abort(404)
    return grievance


def _status_form(grievance: Grievance) -> StatusUpdateForm:
    form = StatusUpdateForm()
    form.status.choices = [
        (status, STATUS_LABELS.get(status, status))
        for status in allowed_next_statuses(grievance.status)
    ]
    return form


@staff_bp.route("/dashboard")
@roles_required("staff")
def dashboard():
    status = request.args.get("status", "").upper() or None
    if status not in STATUS_LABELS:
        status = None
    overdue_value = request.args.get("overdue")
    overdue = True if overdue_value == "1" else False if overdue_value == "0" else None
    grievances = filter_grievances(
        visible_grievances(current_user),
        status=status,
        overdue=overdue,
    ).all()
    return render_template(
        "staff/dashboard.html",
        grievances=grievances,
        case_counts=status_counts(visible_grievances(current_user)),
        selected_status=status or "",
        selected_overdue=overdue_value or "",
    )


@staff_bp.route("/grievances/<int:grievance_id>")
@roles_required("staff")
def grievance_detail(grievance_id: int):
    grievance = _staff_grievance(grievance_id)
    return render_template(
        "grievances/detail.html",
        grievance=grievance,
        status_form=_status_form(grievance),
        staff_view=True,
    )


@staff_bp.route("/grievances/<int:grievance_id>/status", methods=["POST"])
@roles_required("staff")
def update_grievance_status(grievance_id: int):
    grievance = _staff_grievance(grievance_id)
    form = _status_form(grievance)
    if form.validate_on_submit():
        try:
            update_status(
                grievance=grievance,
                actor=current_user,
                new_status=form.status.data,
                remarks=form.remarks.data,
            )
        except DomainError as exc:
            flash(str(exc), "danger")
        else:
            flash("Grievance status and history were updated.", "success")
            return redirect(url_for("staff.grievance_detail", grievance_id=grievance.id))
    else:
        flash("Choose a permitted status and check the remarks.", "danger")
    return redirect(url_for("staff.grievance_detail", grievance_id=grievance.id))
