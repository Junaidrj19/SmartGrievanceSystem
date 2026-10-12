# Resolve — Smart Grievance Management

Resolve is a locally runnable academic MVP for structured student
grievance submission, department assignment, status history, and transparent
deadline-based escalation. It is a Flask server-rendered application backed by
SQLite and SQLAlchemy.

The interface uses a premium Resolve product shell while retaining the
lightweight Flask/Jinja architecture: the backend remains the source of truth
for sessions, authorization, validation, workflows, and data. The frontend
uses reusable Jinja components, an inline SVG icon set, centralized CSS design
tokens, and a small progressive-enhancement script for staggered reveals,
count-up metrics, loading feedback, and reduced-motion support. No separate
React/Next.js service is required.

The public root page is a vertically scrollable Resolve landing experience with
hero, problem, solution, feature, workflow, impact, CTA, and footer sections.
Its navigation anchors use normal document flow and its primary actions route
to the real authentication/submission flow. Authenticated users continue to be
dispatched directly to their role-specific dashboard.

The escalation rules are demonstration rules for this project, not official
institutional policy. There is no AI or background scheduler: escalation checks
run only when an administrator invokes the web action or when the CLI command
is run.

## Requirements

- Python 3.10 or newer
- A local shell with permission to create a virtual environment

## Fresh local setup

Run these commands from the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
export SECRET_KEY='replace-this-with-a-local-development-secret'
python scripts/init_db.py
python scripts/seed_demo.py
python run.py
```

Open <http://127.0.0.1:5000/>. The application is branded **Resolve**; the
underlying local database remains the same. The default database is
`instance/grievance.db`; it is created automatically as well as by the
explicit initialization script. Startup does not seed or overwrite existing
records.

For Windows PowerShell, use `$env:SECRET_KEY = "replace-this-with-a-local-development-secret"`
instead of the `export` command.

## Development-only demo accounts

Every seeded account uses the development-only password `DemoPass123!`.
These fictional credentials must not be reused outside local development.

| Role | Email |
| --- | --- |
| Student | `ava.student@example.edu` |
| Student | `liam.student@example.edu` |
| Staff · Campus Facilities | `maya.staff@example.edu` |
| Staff · Academic Affairs | `noah.staff@example.edu` |
| Administrator | `riley.admin@example.edu` |

Passwords are stored as Werkzeug password hashes. The seed script is
idempotent for the named demo records and creates fictional sample cases.

## Workflow demonstration

1. Sign in as Ava and submit a grievance. The portal creates a unique
   `GRV-YYYY-XXXXXXXX` reference, a response deadline, and an initial history
   event.
2. Sign in as Riley, open the administrative dashboard, assign the case to a
   department and optional staff member, and review the assignment history.
3. Sign in as the assigned staff member to move the case through permitted
   transitions and add remarks. Staff only see cases assigned to them or their
   department.
4. As an administrator, use **Check overdue grievances** to record an event
   for each overdue unresolved case. The same service is available from the
   command line:

```bash
flask --app run.py check-escalations
```

The checker records one event per grievance and escalation level, updates an
open case to `ESCALATED` at the first level, and does not escalate `RESOLVED`
or `CLOSED` cases. Repeating a check immediately skips the current level. The
next level becomes eligible after the configured demonstration interval.

## Configuration

The following environment variables are supported:

- `SECRET_KEY`: Flask session and CSRF secret; set a private value locally.
- `DATABASE_URL`: SQLAlchemy URL. The default is `sqlite:///grievance.db`
  under Flask's `instance/` directory.
- `DEFAULT_DEADLINE_HOURS`: default response deadline for newly submitted
  cases; default `72`.
- `ESCALATION_LEVEL_INTERVAL_HOURS`: minimum interval before the next
  escalation level; default `72`.
- `ESCALATION_MAX_LEVEL`: maximum event level; default `3`.

The destination labels for levels 1–3 are defined in
`grievance_app/config.py` as fictional demonstration authorities.

## Tests

The test suite creates a separate SQLite database under pytest's temporary
directory for each test application. It does not use `instance/grievance.db`.

```bash
source .venv/bin/activate
pytest -q
```

The tests cover valid creation and unique references, required fields,
student ownership, staff scope, authorized updates and history, invalid
transitions, persistence, overdue escalation, resolved/closed exclusions, and
duplicate prevention.

## Project structure

```text
grievance_app/
├── admin/ auth/ main/ staff/ student/   # thin role-specific blueprints
├── models/                               # SQLAlchemy models
├── services/                             # workflow and reporting rules
├── templates/ static/                    # Resolve Jinja UI, CSS, and JS
├── config.py extensions.py forms.py
scripts/                                  # schema and fictional seed commands
tests/                                    # isolated pytest coverage
```

The reference recording is stored at `references/Screen Recording.mov`.
Representative frames extracted with OpenCV during implementation are stored
under `references/frames/` for visual review.

## Current limitations

- Checks are manual or CLI-triggered; no scheduler, email, SMS, or external
  notification integration is included.
- Bootstrap is loaded from a CDN for the small local UI, so styling requires
  network access unless the link is replaced with a local asset.
- Browser-based screenshot comparison was not added to the project. The
  interface has responsive CSS breakpoints, horizontally scrollable data
  tables, responsive navigation, smooth section anchors, and
  `prefers-reduced-motion` handling, but a full automated visual regression
  suite is outside this MVP.
- SQLite and the seeded accounts are intended for a small local academic
  demonstration, not production deployment. Production deployment would need
  managed secrets, hardened server configuration, backups, and operational
  monitoring.
- Public registration, SSO, AI classification, mobile-native clients, and
  external ERP integration are outside this MVP.
