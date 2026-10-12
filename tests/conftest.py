"""Shared isolated application and fictional test data."""

from __future__ import annotations

import pytest

from grievance_app import create_app
from grievance_app.extensions import db
from grievance_app.models import Department, User


@pytest.fixture
def app(tmp_path):
    database_path = tmp_path / "test.sqlite"
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "WTF_CSRF_ENABLED": False,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database_path}",
            "DEFAULT_DEADLINE_HOURS": 24,
            "ESCALATION_LEVEL_INTERVAL_HOURS": 24,
        }
    )
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def data(app):
    with app.app_context():
        facilities = Department(name="Test Facilities", description="Test department")
        academics = Department(name="Test Academics", description="Test department")
        db.session.add_all([facilities, academics])
        db.session.flush()

        def user(name: str, email: str, role: str, department=None) -> User:
            record = User(
                name=name,
                email=email,
                role=role,
                department=department,
            )
            record.set_password("TestPass123!")
            db.session.add(record)
            return record

        student_one = user("Test Student One", "student.one@test.example", "student")
        student_two = user("Test Student Two", "student.two@test.example", "student")
        staff_one = user("Facilities Staff", "staff.one@test.example", "staff", facilities)
        staff_colleague = user(
            "Facilities Colleague", "staff.colleague@test.example", "staff", facilities
        )
        staff_two = user("Academic Staff", "staff.two@test.example", "staff", academics)
        admin = user("Test Admin", "admin@test.example", "admin")
        db.session.commit()
        yield {
            "facilities": facilities,
            "academics": academics,
            "student_one": student_one,
            "student_two": student_two,
            "staff_one": staff_one,
            "staff_colleague": staff_colleague,
            "staff_two": staff_two,
            "admin": admin,
        }


def login(client, user: User):
    return client.post(
        "/login",
        data={"email": user.email, "password": "TestPass123!"},
        follow_redirects=True,
    )
