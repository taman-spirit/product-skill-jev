---
name: conflict-check
description: Detect tag collisions between PRDs in the same sprint across the active project. Use when user says "check conflicts", "conflict check", "any conflicts in sprint", or when creating a new PRD or sprint.
---

# Conflict Check

## Process

Note: Read `_system/active-project.md` to get the current project folder name.
If it does not exist, ask which project before proceeding.

1. Read `[ACTIVE_PROJECT]/sprints/` to find the target sprint file
   - If no sprints folder exists yet, report: "No sprints found for this project. Create a sprint first."
2. From the sprint file, extract all PRD IDs listed in scope
3. For each PRD: read `[ACTIVE_PROJECT]/prd/PRD-NNN-[slug]/PRD-NNN-vX.Y.md` and extract tags from frontmatter
4. Build a map: tag -> [list of PRD IDs using that tag]
5. Flag any tag that appears in 2 or more PRDs in the same sprint
6. Write findings to `[ACTIVE_PROJECT]/prd/conflict-log.md`
7. Report to PM

## Output Format

```
Conflict Check: Sprint SXX - [ACTIVE_PROJECT]
Scanned: PRD-001, PRD-002, PRD-003

CONFLICT: Sprint SXX | Tag #payment | PRD-001 & PRD-003
-> Both touch the payment module in the same sprint.
Risk: Integration collision - two teams modifying the same code path.
Suggestion: Defer PRD-003 payment component to next sprint, or sync squads before start.

Clean: No conflicts on #notification, #profile
```

If no conflicts:
```
No conflicts found in Sprint SXX for [project name].
All PRDs use distinct module tags.
```

## When to Run

- Automatically when a new sprint is created
- Automatically when a new PRD is added to a sprint
- On PM request

## Checklist

- [ ] Active project confirmed from _system/active-project.md
- [ ] Sprint file read and PRD list extracted
- [ ] All PRD tags checked
- [ ] Conflicts written to [ACTIVE_PROJECT]/prd/conflict-log.md
- [ ] PM informed of all conflicts with resolution suggestions
