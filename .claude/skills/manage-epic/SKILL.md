---
name: manage-epic
description: Create, update, version, and approve Epics linked to a PRD. Each Epic has its own versioned file with full Given/When/Then AC. The PRD maintains a live sync table of all linked Epics and their current version/status. Use when user says "create epic", "add epic to PRD-NNN", "update epic", "update AC", "add user story", "approve epic", or "EP-NNN".
---

# Manage Epic

See [EPIC-RULES.md](EPIC-RULES.md) for AC quality standards and change type definitions.

## Architecture

```
PRD-NNN-v1.0.md                   <- Strategic overview. Section 5 = Epic index table only.
  |
  +-- docs/epics/EP-001-[slug]/
  |     EP-001-v1.0.md             <- Approved snapshot (immutable)
  |     EP-001-v1.1.md             <- Current draft
  |     CHANGELOG.md               <- Full change history
  |
  +-- docs/epics/EP-002-[slug]/
        EP-002-v1.0.md
        CHANGELOG.md
```

**PRD and Epic are always in sync.**
The PRD Section 5 is an index table - it never contains detailed AC.
All AC lives in the Epic files. When an Epic changes, the PRD table is updated.

## PRD Section 5 Structure

PRD Section 5 has 3 layers. Every Epic sync must update all 3.

**Layer 1 - Summary table** (quick status overview):
```
| EP-ID | Title | Module | Priority | Version | Status | Points | File |
|-------|-------|--------|----------|---------|--------|--------|------|
| EP-001 | Auth Flow | Portal | P1 | v1.1 | approved | 21 | [link] |
| EP-002 | Policy Mgr | Portal | P2 | v2.0 | draft | 13 | [link] |
```

**Layer 2 - Epic detail block** (one block per Epic, synced on creation and version change):
```
### EP-001 - [Title]
Module: [x] | Priority: P[N] | Version: v1.1 | Status: approved | Points: 21
Epic file: [EP-001-v1.1.md](link)

[1-2 sentences: what this Epic enables users to do]

Key Acceptance Criteria:
- [Critical must-have behavior - outcome focused, not step-by-step]
- [Second key behavior]
- [Key constraint, error handling, or compliance requirement]

Out of scope for this Epic:
- [Explicit exclusion]
```

**Layer 3 - Epic file** (full Given/When/Then AC per user story - NOT in PRD):
Detailed spec lives in `docs/epics/EP-NNN-[slug]/EP-NNN-vX.Y.md`

**What goes in Key AC vs Epic file AC:**

| PRD Key AC (summary) | Epic File AC (detail) |
|---------------------|----------------------|
| "Users can register a product and receive a risk classification" | Given: user fills form / When: clicks submit / Then: classification appears |
| "System blocks unapproved AI models from accessing guardrails" | Given: model status = pending / When: API call made / Then: 403 returned |
| Outcome-focused, 1 sentence | Scenario-based, 3+ per user story |
| For stakeholder review | For developer implementation |

---

## Commands

### 1. Create New Epic

Process:
1. Read the PRD to understand the module structure
2. Get next EP-ID: scan `docs/epics/` folder in the project, take max + 1
3. Ask PM for any missing:
   - Epic title and which PRD section/module it covers
   - Sprint target and priority (P0/P1/P2/P3)
   - Dev owner and QA owner
   - Initial list of User Stories (AC details can be added after)
4. Show draft `EP-NNN-v1.0.md` and wait for PM confirmation
5. Create: `docs/epics/EP-NNN-[slug]/EP-NNN-v1.0.md`
6. Create: `docs/epics/EP-NNN-[slug]/CHANGELOG.md`
7. **Sync PRD Section 5** - update all 3 layers:
   - Layer 1 table: add new row `| EP-NNN | [Title] | [Module] | P[N] | v1.0 | draft | [pts] | [link] |`
   - Layer 2 detail: add new Epic block with description and Key AC (ask PM for 3-4 key criteria in plain English)
   - The Key AC in PRD should be outcome statements, not Given/When/Then scenarios
8. Update project `VERSIONS.md`: add Epic row

Output:
```
Epic created: EP-NNN - [Title]
File: docs/epics/EP-NNN-[slug]/EP-NNN-v1.0.md
Status: draft | Sprint: S[NN] | PRD: PRD-NNN

PRD Section 5 updated - EP-NNN added to Epic index.

User Stories (draft, no AC yet):
  US-001: [title] (P1, [N] pts)
  US-002: [title] (P2, [N] pts)

Next: "Add AC to EP-NNN" to write Acceptance Criteria
```

---

### 2. Add or Update Acceptance Criteria

Status rules:
- **draft**: edit directly, no new version needed
- **in-review**: cannot edit - wait for result or reject and create new version
- **approved**: MUST create new version first (see Command 3)

Process (draft Epic):
1. Read `EP-NNN-[latest version].md`
2. For each User Story being added or updated:
   - Actor, action, benefit in "As a / I want / So that" format
   - Minimum 3 AC scenarios: happy path, edge case, error state
   - Given/When/Then with specific observable outcomes
3. AC quality check (run before saving):
   - [ ] Given describes the system state before the action
   - [ ] When is a single user action or system event
   - [ ] Then describes observable behavior - not implementation
   - [ ] Error scenario includes the specific error message or behavior
   - [ ] Then never says "the system works correctly" (too vague)
4. Update story points total in the Epic frontmatter
5. Show changes and wait for PM confirmation
6. Save the Epic file
7. **Sync PRD Section 5**:
   - Layer 1 table: update story points for EP-NNN
   - Layer 2 detail block: update points and any Key AC if they changed

---

### 3. Create New Epic Version

Rules: Same versioning as PRD. Patch / minor / major based on scope of change.

Process:
1. Confirm Epic is `approved`
2. Ask PM: what is changing? (determines bump type)
3. Create new file: `EP-NNN-v[X.Y].md` (copy from approved version)
4. Set frontmatter: `status: draft`, `prev-version: vX.Y-1`, `changes: [summary]`
5. Mark previous version as `archived` in project VERSIONS.md
6. Add entry to `CHANGELOG.md`:
   ```
   ### v[X.Y] - DD/MM/YYYY
   Change type: [ac-update / story-add / scope-change / ...]
   Changed by: [PM name]
   Summary: [what changed and why]
   Linked CR: CR-NNN (if applicable)
   ```
7. **Sync PRD Section 5**:
   - Layer 1 table: update version and status to draft for EP-NNN
   - Layer 2 detail block: update version number in header line

Output:
```
New draft: EP-NNN-v[X.Y].md
Previous version: EP-NNN-v[X.Y-1].md (archived)

PRD Section 5 synced - EP-NNN now shows v[X.Y] / draft.

Edit EP-NNN-v[X.Y].md, then say "Submit EP-NNN for review" when ready.
```

---

### 4. Submit for Review

Pre-flight (all must pass):
- [ ] All User Stories have minimum 3 AC scenarios (happy path, edge case, error)
- [ ] No [placeholder] text remaining in the file
- [ ] All "Then" statements are specific and testable
- [ ] Technical specifications section complete
- [ ] Dev owner and QA owner assigned
- [ ] Story points estimated for all US

Process:
1. Run pre-flight - block with specific issues if any fail
2. Confirm reviewers with PM
3. Update frontmatter: `status: in-review`, `submitted-review: [today]`, `reviewers: [list]`
4. Update project VERSIONS.md: status -> in-review
5. Create `REVIEW-NNN-DD-MM-YYYY.md` in `reviews/`
6. **Sync PRD Section 5**:
   - Layer 1 table: update EP-NNN status to `in-review`
   - Layer 2 detail block: update status in header line

---

### 5. Approve Epic (Snapshot)

Process:
1. Confirm Epic is `in-review`
2. Confirm approver name with PM
3. Update frontmatter: `status: approved`, `approved: [today]`, `approved-by: [name]`
4. Update project VERSIONS.md: status -> approved
5. Update REVIEW-NNN: outcome -> approved
6. **Sync PRD Section 5**:
   - Layer 1 table: EP-NNN status -> `approved`, version and points confirmed
   - Layer 2 detail block: status in header line -> `approved`, add file link if missing
7. Epic is now an immutable snapshot

Output:
```
SNAPSHOT: EP-NNN-v1.1.md
Approved by: [Name] on DD/MM/YYYY

PRD Section 5 synced - EP-NNN now shows v1.1 / approved.

This version is immutable. Dev team can begin implementation.
To make changes: "New version of EP-NNN"
```

---

### 6. Reject Epic

Process:
1. Update frontmatter: `status: rejected`
2. Update VERSIONS.md: status -> rejected
3. Update REVIEW-NNN: outcome -> rejected, record feedback
4. **Sync PRD Section 5**: Layer 1 table + Layer 2 header: EP-NNN status -> `rejected`
5. Offer to create a new draft version

---

### 7. View Epic Status

Output:
```
EP-NNN - [Title]
PRD: PRD-NNN | Module: [Module] | Sprint: S[NN]

Current version: v1.1 (draft)
Previous:        v1.0 (approved, archived)

User Stories: [N] total
  Done:        [N]
  In progress: [N]
  Not started: [N]

Story points: [total]
Open ACs needing work: [list any US without 3+ scenarios]
Changes since last approval: [summary from CHANGELOG]
```

---

## PRD Sync Rules (Summary)

Every Epic state change must update both Layer 1 (table) and Layer 2 (detail block).

| Epic event | Layer 1 - Summary table | Layer 2 - Detail block |
|-----------|------------------------|----------------------|
| Epic created | Add new row | Add new Epic block with description + Key AC |
| US added / points changed | Update story points | Update points in header |
| Key AC clarified | No change | Update Key AC bullets |
| New version created | Update version, status: draft | Update version + status in header |
| Submitted for review | Status: in-review | Status: in-review in header |
| Approved | Status: approved, confirm version + points | Status: approved, add file link |
| Rejected | Status: rejected | Status: rejected in header |
| Archived | Status: archived | Status: archived in header |

**Rule:** PRD Key AC (Layer 2) stays at summary level - outcome statements.
Full Given/When/Then always stays in the Epic file only.

---

## Checklist

### Create Epic
- [ ] EP-ID confirmed from folder scan
- [ ] Metadata set: module, sprint, priority, dev owner, QA owner
- [ ] EP-NNN-v1.0.md created
- [ ] CHANGELOG.md created
- [ ] Draft shown and PM confirmed
- [ ] VERSIONS.md updated
- [ ] PRD Section 5 updated with new EP-NNN row

### Version change (after approval)
- [ ] Previous version marked archived in VERSIONS.md
- [ ] New file created with correct version and prev-version fields
- [ ] CHANGELOG.md updated with change type and reason
- [ ] PRD Section 5 synced with new version + status: draft

### Submit for review
- [ ] All US have 3+ AC scenarios (Given/When/Then)
- [ ] No placeholder text
- [ ] REVIEW-NNN created
- [ ] PRD Section 5 status updated to in-review

### Approve
- [ ] Frontmatter: status, approved date, approved-by set
- [ ] VERSIONS.md and REVIEW-NNN updated
- [ ] PRD Section 5 status updated to approved
