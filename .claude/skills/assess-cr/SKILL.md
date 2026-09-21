---
name: assess-cr
description: Run a full impact assessment on a Change Request - scope delta, timeline, collateral PRD risk, and technical risk. Use when user says "assess CR-NNN", "evaluate CR", "impact assessment", or wants to understand the consequences of a change before sending to the approval board.
---

# Assess CR

## Process

Note: Read `_system/active-project.md` to get the current project folder name (e.g., my-projects/PROJ-001-ai-alignment).
If this file does not exist, ask the user: "Which project are you working on?"
All file paths below use [ACTIVE_PROJECT] as the project folder name.

1. Read `[ACTIVE_PROJECT]/cr/intake/CR-NNN-[slug].md`
2. Read the linked PRD (latest version) from [ACTIVE_PROJECT]/prd/
3. Read all active PRDs sharing the same tags (check collateral risk)
4. Run the assessment and fill in the Impact Assessment section:

**Scope Delta**

| Dimension | Change |
|-----------|--------|
| Story points | +/- [N] points |
| Timeline | +/- [N] days |
| Additional resource | [N] person-days |

**Collateral PRD Risk**

For each PRD sharing the same module tags:
- Does this CR create a new tag conflict in the current sprint?
- Does it change a shared interface or data schema?

**Technical Risk**

| Level | Criteria |
|-------|---------|
| Low | Minor change, no architecture impact, straightforward to implement |
| Medium | Requires refactor in one module, minor regression risk |
| High | Architecture change, needs a spike or prototype before committing |

**Recommendation**

State clearly: Approve / Reject / Defer - with specific rationale.

5. Move CR file from `[ACTIVE_PROJECT]/cr/intake/` to `[ACTIVE_PROJECT]/cr/assessment/`
6. Update `[ACTIVE_PROJECT]/cr/cr-log.md` status to `assessment`
7. Output summary to PM:

```
Assessment complete: CR-NNN

Scope delta: [+/- N points, +/- N days]
Collateral risk: [none / PRD-X affected]
Technical risk: [Low / Medium / High]

Recommendation: [Approve / Reject / Defer]
Reason: [specific rationale]

File moved to: [ACTIVE_PROJECT]/cr/assessment/
Next: "Move CR-NNN to approval board" when ready for sign-off
```

## Checklist

- [ ] CR file, linked PRD, and related PRDs read
- [ ] Scope delta estimated (points and timeline)
- [ ] Collateral PRD risk checked against tags-registry
- [ ] Technical risk level set with rationale
- [ ] Clear recommendation stated (Approve / Reject / Defer)
- [ ] File moved to [ACTIVE_PROJECT]/cr/assessment/
- [ ] [ACTIVE_PROJECT]/cr/cr-log.md updated
