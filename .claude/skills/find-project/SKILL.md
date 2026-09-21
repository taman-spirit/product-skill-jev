---
name: find-project
description: List all projects or search for a specific project. Use when user says "show all projects", "list projects", "find project [name]", or wants to see what projects exist.
---

# Find Project

## Process

1. Use list_files("my-projects") to see the my-projects folder
2. Identify all folders starting with "PROJ-" inside my-projects/
3. For each folder, read my-projects/PROJ-NNN-[slug]/PROJECT.md
4. Extract: project name, status, priority, product, PM, start date, target end date
5. Build and display a summary table

## Output Format

If projects exist:
```
Your Projects

| Project | Status | Priority | Product | Target End |
|---------|--------|----------|---------|-----------|
| PROJ-001 - AI Alignment | active | P0 | [product] | DD/MM/YYYY |
| PROJ-002 - Checkout Redesign | planning | P1 | [product] | DD/MM/YYYY |

To open a project and see details:
- "Open project PROJ-001"
- "Open AI Alignment project"
- "Status of PROJ-002"
```

If no projects exist:
```
No projects found yet.

To create your first project:
- "Create a new project for [your initiative name]"

A project folder will be created with everything you need inside it.
```

If keyword provided (e.g. "find project alignment"):
- Filter results to projects matching the keyword in name or product
- Show only matching results with the same table format
