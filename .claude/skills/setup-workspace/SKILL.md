---
name: setup-workspace
description: Initialize the PM workspace with shared config files. Each project gets its own isolated folder - this setup only creates the shared _system/ config. Runs automatically when "create project" is called on a fresh directory. Use explicitly when user says "setup workspace", "initialize", or starts fresh.
---

# Setup Workspace

Initialize the shared workspace config. Run once per workspace root.
If `_system/config.md` already exists, skip to the project creation step.

## Detection

```
Does _system/config.md exist?
  YES -> workspace already initialized, proceed to create-project
  NO  -> run full setup below
```

## Step 1 - Collect Config

When workspace does not exist, immediately ask:

```
Let's set up your PM workspace. A few quick questions:

1. What is your team or company name?
2. What products are you managing? (list them, one per line)
3. How long are your sprints? (default: 2 weeks)
4. Your name?
```

Wait for all answers before creating any files.

## Step 2 - Create Shared Config

Create `_system/` and `my-projects/`:

Create empty folder: `my-projects/` (all projects will be created inside this)

**`_system/config.md`**
```
# Workspace Config

Team: [team name]
PM: [pm name]

Products:
- [Product A]
- [Product B]

Sprint-Length: [N] weeks
Current-Sprint: S01

RICE-Approved: 40
RICE-Conditional: 20
ICE-Approved: 30
```

**`_system/tags-registry.md`**
```
# Tags Registry

| Tag | Module | Squad Owner | Notes |
|-----|--------|-------------|-------|
| #auth | Authentication | Platform | Login, session, token |
| #profile | User Profile | Core | Personal info, settings |
| #notification | Notifications | Platform | Push, in-app |
| #search | Search | Core | Indexing, discovery |
| #analytics | Analytics | Data | Events, funnels |
| #payment | Payment | Payment Squad | Transactions, billing |
| #onboarding | Onboarding | Growth | Registration, first run |
```

**`_system/sprint-calendar.md`**
```
# Sprint Calendar

Current-Sprint: S01

| Sprint | Start | End | Goal | Status |
|--------|-------|-----|------|--------|
| S01 | DD/MM/YYYY | DD/MM/YYYY | [Sprint goal] | Active |
| S02 | DD/MM/YYYY | DD/MM/YYYY | TBD | Planned |
```

**`projects-index.md`** (in workspace root)
```
# Projects Index

| PROJ-ID | Name | Product | Priority | PM | Start | Target End | Status |
|---------|------|---------|----------|-----|-------|-----------|--------|
```

## Step 3 - Confirm and Continue

```
Workspace initialized.

Created:
  _system/config.md
  _system/tags-registry.md
  _system/sprint-calendar.md
  projects-index.md

Each project will get its own isolated folder (my-projects/PROJ-NNN-[slug]/)
with its own discovery, PRD, CR, and stakeholder documents inside.

Creating your first project now...
```

Then immediately continue with the create-project skill.

## Checklist

- [ ] Team config collected (name, products, sprint length, PM name)
- [ ] _system/config.md created
- [ ] _system/tags-registry.md created
- [ ] _system/sprint-calendar.md created
- [ ] projects-index.md created in workspace root
- [ ] Confirmation shown
- [ ] Proceed to create-project
