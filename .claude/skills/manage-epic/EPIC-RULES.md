# Epic Rules Reference

## AC Quality Standard

Every Acceptance Criterion scenario MUST have all 3 parts.

### Given
Describes the state of the system BEFORE the action.
- Be specific: "Given the user is logged in as a Tenant Admin"
- Not vague: "Given the user is in the system"
- Include relevant data: "Given there are 3 existing keyword policies"

### When
Describes the action that triggers the behavior.
- One action per scenario: "When the user clicks Save"
- Not multiple actions: "When the user fills the form and clicks Save and confirms"

### Then
Describes the OBSERVABLE outcome. Must be testable by QA.
- Specific: "Then the system displays 'Policy saved successfully' in the top banner"
- Not vague: "Then the system works correctly"
- Not implementation: "Then the database record is created" (QA cannot see DB)
- Includes data: "Then the policy list shows 4 entries, with the new policy at the top"

### And
Optional additional outcomes after Then.
- "And an email is sent to all reviewers"
- "And the audit log records the action with user ID and timestamp"

---

## Minimum AC Scenarios Per User Story

| Scenario Type | Required | Example |
|--------------|----------|---------|
| Happy path | Yes (1+) | Normal successful flow |
| Edge case | Yes (1+) | Boundary conditions, empty states, large data |
| Error / negative | Yes (1+) | Invalid input, permission denied, system error |
| Permission | If applicable | Different roles see different behavior |
| Concurrency | If applicable | Two users doing the same action simultaneously |

---

## Epic Change Types

| Type | When to Use | Version Bump |
|------|------------|-------------|
| `ac-update` | Rewording AC, adding/removing a scenario | Minor |
| `story-add` | Adding a new User Story to the Epic | Minor |
| `story-remove` | Removing a User Story (requires written rationale) | Minor |
| `scope-change` | Changing what the Epic does or does not cover | Major |
| `technical-change` | API contract change, schema change, module change | Minor or Major |
| `bug-in-spec` | Correcting an error in the original specification | Patch |

---

## Story Points Guide

| Points | Complexity | Description |
|--------|-----------|-------------|
| 1 | Trivial | Config change, copy text, simple UI field |
| 2 | Simple | CRUD operation with straightforward UI |
| 3 | Small | Feature with 2-3 AC scenarios, minor backend logic |
| 5 | Medium | Feature with multiple AC scenarios, moderate backend |
| 8 | Large | Complex feature, multiple components, integration needed |
| 13 | Very large | Should be split into smaller stories |

Stories above 8 points should be split before sprint planning.

---

## Status Rules by Epic Status

| Epic Status | Can edit file? | Can add US? | Can change AC? |
|------------|---------------|-------------|----------------|
| draft | Yes | Yes | Yes |
| in-review | No | No - create new version | No - create new version |
| approved | No | No - create new version | No - create new version |
| rejected | No - create new version | No - create new version | No - create new version |
| archived | No | No | No |

---

## Epic vs PRD vs User Story

| Level | Document | Granularity | AC Format |
|-------|----------|------------|-----------|
| Strategic | PRD | Modules and Epics overview | Not detailed |
| Tactical | Epic | Full User Stories | Given/When/Then per scenario |
| Task | User Story (in Epic) | Single behavior | Given/When/Then (3+ scenarios) |
| Execution | Sprint | Tasks for devs | Checklist |
