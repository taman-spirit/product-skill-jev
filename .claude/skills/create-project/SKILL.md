---
name: create-project
description: Create a new self-contained project folder with its own discovery, PRD, CR, and stakeholder subfolders. Each project is completely isolated. Automatically initializes the workspace on first use. Use when user says "create project", "new project", "start project", or names an initiative they want to begin.
---

# Create Project

Each project gets its own dedicated folder with ALL documents inside.
No shared folders between projects - no mixing, no confusion.

See [DOC-STRUCTURE.md](DOC-STRUCTURE.md) for the complete layout.

## Pre-flight: Workspace Check

Check if the workspace is initialized:
```
Does _system/config.md exist?
  NO  -> run setup-workspace skill first, then return here
  YES -> proceed to Step 1
```

---

## Step 1 - Collect Project Info

Scan the `my-projects/` folder for existing PROJ-NNN-* folders to get the next PROJ-ID.
Read `_system/config.md` for the product list and PM name.

Ask for any missing:
- Project name and slug (lowercase-hyphenated, example: `ai-search-assistant`)
- Product (from config.md list or add new one)
- Priority: P0 / P1 / P2 / P3
- Start date and target end date
- Goal in 1-2 sentences

## Step 2 - Show Structure Preview

Show what will be created and wait for PM confirmation:

```
Project to create: PROJ-NNN - [Name]

my-projects/PROJ-NNN-[slug]/               <- dedicated project folder
  PROJECT.md                   <- project definition (v1.0, draft)
  VERSIONS.md                  <- document version registry
  roadmap.md                   <- sprint timeline
  discovery/
    inbox/                     <- feature requests (FR-NNN)
    scoring/                   <- RICE scores (RICE-NNN)
    research/                  <- research docs (RS-NNN)
    gate/                      <- approved / rejected / backlog
  prd/                         <- PRDs (PRD-NNN-vX.Y.md)
  epics/                       <- Epics (EP-NNN-vX.Y.md)
  cr/                          <- change requests (CR-NNN)
    intake/
    assessment/
    approval-board/
    approved/
    rejected/
  stakeholders/                <- stakeholder profiles (SH-NNN)
  decisions/                   <- decision records (DEC-NNN)
  reviews/                     <- review session records

Proceed? (yes / adjust)
```

## Step 3 - Create the Project Folder

Create all directories inside `my-projects/PROJ-NNN-[slug]/`.

Write the following files:

**`PROJECT.md`**
```
---
doc-id: PROJ-NNN
title: [Project Name]
version: v1.0
status: draft
product: [Product]
priority: P[N]
pm: [PM Name]
start: DD/MM/YYYY
target-end: DD/MM/YYYY
created: DD/MM/YYYY
approved: -
approved-by: -
changes: Initial version
---

# PROJ-NNN - [Project Name]

## Goal
[1-2 sentences: what this project achieves and why it matters]

## Scope
- [What is included]

## Out of Scope
- [What is explicitly excluded]

## Team
| Role | Name | Responsibility |
|------|------|---------------|
| Product Manager | [Name] | Overall coordination |
| Tech Lead | [Name] | Technical decisions |

## Linked Documents
### Feature Requests
| FR-ID | Title | Gate Status | RICE |
|-------|-------|------------|------|

### PRDs
| PRD-ID | Title | Version | Status |
|--------|-------|---------|--------|

### Change Requests
| CR-ID | PRD-ID | Title | Status |
|-------|--------|-------|--------|

## Milestones
| ID | Milestone | Target Date | Status |
|----|-----------|------------|--------|
| M1 | Discovery complete | DD/MM/YYYY | Pending |
| M2 | PRDs signed off | DD/MM/YYYY | Pending |
| M3 | Design signed off | DD/MM/YYYY | Pending |
| M4 | Development complete | DD/MM/YYYY | Pending |
| M5 | Launch | DD/MM/YYYY | Pending |

## North Star Metrics
| Metric | Baseline | Target | Source |
|--------|---------|--------|--------|

## Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|

## Decision Log
| Date | Decision | Rationale | Owner |
|------|----------|----------|-------|
```

**`VERSIONS.md`** - initialize with PROJECT.md v1.0 draft row

**`roadmap.md`** - sprint timeline (living doc)

**`discovery/gate/approved.md`**, **`discovery/gate/rejected.md`**, **`discovery/gate/backlog.md`** - empty tables

**`cr/cr-log.md`** - CR master log

**`decisions/README.md`** - decision record index

## Step 4 - Register in Index

Append to `projects-index.md` in the workspace root:
```
| PROJ-NNN | [Name] | [Product] | P[N] | [PM] | DD/MM/YYYY | - | planning |
```

## Step 5 - Next Steps Guide

After confirming creation, always output this guide:

```
Project created: PROJ-NNN - [Project Name]
Folder: my-projects/PROJ-NNN-[slug]/

Your roadmap to the first PRD:

STEP 1 - Capture feature ideas
  Say: "Create a feature request for [description]"
  Files will be saved in: my-projects/PROJ-NNN-[slug]/discovery/inbox/

STEP 2 - Score and prioritize (RICE)
  Say: "Score FR-001 with RICE"
  The AI will interview you for Reach, Impact, Confidence, Effort.

STEP 3 - Run Discovery Gate
  Say: "Gate review FR-001"
  Checks: RICE score, research completeness, stakeholder sponsor.
  If approved, you're ready to write the PRD.

STEP 4 - Write the PRD
  Say: "Create PRD for FR-001"
  The AI will sketch modules, then write the full PRD.

STEP 5 - Break PRD into Epics
  Say: "Create epic for PRD-001: [Epic name]"
  Each Epic gets full Given/When/Then acceptance criteria.

STEP 6 - Stress-test before stakeholder review
  Say: "Grill PRD-001"
  The AI challenges assumptions one question at a time.

STEP 7 - Submit and approve
  Say: "Submit PRD-001-v1.0 for review"
  Say: "Approve PRD-001-v1.0"

Ready? Start with: "Create a feature request for [your first feature]"
```

## Checklist

- [ ] Workspace check passed (_system/config.md exists)
- [ ] Next PROJ-ID confirmed (scan my-projects/ folder for existing PROJ-NNN-* folders)
- [ ] Project info collected: name, slug, product, priority, dates, goal
- [ ] Structure preview shown and PM confirmed
- [ ] All folders created inside my-projects/PROJ-NNN-[slug]/
- [ ] PROJECT.md written with all fields (no placeholders)
- [ ] VERSIONS.md, roadmap.md, gate files, cr-log.md created
- [ ] projects-index.md updated
- [ ] Next steps guide shown to PM
