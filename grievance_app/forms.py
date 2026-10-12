"""WTForms definitions shared by the role-specific routes."""

from __future__ import annotations

from wtforms import (  # type: ignore[import-untyped]
    BooleanField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, Length, Optional
from flask_wtf import FlaskForm


def required_int(value: str | None) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


def optional_int(value: str | None) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired(), Length(max=128)])
    remember = BooleanField("Remember me")
    submit = SubmitField("Sign in")


class LogoutForm(FlaskForm):
    submit = SubmitField("Sign out")


class GrievanceForm(FlaskForm):
    title = StringField(
        "Title",
        validators=[DataRequired(), Length(min=3, max=160)],
        render_kw={"maxlength": 160},
    )
    category = StringField(
        "Category",
        validators=[DataRequired(), Length(min=2, max=80)],
        render_kw={"maxlength": 80},
    )
    description = TextAreaField(
        "Description",
        validators=[DataRequired(), Length(min=10, max=5000)],
        render_kw={"rows": 6, "maxlength": 5000},
    )
    location = StringField(
        "Location (optional)",
        validators=[Optional(), Length(max=160)],
        render_kw={"maxlength": 160},
    )
    submit = SubmitField("Submit grievance")


class AssignmentForm(FlaskForm):
    department_id = SelectField(
        "Department",
        coerce=required_int,
        validators=[DataRequired()],
    )
    assigned_staff_id = SelectField(
        "Assigned staff (optional)",
        coerce=optional_int,
        validators=[Optional()],
    )
    remarks = TextAreaField(
        "Assignment remarks (optional)",
        validators=[Optional(), Length(max=1000)],
        render_kw={"rows": 3, "maxlength": 1000},
    )
    submit = SubmitField("Save assignment")


class StatusUpdateForm(FlaskForm):
    status = SelectField("New status", validators=[DataRequired()])
    remarks = TextAreaField(
        "Progress remarks (optional)",
        validators=[Optional(), Length(max=1000)],
        render_kw={"rows": 4, "maxlength": 1000},
    )
    submit = SubmitField("Save status")


class EscalationCheckForm(FlaskForm):
    submit = SubmitField("Check overdue grievances")
