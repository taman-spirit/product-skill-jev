---
doc-id: PROJ-001
title: AI PM Skills
version: v1.0
status: active
product: AI PM Skills
priority: P0
pm: Product Manager
start: 01/05/2026
target-end: 31/12/2026
created: 01/05/2026
approved: 01/05/2026
approved-by: PM Lead
changes: Initial version
---

# PROJ-001 - AI PM Skills

## Goal

Build an AI co-pilot for Product Managers that automates PM workflows — scoring features, writing PRDs, managing Epics, detecting conflicts, and tracking stakeholders — using plain language commands.

## Scope

- AI-powered chat interface (web + Telegram)
- Project management with versioned document structure
- 20 built-in PM skills (discovery, PRD, CR, stakeholder)
- Multi-provider AI support (Anthropic, Groq, Gemini, OpenAI, Ollama)
- File-based workspace (all data owned by the user)

## Out of Scope

- Real-time collaboration (multi-user editing)
- Built-in video conferencing
- Native mobile app (web is mobile-responsive)

## Team

| Role | Name | Responsibility |
|------|------|---------------|
| Product Manager | [PM Name] | Overall coordination, PRD ownership |
| Tech Lead | [TL Name] | Architecture, backend, Docker |
| Frontend | [FE Name] | Next.js web portal |

## Linked Feature Requests

| FR-ID | Title | Gate Status | RICE |
|-------|-------|------------|------|
| FR-001 | Telegram bot integration | gate-approved | 72 |
| FR-002 | Web portal with chat | gate-approved | 68 |
| FR-003 | Multi-provider AI support | gate-approved | 55 |

## Linked PRDs

| PRD-ID | Title | Version | Status |
|--------|-------|---------|--------|
| PRD-001 | AI PM Skills Platform | v1.0 | approved |

## Milestones

| ID | Milestone | Target Date | Status |
|----|-----------|------------|--------|
| M1 | Discovery complete | 15/05/2026 | Done |
| M2 | PRDs signed off | 01/06/2026 | Done |
| M3 | Telegram bot launched | 15/06/2026 | Done |
| M4 | Web portal launched | 01/07/2026 | In Progress |
| M5 | v1.0 Release | 01/08/2026 | Pending |

## North Star Metrics

| Metric | Baseline | Target | Source |
|--------|---------|--------|--------|
| PRDs created per PM per month | 0 | 4 | Analytics |
| Time to create a PRD | 4 hours | 30 minutes | User survey |
| PM satisfaction score | - | > 4.5/5 | NPS survey |

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| AI model rate limits on free tier | High | Medium | Multi-provider support, guide users to paid plans |
| Complex PM workflows hard to automate | Medium | High | Start with 80% of common workflows, iterate |

## Decision Log

| Date | Decision | Rationale | Owner |
|------|----------|----------|-------|
| 01/05/2026 | Use file-based workspace (markdown) | User owns data, no vendor lock-in, works with Claude Code | PM |
| 03/05/2026 | Python backend (FastAPI) reusing bot code | Avoid duplicating AI agent logic | TL |
| 05/05/2026 | CC BY-NC 4.0 license | Allow open use, prevent commercial copying | PM |
