# Project Document Structure

## Workspace Layout

Each project lives in its own dedicated folder. No shared document folders between projects.

```
my-pm-workspace/
|
|- _system/                     <- shared workspace config
|   |- config.md
|   |- tags-registry.md
|   `- sprint-calendar.md
|
|- projects-index.md            <- index of all projects
|
|- PROJ-001-[slug]/             <- Project 1 - fully self-contained
|   |- PROJECT.md
|   |- VERSIONS.md              <- master document registry
|   |- roadmap.md
|   |
|   |- discovery/
|   |   |- inbox/               <- FR-001.md, FR-002.md ...
|   |   |- scoring/             <- RICE-001.md ...
|   |   |- research/            <- RS-001.md ...
|   |   `- gate/
|   |       |- approved.md
|   |       |- rejected.md
|   |       `- backlog.md
|   |
|   |- prd/
|   |   `- PRD-001-[slug]/
|   |       |- PRD-001-v1.0.md  <- approved (immutable)
|   |       |- PRD-001-v1.1.md  <- current draft
|   |       `- CHANGELOG.md
|   |
|   |- epics/
|   |   `- EP-001-[slug]/
|   |       |- EP-001-v1.0.md
|   |       `- CHANGELOG.md
|   |
|   |- cr/
|   |   |- intake/
|   |   |- assessment/
|   |   |- approval-board/
|   |   |- approved/
|   |   |- rejected/
|   |   `- cr-log.md
|   |
|   |- stakeholders/
|   |   `- SH-001-[name].md
|   |
|   |- decisions/
|   |   `- DEC-001-[slug].md
|   |
|   `- reviews/
|       `- REVIEW-001-DD-MM-YYYY.md
|
|- PROJ-002-[slug]/             <- Project 2 - completely separate
|   `- ...
|
`- PROJ-003-[slug]/
    `- ...
```

## Why Isolated Folders?

Every document for a project lives inside that project's folder.
You never search outside the folder. No confusion about which FR belongs to which project.

## Document Versioning

```
[draft] -> [in-review] -> [approved] (immutable snapshot)
               |
          [rejected] -> [new draft version]
```

Version number is always in the filename: PRD-001-v1.0.md, PRD-001-v1.1.md
VERSIONS.md is the audit log - rows are never deleted.
