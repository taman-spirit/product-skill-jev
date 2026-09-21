---
name: add-stakeholder
description: Build a stakeholder persona through a structured interview. The PM describes the person in their own words - Claude extracts what it can and asks only what is still missing. Creates a full SH-NNN profile and places them in the Power/Interest matrix. Use when user says "add stakeholder", "add persona", "describe stakeholder", or introduces a person who influences product decisions.
---

# Add Stakeholder

## How It Works

The PM describes the stakeholder in natural language. Claude extracts every piece of information it can from the description, then asks only for what is genuinely missing - never repeats what was already given.

Example:
```
PM: "Add A - he'a head of product, very senior, signs off on all product decisions. Hard to get time with him. Prefers executive summaries,
     not detailed docs. Cares most about system performance and security."

Claude extracts:
  Name: A
  Title: head of product
  Power: high (signs off product)
  Interest: medium (hard to get time)
  Communication style: direct / async (executive summaries)
  Interest areas: performance, security

Claude asks only:
  - Which org unit is he in?
  - Does he prefer email, Slack, or another channel?
  - Any past decisions or known preferences worth capturing?
```

---

## Process

### Step 1 - Get Description

If the PM has not described the stakeholder yet, ask:
```
Tell me about this stakeholder. Describe them in your own words:
who they are, what they care about, how they like to communicate,
and how much influence they have over your product decisions.
```

Accept free-form text. The richer the description, the fewer follow-up questions needed.

### Step 2 - Extract What You Know

From the PM's description, extract every field you can infer:

| Field | How to infer |
|-------|-------------|
| Name and title | Directly stated |
| Power level | "signs off", "approves", "blocks", "influences", "is informed" |
| Interest level | How engaged they are: "very involved", "hard to reach", "checks in occasionally" |
| Communication style | "formal", "direct", "prefers summaries", "async", "wants detailed reports" |
| Interest areas | Topics mentioned: "cares about security", "focused on timeline", "wants UX data" |
| Decision history | Any past decisions or stances the PM mentions |

### Step 3 - Ask Only What Is Missing

Ask for missing fields one group at a time, not one by one. Combine related questions.

**Round A** (identity - if missing):
```
A few quick questions to complete the profile:
1. Which team or org unit are they in?
2. Preferred contact channel: email / Slack / Zalo / meeting?
```

**Round B** (depth - optional but valuable):
```
Optional - helps build a more useful profile:
1. What is the one thing they always push back on?
2. Any known past decisions or stances worth remembering?
3. What does a good update look like for them - dashboard, 1-pager, or meeting?
```

Do not ask Round B if the PM says "that's enough" or seems in a hurry.

### Step 4 - Determine Quadrant

Map Power + Interest to a quadrant:

```
High Power + High Interest  ->  Manage Closely   (key approvers, active sponsors)
High Power + Low Interest   ->  Keep Satisfied   (executives, sign-off required)
Low Power + High Interest   ->  Keep Informed    (advocates, power users, allies)
Low Power + Low Interest    ->  Monitor          (peripheral stakeholders)
```

If unsure about power vs interest level, ask the PM:
```
Quick check: can [name] block or delay this project if they are unhappy?
  Yes -> Power: high
  No, but they care a lot -> Power: low / Interest: high
  No, and they are not very involved -> Power: low / Interest: low
```

### Step 5 - Show Draft Persona

Show the full draft before writing:

```
SH-NNN - [Name]

Role: [Title], [Org Unit]
Quadrant: [Manage Closely / Keep Satisfied / Keep Informed / Monitor]
Power: [high/medium/low] | Interest: [high/medium/low]

Communication:
  Style: [formal / direct / async]
  Channel: [email / Slack / Zalo / meeting]
  Format: [executive summary / detailed report / dashboard]

Cares most about:
  [Topic 1], [Topic 2], [Topic 3]

Known preferences / past decisions:
  [What PM shared, or "None captured yet"]

Tags: #[relevant tags from tags-registry]

Confirm or adjust?
```

### Step 6 - Write Files

Note: Read `_system/active-project.md` to get the current project folder name (e.g., my-projects/PROJ-001-ai-alignment).
If this file does not exist, ask the user: "Which project are you working on?"
All file paths below use [ACTIVE_PROJECT] as the project folder name.

After PM confirms:

1. Write `[ACTIVE_PROJECT]/stakeholders/SH-NNN-[name-slug].md`
2. Update `[ACTIVE_PROJECT]/stakeholders/interest-map.md` - add to correct quadrant
3. Update PROJECT.md Team section in [ACTIVE_PROJECT]/

**SH-NNN file structure:**
```markdown
---
sh-id: SH-NNN
name: [Full Name]
title: [Title]
org: [Org Unit]
power: high | medium | low
interest: high | medium | low
quadrant: manage-closely | keep-satisfied | keep-informed | monitor
communication-style: formal | direct | async
channel: email | slack | zalo | meeting
created: DD/MM/YYYY
linked-projects: []
---

# SH-NNN - [Name]

## Role and Influence
[Title], [Org Unit]
[1-2 sentences on their scope of authority and how they interact with the product]

## What They Care About
- [Topic 1]: [Brief context - why this matters to them]
- [Topic 2]: [Brief context]
- [Topic 3]: [Brief context]

## Communication Preferences
- Style: [formal / direct / async]
- Channel: [preferred channel]
- Best format: [executive summary / detailed doc / live demo / dashboard]
- Best time to reach: [if known]

## Known Positions and Past Decisions

| Date | Topic | Stance / Decision | Source |
|------|-------|------------------|--------|
| - | - | - | - |

## Working Notes
[Any other context the PM shared - personality, history, preferences]
```

---

## Commands

| What PM says | What Claude does |
|-------------|-----------------|
| "Add stakeholder [name]" | Start interview from scratch |
| "Add [name], he's VP of X who cares about Y" | Extract from description, ask only gaps |
| "Update SH-NNN, he now prefers async comms" | Update specific field, re-sync interest-map |
| "Who are the high-power stakeholders?" | Read interest-map.md, return Manage Closely + Keep Satisfied list |
| "Who cares about #security?" | Scan all SH files for that tag/topic, rank by power |
| "Log decision: [name] approved X on DD/MM" | Append to SH-NNN Decision History + decision-history.md |

---

## Checklist

- [ ] SH-ID confirmed from folder scan
- [ ] Description received and fields extracted
- [ ] Only missing fields asked (no repeating what PM already said)
- [ ] Power/Interest quadrant determined with PM agreement
- [ ] Draft persona shown and PM confirmed
- [ ] SH-NNN file written to [ACTIVE_PROJECT]/stakeholders/
- [ ] [ACTIVE_PROJECT]/stakeholders/interest-map.md updated in correct quadrant
- [ ] Project team section updated in [ACTIVE_PROJECT]/

---

## Feedback Log (appended to SH-NNN file when feedback is captured)

When feedback is received from a stakeholder, append this section to their profile file:

```markdown
## Feedback Log

### DD/MM/YYYY - [Topic / Document name]
Feedback: [exact words or clear paraphrase]
Context: [which meeting, document, or discussion this came from]
Sentiment: Positive | Concern | Blocking | Suggestion
Related: PRD-NNN, PROJ-NNN, EP-NNN (whichever apply)
Action taken: [updated PRD-001 Section 8 / saved only / pending PM review]
```

After appending feedback, always run the document scan (see TOOL_CONTEXT stakeholder feedback flow).
