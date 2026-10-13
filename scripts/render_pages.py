"""Render every Resolve page to a static HTML file for visual inspection.

Uses the Flask test client against an isolated temporary database seeded with
the fictional demo data, so authenticated pages can be captured without
touching instance/grievance.db. A <base> tag is injected so the saved files
load CSS, fonts and JS from the running dev server.

Usage: python scripts/render_pages.py <output_dir> <asset_base_url>
"""

from __future__ import annotations

import pathlib
import sys
from datetime import timedelta

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from grievance_app import create_app  # noqa: E402
from grievance_app.extensions import db  # noqa: E402
from grievance_app.models import Grievance  # noqa: E402
from grievance_app.seed import DEMO_PASSWORD, seed_demo_data  # noqa: E402
from grievance_app.services.escalation_service import run_escalation_check  # noqa: E402
from grievance_app.services.grievance_service import create_grievance  # noqa: E402
from grievance_app.utils import utcnow  # noqa: E402


def login(client, email: str) -> None:
    client.post(
        "/login",
        data={"email": email, "password": DEMO_PASSWORD},
        follow_redirects=True,
    )


def main(out_dir: str, asset_base: str) -> int:
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    tmp_db = out / "_preview.sqlite"
    if tmp_db.exists():
        tmp_db.unlink()

    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "render-preview-secret",
            "WTF_CSRF_ENABLED": False,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_db}",
        }
    )

    with app.app_context():
        seed_demo_data()
        # Guarantee an escalated case so the escalation panels have content.
        student_case = db.session.query(Grievance).first()
        student_case_id = student_case.id
        overdue = create_grievance(
            student=student_case.student,
            title="Overdue hostel maintenance request",
            category="Facilities",
            description="Captured for the visual review: this case is past its deadline.",
            deadline_at=utcnow() - timedelta(hours=96),
        )
        overdue_id = overdue.id
        run_escalation_check()

    pages: list[tuple[str, str, str | None]] = [
        ("landing", "/", None),
        ("login", "/login", None),
        ("student-dashboard", "/student/dashboard", "ava.student@example.edu"),
        ("student-new-grievance", "/student/grievances/new", "ava.student@example.edu"),
        ("student-detail", f"/student/grievances/{student_case_id}", "ava.student@example.edu"),
        ("staff-dashboard", "/staff/dashboard", "maya.staff@example.edu"),
        ("admin-dashboard", "/admin/dashboard", "riley.admin@example.edu"),
        ("admin-escalations", "/admin/escalations", "riley.admin@example.edu"),
        ("admin-detail", f"/admin/grievances/{overdue_id}", "riley.admin@example.edu"),
        ("error-403", "/admin/dashboard", "ava.student@example.edu"),
    ]

    written = []
    for name, path, email in pages:
        client = app.test_client()
        if email:
            login(client, email)
        response = client.get(path)
        html = response.get_data(as_text=True)
        html = html.replace("<head>", f'<head>\n<base href="{asset_base}">', 1)
        target = out / f"{name}.html"
        target.write_text(html, encoding="utf-8")
        written.append((name, path, response.status_code, len(html)))

    for name, path, status, size in written:
        print(f"{status}  {size:>7}B  {name:<26} {path}")

    if tmp_db.exists():
        tmp_db.unlink()
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
