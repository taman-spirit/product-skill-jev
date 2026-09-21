---
name: intake-cr
description: Create a new Change Request for a signed-off PRD through an interview. Claude asks what needs to change and why, then builds the CR automatically. Use when user says "create CR", "new change request", "raise a change", or a stakeholder requests a scope change after PRD sign-off.
---

# CR Intake

All post-sign-off changes to a PRD must go through a CR. No direct edits to an approved PRD.

## Interview Flow

When triggered, immediately ask:

```
What needs to change and why? Describe the change in your own words -
which PRD it affects, what the stakeholder is asking for, and why it matters now.
```

From the description, extract:
- Which PRD is affected (and version if mentioned)
- Who is requesting the change
- Nature of the change (scope / bug-in-spec / compliance / UX)
- Urgency signals ("urgent", "blocking", "nice to have")

Then ask only for what is missing:

```
A few quick details to complete the CR:

1. Who is requesting this change? (name and role)
2. How urgent is this?
   - Critical: blocking launch or legal risk
   - High: significant user impact, should fix this sprint
   - Medium: important but not blocking
   - Low: improvement, can wait
```

## Process

Note: Read `_system/active-project.md` to get the current project folder name (e.g., my-projects/PROJ-001-ai-alignment).
If this file does not exist, ask the user: "Which project are you working on?"
All file paths below use [ACTIVE_PROJECT] as the project folder name.

1. Read `[ACTIVE_PROJECT]/cr/cr-log.md` to get the next CR number
2. Run the interview above - extract from description, ask only gaps
3. Classify the change type:
   - `scope-change` - adds or removes functionality
   - `bug-in-spec` - corrects an error in the PRD logic or flow
   - `policy-compliance` - required by law or internal policy
   - `stakeholder-request` - business or UX change request
4. Show the full CR draft and wait for PM confirmation:

```
CR-NNN draft:

Title: [short title]
PRD: PRD-NNN v[X.Y]
Requested by: [Name], [Role]
Type: [change type]
Urgency: [level]

Description:
[what is changing]

Business justification:
[why this change is needed now]

Confirm to create, or adjust any field?
```

5. Write to `[ACTIVE_PROJECT]/cr/intake/CR-NNN-[slug].md`
6. Add entry to `[ACTIVE_PROJECT]/cr/cr-log.md` with status: intake
7. Ask: "CR-NNN created. Shall I run the impact assessment now?"

## Checklist

- [ ] Next CR-ID confirmed from cr-log.md
- [ ] Change described and type classified
- [ ] Linked PRD and version confirmed
- [ ] Urgency set
- [ ] Draft shown and PM confirmed
- [ ] CR file written to [ACTIVE_PROJECT]/cr/intake/
- [ ] [ACTIVE_PROJECT]/cr/cr-log.md updated
