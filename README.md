# Resolve — Smart Grievance Management

Resolve is a locally runnable academic MVP for structured student grievance
submission, department assignment, status history, and transparent
deadline-based escalation. It is a Flask server-rendered application backed by
SQLite and SQLAlchemy.

The backend remains the single source of truth for sessions, authorization,
validation, workflows, and data. The frontend is a self-contained design system
built from Jinja components, an inline SVG icon set, five plain CSS files driven
by shared design tokens, self-hosted variable fonts, and one small
progressive-enhancement script. **There is no CSS framework, no JavaScript
bundler, no CDN, and no separate React/Next.js service** — every asset is served
from `grievance_app/static/`, so the interface renders identically offline.

The public root page is a vertically scrollable Resolve landing experience with
hero, problem, solution, feature, workflow, impact, call-to-action, and footer
sections. Its navigation anchors use normal document flow and its primary
actions route into the real authentication and submission flow. Authenticated
users are dispatched directly to their role-specific dashboard.

The escalation rules are demonstration rules for this project, not official
institutional policy. There is no AI and no background scheduler: escalation
checks run only when an administrator invokes the web action or the CLI command.

## Requirements

- Python 3.10 or newer (developed and tested on 3.13.5)
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

Open <http://127.0.0.1:5000/>.

> **macOS note:** port 5000 is also used by the AirPlay Receiver. If startup
> reports `Address already in use`, either disable AirPlay Receiver in
> System Settings or start the server on another port:
> `python -m flask --app run.py run --port 5055`.

The default database is `instance/grievance.db`; it is created automatically as
well as by the explicit initialization script. Startup does not seed or
overwrite existing records.

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

## Frontend architecture

Flask and Jinja are retained deliberately. A separate React/Next.js frontend
would require a parallel JSON API, duplicated session/CSRF/CORS handling, and
authorization mirrored in client code — all of which conflict with keeping the
backend authoritative — for visual quality a hand-authored CSS system already
delivers.

### Stylesheets

Loaded in this order; later files intentionally override earlier ones.

| File | Responsibility |
| --- | --- |
| `static/css/tokens.css` | `@font-face` rules and every design token: colour, type scale, spacing, radii, shadows, motion |
| `static/css/base.css` | Reset, typography, 12-column grid, utilities, forms, tables, buttons, alerts |
| `static/css/shell.css` | Header, navigation, footer; the navy workspace chrome and the light sticky landing header |
| `static/css/landing.css` | Public landing sections and scroll-reveal rules |
| `static/css/app.css` | Authenticated workspaces: metrics, charts, case detail, login, error states |

Together they total roughly 72 KB uncompressed, replacing the previous
Bootstrap 5.3.3 CDN dependency. `designstack.md` asks for custom CSS in "a
static stylesheet"; it is split into five plain files purely for
maintainability — there is still no build step.

### Fonts

Two variable fonts are self-hosted in `static/fonts/` (~75 KB total) and
preloaded: **Inter** for UI text and **Plus Jakarta Sans** for display
headings. Both fall back to the system UI stack. Previously `Inter` was named
in CSS but never loaded, so the interface silently fell back to the system font.

### JavaScript

`static/js/app.js` (~6 KB, no dependencies) adds scroll reveals, metric
count-ups, submit-button loading feedback, dismissible flash messages, table
row stagger, landing scroll-spy, and the responsive navigation toggle. It
honours `prefers-reduced-motion` throughout, and every core action — including
navigation, filtering, and all form submissions — works with JavaScript
disabled.

### Data visualisation

The administrator dashboard renders an SVG donut and department breakdown bars.
Every segment is computed server-side from real database counts by
`reporting_service.queue_summary()`, `status_counts()` and
`department_counts()`. No chart library is used and no figure is hardcoded.

## Backend changes made during the redesign

Deliberately minimal, and covered by tests:

- `services/reporting_service.py`: added `queue_summary()` and
  `department_counts()`, and reimplemented `dashboard_counts()` on top of
  `queue_summary()`. Previously the student dashboard derived its metrics with a
  Jinja `namespace` loop and the staff dashboard summed a dict in the template —
  business logic in templates, which `designstack.md` prohibits. The numbers are
  unchanged; they are now computed in SQL and unit-tested.
- `student/routes.py`, `staff/routes.py`: pass the new `summary` context.
- `admin/routes.py`: pass `department_counts` for the ownership chart.

Models, authentication, sessions, `roles_required`, student-ownership and
staff-scope rules, CSRF protection, server-side validation, reference
generation, status-transition rules, history writes, deadline handling, and the
escalation service (including duplicate prevention) are **unchanged**.

## Tests

The suite creates a separate SQLite database under pytest's temporary
directory for each test application. It never touches `instance/grievance.db`.

```bash
source .venv/bin/activate
pytest -q
```

**Result: 34 passed** (baseline before this work was 17).

| File | Covers |
| --- | --- |
| `test_auth.py` | Login, role guards, landing sections and anchors, required nav destinations, no-CDN policy, styled error pages |
| `test_grievances.py` | Valid creation, unique references, required-field validation, persistence |
| `test_permissions.py` | Student ownership, staff department scope, admin assignment and filtering |
| `test_workflow.py` | Authorized status updates with history, invalid transitions |
| `test_escalation.py` | Overdue escalation, resolved/closed exclusion, duplicate prevention, CLI parity |
| `test_dashboards.py` | `queue_summary` scoping and empty queues, `department_counts`, rendered student metrics, staff filters, donut output, empty-database handling |
| `test_end_to_end.py` | Full submit → assign → progress → resolve lifecycle over HTTP, field errors, idempotent escalation action, escalation panels, CSRF enforcement |

Four landing-copy assertions in `test_auth.py` were updated deliberately,
because the requested hero and section headings are now title case
(`Your Voice. Our Responsibility.`, `How It Works`).

## Verification actually performed

- `pytest -q` — 34 passed.
- Full lifecycle exercised over HTTP in `test_end_to_end.py`: student
  submission, administrator assignment, staff progress and resolution, audit
  trail ordering, and role-specific visibility of workflow controls.
- CSRF confirmed active by asserting a token-less POST is rejected with 400.
- Escalation confirmed idempotent through the admin action; CLI parity covered
  by `test_escalation.py`.
- Visual review of all ten pages rendered by `scripts/render_pages.py` and
  captured with headless Google Chrome at **1440 px**, **900 px** and **600 px**,
  including the open mobile navigation state for both the landing and workspace
  headers. A final live browser pass also checked the landing and authenticated
  workspaces at **375 px**, **600 px**, **768 px**, **1024 px**, and **1440 px**;
  every checked width had no horizontal overflow and both open and closed
  navigation states worked. Three real defects were found and fixed this way:
  the landing header rendering with the navy workspace background (CSS
  source-order conflict), the donut arcs being displaced by a redundant
  `transform-origin`, and the impact panel's decorative orb being promoted into
  the grid flow.
- Confirmed the served HTML contains no `cdn.`, `bootstrap` or Google Fonts
  references, and that the favicon, all five stylesheets, the script, and both
  fonts return HTTP 200.

### Checks not performed

- **Exact 390 px viewport:** a 375 px viewport was inspected, but an exact
  390 px screenshot was not captured. The sub-600 px rules (`575.98px`
  breakpoint) were exercised at 375 px and showed no horizontal overflow.
- **Real-device and cross-browser testing:** only Chromium was used. No Safari,
  Firefox, or physical mobile testing.
- **Automated visual regression:** no screenshot-diff suite is included.
- **Accessibility audit:** semantic landmarks, labels, visible focus rings,
  `aria-live` flash messages, status text that never relies on colour alone, and
  reduced-motion support are implemented, but no automated axe/Lighthouse audit
  or screen-reader pass was run.
- **Load or performance measurement:** no figures are claimed.

## Reference recording

The supplied recording was provided as `references/Screen Recording.mov`
(9.95 s, 60 fps, 3420×1960). It was decoded with `ffmpeg` and sampled at 4 fps
into 40 frames under `references/frames_full/`, all of which were reviewed.

The `references/` directory is design input material rather than part of the
application, so it is git-ignored and not distributed with this repository; it
remains in the local working copy only.

The recording shows a light government-portal layout: a white sticky navigation
bar with a solid pill active state, a navy-to-blue gradient hero with a centred
emblem and letterspaced eyebrow, left-accent tinted callout cards, pastel
icon-tile feature cards, numbered workflow circles, a bright closing
call-to-action band, and a near-black three-column footer.

Resolve adopts that **composition and section rhythm** while keeping its own
midnight-navy/indigo/cyan identity. The reference's Government of India
branding, saffron palette, emblem, contact details, and its
"join thousands of citizens" style claims are deliberately not reproduced.

## Project structure

```text
grievance_app/
├── admin/ auth/ main/ staff/ student/   # thin role-specific blueprints
├── models/                               # SQLAlchemy models
├── services/                             # workflow and reporting rules
├── templates/                            # Jinja pages and components
├── static/css/                           # tokens, base, shell, landing, app
├── static/fonts/                         # self-hosted variable fonts
├── static/js/app.js                      # progressive enhancement
├── config.py extensions.py forms.py
scripts/                                  # schema, seed, and page-render helpers
tests/                                    # isolated pytest coverage
```

`scripts/render_pages.py` writes every page to static HTML against a temporary
seeded database, for visual review without touching the real database:

```bash
python scripts/render_pages.py /tmp/resolve-preview "http://127.0.0.1:5055/"
```

## Documentation conflict worth noting

`designstack.md` §2 asks for "a calm, professional college administration
portal — not a marketing landing page" and to "avoid excessive gradients,
animation"; §6 prohibits React, Vue, Tailwind build tooling, and JS bundlers.
`architecture.md` §1 prohibits separate frontend build systems.

This redesign was explicitly commissioned to add an animated public landing
page, which supersedes §2. The prohibitions on frameworks, bundlers, and a
separate frontend service are **still honoured**. Animation is opt-out via
`prefers-reduced-motion`.

## Current limitations

- Checks are manual or CLI-triggered; no scheduler, email, SMS, or external
  notification integration is included.
- SQLite and the seeded accounts are intended for a small local academic
  demonstration, not production deployment. Production would need managed
  secrets, hardened server configuration, backups, and operational monitoring.
- Public registration, SSO, AI classification, mobile-native clients, and
  external ERP integration are outside this MVP.
- Reopening a closed grievance is not implemented.
