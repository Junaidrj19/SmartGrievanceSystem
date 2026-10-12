"""Transparent, configurable, and idempotent deadline escalation rules."""

from __future__ import annotations

from datetime import datetime, timedelta

from flask import current_app
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from ..extensions import db
from ..models import Escalation, Grievance, User
from ..utils import is_open_status, utcnow
from .grievance_service import apply_system_escalation


def next_escalation_level(grievance: Grievance, at: datetime) -> int | None:
    """Return the next eligible level, or None while the current level is fresh.

    Level one is eligible as soon as a case is overdue. Further levels use
    the configured demonstration interval from the most recent event. This
    makes repeated checker runs idempotent while still allowing a case that
    remains overdue to progress through the configured levels over time.
    """

    if not is_open_status(grievance.status):
        return None
    events = sorted(grievance.escalations, key=lambda event: event.level)
    if not events:
        return 1
    latest = events[-1]
    interval_hours = max(
        1, int(current_app.config.get("ESCALATION_LEVEL_INTERVAL_HOURS", 72))
    )
    if at < latest.created_at + timedelta(hours=interval_hours):
        return None
    candidate = latest.level + 1
    maximum = max(1, int(current_app.config.get("ESCALATION_MAX_LEVEL", 3)))
    return candidate if candidate <= maximum else None


def run_escalation_check(
    *, at: datetime | None = None, actor: User | None = None
) -> dict[str, int]:
    """Escalate every currently overdue unresolved case once per eligible level."""

    at = at or utcnow()
    overdue_cases = (
        Grievance.query.filter(
            Grievance.deadline_at < at,
            Grievance.status.notin_(["RESOLVED", "CLOSED"]),
        )
        .order_by(Grievance.id)
        .all()
    )
    summary = {"examined": 0, "escalated": 0, "skipped": 0, "failed": 0}
    destinations = current_app.config.get("ESCALATION_DESTINATIONS", {})

    for grievance in overdue_cases:
        summary["examined"] += 1
        level = next_escalation_level(grievance, at)
        if level is None:
            summary["skipped"] += 1
            continue
        try:
            # The savepoint keeps a concurrent unique-constraint collision
            # local to this case while the remaining run remains usable.
            with db.session.begin_nested():
                event = Escalation(
                    grievance=grievance,
                    level=level,
                    reason=(
                        "The grievance remains unresolved after its configured "
                        "response deadline."
                    ),
                    source_authority="Automated deadline checker",
                    destination_authority=destinations.get(level, "Next authority"),
                    action_status="OPEN",
                    created_at=at,
                )
                db.session.add(event)
                apply_system_escalation(grievance=grievance, actor=actor, at=at)
                db.session.flush()
            summary["escalated"] += 1
        except IntegrityError:
            summary["skipped"] += 1
        except SQLAlchemyError:
            summary["failed"] += 1

    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        # The caller receives a safe summary rather than an internal error.
        summary["failed"] += summary["escalated"]
        summary["escalated"] = 0
    return summary
