---
name: update-prd
description: Create a new version of an existing PRD, preserving history and linking to the triggering CR. Use when user says "update PRD", "new version PRD-NNN", or after a CR is approved.
---

# Update PRD

Never modify an existing versioned PRD file. Always create a new version.

## Opening Interview

When this skill is triggered, immediately say:

"Which PRD are you updating and what is changing? Describe the change and I'll determine the right version bump."

Wait for the answer before proceeding. Do not assume the PRD ID or the nature of the change.

If the update was triggered automatically by a CR approval, ask:

"CR-NNN has been approved. I'll create a new version of PRD-[X]. Before I draft it, can you confirm: is this a scope expansion or a clarification? That determines whether we go to v[X.1] or v[X+1].0."

## Process

1. Read the latest version of PRD-NNN (find highest vX.Y in the folder)
2. Read the triggering CR if one exists
3. Determine version bump using the rules below
4. Show a diff summary: "These sections will change: [list]"
5. Wait for PM confirmation
6. Write new version: PRD-NNN-v[X.Y].md
7. Update CHANGELOG.md with: version, date, summary, linked CR
8. Update cr-log.md if triggered by a CR
9. If active project: ask "Do you want me to update the project milestone for PROJ-NNN?"

## Version Rules

| Change Type | Example | Bump |
|------------|---------|------|
| Clarification, wording | AC reworded for clarity | Patch: v1.0 -> v1.01 |
| New AC, modified scope | Add error state handling | Minor: v1.0 -> v1.1 |
| Architecture change | Switch from sync to async API | Major: v1.0 -> v2.0 |
| Full rewrite | Problem statement changed | Major: v1.0 -> v2.0 |

## Checklist

- [ ] PM confirmed which PRD and what is changing
- [ ] Latest version of PRD read
- [ ] Version bump type confirmed with PM
- [ ] Diff summary shown before writing
- [ ] PM confirmed changes
- [ ] New version file written
- [ ] CHANGELOG.md updated
- [ ] CR status updated to "approved - PRD updated to vX.Y" in cr-log.md
