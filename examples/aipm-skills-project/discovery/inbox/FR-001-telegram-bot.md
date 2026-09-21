---
fr-id: FR-001
project: PROJ-001
title: Telegram Bot Integration
status: gate-approved
source: stakeholder
requested-by: PM Team
created: 01/05/2026
rice-score: 72
gate-status: gate-approved
linked-prd: PRD-001
---

# FR-001 - Telegram Bot Integration

## Problem Statement

Product Managers need to capture ideas and run PM workflows from anywhere — not just at their desk. Current tools require opening a browser, logging in, and navigating complex interfaces. This adds friction and means ideas get lost.

## Users Affected

- Product Managers (primary) — 100% of target users
- Engineering leads who need PRD updates — 30% of target users

## Current Situation

PMs use notebooks, voice memos, or email-to-self to capture ideas on the go. These never make it into structured documents.

## Requested Solution

A Telegram bot that allows PMs to:
- Create feature requests by describing them in natural language
- Get RICE scores through a quick 4-question conversation
- Check project status and next steps
- Receive AI-generated next step suggestions after each action

## Source

PM team internal discussion, May 2026.

## Notes

- Should work offline (queue messages when disconnected)
- Must support file attachments (send a PDF, bot reads it)
- Response time target: < 10 seconds for simple commands
