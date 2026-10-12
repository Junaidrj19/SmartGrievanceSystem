# Product Requirements Document (PRD)

## Smart Grievance Redressal & Escalation System

**Status:** MVP specification\
**Product:** Local-first web application for an academic project\
**Users:** Students/complainants, department staff, administrators

## 1. Overview and problem

The system centralizes grievance submission, assignment, status
tracking, deadline checking, and escalation history. Informal messages
or disconnected registers can make ownership, progress, and overdue
complaints difficult to track. The MVP's "smart" behaviour means
transparent workflow automation---not AI.

## 2. Goals

-   Structured grievance submission and unique reference IDs.
-   Role-appropriate case access and status visibility.
-   Department/staff assignment.
-   Chronological status history.
-   Deadline-based escalation for unresolved cases.
-   Duplicate escalation prevention.
-   Admin filtering and useful summary counts.
-   Tested, maintainable local application.

## 3. Non-goals

No AI/LLM classification, sentiment analysis, external messaging
gateways, ERP/SSO integration, mobile-native app, multi-tenant SaaS, or
production-scale infrastructure. These are future enhancements only.

## 4. Roles and permissions

### Student

Can submit grievances and view only their own cases, including reference
ID, status, deadline, permitted remarks, and history. Cannot assign
cases or perform administrative actions.

### Staff

Can view cases assigned to them or their department, add progress
remarks, and perform permitted status transitions. Cannot access cases
outside their scope or edit audit history.

### Admin

Can view/filter all cases, assign departments/staff, review overdue
cases and escalation history, run the escalation checker, and view
summary counts. All permissions must be enforced server-side.

## 5. Functional requirements

  -----------------------------------------------------------------------
  ID                                  Requirement
  ----------------------------------- -----------------------------------
  FR-01                               Accept a grievance with title,
                                      category, and description.

  FR-02                               Generate a unique, human-readable
                                      reference ID.

  FR-03                               Persist records using SQLAlchemy
                                      and SQLite.

  FR-04                               Restrict students to their own
                                      grievances.

  FR-05                               Allow admins to assign departments
                                      and optionally staff.

  FR-06                               Validate status transitions for
                                      authorized staff/admins.

  FR-07                               Record old/new status, actor,
                                      timestamp, and remarks.

  FR-08                               Store a deadline for each
                                      grievance.

  FR-09                               Find overdue grievances that remain
                                      unresolved.

  FR-10                               Record escalation level, reason,
                                      timestamp, and destination.

  FR-11                               Prevent duplicate events for the
                                      same grievance and level.

  FR-12                               Never escalate resolved or closed
                                      grievances.

  FR-13                               Provide an admin action and CLI
                                      command for escalation checks.

  FR-14                               Filter by status, category,
                                      department, and overdue state.

  FR-15                               Show total, open, resolved, and
                                      overdue counts.

  FR-16                               Handle invalid inputs, missing
                                      records, and unauthorized actions
                                      safely.

  FR-17                               Seed fictional demo accounts and
                                      sample grievances.

  FR-18                               Provide automated tests for
                                      critical workflows and permissions.
  -----------------------------------------------------------------------

## 6. Status model

Suggested states: `SUBMITTED`, `ASSIGNED`, `IN_PROGRESS`, `ESCALATED`,
`RESOLVED`, `CLOSED`.

Centralize allowed transitions. Suggested flow: Submitted → Assigned →
In Progress → Escalated or Resolved → Closed. A case may resolve from In
Progress or Escalated. Reopening is outside the MVP unless explicitly
implemented and tested.

Escalation events must be stored separately from current status so the
audit trail remains available.

## 7. Escalation policy

Use explicit configurable demonstration rules; do not describe them as
official policy. The checker must select overdue unresolved cases,
determine the next level, create a record transactionally, and avoid
duplicate events. Resolved/closed cases are ineligible. Expose the same
service through an admin-protected POST action and CLI command.

A background scheduler is optional. If none is implemented, state that
checks occur only when the admin action or CLI command runs.

## 8. Non-functional requirements

-   Usability: clear labels, status text, validation messages,
    responsive pages.
-   Security: hashed passwords, server-side authorization, CSRF
    protection.
-   Integrity: relational constraints and transactional
    history/escalation updates.
-   Maintainability: separate routes, services, models, templates, and
    tests.
-   Reliability: repeated checks do not duplicate escalation events.
-   Privacy: fictional seed data and role-limited access.
-   Performance: appropriate for a small local demonstration; no
    unmeasured performance claims.

## 9. Required screens

Login; student dashboard; new grievance form; grievance detail/history;
staff assigned-case dashboard; admin dashboard and filters;
assignment/status forms; overdue cases and escalation history.

## 10. Acceptance criteria

-   Fresh setup initializes the database and starts the app.
-   Demo users can sign in with role-appropriate access.
-   Student submission generates a reference ID.
-   Students cannot access other students' grievances by changing a URL.
-   Authorized staff status changes create history.
-   Admin can assign and filter cases.
-   Overdue unresolved cases escalate when the checker runs.
-   Resolved/closed cases do not escalate.
-   Repeated checks do not duplicate events at the same level.
-   Critical tests are run and actual results documented.
-   README documents setup, demo credentials, tests, and limitations.

## 11. Success and demo data

Success means passing acceptance tests and completing a coherent
end-to-end demonstration. Use fictional names, email addresses,
departments, and grievance descriptions. Do not invent test results,
performance metrics, or user satisfaction statistics.
