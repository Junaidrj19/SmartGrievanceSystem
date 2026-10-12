"""Queries used by role dashboards and administrative reporting."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import false, func, or_

from ..extensions import db
from ..models import Department, Grievance, User
from ..utils import utcnow

STATUS_ORDER = ("SUBMITTED", "ASSIGNED", "IN_PROGRESS", "ESCALATED", "RESOLVED", "CLOSED")


def visible_grievances(user: User):
    """Return a query scoped to the records a user may see."""

    if user.role == "admin":
        return Grievance.query
    if user.role == "student":
        return Grievance.query.filter(Grievance.student_id == user.id)
    if user.role == "staff":
        conditions = [Grievance.assigned_staff_id == user.id]
        if user.department_id is not None:
            conditions.append(Grievance.department_id == user.department_id)
        return Grievance.query.filter(or_(*conditions))
    return Grievance.query.filter(false())


def filter_grievances(
    query,
    *,
    status: str | None = None,
    category: str | None = None,
    department_id: int | None = None,
    overdue: bool | None = None,
    search: str | None = None,
    at: datetime | None = None,
):
    at = at or utcnow()
    if status:
        query = query.filter(Grievance.status == status)
    if category:
        query = query.filter(Grievance.category == category)
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Grievance.reference_id.ilike(term),
                Grievance.title.ilike(term),
                Grievance.description.ilike(term),
                Grievance.category.ilike(term),
            )
        )
    if department_id:
        query = query.filter(Grievance.department_id == department_id)
    if overdue is True:
        query = query.filter(
            Grievance.deadline_at < at,
            Grievance.status.notin_(["RESOLVED", "CLOSED"]),
        )
    elif overdue is False:
        query = query.filter(
            (Grievance.deadline_at >= at)
            | Grievance.status.in_(["RESOLVED", "CLOSED"])
        )
    return query.order_by(Grievance.updated_at.desc(), Grievance.id.desc())


def dashboard_counts(*, at: datetime | None = None) -> dict[str, int]:
    at = at or utcnow()
    total = db.session.query(func.count(Grievance.id)).scalar() or 0
    resolved = (
        db.session.query(func.count(Grievance.id))
        .filter(Grievance.status.in_(["RESOLVED", "CLOSED"]))
        .scalar()
        or 0
    )
    overdue = (
        db.session.query(func.count(Grievance.id))
        .filter(
            Grievance.deadline_at < at,
            Grievance.status.notin_(["RESOLVED", "CLOSED"]),
        )
        .scalar()
        or 0
    )
    escalated = (
        db.session.query(func.count(Grievance.id))
        .filter(Grievance.status == "ESCALATED")
        .scalar()
        or 0
    )
    return {
        "total": int(total),
        "open": int(total - resolved),
        "resolved": int(resolved),
        "overdue": int(overdue),
        "escalated": int(escalated),
    }


def status_counts(query=None) -> dict[str, int]:
    """Return real status totals for a supplied visibility-scoped query."""

    query = query or Grievance.query
    rows = query.with_entities(Grievance.status, func.count(Grievance.id)).group_by(
        Grievance.status
    ).all()
    counts = {status: 0 for status in STATUS_ORDER}
    counts.update({status: int(total) for status, total in rows})
    return counts


def department_choices() -> list[Department]:
    return Department.query.order_by(Department.name).all()


def staff_for_department(department_id: int | None) -> list[User]:
    if not department_id:
        return []
    return User.query.filter_by(role="staff", department_id=department_id).order_by(
        User.name
    ).all()
