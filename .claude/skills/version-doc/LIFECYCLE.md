# Document Lifecycle Reference

## State Machine

```
                    [Create new file]
                           |
                           v
                        [draft]
                     (editable freely)
                           |
              [Submit for review]
                           |
                           v
                      [in-review]
                  (no direct edits)
                    /           \
          [Approve]              [Reject]
               |                     |
               v                     v
          [approved]             [rejected]
          (immutable              (visible as
           snapshot)               history)
               |                     |
          [New change              [New draft
           needed]                  version]
               |                     |
               v                     v
         [archived]              [draft v+1]
       (prev version)
```

## Version File Naming

```
[DOC-ID]-v[MAJOR].[MINOR].md

PRD-001-v1.0.md     <- first approved version
PRD-001-v1.1.md     <- second approved version (minor change)
PRD-001-v2.0.md     <- major rewrite (current draft)
```

The version number is always in the filename.
The status is always in the frontmatter.
VERSIONS.md mirrors both.

## Immutability Contract

Once a document is `approved`:
- Its file MUST NOT be edited
- VERSIONS.md status for that version MUST NOT change (except to `archived`)
- `archived` = superseded by a newer approved version (not deleted, not edited)

This creates a permanent audit trail:
- Who wrote each version
- Who approved each version
- What changed between versions
- Why changes were made (via `changes:` field and REVIEW records)

## VERSIONS.md as Audit Log

The VERSIONS.md registry NEVER has rows deleted.
Every version that ever existed stays in the table.

Reading VERSIONS.md tells you:
- Current working document (status: draft)
- Documents awaiting approval (status: in-review)
- Approved snapshots (status: approved)
- History of all superseded versions (status: archived)
- Review failures (status: rejected)

## Version Bump Decision Guide

Ask: "What is the scope of the change?"

| If the change... | Bump | Reasoning |
|-----------------|------|-----------|
| Only fixes wording, typos, formatting | Patch (v1.0 -> v1.01) | Behavior unchanged |
| Adds or changes AC, adds new user story | Minor (v1.0 -> v1.1) | Scope expanded |
| Modifies an existing module interface | Minor (v1.0 -> v1.1) | Design changed |
| Changes the problem statement | Major (v1.0 -> v2.0) | Fundamental rethink |
| Adds a new module or Epic | Major (v1.0 -> v2.0) | Architecture changed |
| Full rewrite after rejection | Major (v1.0 -> v2.0) | New approach |

When in doubt: ask PM. Do not guess.

## Review Record Naming

```
reviews/REVIEW-NNN-DD-MM-YYYY.md

REVIEW-001-15-05-2026.md
REVIEW-002-22-05-2026.md
```

NNN = sequential, unique across the project.
One review record per review session.
A single review session can cover multiple documents.
