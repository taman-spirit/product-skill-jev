---
name: score-feature
description: Calculate RICE and ICE scores for a Feature Request. Use when the user says "score", "rate this feature", "calculate RICE", "prioritize FR-NNN", or mentions a Feature Request needing a priority score.
---

# Score Feature

## Formula

**RICE = (Reach x Impact x Confidence%) / Effort**

| Input | Scale | Definition |
|-------|-------|-----------|
| Reach | 1-10 | Users/transactions affected per sprint. 10 = entire user base |
| Impact | 0.25 / 0.5 / 1 / 2 / 3 | Minimal / Low / Medium / High / Massive |
| Confidence | 20% / 50% / 80% / 100% | Guess / Some data / Clear evidence / Proven |
| Effort | person-weeks | 1 = one developer for one week |

**ICE = Impact x Confidence x Ease**
- Ease: 1-10 (10 = very easy to implement)

## Interview Flow

When scoring begins, read the FR file first. Then open the scoring session with:

"To calculate the RICE score for [feature name], I need a few inputs from you. Let's go through them one at a time.

**Question 1 -- Reach:** On a scale of 1 to 10, how many users or transactions does this feature affect per sprint? (1 = a small subset, 10 = your entire user base)

I'll ask about Impact, Confidence, and Effort after you answer this one."

After each answer, confirm understanding and move to the next:

- "**Question 2 -- Impact:** Which best describes the per-user impact? Options: 0.25 (Minimal), 0.5 (Low), 1 (Medium), 2 (High), 3 (Massive)."
- "**Question 3 -- Confidence:** How confident are you in these estimates? Options: 20% (gut feel), 50% (some data), 80% (clear evidence), 100% (already proven)."
- "**Question 4 -- Effort:** How many person-weeks to build this feature? (1 = one developer, one week)"
- "**Question 5 -- Ease (for ICE):** On a scale of 1 to 10, how easy is this to implement? (10 = very straightforward, no blockers)"

Do NOT guess or assume any of these values. If the PM is unsure, explain the scale again with examples before accepting an answer.

## Process

Note: Read `_system/active-project.md` to get the current project folder name (e.g., my-projects/PROJ-001-ai-alignment).
If this file does not exist, ask the user: "Which project are you working on?"
All file paths below use [ACTIVE_PROJECT] as the project folder name.

1. Read the FR file referenced by the PM
2. Run the interview above for any missing inputs -- do NOT guess Impact or Reach
3. Calculate both RICE and ICE, showing the full formula
4. Show the draft result and wait for PM confirmation before writing files
5. Write output to `[ACTIVE_PROJECT]/discovery/scoring/RICE-NNN-[slug].md`
6. Update `[ACTIVE_PROJECT]/discovery/scoring/scoring-dashboard.md`

## Output Format

```
RICE Score: [value]
Formula: ([Reach] x [Impact] x [Confidence]%) / [Effort] = [result]

ICE Score: [value]
Formula: [Impact] x [Confidence] x [Ease] = [result]

Recommendation: [ELIGIBLE / NEEDS RESEARCH / RECOMMEND REJECT]
Rationale: [1-2 sentences]
```

## Gate Thresholds

- RICE >= 40: eligible for Discovery Gate
- RICE 20-39: proceed to research before gate
- RICE < 20: recommend reject -- proactively suggest whether the idea fits better as a CR on an existing PRD

## Checklist

- [ ] FR file read and understood
- [ ] All 4 RICE inputs confirmed with PM through interview (not assumed)
- [ ] Ease confirmed for ICE calculation
- [ ] Both RICE and ICE calculated with formula shown
- [ ] Draft shown and PM confirmed before writing
- [ ] RICE-NNN file written to [ACTIVE_PROJECT]/discovery/scoring/
- [ ] scoring-dashboard.md updated
