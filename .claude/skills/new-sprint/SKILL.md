---
name: new-sprint
description: Create a new sprint file and automatically run conflict detection across all PRDs in scope. Use when user says "new sprint", "create sprint", or "start a new sprint".
---

# New Sprint

## Process

Note: Read `_system/active-project.md` to get the current project folder name (e.g., my-projects/PROJ-001-ai-alignment).
If this file does not exist, ask the user: "Which project are you working on?"
All file paths below use [ACTIVE_PROJECT] as the project folder name.

1. Read `_system/sprint-calendar.md` to get the next sprint number and dates
2. Run the interview below to collect sprint details from the PM
3. Create `[ACTIVE_PROJECT]/sprints/S[NN]-sprint-[start-date].md` with the sprint content directly (no external template needed)
4. Automatically run the `conflict-check` skill for this sprint
5. Append conflict check results to the sprint file
6. Update `_system/sprint-calendar.md` Current-Sprint field

## Interview

When this skill is triggered, immediately say:

"Let's set up Sprint S[NN]. I need a few details:

1. What is the sprint goal? (one sentence)
2. Which PRDs are in scope for this sprint?
3. Which project(s) does this sprint serve?
4. What is the team capacity in person-weeks?"

Wait for the PM to answer all four questions before proceeding. If any answer is missing, ask for it specifically before creating the file.

## Auto-Conflict Check

After creating the sprint file, run conflict detection immediately without waiting for the PM to ask.
If conflicts are found: present them with resolution suggestions before the PM starts planning work.

## Checklist

- [ ] Sprint ID and dates confirmed from sprint-calendar.md
- [ ] Sprint goal, PRDs in scope, capacity collected from PM
- [ ] Sprint file created at [ACTIVE_PROJECT]/sprints/S[NN]-sprint-[start-date].md
- [ ] Conflict check run automatically
- [ ] Results appended to sprint file
- [ ] _system/sprint-calendar.md updated
