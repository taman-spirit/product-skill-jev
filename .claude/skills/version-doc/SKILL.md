---
name: version-doc
description: Manage the document lifecycle: create new draft versions, submit for review, record approvals, and snapshot approved documents. Use when user says "create new version", "new draft of [doc]", "submit for review", "approve doc", or when a document needs to change after being approved.
---

# Version Document

See [LIFECYCLE.md](LIFECYCLE.md) for the full state machine and rules.

## Commands

### 1. Create New Draft Version

When PM says "Create new version of PRD-NNN" or "New draft of [doc]":

Process:
1. Read the current document to find the latest version (scan folder or VERSIONS.md)
2. Ask the PM: "What type of change is this -- patch (typo/minor fix), minor (new section or requirement added), or major (significant rewrite or scope change)?"
3. Create new file: `[DOC-ID]-v[X.Y].md` with frontmatter `status: draft`
4. Copy content from previous approved version as starting point
5. Set `prev-version:` to the version being built upon
6. Set `changes:` to a summary of what this version will address
7. Add new row to VERSIONS.md (status: draft)
8. Update previous version row in VERSIONS.md to `archived`

Output:
```
New draft created: PRD-NNN-v1.1.md
Previous version: PRD-NNN-v1.0.md (archived)
Status: draft
Changes: [what this version addresses]

Edit PRD-NNN-v1.1.md, then say "Submit PRD-NNN-v1.1 for review" when ready.
```

### 2. Submit for Review

When PM says "Submit [doc] for review":

Process:
1. Read the draft document - confirm it is complete (no [placeholder] text remaining)
2. Ask the PM: "Who needs to review and approve this document? Please list their names."
3. Update frontmatter: `status: in-review`, `submitted-review: [today]`, `reviewers: [list]`
4. Update VERSIONS.md: status column -> in-review
5. Create a `REVIEW-NNN` file in `reviews/` using `_template-review.md`
6. Update docs/README.md with in-review status

Output:
```
PRD-NNN-v1.1.md submitted for review.

Reviewers: [Name 1], [Name 2]
Review record: reviews/REVIEW-001-DD-MM-YYYY.md

Waiting for approval. Say:
- "Approve PRD-NNN-v1.1" to record approval
- "Reject PRD-NNN-v1.1 with feedback: [notes]" to record rejection
```

### 3. Approve Document (Snapshot)

When PM says "Approve [doc]" or "[Name] approved [doc]":

Process:
1. Read the document - confirm status is `in-review`
2. Ask the PM: "Who is recording this approval -- please confirm the approver's name."
3. Update frontmatter: `status: approved`, `approved: [today]`, `approved-by: [name]`
4. Update VERSIONS.md: status column -> approved
5. Update the REVIEW-NNN file: outcome -> approved
6. Update docs/README.md: status -> approved
7. If linked to a project milestone: ask "Shall I update the corresponding milestone?"

The document is now an immutable snapshot. No further edits allowed.

Output:
```
SNAPSHOT CREATED: PRD-NNN-v1.1.md
Status: approved
Approved by: [Name] on DD/MM/YYYY

This version is now immutable.
To make changes: say "Create new version of PRD-NNN" to start v1.2.
```

### 4. Reject Document

When PM says "Reject [doc]" or "Review failed":

Process:
1. Update frontmatter: `status: rejected`
2. Update VERSIONS.md: status -> rejected
3. Update REVIEW-NNN: outcome -> rejected, record feedback
4. Do NOT mark as archived - rejected versions stay visible as history

Output:
```
PRD-NNN-v1.1.md marked as rejected.
Feedback recorded in: reviews/REVIEW-001-DD-MM-YYYY.md

To address feedback: say "Create new version of PRD-NNN"
New version will start from v1.2 incorporating the review feedback.
```

## Checklist

### Create new draft
- [ ] Latest version identified
- [ ] Version bump type confirmed with PM
- [ ] New file created with correct version in filename
- [ ] Frontmatter complete (status: draft, prev-version, changes)
- [ ] VERSIONS.md updated (new row added, previous row archived)

### Submit for review
- [ ] No placeholder text ([placeholder]) remaining in document
- [ ] Reviewers confirmed with PM
- [ ] Frontmatter updated (status: in-review, submitted-review, reviewers)
- [ ] VERSIONS.md updated
- [ ] REVIEW-NNN file created

### Approve (snapshot)
- [ ] Document was in-review status
- [ ] Approver name confirmed
- [ ] Frontmatter updated (status: approved, approved, approved-by)
- [ ] VERSIONS.md updated
- [ ] REVIEW-NNN updated with outcome
- [ ] Milestone update offered if project-linked
