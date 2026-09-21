---
name: gate-review
description: Run the Discovery Gate checklist for a Feature Request to determine if it is ready to become a PRD. Use when the user says "gate review", "gate check", "run gate for FR-NNN", or wants to approve or reject a feature for development.
---

# Discovery Gate Review

## Required Checklist (ALL must pass)

- [ ] RICE score exists and is calculated (not estimated)
- [ ] Research document RS-NNN exists with all 4 required sections complete:
  - [ ] Technical Feasibility
  - [ ] Security & Compliance (Decree 13/2023 -- mandatory, cannot be skipped)
  - [ ] Competitive Analysis (minimum 2 competitors)
  - [ ] Definition of Success / North Star Metrics
- [ ] At least one stakeholder identified as sponsor (SH-NNN linked)
- [ ] No open blocking technical risk in research (or documented resolution plan)

## Decision Rules

| RICE | ICE | Decision |
|------|-----|----------|
| >= 40 | >= 30 | APPROVED -- add to [ACTIVE_PROJECT]/discovery/gate/approved.md |
| 20-39 | any | CONDITIONAL -- add to [ACTIVE_PROJECT]/discovery/gate/backlog.md with conditions to promote |
| < 20 | any | REJECTED (unless PM provides written strategic rationale) |

## Process

Note: Read `_system/active-project.md` to get the current project folder name (e.g., my-projects/PROJ-001-ai-alignment).
If this file does not exist, ask the user: "Which project are you working on?"
All file paths below use [ACTIVE_PROJECT] as the project folder name.

1. Read the FR file and linked RICE-NNN and RS-NNN documents from [ACTIVE_PROJECT]/discovery/
2. Run the checklist above -- fail immediately if any mandatory item is missing
3. If the Security & Compliance section is missing: block and state the reason before proceeding
4. Output the decision with specific rationale for each failed or passed item
5. Update the FR status field to: gate-approved / gate-conditional / gate-rejected
6. Write the entry to the appropriate gate file under [ACTIVE_PROJECT]/discovery/gate/
7. If APPROVED, say: "FR-NNN has passed the Discovery Gate. Shall I create the PRD draft?"

## Output Format

```
Gate Review: FR-NNN - [Feature Name]
Date: DD/MM/YYYY

Checklist Results:
[x] RICE score: [value] (calculated DD/MM/YYYY)
[x] Research document: RS-NNN complete
[ ] Security & Compliance section: MISSING -- gate blocked
[x] Stakeholder sponsor: SH-NNN [Name]
[x] No blocking technical risk

Decision: BLOCKED / APPROVED / CONDITIONAL / REJECTED

Reason:
[Specific explanation for the decision. If blocked or rejected, state exactly what is missing and what must be done to resubmit.]

Next step:
[One clear action the PM must take.]
```

## Blocking Rules

- Missing Security & Compliance section: always blocks the gate, regardless of RICE score
- RICE score estimated rather than calculated: blocks the gate
- No identified sponsor stakeholder: blocks the gate
- Open blocking technical risk with no resolution plan: blocks the gate
