---
name: project-status
description: Open a project, show a comprehensive status dashboard with evaluation and suggested next steps. Use when user says "open project PROJ-NNN", "status of [project name]", "work on [project]", "what's the status of [project]", or "summary of [project]".
---

# Project Status

## Step 1 - Find the Project Folder

The project folder is inside my-projects/, named PROJ-NNN-[slug].
Use list_files("my-projects") to see all projects, then identify the right one.
If the user said a project name (not ID), match it to the closest folder name.

## Step 2 - Read All Documents

Read these files from inside the project folder:
- PROJECT.md - project definition, milestones, risks, team
- VERSIONS.md - document status registry
- discovery/gate/approved.md - approved feature requests
- discovery/gate/rejected.md - rejected features
- discovery/inbox/ - list all FR files (count them)
- prd/ - list all PRD folders (count and check versions)
- cr/ - list cr-log.md for open CRs

## Step 3 - Generate Dashboard

Output a clear, structured summary:

```
PROJECT: PROJ-NNN - [Project Name]
[Product] | Priority: P[N] | PM: [Name]
Timeline: [Start] to [Target End] | Status: [status]

--- Progress ---

Discovery
  Feature Requests: [X] captured, [Y] gate-approved, [Z] rejected
  Research docs:    [X] complete

PRDs
  [X] PRDs total
  - PRD-001 - [Title]: v1.1, approved
  - PRD-002 - [Title]: v1.0, draft
  - PRD-003 - [Title]: not started

Epics
  [X] epics across all PRDs
  - [X] approved, [Y] in draft, [Z] not started

Change Requests
  [X] open, [Y] approved this month

Milestones
  M1 - Discovery complete:    [Done / In Progress / Pending]
  M2 - PRDs signed off:       [Done / In Progress / Pending]
  M3 - Design signed off:     [Done / In Progress / Pending]
  M4 - Development complete:  [Done / In Progress / Pending]
  M5 - Launch:                [Done / In Progress / Pending]

Open Risks
  [List risks from PROJECT.md risks table, if any]
```

## Step 4 - Evaluate and Suggest Next Steps

After the dashboard, evaluate the project health and give specific recommendations.
Be direct and concrete - tell the PM exactly what to do next.

```
--- What to do next ---

[Evaluation sentence: e.g. "Your project has 3 feature requests but none have been scored yet."]

Priority actions:
1. "[Exact command]" - [why this is the most important thing to do now]
2. "[Exact command]" - [second priority]
3. "[Exact command]" - [third priority]
```

Evaluation logic:
- No FRs exist -> priority: create feature requests first
- FRs exist but no RICE scores -> priority: score them
- RICE scored but gate not run -> priority: run gate review
- Gate approved but no PRD -> priority: create PRD
- PRD exists but no epics -> priority: create epics
- Epics exist but PRD not grilled -> priority: grill PRD before stakeholder review
- PRD in draft too long -> flag: consider submitting for review
- Open CRs not assessed -> flag: assess pending change requests
- Risks with no mitigation owner -> flag: assign risk owners
- All milestones green -> congratulate and suggest launch prep

## Step 5 - Set Active Project Context

After showing the dashboard, remember this as the active project for the session.
For any new document created in this session, automatically ask: "Link this to PROJ-NNN?"

Write the FULL relative path to `_system/active-project.md`:
```
my-projects/PROJ-NNN-[slug]
```
This allows all other skills (score-feature, to-prd, cr intake, etc.) to know
which project folder to read from and write to without asking every time.
