from datetime import timedelta

from grievance_app.extensions import db
from grievance_app.models import Escalation, Grievance
from grievance_app.services.escalation_service import run_escalation_check
from grievance_app.services.grievance_service import assign_grievance, create_grievance, update_status
from grievance_app.utils import utcnow


def overdue_case(app, data, title):
    grievance = create_grievance(
        student=data["student_one"],
        title=title,
        category="Facilities",
        description="An overdue test case with a complete description.",
        deadline_at=utcnow() - timedelta(hours=2),
    )
    return grievance


def test_overdue_case_escalates_once_when_checker_repeats(app, data):
    with app.app_context():
        grievance = overdue_case(app, data, "Overdue unresolved case")
        now = utcnow()

        first = run_escalation_check(at=now)
        second = run_escalation_check(at=now)

        assert first["examined"] == 1
        assert first["escalated"] == 1
        assert second["escalated"] == 0
        assert second["skipped"] == 1
        assert Escalation.query.filter_by(grievance_id=grievance.id).count() == 1
        assert db.session.get(Grievance, grievance.id).status == "ESCALATED"


def test_resolved_and_closed_cases_never_escalate(app, data):
    with app.app_context():
        resolved = overdue_case(app, data, "Overdue resolved case")
        assign_grievance(
            grievance=resolved,
            actor=data["admin"],
            department=data["facilities"],
            assigned_staff=data["staff_one"],
        )
        update_status(
            grievance=resolved,
            actor=data["staff_one"],
            new_status="IN_PROGRESS",
        )
        update_status(
            grievance=resolved,
            actor=data["staff_one"],
            new_status="RESOLVED",
        )

        closed = overdue_case(app, data, "Overdue closed case")
        assign_grievance(
            grievance=closed,
            actor=data["admin"],
            department=data["facilities"],
            assigned_staff=data["staff_one"],
        )
        update_status(grievance=closed, actor=data["staff_one"], new_status="IN_PROGRESS")
        update_status(grievance=closed, actor=data["staff_one"], new_status="RESOLVED")
        update_status(grievance=closed, actor=data["admin"], new_status="CLOSED")

        summary = run_escalation_check(at=utcnow())

        assert summary["examined"] == 0
        assert Escalation.query.filter_by(grievance_id=resolved.id).count() == 0
        assert Escalation.query.filter_by(grievance_id=closed.id).count() == 0


def test_cli_checker_uses_same_escalation_service(app, data):
    with app.app_context():
        overdue_case(app, data, "CLI overdue case")
    runner = app.test_cli_runner()

    result = runner.invoke(args=["check-escalations"])

    assert result.exit_code == 0
    assert "escalated=1" in result.output
