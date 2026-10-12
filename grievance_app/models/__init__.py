"""SQLAlchemy persistence models for users, grievances, history, and events."""

from __future__ import annotations

from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db
from ..utils import is_open_status, utcnow


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, index=True)
    department_id = db.Column(
        db.Integer, db.ForeignKey("department.id", ondelete="SET NULL"), nullable=True
    )
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    department = db.relationship("Department", back_populates="users")
    submitted_grievances = db.relationship(
        "Grievance",
        back_populates="student",
        foreign_keys="Grievance.student_id",
    )
    assigned_grievances = db.relationship(
        "Grievance",
        back_populates="assigned_staff",
        foreign_keys="Grievance.assigned_staff_id",
    )
    history_entries = db.relationship(
        "GrievanceHistory",
        back_populates="actor_user",
        foreign_keys="GrievanceHistory.actor_user_id",
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:  # pragma: no cover - debugging convenience
        return f"<User {self.email!r} ({self.role})>"


class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.String(500), nullable=True)

    users = db.relationship("User", back_populates="department")
    grievances = db.relationship("Grievance", back_populates="department")


class Grievance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference_id = db.Column(db.String(32), unique=True, nullable=False, index=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="RESTRICT"), nullable=False
    )
    department_id = db.Column(
        db.Integer, db.ForeignKey("department.id", ondelete="SET NULL"), nullable=True
    )
    assigned_staff_id = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    title = db.Column(db.String(160), nullable=False)
    category = db.Column(db.String(80), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(160), nullable=True)
    priority = db.Column(db.String(20), nullable=False, default="NORMAL")
    status = db.Column(db.String(20), nullable=False, default="SUBMITTED", index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    deadline_at = db.Column(db.DateTime, nullable=False, index=True)
    resolved_at = db.Column(db.DateTime, nullable=True)

    student = db.relationship(
        "User", back_populates="submitted_grievances", foreign_keys=[student_id]
    )
    department = db.relationship("Department", back_populates="grievances")
    assigned_staff = db.relationship(
        "User", back_populates="assigned_grievances", foreign_keys=[assigned_staff_id]
    )
    history = db.relationship(
        "GrievanceHistory",
        back_populates="grievance",
        cascade="all, delete-orphan",
        order_by="GrievanceHistory.created_at",
    )
    escalations = db.relationship(
        "Escalation",
        back_populates="grievance",
        cascade="all, delete-orphan",
        order_by="Escalation.level",
    )

    @property
    def is_open(self) -> bool:
        return is_open_status(self.status)

    def is_overdue(self, at: datetime | None = None) -> bool:
        return self.is_open and self.deadline_at < (at or utcnow())


class GrievanceHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    grievance_id = db.Column(
        db.Integer, db.ForeignKey("grievance.id", ondelete="CASCADE"), nullable=False
    )
    actor_user_id = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    old_status = db.Column(db.String(20), nullable=True)
    new_status = db.Column(db.String(20), nullable=False)
    remarks = db.Column(db.String(1000), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)

    grievance = db.relationship("Grievance", back_populates="history")
    actor_user = db.relationship(
        "User", back_populates="history_entries", foreign_keys=[actor_user_id]
    )


class Escalation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    grievance_id = db.Column(
        db.Integer, db.ForeignKey("grievance.id", ondelete="CASCADE"), nullable=False
    )
    level = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(500), nullable=False)
    source_authority = db.Column(db.String(120), nullable=False)
    destination_authority = db.Column(db.String(120), nullable=False)
    action_status = db.Column(db.String(30), nullable=False, default="OPEN")
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)

    grievance = db.relationship("Grievance", back_populates="escalations")

    __table_args__ = (
        db.UniqueConstraint(
            "grievance_id", "level", name="uq_escalation_grievance_level"
        ),
        db.Index("ix_escalation_grievance_created", "grievance_id", "created_at"),
    )


__all__ = [
    "Department",
    "Escalation",
    "Grievance",
    "GrievanceHistory",
    "User",
]
