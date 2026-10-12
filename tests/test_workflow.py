import pytest

from grievance_app.models import GrievanceHistory
from grievance_app.services.exceptions import InvalidTransitionError
from grievance_app.services.grievance_service import (
    assign_grievance,
    create_grievance,
    update_status,
)


def test_authorized_staff_update_records_history(app, data):
    with app.app_context():
        grievance = create_grievance(
            student=data["student_one"],
            title="Status workflow case",
            category="Facilities",
            description="A case used to check authorized staff status changes.",
        )
        assign_grievance(
            grievance=grievance,
            actor=data["admin"],
            department=data["facilities"],
            assigned_staff=data["staff_one"],
        )
        update_status(
            grievance=grievance,
            actor=data["staff_one"],
            new_status="IN_PROGRESS",
            remarks="Staff began reviewing the case.",
        )

        latest = GrievanceHistory.query.filter_by(grievance_id=grievance.id).order_by(
            GrievanceHistory.id.desc()
        ).first()
        assert grievance.status == "IN_PROGRESS"
        assert latest.old_status == "ASSIGNED"
        assert latest.new_status == "IN_PROGRESS"
        assert latest.actor_user_id == data["staff_one"].id
        assert latest.remarks == "Staff began reviewing the case."


def test_invalid_status_transition_is_rejected(app, data):
    with app.app_context():
        grievance = create_grievance(
            student=data["student_one"],
            title="Invalid transition case",
            category="Academic",
            description="A case used to check the centralized status transition map.",
        )
        with pytest.raises(InvalidTransitionError):
            update_status(
                grievance=grievance,
                actor=data["admin"],
                new_status="RESOLVED",
                remarks="This should not be allowed before assignment.",
            )
