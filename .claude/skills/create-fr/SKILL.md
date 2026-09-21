---
name: create-fr
description: Create a new Feature Request document in the active project. Use when user says "create feature request", "add feature", "new feature idea", "capture idea", or describes something they want to build.
---

# Create Feature Request

## Before Starting

Read `_system/active-project.md` to get the active project path (e.g. my-projects/PROJ-001-ai-alignment).
If the file does not exist, ask: "Which project is this feature request for?"

## Interview

When user says "create feature request" or describes a feature, ask:

```
Got it - capturing this as a feature request.

A few quick questions:
1. Who is asking for this? (user feedback / internal team / data insight / stakeholder)
2. What problem does it solve? (one sentence - the "why")
3. Who are the users affected?
```

Extract anything already mentioned by the user before asking.

## Process

1. Read `_system/active-project.md` -> get [ACTIVE_PROJECT]
2. List files in `[ACTIVE_PROJECT]/discovery/inbox/` to get next FR number
3. Create slug from feature name (lowercase, hyphens)
4. Write `[ACTIVE_PROJECT]/discovery/inbox/FR-NNN-[slug].md`:

```markdown
---
fr-id: FR-NNN
project: PROJ-NNN
title: [Feature name]
status: draft
source: user-feedback | internal | data | stakeholder
requested-by: [Name or team]
created: DD/MM/YYYY
rice-score: not scored
gate-status: not reviewed
linked-prd: -
---

# FR-NNN - [Feature Name]

## Problem Statement
[What problem does this solve? From the user's perspective.]

## Users Affected
[Who experiences this problem? How many?]

## Current Situation
[What do users do today without this feature?]

## Requested Solution
[What the requester is asking for - in their own words]

## Source
[Where did this request come from? Link to ticket/email/NPS if available]

## Notes
[Any additional context]
```

5. Confirm:
```
Feature request created: FR-NNN - [Title]
File: [ACTIVE_PROJECT]/discovery/inbox/FR-NNN-[slug].md
Status: draft

---
What to do next:
- "Score FR-NNN with RICE" - calculate priority score (takes 2 minutes)
- "Create feature request for [another feature]" - capture more ideas
- "Show all projects" - go back to project overview
```

## Checklist

- [ ] Active project confirmed
- [ ] FR-ID confirmed from inbox/ folder count
- [ ] Problem statement written (not just the solution)
- [ ] File written to [ACTIVE_PROJECT]/discovery/inbox/
- [ ] Next steps shown
