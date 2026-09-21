---
name: to-prd
description: Convert a gate-approved Feature Request and its Research document into a full PRD. The PRD is a strategic overview - Section 5 contains an Epic index table only, not detailed AC. Detailed AC lives in individual Epic files. Use when user says "create PRD", "write PRD", "PRD for FR-NNN", or after a feature passes the Discovery Gate.
---

# To PRD

Convert a gate-approved FR + Research into a structured PRD.
Do NOT start without a gate-approved FR and a complete RS-NNN document.

## PRD vs Epic - What Goes Where

| Content | Lives in |
|---------|---------|
| Problem, solution, personas, journey | PRD |
| Platform architecture, tech specs overview | PRD |
| Success metrics, risks, roadmap, stakeholders | PRD |
| Epic index table (EP-ID, title, version, status) | PRD Section 5 |
| Full User Stories with Given/When/Then AC | Epic files (EP-NNN) |
| Technical specs per Epic, API contracts | Epic files (EP-NNN) |

The PRD Section 5 is a **live index table** that always reflects current Epic versions and statuses.
Detailed AC is never written inside the PRD.

## Pre-flight

- [ ] FR-NNN status is gate-approved
- [ ] RS-NNN exists with all 4 sections complete
- [ ] No open blocking technical risks in research

## Process

### 1. Explore Context

Note: Read `_system/active-project.md` to get the current project folder name (e.g., my-projects/PROJ-001-ai-alignment).
If this file does not exist, ask the user: "Which project are you working on?"
All file paths below use [ACTIVE_PROJECT] as the project folder name.

- Read FR-NNN, RS-NNN, and any linked stakeholder files from [ACTIVE_PROJECT]/discovery/
- Check `_system/tags-registry.md` to identify relevant tags
- Write them into the PRD frontmatter as `tags: #tag-one, #tag-two`. The conflict-check
  skill reads that field. A PRD without it is invisible to conflict detection, which
  reports as silence rather than as an error.
- Check `[ACTIVE_PROJECT]/prd/` for existing PRDs sharing the same tags (conflict risk)

### 2. Design Modules and Epic Boundaries

Before writing anything, sketch the major modules and how they map to Epics.
Each Epic should map to one module or one coherent user-facing capability.

Present to PM and confirm:
- Do these modules match expectations?
- How many Epics will this PRD have?
- Which Epics are in scope for the first sprint vs later?

### 3. Write the PRD

Write the PRD content directly using the section structure below. No external template needed. Key sections:

**Section 1 - Executive Summary**: overall scope, what the product does
**Section 2 - Customer Problem**: problem statement, customer evidence
**Section 3 - Target Customers**: personas, customer journey
**Section 4 - Product Vision**: what we are building and why
**Section 5 - Epics** (3-layer structure):

Layer 1 - Summary table (status at a glance):
```
| EP-ID | Title | Module | Priority | Version | Status | Points | File |
|-------|-------|--------|----------|---------|--------|--------|------|
| EP-001 | [Title] | [Module] | P1 | not created | - | - | - |
| EP-002 | [Title] | [Module] | P2 | not created | - | - | - |
```

Layer 2 - Detail block per Epic (description + key AC for stakeholder review):
For each Epic, write:
- 1-2 sentences: what it enables users to do
- Key Acceptance Criteria: 3-4 outcome-focused statements (NOT Given/When/Then)
- Out of scope: 1-2 explicit exclusions

Example Key AC format:
```
- Users can register a product and receive an automated risk classification
- Policy admins can approve or reject keyword changes before they go live
- The system blocks unapproved models from accessing the guardrails API
```

Layer 3 - Epic files (full Given/When/Then):
Created separately after PRD approval via "Create epic for PRD-NNN: [name]"

**Section 6 - Platform Architecture**: system design, key technical decisions
**Section 7 - Success Metrics**: from RS-NNN Section 4, with concrete targets
**Section 8 - Risks**: risk table with mitigation
**Section 9 - Roadmap**: Epic delivery sequence across sprints
**Section 10 - Stakeholders**: team and approvers

### 4. Conflict Check

Run the conflict-check skill for the target sprint before finalizing.
If conflicts found: warn PM with specific resolution before proceeding.

### 5. Publish

- Show full draft and wait for PM confirmation
- Write to `[ACTIVE_PROJECT]/prd/PRD-NNN-[slug]/PRD-NNN-v1.0.md`
- Create `[ACTIVE_PROJECT]/prd/PRD-NNN-[slug]/CHANGELOG.md`
- Update FR-NNN status to `prd-draft`
- Update PROJECT.md Linked Items and VERSIONS.md in [ACTIVE_PROJECT]/
- Update `[ACTIVE_PROJECT]/prd/conflict-log.md` with any detected conflicts

### 6. After PRD - Create Epics

After the PRD is approved, create Epic files for each row in Section 5:
```
"Create epic for PRD-NNN: [Epic title]"
```
Each Epic created will auto-sync back to PRD Section 5 with version and status.

## Checklist

- [ ] FR gate-approved, RS-NNN complete
- [ ] Module sketch and Epic boundaries confirmed with PM
- [ ] Section 5 has Epic index table (no detailed AC inside PRD)
- [ ] Out of Scope section explicitly defined
- [ ] Success metrics concrete with targets
- [ ] Conflict check run for target sprint
- [ ] Draft shown and PM confirmed
- [ ] PRD-NNN-v1.0.md and CHANGELOG.md written to [ACTIVE_PROJECT]/prd/PRD-NNN-[slug]/
- [ ] FR-NNN status updated to prd-draft
- [ ] Project VERSIONS.md updated in [ACTIVE_PROJECT]/
