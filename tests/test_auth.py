from grievance_app.models import User

from .conftest import login


def test_login_uses_hashed_password_and_role_dashboard(client, data):
    response = login(client, data["student_one"])

    assert response.status_code == 200
    assert b"My grievances" in response.data
    assert data["student_one"].password_hash != "TestPass123!"
    assert data["student_one"].check_password("TestPass123!")


def test_role_guard_blocks_student_from_admin_dashboard(client, data):
    login(client, data["student_one"])

    response = client.get("/admin/dashboard")

    assert response.status_code == 403


def test_public_root_is_scrollable_landing_page(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Your voice." in response.data
    assert b"THE CHALLENGE" in response.data
    assert b"How it works" in response.data
    assert b"Raise a grievance" in response.data


def test_authenticated_root_still_dispatches_to_role_dashboard(client, data):
    login(client, data["student_one"])

    response = client.get("/")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")
