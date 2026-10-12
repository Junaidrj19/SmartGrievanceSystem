from datetime import timedelta

from grievance_app.extensions import db
from grievance_app.models import Grievance, GrievanceHistory
from grievance_app.services.grievance_service import create_grievance
from grievance_app.utils import utcnow

from .conftest import login


def test_valid_creation_generates_unique_reference_and_initial_history(app, data):
    with app.app_context():
        first = create_grievance(
            student=data["student_one"],
            title="Broken classroom projector",
            category="Facilities",
            description="The projector in the test classroom does not turn on.",
        )
        second = create_grievance(
            student=data["student_one"],
            title="Missing course material",
            category="Academic",
            description="The course material for the test module is unavailable.",
        )

        assert first.reference_id.startswith("GRV-")
        assert first.reference_id != second.reference_id
        history = GrievanceHistory.query.filter_by(grievance_id=first.id).one()
        assert history.old_status is None
        assert history.new_status == "SUBMITTED"
        assert history.actor_user_id == data["student_one"].id


def test_required_fields_are_rejected(client, data):
    login(client, data["student_one"])

    response = client.post(
        "/student/grievances/new",
        data={"title": "", "category": "", "description": ""},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"This field is required" in response.data


def test_student_submission_persists_and_shows_reference(client, app, data):
    login(client, data["student_one"])

    response = client.post(
        "/student/grievances/new",
        data={
            "title": "Noise in study area",
            "category": "Facilities",
            "description": "The study area is unusually noisy during the scheduled quiet period.",
            "location": "Test Library",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"GRV-" in response.data
    with app.app_context():
        grievance = Grievance.query.filter_by(title="Noise in study area").one()
        assert grievance.location == "Test Library"
        assert grievance.deadline_at > utcnow() - timedelta(minutes=1)
        assert len(grievance.history) == 1


def test_grievance_and_history_survive_session_reload(app, data):
    with app.app_context():
        grievance = create_grievance(
            student=data["student_one"],
            title="Persistence check",
            category="Other",
            description="This record is used to verify database persistence.",
        )
        grievance_id = grievance.id
        db.session.remove()
        reloaded = db.session.get(Grievance, grievance_id)
        assert reloaded is not None
        assert reloaded.reference_id == grievance.reference_id
        assert reloaded.history[0].new_status == "SUBMITTED"
