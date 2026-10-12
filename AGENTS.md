# Agent Instructions --- Smart Grievance Redressal & Escalation System

## Mission

Build a complete, locally runnable academic MVP. Inspect the workspace,
implement the app, run it, test it, fix failures, and document what was
actually verified. Do not stop after planning or generating code.

## Source of truth

-   `prd.md`: scope, roles, requirements, acceptance criteria.
-   `architecture.md`: components, data model, workflows, security
    boundaries.
-   `designstack.md`: technology and UI conventions.
-   This file: execution and quality rules.

If documents conflict, identify the conflict instead of silently
inventing scope. Prefer specific product requirements unless they
conflict with security or correctness.

## Execution rules

1.  Inspect the workspace before editing. Preserve useful work and do
    not overwrite unrelated files.
2.  Make a brief plan, then proceed autonomously for routine decisions.
3.  Build the smallest complete solution that meets the PRD acceptance
    criteria.
4.  Use a modular Flask application; keep routes thin and business logic
    in services.
5.  Use fictional seed data only.
6.  Do not add AI APIs, paid services, cloud infrastructure, or
    microservices.
7.  Do not claim a feature or test was verified unless it was actually
    checked.
8.  If blocked, state the exact blocker and continue with other feasible
    checks.

## Required functionality

-   Student, Staff, and Admin roles.
-   Login/logout and server-side authorization.
-   Student grievance submission and own-case tracking.
-   Staff access to assigned cases and authorized status updates.
-   Admin assignment, filtering, dashboard counts, and escalation
    history.
-   Unique grievance reference IDs.
-   Status history with actor, timestamp, and remarks.
-   Configurable deadline-based escalation.
-   Idempotent escalation checker available through an admin action and
    CLI.
-   Database initialization, fictional demo data, tests, and README.

## Security and correctness

-   Hash passwords; never store plaintext passwords.
-   Enforce roles and record ownership on the server.
-   Restrict staff to their assigned cases or department.
-   Protect state-changing forms against CSRF.
-   Use SQLAlchemy or parameterized queries.
-   Validate inputs and reasonable field lengths.
-   Do not expose tracebacks, secrets, or internal exceptions to users.
-   Resolved/closed grievances must not be escalated.
-   Repeated checks must not duplicate an escalation at the same level.
-   Use transactions when changing state and writing history together.
-   Keep secrets out of source control.

## Tests to implement and run

1.  Valid grievance creation and unique reference ID.
2.  Required-field validation.
3.  Student ownership boundaries.
4.  Staff assignment boundaries.
5.  Authorized status update and history entry.
6.  Invalid status transition.
7.  Overdue unresolved grievance escalation.
8.  No escalation for resolved/closed grievances.
9.  No duplicate event when checker runs twice.
10. Persistence of grievance and history.

Use an isolated test database. Fix failures and rerun relevant tests.

## Definition of done

-   Fresh local setup instructions work.
-   Database initialization and demo seeding work.
-   App starts locally and demo accounts can sign in.
-   Core grievance lifecycle works.
-   Escalation can be invoked and tested.
-   Test results are real and documented.
-   README includes setup, credentials, tests, and limitations.
-   No mockup or planned feature is described as implemented.

## Final response

Summarize implemented features, files changed, exact commands,
development-only demo credentials, tests actually run, checks not
performed, and remaining limitations.
