"""Small shared helpers that do not depend on application services."""

from __future__ import annotations

from datetime import datetime, timezone


ROLE_LABELS = {
    "student": "Student",
    "staff": "Staff",
    "admin": "Administrator",
}

STATUS_LABELS = {
    "SUBMITTED": "Submitted",
    "ASSIGNED": "Assigned",
    "IN_PROGRESS": "In Progress",
    "ESCALATED": "Escalated",
    "RESOLVED": "Resolved",
    "CLOSED": "Closed",
}


def utcnow() -> datetime:
    """Return a naive UTC datetime suitable for SQLite DateTime columns."""

    return datetime.now(timezone.utc).replace(tzinfo=None)


def format_datetime(value: datetime | None) -> str:
    if value is None:
        return "—"
    return value.strftime("%d %b %Y, %H:%M UTC")


def status_label(status: str) -> str:
    return STATUS_LABELS.get(status, status.replace("_", " ").title())


def is_open_status(status: str) -> bool:
    return status not in {"RESOLVED", "CLOSED"}
