---
name: grill-prd
description: Stress-test a PRD by challenging assumptions, surfacing gaps, and pressure-testing user stories against edge cases. Use when user says "grill PRD", "review PRD", "stress test PRD-NNN", or wants to validate a PRD before stakeholder review.
---

# Grill PRD

Challenge every assumption in the PRD relentlessly until the PM is confident it is complete and defensible. Ask questions one at a time, wait for the answer before continuing.

Do NOT summarize the PRD back to the PM. Probe it.

## What to Challenge

### Problem Statement
- Can the PM explain the problem without mentioning the solution?
- Is this a real user problem or an assumed problem?
- What data or user evidence supports this problem statement?

### User Stories
- For each user story: what happens when the preconditions are not met?
- Is every actor covered? (end users, admins, integrators, ops team)
- What are the error states, empty states, and edge cases?
- Which user stories are implicitly dependencies of others?

### Implementation Decisions
- Which module decisions are hard to reverse? Should they be in an ADR?
- Are the interfaces simple enough that they could be tested in isolation?
- What happens when a dependency (external API, another squad) is unavailable?
- Which decisions have the highest cost if they turn out to be wrong?

### Out of Scope
- Is anything in "Out of Scope" likely to come back as a CR within 30 days?
- Are stakeholders aware of what is out of scope?

### Success Metrics
- Can the primary metric be measured today (baseline exists)?
- Is the target realistic given current baseline?
- What would a false positive look like? (metric looks good but users are not happy)

### Risks
- What is the single most likely reason this PRD will be rejected at sign-off?
- What external dependency has the highest probability of slipping?

## Process

1. Read the full PRD
2. Explore the relevant codebase or linked documents if available
3. Start with the section that has the weakest evidence
4. Ask questions one at a time, waiting for the PM's answer
5. When a term conflicts with the project glossary: flag it immediately
6. When a decision is hard to reverse: offer to document it in the PRD Decision Log
7. End with a confidence score: Low / Medium / High and specific items that need resolution

## Output Format

End each session with:

```
Grill Session: PRD-NNN
Confidence: [Low / Medium / High]

Resolved during session:
- [item]

Still open:
- [item] - recommended action: [action]

Next step: [specific action before stakeholder review]
```

## Checklist (end of session)

- [ ] Problem statement defensible with evidence
- [ ] All major actors have user stories
- [ ] Key edge cases and error states covered
- [ ] Hard-to-reverse decisions documented
- [ ] Out of scope list reviewed with PM
- [ ] Success metrics have baselines
- [ ] Risks section updated with new findings
