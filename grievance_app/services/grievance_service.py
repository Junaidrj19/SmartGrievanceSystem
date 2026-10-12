"""Grievance creation, assignment, access, and status workflow services."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta

from flask import current_app
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from ..extensions import db
from ..models import Department, Grievance, GrievanceHistory, User
from ..utils import is_open_status, utcnow
from .exceptions import AuthorizationError, InvalidTransitionError, ValidationError

ALL_STATUSES = (
    "SUBMITTED",
    "ASSIGNED",
    "IN_PROGRESS",
    "ESCALATED",
    "RESOLVED",
    "CLOSED",
)

ALLOWED_TRANSITIONS = {
    "SUBMITTED": {"ASSIGNED", "ESCALATED"},
    "ASSIGNED": {"IN_PROGRESS", "ESCALATED"},
    "IN_PROGRESS": {"ESCALATED", "RESOLVED"},
    "ESCALATED": {"RESOLVED"},
    "RESOLVED": {"CLOSED"},
    "CLOSED": set(),
}


def allowed_next_statuses(status: str) -> list[str]:
    return sorted(ALLOWED_TRANSITIONS.get(status, set()))


def _clean(value: str | None) -> str:
    return (value or "").strip()


def _validate_length(value: str, field: str, minimum: int, maximum: int) -> str:
    value = _clean(value)
    if len(value) < minimum or len(value) > maximum:
        raise ValidationError(
            f"{field} must be between {minimum} and {maximum} characters."
        )
    return value


def _new_reference_id() -> str:
    year = utcnow().year
    for _ in range(10):
        candidate = f"GRV-{year}-{secrets.token_hex(4).upper()}"
        if not Grievance.query.filter_by(reference_id=candidate).first():
            return candidate
    raise ValidationError("A unique grievance reference could not be generated.")


def create_grievance(
    *,
    student: User,
    title: str,
    category: str,
    description: str,
    location: str | None = None,
    deadline_at: datetime | None = None,
) -> Grievance:
    """Create a grievance and its initial history row atomically."""

    if student.role != "student":
        raise AuthorizationError("Only students can submit grievances.")
    title = _validate_length(title, "Title", 3, 160)
    category = _validate_length(category, "Category", 2, 80)
    description = _validate_length(description, "Description", 10, 5000)
    location = _clean(location) or None
    if location and len(location) > 160:
        raise ValidationError("Location must be 160 characters or fewer.")

    created_at = utcnow()
    if deadline_at is None:
        deadline_at = created_at + timedelta(
            hours=current_app.config["DEFAULT_DEADLINE_HOURS"]
        )

    grievance = Grievance(
        reference_id=_new_reference_id(),
        student_id=student.id,
        title=title,
        category=category,
        description=description,
        location=location,
        priority="NORMAL",
        status="SUBMITTED",
        created_at=created_at,
        updated_at=created_at,
        deadline_at=deadline_at,
    )
    db.session.add(grievance)
    try:
        db.session.flush()
        db.session.add(
            GrievanceHistory(
                grievance_id=grievance.id,
                actor_user_id=student.id,
                old_status=None,
                new_status="SUBMITTED",
                remarks="Grievance submitted.",
                created_at=created_at,
            )
        )
        db.session.commit()
    except (IntegrityError, SQLAlchemyError) as exc:
        db.session.rollback()
        raise ValidationError("The grievance could not be saved. Please try again.") from exc
    return grievance


def can_access_grievance(user: User, grievance: Grievance) -> bool:
    """Return whether a user may view a grievance."""

    if user.role == "admin":
        return True
    if user.role == "student":
        return grievance.student_id == user.id
    if user.role == "staff":
        return grievance.assigned_staff_id == user.id or (
            user.department_id is not None
            and grievance.department_id == user.department_id
        )
    return False


def assign_grievance(
    *,
    grievance: Grievance,
    actor: User,
    department: Department,
    assigned_staff: User | None = None,
    remarks: str | None = None,
) -> Grievance:
    """Assign a grievance to a department and optional staff member."""

    if actor.role != "admin":
        raise AuthorizationError("Only administrators can assign grievances.")
    if assigned_staff is not None:
        if assigned_staff.role != "staff" or assigned_staff.department_id != department.id:
            raise ValidationError("Assigned staff must belong to the selected department.")
    remarks = _clean(remarks) or None
    if remarks and len(remarks) > 1000:
        raise ValidationError("Assignment remarks must be 1000 characters or fewer.")

    old_status = grievance.status
    grievance.department_id = department.id
    grievance.assigned_staff_id = assigned_staff.id if assigned_staff else None
    if grievance.status == "SUBMITTED":
        grievance.status = "ASSIGNED"
        db.session.add(
            GrievanceHistory(
                grievance=grievance,
                actor_user_id=actor.id,
                old_status=old_status,
                new_status="ASSIGNED",
                remarks=remarks or f"Assigned to {department.name}.",
            )
        )
    try:
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        raise ValidationError("The assignment could not be saved.") from exc
    return grievance


def update_status(
    *,
    grievance: Grievance,
    actor: User,
    new_status: str,
    remarks: str | None = None,
) -> Grievance:
    """Validate scope and transition, then write status plus history together."""

    new_status = _clean(new_status).upper()
    if actor.role not in {"staff", "admin"}:
        raise AuthorizationError("You are not allowed to update grievance status.")
    if actor.role == "staff" and not can_access_grievance(actor, grievance):
        raise AuthorizationError("This grievance is outside your authorized scope.")
    if new_status not in ALL_STATUSES:
        raise InvalidTransitionError("That status is not recognized.")
    if new_status not in ALLOWED_TRANSITIONS.get(grievance.status, set()):
        raise InvalidTransitionError(
            f"A grievance cannot move from {grievance.status.replace('_', ' ').title()} "
            f"to {new_status.replace('_', ' ').title()}."
        )

    remarks = _clean(remarks) or None
    if remarks and len(remarks) > 1000:
        raise ValidationError("Remarks must be 1000 characters or fewer.")

    old_status = grievance.status
    grievance.status = new_status
    if new_status == "RESOLVED":
        grievance.resolved_at = utcnow()
    try:
        db.session.add(
            GrievanceHistory(
                grievance=grievance,
                actor_user_id=actor.id,
                old_status=old_status,
                new_status=new_status,
                remarks=remarks,
            )
        )
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        raise ValidationError("The status update could not be saved.") from exc
    return grievance


def apply_system_escalation(
    *,
    grievance: Grievance,
    actor: User | None,
    at: datetime,
) -> None:
    """Apply the first escalation status change inside a caller transaction."""

    if not is_open_status(grievance.status) or grievance.status == "ESCALATED":
        return
    old_status = grievance.status
    grievance.status = "ESCALATED"
    db.session.add(
        GrievanceHistory(
            grievance=grievance,
            actor_user_id=actor.id if actor else None,
            old_status=old_status,
            new_status="ESCALATED",
            remarks="Automatically escalated after the configured deadline.",
            created_at=at,
        )
    )
