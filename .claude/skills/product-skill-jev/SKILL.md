---
name: product-skill-jev
description: Use TypeSafe AI's Jev System One model to turn unstructured text into typed judgments (Choice, Score, Noul) with calibrated probabilities. Use when the user says "Jev", "TypeSafe", "Nhật Nguyệt", "Nhat Nguyet", "System One", "classify this", "auto-triage", "auto-score", "confidence gate", "smart routing", or when a workflow needs a semantic decision that plain code cannot make and a full LLM call is too slow or too expensive.
---

# TypeSafe Jev

Jev is a System One model. It does not generate text and it does not explain itself.
It takes a **state** (the content to judge) plus a map of typed **questions**, and returns
typed answers with calibrated probabilities. Code owns the workflow, Jev supplies the
semantic judgment where ordinary code needs common sense.

Live docs are the source of truth: https://docs.typesafe.ai/llms.txt
Mintlify serves markdown by appending `.md` to any page path.

Ownership: Jev, the API, and the SDKs belong to TypeSafe AI. This skill is the Nhat Nguyet
wrapper around them, which is why the folder is `product-skill-jev` while every endpoint,
environment variable, package, and class name below is TypeSafe's. Those are real external
identifiers. Renaming them to match whoever owns the wrapper breaks every call.

## When to use Jev

Use Jev when all of these are true:

- The decision is a classification, a rating, or a yes/no over text
- The answer feeds an `if`, a sort, a filter, or a route
- Latency or cost matters. Jev responds in roughly 70 to 500 ms at $0.042 per MTok input, output tokens free

Do NOT use Jev when:

- The output must be prose. PRD bodies, research writeups, and stakeholder emails stay with the LLM.
- The rule is deterministic. Tag matching, ID allocation, and RICE arithmetic stay in code.
- The answer would write a file with no human review. See "Repo rules" below.

Rule of thumb: if you were about to write an LLM prompt that ends with "reply with only one
word" or "return JSON", that is a Jev question.

## Setup

API key from https://console.typesafe.ai/keys

Add to `.env` and `.env.example`:

```
TYPESAFE_API_KEY=
TYPESAFE_DEFAULT_MODEL=jev-latest
```

Python (bot and apps/backend):

```
pip install typesafe-sdk
```

TypeScript (apps/frontend, Node 20 or newer):

```
npm install @typesafe-ai/sdk
```

Both SDKs read `TYPESAFE_API_KEY` from the environment automatically.
Default base URL is `https://api.typesafe.ai`, default model is `jev-latest`.
Never call Jev from browser code. Keep the key server side, in a route handler or the backend.

## The three primitives

| Need | Primitive | Returns |
|------|-----------|---------|
| One of a defined set | `Choice` | `choice`, `probabilities`, `confidence` |
| Degree on an ordered scale | `Score` | `score` (float), `legend`, `probabilities`, `confidence` |
| Whether a condition holds | `Noul` | `noul`, a probability from 0 to 1. No separate confidence field. |

Key distinctions:

- `Choice` picks exactly one label. Its probabilities compare competing options, so include a
  no-match label when nothing may fit.
- `Score` returns a probability-weighted average, so `1.7` between levels 1 and 2 is normal and
  meaningful. Levels must be ordered and each must describe a concrete situation.
- `Noul` near 0.5 means "yes and no are equally likely", not "medium intensity". Use one Noul per
  label when several labels can be true at once.

Full request and response shapes, error types, and retry behaviour: `references/api-reference.md`

## Writing good questions

- Put the judgment in `instructions`, put the possible answers in `criteria`.
- Question IDs are for your code only. They are not sent to the model, so the meaning must be
  complete inside `instructions`.
- Give the question enough state to answer: source text, policy, identities, current facts.
  Prefer a named JSON object over one blob when the context has several parts.
- Reference nested state with backticked paths, for example `ticket.messages[0].text`.
- Ask one narrow judgment per question. Split independent dimensions into separate questions.
- All questions in one request run in parallel against the same state and cannot see each
  other's answers. Adding questions barely changes latency.
- Send a second request only when an answer is needed to fetch new evidence or build new state.

## Confidence gating

`Choice` and `Score` return `confidence` from 0 to 1, derived from how concentrated the
probability distribution is. Treat these as starting bands and tune them on real data.

| Confidence | Behaviour |
|------------|-----------|
| Above 0.9 | Act automatically |
| 0.5 to 0.9 | Proceed but surface the answer to the PM for confirmation |
| Below 0.5 | Do not act. Fall back to the interview, the LLM, or a human. |

For `Noul` there is no confidence field. Gate on the probability itself, for example act on
`noul > 0.85`, escalate between 0.15 and 0.85, treat below 0.15 as a clear no.

Raise the threshold when the consequence is expensive. A read-only suggestion can act at 0.7.
Anything that writes a file, changes a status, or notifies a stakeholder needs 0.9 or a human.

Confidence describes distribution shape, not truth. Typed output guarantees the interface, not
the answer. Validate on representative cases from this repo before trusting a threshold.

## Applying Jev to the AI PM workflows

| Workflow | Jev's job | Never |
|----------|-----------|-------|
| `create-fr` | Classify the incoming idea, flag it if it is really a CR | Write the FR file unreviewed |
| `score-feature` | Suggest bands for Reach, Impact, Effort as interview starters | Replace the RICE interview or fill a value the PM did not confirm |
| `gate-review` | Check the research doc has a real Security section, rate research depth | Pass a gate on Jev's word alone |
| `conflict-check` | Judge whether two PRDs sharing a tag actually collide, and how badly | Skip the deterministic tag match. Jev ranks, code detects. |
| `assess-cr` | Rate scope impact, pick the affected area, flag whether a new PRD version is needed | Approve or reject a CR |
| `add-stakeholder`, `draft-comms` | Route incoming feedback by type and urgency | Send an email |

Ready-to-use question sets for each row, with thresholds: `references/pm-recipes.md`

## Repo rules

These override anything in the TypeSafe docs.

1. **Draft first, always.** `CLAUDE.md` requires showing a draft and waiting for PM confirmation
   before writing any file. A Jev answer is a draft input, never a committed value.
2. **RICE inputs are never guessed.** `score-feature` forbids assuming Reach, Impact,
   Confidence, or Effort. Jev may pre-fill the interview as a visible suggestion labelled
   "suggested", and the PM must confirm or change each one.
3. **Centralize questions and thresholds.** Put every question definition and every threshold in
   one module so a PM can review them without reading call sites. Suggested home:
   `_system/jev-questions.md` for the documented set, and one constants file per app.
4. **Log the answer, not just the decision.** When a Jev judgment influences a written document,
   record the question ID, the answer, and the confidence in the document's change log so the
   decision can be audited later.
5. **Fail open to the human.** On a Jev API error, timeout, or low confidence, fall back to the
   existing manual flow. Never block a PM workflow on the API being up.
6. **Document formatting still applies.** Anything Jev output reaches must follow `CLAUDE.md`:
   no emoji, no em-dash, no semicolon, hyphen bullets, dates as DD/MM/YYYY.

## Checklist

- [ ] Confirmed the decision is a judgment, not a deterministic rule
- [ ] Chose the primitive by what the answer means, not by habit
- [ ] Question carries its full meaning in `instructions`, criteria cover a no-match case
- [ ] State includes every fact the question needs, structured as named fields
- [ ] Independent questions batched into one request
- [ ] Confidence threshold set from the cost of being wrong, not copied from the docs
- [ ] Fallback path defined for low confidence and for API failure
- [ ] Question definitions and thresholds live in one reviewable place
- [ ] Draft shown to the PM before any file is written
- [ ] Tested on real examples from this repo, not invented ones
