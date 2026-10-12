"""Fictional, idempotent development data for local demonstrations."""

from __future__ import annotations

from datetime import timedelta

from .extensions import db
from .models import Department, Grievance, User
from .services.grievance_service import assign_grievance, create_grievance, update_status
from .utils import utcnow


DEMO_PASSWORD = "DemoPass123!"

DEPARTMENTS = [
    ("Academic Affairs", "Academic records and curriculum support."),
    ("Campus Facilities", "Buildings, classrooms, and campus services."),
    ("Student Finance", "Fees, scholarships, and account support."),
]

USERS = [
    ("Ava Sen", "ava.student@example.edu", "student", ""),
    ("Liam Noor", "liam.student@example.edu", "student", ""),
    ("Maya Hart", "maya.staff@example.edu", "staff", "Campus Facilities"),
    ("Noah Reed", "noah.staff@example.edu", "staff", "Academic Affairs"),
    ("Riley Quinn", "riley.admin@example.edu", "admin", ""),
]


def _get_or_create_department(name: str, description: str) -> Department:
    department = Department.query.filter_by(name=name).first()
    if department is None:
        department = Department(name=name, description=description)
        db.session.add(department)
        db.session.flush()
    return department


def _get_or_create_user(
    name: str, email: str, role: str, department: Department | None
) -> User:
    user = User.query.filter_by(email=email).first()
    if user is None:
        user = User(name=name, email=email, role=role, department=department)
        user.set_password(DEMO_PASSWORD)
        db.session.add(user)
        db.session.flush()
    else:
        user.name = name
        user.role = role
        user.department = department
        # Keep the development login deterministic if data was recreated.
        user.set_password(DEMO_PASSWORD)
    return user


def _sample_grievance(
    *,
    student: User,
    admin: User,
    staff: User,
    title: str,
    category: str,
    description: str,
    department: Department,
    deadline_at,
    final_status: str,
) -> Grievance:
    existing = Grievance.query.filter_by(student_id=student.id, title=title).first()
    if existing is not None:
        return existing
    grievance = create_grievance(
        student=student,
        title=title,
        category=category,
        description=description,
        location="Fictional campus demonstration data",
        deadline_at=deadline_at,
    )
    assign_grievance(
        grievance=grievance,
        actor=admin,
        department=department,
        assigned_staff=staff,
        remarks="Initial demo assignment.",
    )
    if final_status in {"IN_PROGRESS", "RESOLVED", "CLOSED"}:
        update_status(
            grievance=grievance,
            actor=staff,
            new_status="IN_PROGRESS",
            remarks="Demo staff member started review.",
        )
    if final_status in {"RESOLVED", "CLOSED"}:
        update_status(
            grievance=grievance,
            actor=staff,
            new_status="RESOLVED",
            remarks="Demo resolution recorded.",
        )
    if final_status == "CLOSED":
        update_status(
            grievance=grievance,
            actor=admin,
            new_status="CLOSED",
            remarks="Demo case closed after resolution.",
        )
    return grievance


def seed_demo_data() -> dict[str, int]:
    """Create fictional demo departments, users, and sample grievances."""

    departments = {
        name: _get_or_create_department(name, description)
        for name, description in DEPARTMENTS
    }
    db.session.commit()

    users = {
        email: _get_or_create_user(
            name,
            email,
            role,
            departments.get(department_name) if department_name else None,
        )
        for name, email, role, department_name in USERS
    }
    db.session.commit()

    now = utcnow()
    _sample_grievance(
        student=users["ava.student@example.edu"],
        admin=users["riley.admin@example.edu"],
        staff=users["maya.staff@example.edu"],
        title="Library study room booking issue",
        category="Facilities",
        description="The online booking page does not show the available study rooms for the evening slot.",
        department=departments["Campus Facilities"],
        deadline_at=now + timedelta(hours=36),
        final_status="IN_PROGRESS",
    )
    _sample_grievance(
        student=users["liam.student@example.edu"],
        admin=users["riley.admin@example.edu"],
        staff=users["noah.staff@example.edu"],
        title="Transcript correction request",
        category="Academic",
        description="A completed elective is missing from the fictional student transcript and needs review.",
        department=departments["Academic Affairs"],
        deadline_at=now - timedelta(hours=12),
        final_status="ASSIGNED",
    )
    _sample_grievance(
        student=users["ava.student@example.edu"],
        admin=users["riley.admin@example.edu"],
        staff=users["maya.staff@example.edu"],
        title="Sample resolved fee question",
        category="Finance",
        description="A demonstration fee receipt needs a clearer label in the student account view.",
        department=departments["Campus Facilities"],
        deadline_at=now - timedelta(hours=6),
        final_status="RESOLVED",
    )

    return {
        "departments": Department.query.count(),
        "users": User.query.count(),
        "grievances": Grievance.query.count(),
    }
