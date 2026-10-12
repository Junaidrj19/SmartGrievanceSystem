"""Dashboard reporting and rendering.

These tests pin the numbers shown on each role dashboard to the database so a
template can never drift from the real counts.
"""

from datetime import timedelta

from grievance_app.services.grievance_service import (
    assign_grievance,
    create_grievance,
    update_status,
)
from grievance_app.services.reporting_service import (
    department_counts,
    queue_summary,
    visible_grievances,
)
from grievance_app.utils import utcnow

from .conftest import login


def _case(data, *, student=None, title, category="Facilities", hours=12):
    return create_grievance(
        student=student or data["student_one"],
        title=title,
        category=category,
        description="A sufficiently detailed description for the dashboard tests.",
        deadline_at=utcnow() + timedelta(hours=hours),
    )


def test_queue_summary_counts_open_resolved_and_overdue(app, data):
    with app.app_context():
        _case(data, title="Open and on time")
        overdue = _case(data, title="Open but overdue", hours=-6)
        resolved = _case(data, title="Will be resolved")

        assign_grievance(
            grievance=resolved,
            actor=data["admin"],
            department=data["facilities"],
            assigned_staff=data["staff_one"],
        )
        update_status(grievance=resolved, actor=data["staff_one"], new_status="IN_PROGRESS")
        update_status(grievance=resolved, actor=data["staff_one"], new_status="RESOLVED")

        summary = queue_summary(visible_grievances(data["student_one"]))

        assert summary["total"] == 3
        assert summary["resolved"] == 1
        assert summary["open"] == 2
        assert summary["overdue"] == 1
        assert summary["escalated"] == 0
        assert overdue.is_overdue() is True


def test_queue_summary_is_scoped_to_the_requesting_user(app, data):
    with app.app_context():
        _case(data, student=data["student_one"], title="Belongs to student one")
        _case(data, student=data["student_two"], title="Belongs to student two")
        _case(data, student=data["student_two"], title="Also student two")

        assert queue_summary(visible_grievances(data["student_one"]))["total"] == 1
        assert queue_summary(visible_grievances(data["student_two"]))["total"] == 2
        assert queue_summary(visible_grievances(data["admin"]))["total"] == 3


def test_queue_summary_on_an_empty_queue_returns_zeroes(app, data):
    with app.app_context():
        summary = queue_summary(visible_grievances(data["student_one"]))

        assert summary == {
            "total": 0,
            "open": 0,
            "resolved": 0,
            "overdue": 0,
            "escalated": 0,
        }


def test_department_counts_groups_unassigned_cases(app, data):
    with app.app_context():
        assigned = _case(data, title="Assigned to facilities")
        assign_grievance(
            grievance=assigned,
            actor=data["admin"],
            department=data["facilities"],
            assigned_staff=data["staff_one"],
        )
        _case(data, title="Still unassigned")

        counts = dict(department_counts())

        assert counts["Test Facilities"] == 1
        assert counts["Unassigned"] == 1


def test_student_dashboard_renders_real_metrics(client, app, data):
    with app.app_context():
        _case(data, title="Student metric case")
        _case(data, title="Student overdue case", hours=-4)
    login(client, data["student_one"])

    response = client.get("/student/dashboard")

    assert response.status_code == 200
    # queue_summary supplies these, so the rendered count must match the DB.
    assert b'data-count="2"' in response.data
    assert b"Overdue open" in response.data
    assert b"Total submissions" in response.data


def test_student_dashboard_shows_an_empty_state(client, data):
    login(client, data["student_one"])

    response = client.get("/student/dashboard")

    assert response.status_code == 200
    assert b"No grievances yet" in response.data


def test_staff_dashboard_filters_by_status_and_deadline(client, app, data):
    with app.app_context():
        case = _case(data, title="Staff filter case")
        assign_grievance(
            grievance=case,
            actor=data["admin"],
            department=data["facilities"],
            assigned_staff=data["staff_one"],
        )
        reference = case.reference_id
    login(client, data["staff_one"])

    matching = client.get("/staff/dashboard?status=ASSIGNED")
    assert matching.status_code == 200
    assert reference.encode() in matching.data

    excluded = client.get("/staff/dashboard?status=RESOLVED")
    assert excluded.status_code == 200
    assert reference.encode() not in excluded.data

    not_overdue = client.get("/staff/dashboard?overdue=0")
    assert reference.encode() in not_overdue.data

    overdue_only = client.get("/staff/dashboard?overdue=1")
    assert reference.encode() not in overdue_only.data


def test_admin_dashboard_renders_status_chart_from_real_counts(client, app, data):
    with app.app_context():
        case = _case(data, title="Admin chart case")
        assign_grievance(
            grievance=case,
            actor=data["admin"],
            department=data["facilities"],
            assigned_staff=data["staff_one"],
        )
    login(client, data["admin"])

    response = client.get("/admin/dashboard")
    body = response.data

    assert response.status_code == 200
    # One assigned case: the donut must carry an Assigned arc and a legend row.
    assert b"donut-arc arc-assigned" in body
    assert b"<title>Assigned: 1</title>" in body
    assert b"Cases by department" in body
    assert b"Test Facilities" in body


def test_admin_dashboard_handles_an_empty_database(client, data):
    login(client, data["admin"])

    response = client.get("/admin/dashboard")

    assert response.status_code == 200
    assert b"No cases recorded yet" in response.data
    # No divide-by-zero and no fabricated numbers.
    assert b"donut-arc" not in response.data
