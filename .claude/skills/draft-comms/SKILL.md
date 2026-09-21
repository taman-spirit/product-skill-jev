---
name: draft-comms
description: Draft stakeholder communication (email, Zalo, meeting summary) adapted to the stakeholder's preferred style. Use when user says "draft email", "draft message", "notify stakeholder", "communicate decision", or needs to send an update to a specific person.
---

# Draft Communications

## Opening Interview

When this skill is triggered, immediately say:

"Who is the recipient and what do you need to communicate? Give me the context and I'll draft the right message."

Wait for the answer. Do not assume the stakeholder or the topic.

If the user named a stakeholder but did not describe the content, ask:

"Got it - drafting for [Name]. What is the message about? Give me the key point you need them to understand or act on."

If the user described content but did not name a stakeholder, ask:

"Who is this going to? Give me a name or their SH-NNN ID."

## Process

Note: Read `_system/active-project.md` to get the current project folder name (e.g., my-projects/PROJ-001-ai-alignment).
If this file does not exist, ask the user: "Which project are you working on?"
All file paths below use [ACTIVE_PROJECT] as the project folder name.

1. Collect: recipient identity and communication context (from the interview above)
2. Read the stakeholder's SH-NNN file from `[ACTIVE_PROJECT]/stakeholders/` to get:
   - Communication style: formal / direct / async
   - Preferred channel
   - Decision history (to understand their priorities and past reactions)
   - Interest areas (what they care about most)
3. Draft the communication adapted to their style using the rules below
4. Show draft and wait for PM confirmation before any action

## Style Rules

**formal** (senior executives, legal/compliance team)
- Full respectful greeting appropriate to the recipient's seniority
- Complete sentences, no abbreviations
- Formal closing
- Lead with context before the request or decision

**direct** (technical leads, product peers)
- Bullet points with specific numbers
- State the decision first, then context
- No preamble or pleasantries

**async** (Zalo message, email update)
- Self-contained: recipient should not need to ask follow-up questions
- Include: what happened, what is needed from them (if anything), deadline

## Log After Sending

After the PM confirms the communication was sent:
1. Append to `[ACTIVE_PROJECT]/decisions/communication-log.md`
2. If a decision was communicated: append to `[ACTIVE_PROJECT]/decisions/decision-history.md`
3. Update the relevant SH-NNN file's Decision History section in [ACTIVE_PROJECT]/stakeholders/

## Checklist

- [ ] Recipient identified and SH-NNN file read
- [ ] Communication context collected from PM
- [ ] Style rules applied based on stakeholder profile
- [ ] Draft shown and PM confirmed
- [ ] Log updated after sending
