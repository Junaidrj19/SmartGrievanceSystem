"""Administrative dashboards, assignment, filtering, and escalation actions."""

from __future__ import annotations

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from ..auth.decorators import roles_required
from ..extensions import db
from ..forms import AssignmentForm, EscalationCheckForm, StatusUpdateForm
from ..models import Department, Escalation, Grievance, User
from ..services.escalation_service import run_escalation_check
from ..services.exceptions import DomainError
from ..services.grievance_service import (
    allowed_next_statuses,
    assign_grievance,
    update_status,
)
from ..services.reporting_service import (
    dashboard_counts,
    department_choices,
    department_counts,
    filter_grievances,
    staff_for_department,
    status_counts,
    visible_grievances,
)
from ..utils import STATUS_LABELS
from . import admin_bp


def _admin_grievance(grievance_id: int) -> Grievance:
    grievance = db.session.get(Grievance, grievance_id)
    if grievance is None:
        abort(404)
    return grievance


def _assignment_form(grievance: Grievance) -> AssignmentForm:
    form = AssignmentForm()
    departments = department_choices()
    form.department_id.choices = [(department.id, department.name) for department in departments]
    selected_department_id = grievance.department_id
    if selected_department_id:
        form.assigned_staff_id.choices = [
            ("", "Unassigned")
        ] + [
            (staff.id, staff.name)
            for staff in staff_for_department(selected_department_id)
        ]
    else:
        form.assigned_staff_id.choices = [("", "Unassigned")]
    return form


def _status_form(grievance: Grievance) -> StatusUpdateForm:
    form = StatusUpdateForm()
    form.status.choices = [
        (status, STATUS_LABELS.get(status, status))
        for status in allowed_next_statuses(grievance.status)
    ]
    return form


@admin_bp.route("/dashboard")
@roles_required("admin")
def dashboard():
    status = request.args.get("status", "").upper() or None
    if status not in STATUS_LABELS:
        status = None
    category = request.args.get("category", "").strip() or None
    search = request.args.get("q", "").strip() or None
    department_id = request.args.get("department", type=int)
    overdue_value = request.args.get("overdue")
    overdue = True if overdue_value == "1" else False if overdue_value == "0" else None
    grievances = filter_grievances(
        visible_grievances(current_user),
        status=status,
        category=category,
        department_id=department_id,
        overdue=overdue,
        search=search,
    ).all()
    escalation_form = EscalationCheckForm()
    return render_template(
        "admin/dashboard.html",
        grievances=grievances,
        counts=dashboard_counts(),
        status_counts=status_counts(),
        department_counts=department_counts(),
        departments=department_choices(),
        categories=[row[0] for row in db.session.query(Grievance.category).distinct().order_by(Grievance.category)],
        escalation_form=escalation_form,
        selected_status=status or "",
        selected_category=category or "",
        selected_department=department_id or "",
        selected_overdue=overdue_value or "",
        selected_search=search or "",
    )


@admin_bp.route("/grievances/<int:grievance_id>")
@roles_required("admin")
def grievance_detail(grievance_id: int):
    grievance = _admin_grievance(grievance_id)
    assignment_form = _assignment_form(grievance)
    assignment_form.department_id.data = grievance.department_id
    assignment_form.assigned_staff_id.data = grievance.assigned_staff_id
    return render_template(
        "grievances/detail.html",
        grievance=grievance,
        assignment_form=assignment_form,
        status_form=_status_form(grievance),
        admin_view=True,
    )


@admin_bp.route("/grievances/<int:grievance_id>/assign", methods=["POST"])
@roles_required("admin")
def assign(grievance_id: int):
    grievance = _admin_grievance(grievance_id)
    form = AssignmentForm()
    departments = department_choices()
    form.department_id.choices = [(department.id, department.name) for department in departments]
    posted_department_id = request.form.get("department_id", type=int)
    selected_department_id = posted_department_id or grievance.department_id
    form.assigned_staff_id.choices = [
        ("", "Unassigned")
    ] + [
        (staff.id, staff.name) for staff in staff_for_department(selected_department_id)
    ]
    if form.validate_on_submit():
        department = db.session.get(Department, form.department_id.data)
        assigned_staff = (
            db.session.get(User, form.assigned_staff_id.data)
            if form.assigned_staff_id.data
            else None
        )
        if department is None:
            flash("Select a valid department.", "danger")
        else:
            try:
                assign_grievance(
                    grievance=grievance,
                    actor=current_user,
                    department=department,
                    assigned_staff=assigned_staff,
                    remarks=form.remarks.data,
                )
            except DomainError as exc:
                flash(str(exc), "danger")
            else:
                flash("Assignment saved.", "success")
                return redirect(url_for("admin.grievance_detail", grievance_id=grievance.id))
    else:
        flash("Choose a valid department and optional staff member.", "danger")
    return redirect(url_for("admin.grievance_detail", grievance_id=grievance.id))


@admin_bp.route("/grievances/<int:grievance_id>/status", methods=["POST"])
@roles_required("admin")
def update_grievance_status(grievance_id: int):
    grievance = _admin_grievance(grievance_id)
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
            return redirect(url_for("admin.grievance_detail", grievance_id=grievance.id))
    else:
        flash("Choose a permitted status and check the remarks.", "danger")
    return redirect(url_for("admin.grievance_detail", grievance_id=grievance.id))


@admin_bp.route("/escalations")
@roles_required("admin")
def escalations():
    events = Escalation.query.order_by(Escalation.created_at.desc()).all()
    return render_template("admin/escalations.html", events=events)


@admin_bp.route("/escalations/check", methods=["POST"])
@roles_required("admin")
def check_escalations():
    form = EscalationCheckForm()
    if not form.validate_on_submit():
        flash("The escalation check could not be verified.", "danger")
    else:
        summary = run_escalation_check(actor=current_user)
        flash(
            "Escalation check complete: "
            f"{summary['examined']} examined, "
            f"{summary['escalated']} escalated, "
            f"{summary['skipped']} skipped, "
            f"{summary['failed']} failed.",
            "success" if summary["failed"] == 0 else "warning",
        )
    return redirect(url_for("admin.dashboard"))
