from datetime import timedelta

from grievance_app.extensions import db
from grievance_app.models import Grievance
from grievance_app.services.grievance_service import assign_grievance, create_grievance
from grievance_app.utils import utcnow

from .conftest import login


def make_assigned_case(app, data, *, student=None, department=None, staff=None):
    student = student or data["student_one"]
    department = department or data["facilities"]
    staff = staff or data["staff_one"]
    with app.app_context():
        grievance = create_grievance(
            student=student,
            title="Assigned test case",
            category="Facilities",
            description="A sufficiently detailed assigned test case description.",
            deadline_at=utcnow() + timedelta(hours=12),
        )
        assign_grievance(
            grievance=grievance,
            actor=data["admin"],
            department=department,
            assigned_staff=staff,
        )
        return grievance.id


def test_student_cannot_view_another_students_case(client, app, data):
    with app.app_context():
        grievance = create_grievance(
            student=data["student_two"],
            title="Private student case",
            category="Academic",
            description="This case belongs only to the second test student.",
        )
        grievance_id = grievance.id
    login(client, data["student_one"])

    response = client.get(f"/student/grievances/{grievance_id}")

    assert response.status_code == 404


def test_staff_scope_allows_department_and_rejects_other_department(client, app, data):
    with app.app_context():
        grievance = create_grievance(
            student=data["student_one"],
            title="Department-scoped case",
            category="Facilities",
            description="The facilities team must be able to see this test case.",
        )
        assign_grievance(
            grievance=grievance,
            actor=data["admin"],
            department=data["facilities"],
            assigned_staff=data["staff_one"],
        )
        grievance_id = grievance.id
    login(client, data["staff_one"])
    allowed = client.get(f"/staff/grievances/{grievance_id}")
    assert allowed.status_code == 200

    client.post("/logout")
    login(client, data["staff_colleague"])
    same_department = client.get(f"/staff/grievances/{grievance_id}")
    assert same_department.status_code == 200

    client.post("/logout")
    login(client, data["staff_two"])
    other_department = client.get(f"/staff/grievances/{grievance_id}")
    assert other_department.status_code == 404

    outside_id = make_assigned_case(
        app,
        data,
        student=data["student_one"],
        department=data["academics"],
        staff=data["staff_two"],
    )
    outside = client.get(f"/staff/grievances/{outside_id}")
    assert outside.status_code == 200


def test_staff_cannot_access_unassigned_other_department_case(client, app, data):
    with app.app_context():
        grievance = create_grievance(
            student=data["student_one"],
            title="Outside department case",
            category="Academic",
            description="This case is intentionally outside the staff scope.",
        )
        assign_grievance(
            grievance=grievance,
            actor=data["admin"],
            department=data["academics"],
            assigned_staff=data["staff_two"],
        )
        grievance_id = grievance.id
    login(client, data["staff_one"])

    response = client.get(f"/staff/grievances/{grievance_id}")

    assert response.status_code == 404


def test_admin_can_assign_and_filter_cases(client, app, data):
    with app.app_context():
        grievance = create_grievance(
            student=data["student_one"],
            title="Admin dashboard case",
            category="Facilities",
            description="The administrator dashboard should find this case.",
        )
        grievance_id = grievance.id
        reference_id = grievance.reference_id
    login(client, data["admin"])

    response = client.post(
        f"/admin/grievances/{grievance_id}/assign",
        data={
            "department_id": data["facilities"].id,
            "assigned_staff_id": data["staff_one"].id,
            "remarks": "Assigned during the dashboard test.",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Assignment saved" in response.data
    with app.app_context():
        saved = db.session.get(Grievance, grievance_id)
        assert saved.status == "ASSIGNED"
        assert saved.assigned_staff_id == data["staff_one"].id

    filtered = client.get(
        f"/admin/dashboard?status=ASSIGNED&category=Facilities&department={data['facilities'].id}"
    )
    assert filtered.status_code == 200
    assert reference_id.encode() in filtered.data

    searched = client.get("/admin/dashboard?q=Admin+dashboard+case")
    assert searched.status_code == 200
    assert reference_id.encode() in searched.data

    absent = client.get("/admin/dashboard?q=does-not-exist")
    assert absent.status_code == 200
    assert reference_id.encode() not in absent.data
