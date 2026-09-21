# Jev Recipes for the AI PM Workflows

Each recipe gives the state to send, the questions to ask, and what to do with the answers.
All of them produce a draft for the PM. None of them write a file on their own.

Thresholds below are starting points. Measure them on real items from `my-projects/` before
treating them as settled, and keep the final numbers in one reviewable constants file.

---

## 1. FR intake triage

Used by `create-fr`. Runs once when an idea arrives, before the FR file is drafted.

State:

```python
state = {
    "idea": raw_text_from_pm,
    "active_project": "PROJ-001-ai-alignment",
    "existing_prd_titles": [ ... titles in this project ... ],
}
```

Questions:

```python
{
  "category": Choice(
      instructions="Which part of the product does `idea` change?",
      criteria={
          "new_capability": "Introduces behaviour the product does not have yet.",
          "improvement": "Changes how an existing capability already works.",
          "bug_or_gap": "Fixes something already specified but not working.",
          "non_product": "Process, tooling, or internal request, not a product change.",
      },
  ),
  "is_really_a_cr": Noul(
      instructions="Is `idea` a modification to one of `existing_prd_titles` rather than a standalone feature?",
      criteria={
          "true": "It changes the scope of an existing PRD.",
          "false": "It stands on its own as a new feature request.",
      },
  ),
  "touches_security": Noul(
      instructions="Does `idea` involve authentication, authorization, personal data, payments, or audit logging?",
  ),
  "clarity": Score(
      instructions="How ready is `idea` to be written up as a Feature Request?",
      criteria=[
          "A one-line wish with no problem, user, or outcome stated.",
          "A problem is described but the user or the outcome is missing.",
          "Problem, affected user, and desired outcome are all stated.",
      ],
  ),
}
```

Use the answers:

- `category` at confidence above 0.85 pre-fills the FR type field, otherwise leave it blank and ask.
- `is_really_a_cr` above 0.8 triggers the existing proactive behaviour: suggest `intake-cr`
  instead of creating a new FR.
- `touches_security` above 0.6 sets a flag so `gate-review` will require the Security
  section. Threshold is deliberately low because missing this is more expensive than a false alarm.
- `clarity` below 1.0 means run the clarifying interview before drafting anything.

---

## 2. RICE interview pre-fill

Used by `score-feature`. This recipe has the strictest rule in the repo.

`score-feature` states: "Do NOT guess or assume any of these values." Jev does not change that.
Jev produces a **suggested starting point that is shown to the PM inside the question**, and the
PM's answer is what gets recorded. If confidence is below 0.7, show no suggestion at all.

State: the full FR file text, plus the research doc when one exists.

Questions:

```python
{
  "reach_band": Score(
      instructions="How many users or transactions per sprint does this feature affect?",
      criteria=[
          "A single user or a rare edge case.",
          "A small named subset of users.",
          "A large share of active users.",
          "Effectively the entire user base.",
      ],
  ),
  "impact_band": Score(
      instructions="How much does this change a single affected user's outcome?",
      criteria=[
          "Barely noticeable.",
          "A small convenience.",
          "A clear improvement to how the work gets done.",
          "Removes a blocker or unlocks work that was impossible.",
      ],
  ),
  "effort_band": Score(
      instructions="How much engineering work does this feature require, judging only from what is described?",
      criteria=[
          "Under one person-week.",
          "One to three person-weeks.",
          "Four to eight person-weeks.",
          "More than two person-months, or the scope is not yet bounded.",
      ],
  ),
  "evidence_strength": Score(
      instructions="What evidence backs the claims in this request?",
      criteria=[
          "Opinion only, no data referenced.",
          "Anecdote or a single report from one user.",
          "Data or research is referenced.",
          "Measured results from a prior change are cited.",
      ],
  ),
}
```

Use the answers:

- Map each band to the scale in `score-feature`, then present it as
  `Question 1 - Reach: ... (suggested: 7, from the FR text. Confirm or change.)`
- `evidence_strength` maps to the Confidence percentage the same way, and this one is the safest
  to suggest because it is a property of the document rather than a forecast.
- Record in the RICE file which values the PM changed from the suggestion. That is the data you
  need later to decide whether the suggestions are worth keeping.

---

## 3. Conflict check

Used by `conflict-check`. Code still does the tag match. Jev only judges the pairs that the
tag match already surfaced, so Jev never causes a missed conflict.

State, one request per candidate pair:

```python
state = {
    "sprint": "S12",
    "shared_tag": "#auth",
    "prd_a": {"id": "PRD-004", "title": ..., "scope": ..., "out_of_scope": ...},
    "prd_b": {"id": "PRD-009", "title": ..., "scope": ..., "out_of_scope": ...},
}
```

Questions:

```python
{
  "is_real_conflict": Noul(
      instructions="Do `prd_a` and `prd_b` change the same thing in a way that one would break or rework the other if both ship in `sprint`?",
      criteria={
          "true": "They modify the same module, contract, or surface in incompatible ways.",
          "false": "They share the tag but touch separate areas or compose cleanly.",
      },
  ),
  "conflict_type": Choice(
      instructions="If `prd_a` and `prd_b` collide, what collides?",
      criteria={
          "data_model": "Both change the same schema, entity, or stored shape.",
          "api_contract": "Both change the same endpoint, payload, or interface.",
          "ui_surface": "Both change the same screen or component.",
          "sequencing": "One must ship before the other to work at all.",
          "none": "They do not collide.",
      },
  ),
  "severity": Score(
      instructions="If both ship in `sprint` with no coordination, how bad is the outcome?",
      criteria=[
          "Minor rework, caught in review.",
          "One team redoes work already done.",
          "A release is blocked or a regression reaches users.",
      ],
  ),
}
```

Use the answers:

- `is_real_conflict` below 0.3 downgrades the pair to a note rather than a CONFLICT block.
  Do not drop it entirely. The tag match found it, so the PM still sees it.
- Above 0.7, emit the CONFLICT block from `CLAUDE.md` and use `conflict_type` to fill the
  "Both touch [module]" slot and `severity` to fill "Risk: [impact]".
- Between 0.3 and 0.7, emit the block and label it "possible conflict, needs PM judgment".

---

## 4. CR assessment

Used by `assess-cr`.

State: the CR intake text, plus the current PRD scope and version.

Questions:

```python
{
  "affected_area": Choice(
      instructions="What does this change request actually change in the PRD?",
      criteria={
          "scope": "Adds or removes functionality.",
          "acceptance_criteria": "Changes how existing functionality is verified.",
          "design": "Changes the interface or flow but not what the feature does.",
          "timeline": "Changes only when the work happens.",
          "clarification": "Restates something already implied, no real change.",
      },
  ),
  "scope_impact": Score(
      instructions="How much does this change request expand the work already committed in the PRD?",
      criteria=[
          "No additional work.",
          "A small addition inside the existing plan.",
          "A meaningful addition that changes the estimate.",
          "Large enough that it should be its own feature request.",
      ],
  ),
  "needs_major_version": Noul(
      instructions="Does this change the intent of the PRD rather than refine it?",
      criteria={
          "true": "A reader of the old version would be misled about what is being built.",
          "false": "The original intent still holds, the detail is refined.",
      },
  ),
  "creates_new_tag": Noul(
      instructions="Does this change request pull in a module or area the PRD did not previously touch?",
  ),
}
```

Use the answers:

- `affected_area` = `clarification` at confidence above 0.9 suggests handling it as a PRD edit
  note rather than a full CR.
- `scope_impact` at level 3 triggers the existing proactive behaviour: suggest this belongs in
  `create-fr` as a new FR.
- `needs_major_version` above 0.8 suggests v2.0 in `version-doc`, otherwise v1.1.
  The PM confirms the version number either way.
- `creates_new_tag` above 0.7 re-runs `conflict-check` for the current sprint. This
  implements proactive behaviour 3 from `CLAUDE.md`.

---

## 5. Gate review readiness

Used by `gate-review`. Compliance is mandatory, so this recipe is a pre-check that can
only block, never pass.

State: the research document, plus the FR and the RICE result.

Questions:

```python
{
  "has_security_section": Noul(
      instructions="Does the research document contain a section that analyses security, privacy, or compliance implications with specific findings?",
      criteria={
          "true": "A section exists and states actual findings or risks.",
          "false": "No such section, or a heading with no substance under it.",
      },
  ),
  "research_depth": Score(
      instructions="How thoroughly does the research document support the decision to build?",
      criteria=[
          "Restates the feature request with no new information.",
          "Some investigation, but key questions are left open.",
          "Alternatives considered and the recommendation is justified.",
          "Alternatives, risks, and measured evidence all present.",
      ],
  ),
  "open_questions_remain": Noul(
      instructions="Does the document leave a question open that would change the build decision if answered differently?",
  ),
}
```

Use the answers:

- `has_security_section` below 0.5 blocks the gate. This is proactive behaviour 6 in `CLAUDE.md`.
  Between 0.5 and 0.85, flag it for the PM to confirm rather than blocking outright.
- `research_depth` below 1.5 produces a written list of what is missing, not a pass or fail.
- `open_questions_remain` above 0.7 asks the PM to name the question before the gate proceeds.
- A clean result on all three does not pass the gate. It only removes the automated objections.

---

## 6. Stakeholder feedback routing

Used by the "add feedback from [name]" command and `draft-comms`.

State:

```python
state = {
    "feedback": raw_text,
    "from": "SH-003 Robert, Engineering Lead",
    "context": "PRD-004 is in review this sprint",
}
```

Questions:

```python
{
  "feedback_type": Choice(
      instructions="What is `from` doing in `feedback`?",
      criteria={
          "blocker": "Stating an objection that must be resolved before work proceeds.",
          "concern": "Raising a risk without blocking.",
          "suggestion": "Proposing an addition or alternative.",
          "approval": "Agreeing or signing off.",
          "question": "Asking for information only.",
      },
  ),
  "urgency": Score(
      instructions="How soon does `feedback` need a response?",
      criteria=[
          "Can be answered in the next regular update.",
          "Should be answered this week.",
          "Blocks work until answered.",
      ],
  ),
  "implies_cr": Noul(
      instructions="Does acting on `feedback` require changing a document that is already approved?",
  ),
}
```

Use the answers:

- `feedback_type` = `blocker` at confidence above 0.8 files the feedback and immediately suggests
  `intake-cr` or a decision entry.
- `urgency` at level 2 surfaces the item at the top of the project status view.
- `implies_cr` above 0.75 offers to draft the CR. It never creates one.
- All five types are mutually exclusive by design. If feedback genuinely contains two of them,
  the confidence will be low, which is the signal to split it into two entries and re-run.

---

## Implementation notes

- Batch every question for one item into a single request. All six recipes above are one
  request each, which is one round trip of roughly 70 to 500 ms.
- Keep question definitions in one module per app and reference them by constant, never inline
  at the call site. A PM should be able to review every question the system asks by opening one file.
- When a Jev answer influences a written document, append a line to that document's change log
  giving the question ID, the answer, and the confidence.
- The PM documents in `my-projects/` are Vietnamese in places. Keep `instructions` and `criteria`
  in English and put the Vietnamese text in `state`. English is Jev's primary training language.
- Before rolling a recipe out, run it over at least ten real items from `my-projects/` and compare
  against what the PM decided. Adjust the criteria wording first, the thresholds second.
