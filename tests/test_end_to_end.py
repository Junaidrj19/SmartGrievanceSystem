"""End-to-end HTTP verification of the grievance lifecycle.

These drive the real routes through the test client rather than calling the
service layer directly, so templates, forms, redirects, authorization and
flash feedback are all exercised together.
"""

from datetime import timedelta

import pytest

from grievance_app import create_app
from grievance_app.extensions import db
from grievance_app.models import Escalation, Grievance
from grievance_app.services.grievance_service import create_grievance
from grievance_app.utils import utcnow

from .conftest import login


def test_full_lifecycle_submit_assign_progress_resolve(client, app, data):
    # 1. A student signs in and submits a grievance.
    login(client, data["student_one"])
    submission = client.post(
        "/student/grievances/new",
        data={
            "title": "Lecture hall projector is broken",
            "category": "Facilities",
            "description": "The projector in lecture hall 2 has not worked for three days.",
            "location": "Lecture hall 2",
        },
        follow_redirects=True,
    )

    assert submission.status_code == 200
    assert b"Grievance submitted successfully" in submission.data
    assert b"GRV-" in submission.data

    with app.app_context():
        grievance = Grievance.query.filter_by(title="Lecture hall projector is broken").one()
        grievance_id = grievance.id
        reference = grievance.reference_id
        assert grievance.status == "SUBMITTED"
        assert grievance.deadline_at is not None

    # The student can see it on their own dashboard.
    dashboard = client.get("/student/dashboard")
    assert reference.encode() in dashboard.data

    # 2. An administrator assigns it.
    client.post("/logout")
    login(client, data["admin"])
    assignment = client.post(
        f"/admin/grievances/{grievance_id}/assign",
        data={
            "department_id": data["facilities"].id,
            "assigned_staff_id": data["staff_one"].id,
            "remarks": "Routing to the facilities team.",
        },
        follow_redirects=True,
    )
    assert assignment.status_code == 200
    assert b"Assignment saved" in assignment.data

    # 3. The assigned staff member progresses then resolves the case.
    client.post("/logout")
    login(client, data["staff_one"])
    progressed = client.post(
        f"/staff/grievances/{grievance_id}/status",
        data={"status": "IN_PROGRESS", "remarks": "Replacement lamp ordered."},
        follow_redirects=True,
    )
    assert progressed.status_code == 200
    assert b"Grievance status and history were updated." in progressed.data

    resolved = client.post(
        f"/staff/grievances/{grievance_id}/status",
        data={"status": "RESOLVED", "remarks": "Projector replaced and tested."},
        follow_redirects=True,
    )
    assert resolved.status_code == 200

    # 4. The audit trail holds every transition in order.
    with app.app_context():
        grievance = db.session.get(Grievance, grievance_id)
        assert grievance.status == "RESOLVED"
        assert grievance.resolved_at is not None
        transitions = [entry.new_status for entry in grievance.history]
        assert transitions == ["SUBMITTED", "ASSIGNED", "IN_PROGRESS", "RESOLVED"]
        assert grievance.history[-1].remarks == "Projector replaced and tested."

    # 5. The case detail page renders the timeline for the student.
    client.post("/logout")
    login(client, data["student_one"])
    detail = client.get(f"/student/grievances/{grievance_id}")
    assert detail.status_code == 200
    assert reference.encode() in detail.data
    assert b"Status history" in detail.data
    assert b"Projector replaced and tested." in detail.data
    # A student must not be offered workflow controls.
    assert b"Update status" not in detail.data
    assert b"Assignment" not in detail.data


def test_invalid_submission_is_rejected_with_field_errors(client, data):
    login(client, data["student_one"])

    response = client.post(
        "/student/grievances/new",
        data={"title": "x", "category": "", "description": "too short"},
    )

    assert response.status_code == 200
    assert b"field-error" in response.data
    assert b"This field is required" in response.data


def test_admin_escalation_action_is_idempotent(client, app, data):
    with app.app_context():
        overdue = create_grievance(
            student=data["student_one"],
            title="Overdue case for the checker",
            category="Facilities",
            description="This case is deliberately past its response deadline.",
            deadline_at=utcnow() - timedelta(hours=48),
        )
        grievance_id = overdue.id

    login(client, data["admin"])

    first = client.post("/admin/escalations/check", follow_redirects=True)
    assert first.status_code == 200
    assert b"Escalation check complete" in first.data
    assert b"1 escalated" in first.data

    with app.app_context():
        events = Escalation.query.filter_by(grievance_id=grievance_id).all()
        assert len(events) == 1
        assert events[0].level == 1
        assert db.session.get(Grievance, grievance_id).status == "ESCALATED"

    # Running again immediately must not duplicate the level-1 event.
    second = client.post("/admin/escalations/check", follow_redirects=True)
    assert second.status_code == 200
    assert b"0 escalated" in second.data

    with app.app_context():
        assert Escalation.query.filter_by(grievance_id=grievance_id).count() == 1

    history = client.get("/admin/escalations")
    assert history.status_code == 200
    assert b"Level 1" in history.data
    assert b"Department Head" in history.data


def test_escalated_case_shows_event_panel_on_detail_page(client, app, data):
    with app.app_context():
        overdue = create_grievance(
            student=data["student_one"],
            title="Overdue case with a panel",
            category="Facilities",
            description="This case is deliberately past its response deadline.",
            deadline_at=utcnow() - timedelta(hours=48),
        )
        grievance_id = overdue.id

    login(client, data["admin"])
    client.post("/admin/escalations/check", follow_redirects=True)

    detail = client.get(f"/admin/grievances/{grievance_id}")

    assert detail.status_code == 200
    assert b"Escalation events" in detail.data
    assert b"Level 1" in detail.data
    # Admins do get the workflow controls.
    assert b"Update status" in detail.data
    assert b"Assignment" in detail.data


@pytest.fixture
def csrf_app(tmp_path):
    """An application with CSRF protection left switched on."""
    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "csrf-test-secret",
            "WTF_CSRF_ENABLED": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'csrf.sqlite'}",
        }
    )
    yield application
    with application.app_context():
        db.session.remove()
        db.drop_all()


def test_state_changing_posts_require_a_csrf_token(csrf_app):
    client = csrf_app.test_client()

    response = client.post(
        "/login",
        data={"email": "someone@test.example", "password": "TestPass123!"},
    )

    # Flask-WTF rejects the unprotected form before any credential check.
    assert response.status_code == 400
