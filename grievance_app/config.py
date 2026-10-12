"""Configuration defaults for local development and tests."""

from __future__ import annotations

import os


def _integer_env(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "local-development-key-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///grievance.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_TIME_LIMIT = None

    # These are explicit demonstration rules, not an institutional policy.
    DEFAULT_DEADLINE_HOURS = _integer_env("DEFAULT_DEADLINE_HOURS", 72)
    ESCALATION_LEVEL_INTERVAL_HOURS = _integer_env(
        "ESCALATION_LEVEL_INTERVAL_HOURS", 72
    )
    ESCALATION_MAX_LEVEL = _integer_env("ESCALATION_MAX_LEVEL", 3)
    ESCALATION_DESTINATIONS = {
        1: "Department Head",
        2: "Dean's Office",
        3: "Grievance Committee",
    }
