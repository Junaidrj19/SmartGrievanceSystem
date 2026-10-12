# Design Stack and UI Guidelines

## Smart Grievance Redressal & Escalation System

## 1. Stack

  -----------------------------------------------------------------------
  Area                    Choice                  Purpose
  ----------------------- ----------------------- -----------------------
  Language                Python 3                Backend and tests

  Web framework           Flask                   Routes and
                                                  server-rendered app

  Templates               Jinja                   HTML rendering

  UI                      Bootstrap 5, HTML, CSS  Responsive interface

  Database                SQLite                  Local relational
                                                  storage

  ORM                     Flask-SQLAlchemy /      Models, relationships,
                          SQLAlchemy              transactions

  Authentication          Flask-Login             Session management

  Password hashing        Werkzeug security       Store password hashes
                          utilities               

  CSRF                    Flask-WTF or maintained Protect state-changing
                          equivalent              forms

  Testing                 pytest                  Unit and integration
                                                  tests

  Version control         Git                     Change history
  -----------------------------------------------------------------------

Choose mutually compatible maintained versions. Pin dependencies in
`requirements.txt` after resolving and testing the environment.

## 2. Visual direction

Build a calm, professional college administration portal---not a
marketing landing page. Use clear hierarchy, consistent spacing,
readable typography, responsive tables, visible focus states, and useful
empty states. Avoid excessive gradients, animation, and decorative
metrics.

Suggested design tokens:

``` css
:root {
  --color-primary: #1f4e79;
  --color-primary-hover: #163b5c;
  --color-accent: #2a9d8f;
  --color-background: #f5f7fa;
  --color-surface: #ffffff;
  --color-text: #1f2937;
  --color-muted: #64748b;
  --color-border: #dbe3ec;
  --color-danger: #b42318;
  --color-warning: #a15c00;
  --color-success: #18794e;
  --radius-card: 12px;
}
```

These are starting values; maintain contrast and keyboard accessibility.

## 3. Shared layout

-   Product label: "Grievance Portal".
-   Show signed-in user's name and role.
-   Render role-appropriate navigation, while still enforcing
    permissions server-side.
-   Use shared template inheritance.
-   Provide success/error feedback after actions.
-   Use readable text with all status badges; never rely on color alone.

Suggested status labels: Submitted (neutral/blue), Assigned (blue), In
Progress (amber), Escalated (red/warning), Resolved (green), Closed
(muted).

## 4. Required screens

### Login

Email/password form, clear errors, no plaintext credentials. Public
self-registration is not required; use seeded demo accounts.

### Student dashboard

Primary "Submit grievance" action and table of the student's own cases:
reference ID, title, category, date, status, last updated.

### New grievance form

Title, category, description, optional location. Label required fields
and show validation errors. On success, display the reference ID
clearly.

### Grievance detail

Reference ID, current status, category, created time, deadline,
department, assigned staff, description, permitted remarks,
chronological history, and escalation events.

### Staff dashboard

Only cases within authorized scope, filters by status/overdue state, and
a route to update status and remarks.

### Admin dashboard

Real counts for total/open/resolved/overdue cases, filters by
status/category/department/overdue, assignment controls, escalation
history, and a confirmed "Check overdue grievances" action. Show the
actual checker summary.

## 5. Accessibility and interaction

-   Associate labels with inputs.
-   Support keyboard navigation and visible focus.
-   Use semantic headings and sufficient contrast.
-   Use POST for mutations, never GET.
-   Enable CSRF protection.
-   Keep core actions functional without JavaScript.
-   Do not provide placeholder buttons or fake dashboard counts.
-   Avoid deletion of grievance/audit records in the MVP.

## 6. Implementation constraints

-   Keep custom CSS in a static stylesheet.
-   Use Jinja template inheritance with a shared base template.
-   Avoid business logic in templates.
-   Do not add React, Vue, Tailwind build tooling, or a JS bundler
    unless scope changes.
-   A CDN may be used for Bootstrap if documented; consider local assets
    if offline operation matters.
-   Use fictional names, emails, departments, and grievance examples
    only.
-   Demo credentials must be marked development-only.
-   Never label a mockup as a working application screenshot.

## 7. Final UI checklist

-   [ ] Consistent navigation, spacing, typography, and buttons.
-   [ ] All required screens connect to backend behaviour.
-   [ ] Success/error messages and empty states work.
-   [ ] Responsive at desktop and narrow widths.
-   [ ] Status text is clear without color.
-   [ ] No fake metrics, placeholder actions, secrets, or real personal
    data.
