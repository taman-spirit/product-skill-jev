---
name: deep-research
description: Create a structured research document for a Feature Request before it enters the Discovery Gate. Use when the user says "research feature", "investigate feasibility", "deep research", or wants to explore technical, compliance, or market context for a feature.
---

# Deep Research

A feature cannot pass the Discovery Gate without a complete research document.
All 4 sections are mandatory. Do not mark research complete if any section is missing.

## Required Sections

### 1. Technical Feasibility
- Current system dependencies and affected components
- Estimated complexity: Low (under 2 weeks, 1 dev) / Medium (2-6 weeks) / High (over 6 weeks, multiple squads)
- Known blockers or tech debt that must be resolved first
- Open technical questions (with owner and deadline)

### 2. Security & Compliance
This section is mandatory and cannot be skipped.
- Decree 13/2023/ND-CP (personal data protection) implications
- PII data handling: what is collected, stored, shared, deleted
- Internal security policy alignment
- Audit trail requirements
- Any regulatory risk if the feature is built incorrectly

### 3. Competitive Analysis
- How at least 2 direct competitors solve this problem (strengths and weaknesses)
- Competitive advantage angle
- Benchmark against comparable products in your portfolio

### 4. Definition of Success / North Star Metrics
- Primary metric: the single number that proves success
- Supporting metrics: maximum 3
- Measurement method and data source
- Timeline to see a meaningful signal (weeks or months)

## Interview Flow

When research begins, read the FR file first. Then open the session with:

"Before I structure the research document for [feature name], I want to understand what you already know.

What do you already know about this feature? Describe the context, the problem it solves, and any constraints or risks you're already aware of."

After the PM responds, acknowledge what was shared and identify which of the 4 sections have partial information. Then work through each section that needs input:

**Technical Feasibility:**
"Which systems or components would this feature touch? Do you know of any existing blockers or tech debt that needs to be resolved first?"

**Security & Compliance:**
"Does this feature handle any personal data -- names, IDs, location, transaction history? If so, what gets collected, stored, or shared?"

**Competitive Analysis:**
"Which competitors or comparable products have you looked at for this problem? What do they do well, and where do they fall short?"

**Definition of Success:**
"If this feature ships and works perfectly, what is the single metric that would prove it? And what is the realistic timeline to see a meaningful signal?"

After collecting inputs, draft each section. Mark any item as TBD with a specific owner and deadline if the PM cannot answer it. Do not leave TBD items without an owner.

## Process

Note: Read `_system/active-project.md` to get the current project folder name (e.g., my-projects/PROJ-001-ai-alignment).
If this file does not exist, ask the user: "Which project are you working on?"
All file paths below use [ACTIVE_PROJECT] as the project folder name.

1. Read the FR file
2. Run the interview above to collect context before drafting
3. Draft RS-NNN-[slug].md content directly (no external template needed)
4. Fill all 4 sections -- mark TBD with specific owner if information is unavailable
5. Flag any section that cannot be completed as a blocker with an explanation
6. Write a Recommendation: proceed / conditional / do not proceed
7. Show the draft and wait for PM confirmation before writing the file
8. Write to `[ACTIVE_PROJECT]/discovery/research/RS-NNN-[slug].md`

## Checklist

- [ ] FR file read and understood
- [ ] Opening interview completed -- PM context captured
- [ ] RS-NNN file created with correct ID in [ACTIVE_PROJECT]/discovery/research/
- [ ] Section 1: Technical Feasibility complete
- [ ] Section 2: Security & Compliance complete (cannot skip)
- [ ] Section 3: Competitive Analysis with 2 or more competitors
- [ ] Section 4: North Star metric defined with measurement method
- [ ] Recommendation stated with rationale
- [ ] Draft shown and PM confirmed before writing
- [ ] Linked to FR-NNN in the FR file
