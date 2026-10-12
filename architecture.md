# System Architecture

## Smart Grievance Redressal & Escalation System

## 1. Overview

Use a modular Flask monolith with three logical layers: 1. Presentation:
Jinja templates, HTML, CSS, Bootstrap. 2. Application: Flask
routes/blueprints, authorization, validation, workflow services. 3.
Persistence: SQLAlchemy models backed by SQLite.

Avoid microservices, message brokers, and separate frontend build
systems unless requirements change.

## 2. Components

-   **Auth routes:** login/logout.
-   **Student routes:** dashboard, submission, own-case detail.
-   **Staff routes:** assigned cases, progress notes, status changes.
-   **Admin routes:** assignment, filters, dashboard, escalation
    history, manual checker.
-   **Grievance service:** creation, reference IDs, assignment,
    validated status transitions.
-   **Escalation service:** deadline check, next-level policy,
    idempotent event creation.
-   **Reporting service:** dashboard counts and filtered queries.
-   **Persistence:** SQLAlchemy models and transaction boundaries.

Routes should remain thin and call testable service functions.

## 3. Request flow

``` text
Browser
  -> Flask route
  -> Authentication / role / ownership checks
  -> Input validation
  -> Application service and workflow rules
  -> SQLAlchemy ORM
  -> SQLite
  -> Response rendered to browser
```

## 4. Suggested project layout

``` text
smart-grievance-system/
├── AGENTS.md
├── README.md
├── requirements.txt
├── .gitignore
├── run.py
├── grievance_app/
│   ├── __init__.py
│   ├── config.py
│   ├── extensions.py
│   ├── models/
│   ├── services/
│   │   ├── grievance_service.py
│   │   ├── escalation_service.py
│   │   └── reporting_service.py
│   ├── auth/
│   ├── student/
│   ├── staff/
│   ├── admin/
│   ├── templates/
│   └── static/
├── scripts/
│   ├── init_db.py
│   └── seed_demo.py
└── tests/
    ├── conftest.py
    ├── test_auth.py
    ├── test_grievances.py
    ├── test_permissions.py
    └── test_escalation.py
```

Simplify if appropriate, but keep responsibilities separated and
testable.

## 5. Data model

### User

`id`, `name`, unique `email`, `password_hash`, `role`, optional
`department_id`, `created_at`.

### Department

`id`, unique `name`, optional description.

### Grievance

`id`, unique `reference_id`, `student_id`, nullable `department_id`,
nullable `assigned_staff_id`, `title`, `category`, `description`,
optional `location`, `priority`, `status`, `created_at`, `updated_at`,
`deadline_at`, optional `resolved_at`.

### GrievanceHistory

`id`, `grievance_id`, `actor_user_id`, nullable `old_status`,
`new_status`, optional `remarks`, `created_at`.

### Escalation

`id`, `grievance_id`, `level`, `reason`, source/destination authority or
equivalent, `created_at`, optional `action_status`. Add a unique
constraint on `(grievance_id, level)` for one event per level.

Relationships: one student to many grievances; one department to many
grievances; one grievance to many history entries and escalation events.
Add indexes for status, department, deadline, and reference ID where
useful.

Use consistent timezone handling, preferably UTC internally.

## 6. Grievance status and update transaction

Baseline states: `SUBMITTED`, `ASSIGNED`, `IN_PROGRESS`, `ESCALATED`,
`RESOLVED`, `CLOSED`. Centralize allowed transitions. For every
update: 1. Verify actor role and case scope. 2. Validate the transition.
3. Update the grievance. 4. Insert the history entry. 5. Commit the
related changes together.

## 7. Escalation workflow

1.  Query cases whose deadline has passed.
2.  Exclude resolved/closed cases.
3.  Determine the next level using a small explicit policy function.
4.  Check whether that level already exists.
5.  Create the event and any intended status update transactionally.
6.  Return counts for examined, escalated, skipped, and failed cases.

Provide an admin-protected POST action and CLI command that call the
same service. Without a scheduler, do not claim background or continuous
monitoring.

## 8. Security

Use Flask-Login, Werkzeug password hashing, CSRF protection, server-side
role/ownership checks, ORM/parameterized queries, input validation, safe
error pages, and environment-based secrets where practical. Never seed
real personal data or commit secrets.

## 9. Error handling

Handle invalid forms, unknown IDs, forbidden actions, invalid
transitions, and database exceptions. Roll back related changes on
failure. Duplicate escalation prevention must exist both in service
logic and as a database constraint.

## 10. Testing

Use pytest with an isolated temporary database and Flask test client.
Cover auth, ownership, staff scope, creation, status history, invalid
transitions, overdue escalation, duplicate prevention, and persistence.

## 11. Decisions

-   Flask server-rendered pages keep setup small.
-   SQLite simplifies local development.
-   SQLAlchemy clarifies relationships and transactions.
-   Rule-based escalation is transparent and testable.
-   Separate history/event tables preserve accountability.
