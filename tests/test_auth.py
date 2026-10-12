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
    # Hero, every landing section anchor, and the primary call to action.
    assert b"Your Voice." in response.data
    assert b"Our Responsibility." in response.data
    assert b"THE CHALLENGE" in response.data
    assert b"How It Works" in response.data
    assert b"Raise a grievance" in response.data
    for anchor in (b'id="hero"', b'id="problem"', b'id="solution"', b'id="features"',
                   b'id="how-it-works"', b'id="impact"', b'id="raise"'):
        assert anchor in response.data


def test_landing_page_ships_without_cdn_dependencies(client):
    """The portal must render identically offline, so no external assets."""
    response = client.get("/")

    assert response.status_code == 200
    assert b"cdn.jsdelivr.net" not in response.data
    assert b"fonts.googleapis.com" not in response.data
    assert b"bootstrap" not in response.data.lower()


def test_landing_navigation_exposes_required_destinations(client):
    response = client.get("/")
    body = response.data

    assert b">Home</a>" in body
    assert b">Features</a>" in body
    assert b">How It Works</a>" in body
    assert b">Raise a Grievance</a>" in body
    assert b">Track Grievance</a>" in body
    # Anonymous visitors are offered sign-in rather than a workspace link.
    assert b"Sign in" in body
    assert b'data-menu-target="portalNav"' in body


def test_error_pages_render_with_the_product_shell(client, data):
    login(client, data["student_one"])

    response = client.get("/admin/dashboard")

    assert response.status_code == 403
    assert b"Access denied" in response.data
    # The styled shell, not a bare Werkzeug error page.
    assert b"css/tokens.css" in response.data
    assert b"skip-link" in response.data


def test_authenticated_root_still_dispatches_to_role_dashboard(client, data):
    login(client, data["student_one"])

    response = client.get("/")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")
