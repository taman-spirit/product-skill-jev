"""
TypeSafe Jev integration for the PM bot.

Jev, the API, and the SDKs belong to TypeSafe AI. Nhat Nguyet maintains this
integration and the product-skill-jev skill that documents it. The TYPESAFE_
names below are TypeSafe's real identifiers, so do not rebrand them.

Jev is a System One model. It does not generate text. It takes a state plus a
map of typed questions and returns typed answers with calibrated probabilities.
Code owns the workflow, Jev supplies the semantic judgment.

Every question the bot asks Jev and every threshold it applies lives in this
file. A PM should be able to review the whole behaviour by reading this module,
without opening a single call site.

The bot must keep working when Jev is unavailable. Every public function here
returns None on a missing key, a timeout, an API error, or a malformed
response, and callers fall back to the flow that existed before.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("pm-bot.jev")

# -inf, not 0.0: time.monotonic() starts near zero in a new process, so 0.0
# would read as "loaded a moment ago" and serve an empty cache on startup.
_NEVER_LOADED = float("-inf")
_settings_cache: tuple[float, dict] = (_NEVER_LOADED, {})

API_KEY_ENV = "TYPESAFE_API_KEY"
DEFAULT_BASE_URL = "https://api.typesafe.ai"
MODEL = os.environ.get("TYPESAFE_DEFAULT_MODEL", "jev-latest")

# The web portal writes Jev settings here. The bot and the backend both mount the
# workspace, so one key set in the UI reaches both without any syncing.
SETTINGS_DB = "_system/settings.db"
DEFAULT_WORKSPACE = "/workspace"

# Settings are read on the request path, so they are cached briefly. A change made
# in the UI takes effect within this window without a restart.
SETTINGS_CACHE_SECONDS = 3.0

# A person is waiting in a chat window. A judgment that arrives late is worse
# than no judgment at all, so this is deliberately tighter than the 10 second
# SDK default. We also do not retry: a retry would double the wait on the one
# path where latency is most visible.
TIMEOUT_SECONDS = float(os.environ.get("TYPESAFE_TIMEOUT", "3.0"))


def _load_settings() -> dict:
    """Read what the web portal saved, or {} when there is nothing to read.

    Never raises and never writes. A missing file, a missing table, a locked
    database, or a corrupt row all mean "no settings", which leaves the
    environment variables and the measured defaults in charge.
    """
    global _settings_cache
    now = time.monotonic()
    cached_at, cached = _settings_cache
    if now - cached_at < SETTINGS_CACHE_SECONDS:
        return cached

    settings: dict = {}
    path = Path(os.environ.get("WORKSPACE_PATH", DEFAULT_WORKSPACE)) / SETTINGS_DB
    if path.is_file():
        try:
            conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=1.0)
            try:
                rows = conn.execute("SELECT name, value FROM jev_settings").fetchall()
                settings = {name: value for name, value in rows}
            finally:
                conn.close()
        except Exception as e:
            logger.debug("Jev settings unreadable, using environment: %s", e)

    _settings_cache = (now, settings)
    return settings


def reset_settings_cache() -> None:
    """Drop the cache so the next read hits the database. For tests and for the
    backend to call right after it writes."""
    global _settings_cache
    _settings_cache = (_NEVER_LOADED, {})


def is_enabled() -> bool:
    """False only when the portal explicitly turned Jev off."""
    return _load_settings().get("enabled", "1") != "0"


def api_key() -> str:
    """The portal's key when it set one, otherwise the environment."""
    return _load_settings().get("api_key") or os.environ.get(API_KEY_ENV, "")


def base_url() -> str:
    return (
        _load_settings().get("base_url")
        or os.environ.get("TYPESAFE_BASE_URL")
        or DEFAULT_BASE_URL
    )


# ── Thresholds ────────────────────────────────────────────────────────────────
#
# Measured on 13 labelled messages against jev-1.13.0: intent 9/9 on command
# messages, feedback 12/13, no false positives. Re-measure after any change to
# the questions below. Raise a threshold when being wrong gets expensive.
#
# The one miss is worth knowing about. "Chi Hoa hoi bao gio co ban demo" returns
# none at 0.71 against question at 0.29, while the same sentence in English
# returns question at 0.95. Lowering the threshold does not fix that, the model
# picked the wrong label outright. It is the accuracy gap on Vietnamese that the
# API reference warns about, and it costs a missed hint, never a wrong action.

# Intent only picks which command hints to show and which flow the agent leans
# towards. Nothing is written on its own. The alternative when Jev declines is
# keyword matching, which is weaker, so the bar here is "better than keywords"
# rather than "certainly right". 0.5 is the floor below which we do not act.
INTENT_MIN_CONFIDENCE = 0.5

# Feedback type steers whether the agent offers to raise a CR, so it carries a
# real consequence for the PM. Recipe 6 in the skill uses 0.8 for this.
FEEDBACK_TYPE_MIN_CONFIDENCE = 0.8

# Score questions are 0 indexed. Level 2 of 3 means "blocks work until
# answered", which is what promotes an item to the top of the status view.
URGENCY_BLOCKING_LEVEL = 1.5


# ── Questions ─────────────────────────────────────────────────────────────────
#
# Question IDs are for this code only, they are never sent to the model, so each
# `instructions` string has to carry its full meaning on its own. All three run
# in parallel against the same state in a single request, so adding one barely
# changes latency. They cannot see each other's answers, which is why the
# conditional logic below lives in Python rather than in the questions.

# Labels match the keys of COMMAND_HINTS in bot.py. Keep the two in step.
MESSAGE_QUESTIONS = {
    "intent": {
        "type": "choice",
        "instructions": (
            "A product manager sent `message` to a product management assistant "
            "that manages projects, feature requests, PRDs, epics, change "
            "requests, and stakeholders as markdown files. Which area of that "
            "system is the manager trying to act on? `recent_turns` holds the "
            "last few turns of the conversation for context when `message` is "
            "a short follow up."
        ),
        "criteria": {
            "project": "Creating, listing, opening, or checking the status of a project.",
            "feature": "A feature request, a RICE or ICE score, research, or a discovery gate.",
            "prd": (
                "Writing, reviewing, grilling, versioning, or approving a product "
                "requirements document as a whole."
            ),
            "epic": "An epic, a user story, or acceptance criteria under a PRD.",
            "change": (
                "Changing, adding to, or removing from the scope of a PRD that "
                "already exists, or handling a change request that does so."
            ),
            "stakeholder": "A person: their profile, their feedback, or a message to send them.",
            "other": "None of the above, or the message is too vague to place.",
        },
    },
    "feedback_type": {
        "type": "choice",
        "instructions": (
            "A product manager typed `message` into a product management "
            "assistant. Most messages are instructions to that assistant. A few "
            "instead report how a named person reacted to the work. Only when "
            "`message` reports a named person's reaction, decide what that "
            "person is doing, judging their words rather than the manager's "
            "framing. Answer none for everything else, including any request, "
            "command, or question that is aimed at the assistant itself."
        ),
        "criteria": {
            "blocker": "Stating an objection that must be resolved before work proceeds.",
            "concern": "Raising a risk without blocking the work.",
            "suggestion": "Proposing an addition or an alternative.",
            "approval": "Agreeing, accepting, or signing off.",
            "question": "Asking for information only.",
            "none": (
                "An instruction, request, or question aimed at the assistant, or "
                "any message that reports no named person's reaction."
            ),
        },
    },
    "feedback_urgency": {
        "type": "score",
        "instructions": (
            "If `message` relays feedback from a stakeholder, how soon does that "
            "feedback need a response? Judge only the urgency of the feedback "
            "itself, not how quickly the product manager typed it."
        ),
        "criteria": [
            "Can be answered in the next regular update.",
            "Should be answered this week.",
            "Blocks work until it is answered.",
        ],
    },
}


# ── Document question sets ────────────────────────────────────────────────────
#
# These judge a document rather than a chat message, so the agent reaches them
# through the `judge` tool: only the agent has the file contents in hand. Every
# set below returns a draft input. None of them decides anything, and none of
# them may cause a file to be written without the PM confirming first.

FR_TRIAGE_QUESTIONS = {
    "category": {
        "type": "choice",
        "instructions": "Which part of the product does the idea in `idea` change?",
        "criteria": {
            "new_capability": "Introduces behaviour the product does not have yet.",
            "improvement": "Changes how an existing capability already works.",
            "bug_or_gap": "Fixes something already specified but not working.",
            "non_product": "Process, tooling, or an internal request, not a product change.",
        },
    },
    "is_really_a_cr": {
        "type": "noul",
        "instructions": (
            "Is `idea` a modification to one of the products described in "
            "`existing_work` rather than a feature that stands on its own?"
        ),
        "criteria": {
            "true": "It changes the scope of work that is already specified.",
            "false": "It stands on its own as a new feature request.",
        },
    },
    "touches_security": {
        "type": "noul",
        "instructions": (
            "Does `idea` involve authentication, authorization, personal data, "
            "payments, or audit logging?"
        ),
    },
    "clarity": {
        "type": "score",
        "instructions": "How ready is `idea` to be written up as a Feature Request?",
        "criteria": [
            "A one line wish with no problem, user, or outcome stated.",
            "A problem is described but the user or the outcome is missing.",
            "Problem, affected user, and desired outcome are all stated.",
        ],
    },
}

GATE_REVIEW_QUESTIONS = {
    "has_security_section": {
        "type": "noul",
        "instructions": (
            "Does the research document in `research_document` contain a section "
            "that analyses security, privacy, or compliance implications, with "
            "specific findings rather than a heading alone?"
        ),
        "criteria": {
            "true": "Such a section exists and states actual findings or risks.",
            "false": "No such section, or a heading with no substance under it.",
        },
    },
    "research_depth": {
        "type": "score",
        "instructions": (
            "How thoroughly does `research_document` support a decision to build "
            "the feature described in `feature_request`?"
        ),
        "criteria": [
            "Restates the feature request with no new information.",
            "Some investigation, but key questions are left open.",
            "Alternatives considered and the recommendation is justified.",
            "Alternatives, risks, and measured evidence are all present.",
        ],
    },
    "open_questions_remain": {
        "type": "noul",
        "instructions": (
            "Does `research_document` leave a question open that would change the "
            "decision to build if it were answered differently?"
        ),
    },
}

CR_ASSESSMENT_QUESTIONS = {
    "affected_area": {
        "type": "choice",
        "instructions": (
            "What does the change request in `change_request` actually change "
            "about the document in `current_prd`?"
        ),
        "criteria": {
            "scope": "Adds or removes functionality.",
            "acceptance_criteria": "Changes how existing functionality is verified.",
            "design": "Changes the interface or the flow but not what the feature does.",
            "timeline": "Changes only when the work happens.",
            "clarification": "Restates something already implied, no real change.",
        },
    },
    "scope_impact": {
        "type": "score",
        "instructions": (
            "How much does `change_request` expand the work already committed in "
            "`current_prd`?"
        ),
        "criteria": [
            "No additional work.",
            "A small addition inside the existing plan.",
            "A meaningful addition that changes the estimate.",
            "Large enough that it should be its own feature request.",
        ],
    },
    "needs_major_version": {
        "type": "noul",
        "instructions": (
            "Does `change_request` change the intent of `current_prd` rather than "
            "refine it?"
        ),
        "criteria": {
            "true": "A reader of the old version would be misled about what is being built.",
            "false": "The original intent still holds, the detail is refined.",
        },
    },
    "creates_new_tag": {
        "type": "noul",
        "instructions": (
            "Does `change_request` pull in a module or an area that `current_prd` "
            "did not previously touch?"
        ),
    },
}

CONFLICT_PAIR_QUESTIONS = {
    "is_real_conflict": {
        "type": "noul",
        "instructions": (
            "Do `document_a` and `document_b` change the same thing in a way that "
            "one would break or force rework of the other if both shipped in the "
            "same sprint?"
        ),
        "criteria": {
            "true": "They modify the same module, contract, or surface incompatibly.",
            "false": "They touch separate areas, or they compose cleanly.",
        },
    },
    "conflict_type": {
        "type": "choice",
        "instructions": "If `document_a` and `document_b` collide, what collides?",
        "criteria": {
            "data_model": "Both change the same schema, entity, or stored shape.",
            "api_contract": "Both change the same endpoint, payload, or interface.",
            "ui_surface": "Both change the same screen or component.",
            "sequencing": "One must ship before the other to work at all.",
            "none": "They do not collide.",
        },
    },
    "severity": {
        "type": "score",
        "instructions": (
            "If `document_a` and `document_b` both ship in the same sprint with no "
            "coordination between the teams, how bad is the outcome?"
        ),
        "criteria": [
            "No shared work. An isolated change.",
            "Minor rework, caught in review.",
            "One team redoes work it had already finished.",
            "A release is blocked, or a regression reaches users.",
        ],
    },
}

RICE_BAND_QUESTIONS = {
    "reach_band": {
        "type": "score",
        "instructions": (
            "Judging only from `feature_request` and `research_document`, how many "
            "users or transactions per sprint does this feature affect?"
        ),
        "criteria": [
            "A single user or a rare edge case.",
            "A small named subset of users.",
            "A large share of active users.",
            "Effectively the entire user base.",
        ],
    },
    "impact_band": {
        "type": "score",
        "instructions": "How much does this change a single affected user's outcome?",
        "criteria": [
            "Barely noticeable.",
            "A small convenience.",
            "A clear improvement to how the work gets done.",
            "Removes a blocker, or unlocks work that was impossible.",
        ],
    },
    "effort_band": {
        "type": "score",
        "instructions": (
            "How much engineering work does this feature require, judging only "
            "from what `feature_request` and `research_document` describe?"
        ),
        "criteria": [
            "Under one person week.",
            "One to three person weeks.",
            "Four to eight person weeks.",
            "More than two person months, or the scope is not yet bounded.",
        ],
    },
    "evidence_strength": {
        "type": "score",
        "instructions": "What evidence backs the claims in `feature_request`?",
        "criteria": [
            "Opinion only, no data referenced.",
            "Anecdote, or a single report from one user.",
            "Data or research is referenced.",
            "Measured results from a prior change are cited.",
        ],
    },
}

DOC_ROUTING_QUESTIONS = {
    "doc_kind": {
        "type": "choice",
        "instructions": (
            "A product manager uploaded a file and `document` is its text. What "
            "kind of document is it?"
        ),
        "criteria": {
            "feature_request": (
                "Asks for something to be built. States a problem, who it affects, "
                "and a wanted outcome, without investigating whether or how to build it."
            ),
            "research": (
                "Investigates a feature that someone already asked for. Weighs "
                "feasibility, alternatives, market, security, or compliance, and "
                "reports findings. Often closes with a recommendation, which does "
                "not make it a request."
            ),
            "prd": "Specifies a product in full: scope, epics, acceptance criteria.",
            "stakeholder_notes": "Records what named people said, wanted, or objected to.",
            "meeting_minutes": "A record of a meeting: attendees, discussion, actions.",
            "other": "None of the above, or the text is too short to tell.",
        },
    },
}


@dataclass
class Signals:
    """What Jev concluded about one incoming message.

    A field is None when Jev declined, when confidence fell under the threshold,
    or when the question did not apply. None always means "fall back", never
    "the answer is no".
    """

    intent: str | None = None
    intent_confidence: float = 0.0
    feedback_type: str | None = None
    feedback_confidence: float = 0.0
    urgency: float | None = None

    @property
    def is_blocking_feedback(self) -> bool:
        return (
            self.feedback_type == "blocker"
            or (self.urgency is not None and self.urgency >= T("URGENCY_BLOCKING_LEVEL"))
        )

    def audit_line(self) -> str:
        """One line for the log, so a judgment can be traced after the fact."""
        parts = []
        if self.intent:
            parts.append(f"intent={self.intent}@{self.intent_confidence:.2f}")
        if self.feedback_type:
            parts.append(f"feedback={self.feedback_type}@{self.feedback_confidence:.2f}")
        if self.urgency is not None:
            parts.append(f"urgency={self.urgency:.1f}/2")
        return " ".join(parts) or "no signals above threshold"

    def as_prompt_note(self) -> str | None:
        """An advisory block for the agent, or None when there is nothing to say.

        This is deliberately worded as a hint. CLAUDE.md requires a draft and a
        PM confirmation before any file is written, and a Jev answer is a draft
        input, never a committed value.
        """
        lines = []
        if self.intent:
            lines.append(f"- Topic: {self.intent} (confidence {self.intent_confidence:.2f})")
        if self.feedback_type:
            lines.append(
                f"- Stakeholder feedback type: {self.feedback_type} "
                f"(confidence {self.feedback_confidence:.2f})"
            )
        if self.urgency is not None:
            lines.append(f"- Feedback urgency: {self.urgency:.1f} of 2")
        if not lines:
            return None

        note = [
            "",
            "## Jev signals for the latest message",
            "",
            "A System One model classified the message before you saw it. These",
            "are probabilistic judgments, not facts. Use them to pick which flow",
            "to run and which Sentiment value to suggest. They do not authorise",
            "writing a file and they do not replace asking the PM to confirm.",
            "",
            *lines,
        ]
        if self.feedback_type and self.feedback_type != "none":
            note += [
                "",
                "Put the matching Sentiment in the feedback log entry: blocker maps",
                "to Blocking, concern to Concern, suggestion to Suggestion, approval",
                "to Positive. Show the draft and wait for confirmation as usual.",
            ]
        if self.is_blocking_feedback:
            note += [
                "",
                "This reads as blocking. After saving the feedback, offer to raise a",
                "change request or record a decision. Offer only, do not create one.",
            ]
        return "\n".join(note)


async def _system_one(state: dict, questions: dict) -> dict | None:
    """POST one request to Jev. Returns the answers map, or None on any failure."""
    if not is_enabled():
        return None
    key = api_key()
    if not key:
        return None

    try:
        import httpx
    except ImportError:
        logger.warning("httpx is not installed, Jev disabled")
        return None

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            resp = await client.post(
                f"{base_url()}/v1/systemone",
                headers={"Authorization": f"Bearer {key}"},
                json={"model": MODEL, "state": state, "questions": questions},
            )
            resp.raise_for_status()
            return resp.json().get("answers")
    except Exception as e:
        # Rule 5 of the skill: fail open to the human. A PM workflow is never
        # blocked on this API being up.
        request_id = ""
        response = getattr(e, "response", None)
        if response is not None:
            request_id = response.headers.get("x-typesafe-request-id", "")
        logger.warning(
            "Jev unavailable, falling back: %s%s",
            e,
            f" (request {request_id})" if request_id else "",
        )
        return None


def _choice(answers: dict, key: str, floor: float) -> tuple[str | None, float]:
    a = answers.get(key) or {}
    label, confidence = a.get("choice"), a.get("confidence", 0.0)
    if not label or confidence < floor:
        return None, confidence
    return label, confidence


async def analyze_message(text: str, recent_turns: list | None = None) -> Signals | None:
    """Classify one incoming PM message. Returns None when Jev is unavailable.

    Callers must treat None and an empty Signals the same way: keep doing what
    the bot did before Jev existed.
    """
    if not text or not text.strip():
        return None

    state: dict = {"message": text}
    if recent_turns:
        # Only the tail, and only the text, to keep the request small.
        state["recent_turns"] = [
            str(t.get("content", ""))[:500] for t in recent_turns if t.get("content")
        ]

    answers = await _system_one(state, MESSAGE_QUESTIONS)
    if not answers:
        return None

    signals = Signals()
    signals.intent, signals.intent_confidence = _choice(
        answers, "intent", T("INTENT_MIN_CONFIDENCE")
    )
    if signals.intent == "other":
        signals.intent = None

    feedback_type, confidence = _choice(
        answers, "feedback_type", T("FEEDBACK_TYPE_MIN_CONFIDENCE")
    )
    if feedback_type and feedback_type != "none":
        signals.feedback_type = feedback_type
        signals.feedback_confidence = confidence
        urgency = (answers.get("feedback_urgency") or {}).get("score")
        if isinstance(urgency, (int, float)):
            signals.urgency = float(urgency)

    return signals


# ── Document judgments ────────────────────────────────────────────────────────
#
# Thresholds for the document sets. They live here, next to the questions, and
# the agent never sees a raw number it has to reason about: judge() turns each
# answer into a sentence that states the consequence. That keeps the policy in
# reviewable code instead of spread through a prompt.

# Measured on realistic fixtures against jev-1.13.0: 8 of 9 document judgments
# as expected, document routing 6 of 6 at confidence 1.00. The case this set
# exists for, a research document with a Security heading and nothing under it,
# scores 0.05 and blocks the gate. Pair each research document with the feature
# request it is actually about when re-measuring: research_depth asks how well
# one supports the other, so a mismatched pair scores near zero and looks like
# a defect that is not there.
#
# Missing a security problem costs far more than a false alarm, so this one is
# deliberately generous. Below it the gate is blocked outright.
SECURITY_SECTION_BLOCKS_BELOW = 0.5
SECURITY_SECTION_CONFIRM_BELOW = 0.85
RESEARCH_DEPTH_THIN_BELOW = 1.5
OPEN_QUESTIONS_ASK_ABOVE = 0.7

FR_CATEGORY_PREFILL_ABOVE = 0.85
IS_REALLY_A_CR_ABOVE = 0.8
TOUCHES_SECURITY_FLAG_ABOVE = 0.6
CLARITY_INTERVIEW_BELOW = 1.0

CLARIFICATION_ONLY_ABOVE = 0.9
SCOPE_IMPACT_OWN_FR_ABOVE = 2.5
NEEDS_MAJOR_VERSION_ABOVE = 0.8
CREATES_NEW_TAG_ABOVE = 0.7

# A pair that both rewrite POST /auth/login measured 0.68 on one run and 0.73 on
# another, so it straddles this bar and its label flips between "yes" and
# "possible, needs PM judgment". The PM sees the same CONFLICT block either way,
# which is what makes the wobble tolerable. Left at the recipe's 0.7 on purpose:
# one run is not evidence for moving a threshold, and a band tuned to fit a
# single example stops meaning anything.
CONFLICT_REAL_ABOVE = 0.7
CONFLICT_NOTE_BELOW = 0.3

# Recipe 2 of the skill: below this, show the PM no RICE suggestion at all.
# score-feature forbids guessing, so a weak guess is worse than none.
RICE_SUGGEST_ABOVE = 0.7

DOC_ROUTING_ABOVE = 0.75

# A whole PRD is a fine thing to send. A pasted log file is not.
MAX_CONTENT_CHARS = 20000


# ── Threshold registry ────────────────────────────────────────────────────────
#
# The numbers above are the defaults, and they are what the comments next to
# them were measured against. The web portal can override any of them, which is
# why each entry carries the range it must stay inside and a sentence about what
# goes wrong when it moves. An override does not re-run the measurements, so a
# changed value invalidates the note that justified the default.

THRESHOLDS = {
    "INTENT_MIN_CONFIDENCE": {
        "default": INTENT_MIN_CONFIDENCE, "min": 0.0, "max": 1.0,
        "area": "Message", "label": "Intent routing",
        "effect": "Lower routes more messages by topic. Higher falls back to the "
                  "English keyword table more often.",
    },
    "FEEDBACK_TYPE_MIN_CONFIDENCE": {
        "default": FEEDBACK_TYPE_MIN_CONFIDENCE, "min": 0.0, "max": 1.0,
        "area": "Message", "label": "Stakeholder feedback type",
        "effect": "Lower makes the agent treat more messages as relayed feedback, "
                  "including plain commands. Higher misses real feedback.",
    },
    "URGENCY_BLOCKING_LEVEL": {
        "default": URGENCY_BLOCKING_LEVEL, "min": 0.0, "max": 2.0,
        "area": "Message", "label": "Urgency counts as blocking",
        "effect": "Lower offers to raise a CR more often. Higher lets urgent "
                  "feedback pass as routine.",
    },
    "SECURITY_SECTION_BLOCKS_BELOW": {
        "default": SECURITY_SECTION_BLOCKS_BELOW, "min": 0.0, "max": 1.0,
        "area": "Gate", "label": "Security section blocks the gate",
        "effect": "Lower lets a thin security section through the gate. Compliance "
                  "is mandatory in CLAUDE.md, so raising is the safer mistake.",
    },
    "SECURITY_SECTION_CONFIRM_BELOW": {
        "default": SECURITY_SECTION_CONFIRM_BELOW, "min": 0.0, "max": 1.0,
        "area": "Gate", "label": "Security section needs PM confirmation",
        "effect": "Between this and the blocking value the PM is asked instead of "
                  "blocked. Must stay above the blocking value.",
    },
    "RESEARCH_DEPTH_THIN_BELOW": {
        "default": RESEARCH_DEPTH_THIN_BELOW, "min": 0.0, "max": 3.0,
        "area": "Gate", "label": "Research counts as thin",
        "effect": "Higher asks for more research before the gate. It lists what is "
                  "missing, it never fails the gate by itself.",
    },
    "OPEN_QUESTIONS_ASK_ABOVE": {
        "default": OPEN_QUESTIONS_ASK_ABOVE, "min": 0.0, "max": 1.0,
        "area": "Gate", "label": "Open question needs naming",
        "effect": "Lower asks the PM to name an open question more often.",
    },
    "FR_CATEGORY_PREFILL_ABOVE": {
        "default": FR_CATEGORY_PREFILL_ABOVE, "min": 0.0, "max": 1.0,
        "area": "Feature request", "label": "Pre-fill the FR type",
        "effect": "Lower pre-fills the type field more often. The PM can still "
                  "change it, so this is a convenience, not a decision.",
    },
    "IS_REALLY_A_CR_ABOVE": {
        "default": IS_REALLY_A_CR_ABOVE, "min": 0.0, "max": 1.0,
        "area": "Feature request", "label": "Offer a CR instead of an FR",
        "effect": "Lower offers intake-cr more often. It only ever offers.",
    },
    "TOUCHES_SECURITY_FLAG_ABOVE": {
        "default": TOUCHES_SECURITY_FLAG_ABOVE, "min": 0.0, "max": 1.0,
        "area": "Feature request", "label": "Flag as security touching",
        "effect": "Deliberately generous. Missing this costs more than a false "
                  "alarm, because the gate then never demands a Security section.",
    },
    "CLARITY_INTERVIEW_BELOW": {
        "default": CLARITY_INTERVIEW_BELOW, "min": 0.0, "max": 2.0,
        "area": "Feature request", "label": "Interview before drafting",
        "effect": "Higher asks more clarifying questions before writing an FR.",
    },
    "CLARIFICATION_ONLY_ABOVE": {
        "default": CLARIFICATION_ONLY_ABOVE, "min": 0.0, "max": 1.0,
        "area": "Change request", "label": "Treat as a clarification",
        "effect": "Lower suggests handling more CRs as a PRD edit note rather than "
                  "a full change request.",
    },
    "SCOPE_IMPACT_OWN_FR_ABOVE": {
        "default": SCOPE_IMPACT_OWN_FR_ABOVE, "min": 0.0, "max": 3.0,
        "area": "Change request", "label": "Scope big enough for its own FR",
        "effect": "Lower suggests splitting more change requests into new feature "
                  "requests.",
    },
    "NEEDS_MAJOR_VERSION_ABOVE": {
        "default": NEEDS_MAJOR_VERSION_ABOVE, "min": 0.0, "max": 1.0,
        "area": "Change request", "label": "Suggest a major version",
        "effect": "Lower suggests v2.0 more often. The PM confirms the number "
                  "either way.",
    },
    "CREATES_NEW_TAG_ABOVE": {
        "default": CREATES_NEW_TAG_ABOVE, "min": 0.0, "max": 1.0,
        "area": "Change request", "label": "Offer a conflict rescan",
        "effect": "Lower offers a conflict scan after more change requests.",
    },
    "CONFLICT_REAL_ABOVE": {
        "default": CONFLICT_REAL_ABOVE, "min": 0.0, "max": 1.0,
        "area": "Conflict", "label": "Call it a real conflict",
        "effect": "Above this the CONFLICT block is stated firmly. Below it the "
                  "same block is shown, labelled as needing PM judgment.",
    },
    "CONFLICT_NOTE_BELOW": {
        "default": CONFLICT_NOTE_BELOW, "min": 0.0, "max": 1.0,
        "area": "Conflict", "label": "Downgrade to a note",
        "effect": "Below this the pair is shown as a note. It is never hidden: the "
                  "tag scan found it, so the PM sees it. Must stay below the "
                  "real conflict value.",
    },
    "RICE_SUGGEST_ABOVE": {
        "default": RICE_SUGGEST_ABOVE, "min": 0.0, "max": 1.0,
        "area": "RICE", "label": "Show a suggested band",
        "effect": "Below this no number is shown at all. score-feature forbids "
                  "assuming a RICE value, so a weak suggestion is worse than none.",
    },
    "DOC_ROUTING_ABOVE": {
        "default": DOC_ROUTING_ABOVE, "min": 0.0, "max": 1.0,
        "area": "Uploads", "label": "Suggest a destination folder",
        "effect": "Lower proposes a folder for more uploads, including ones it has "
                  "read wrong.",
    },
}


def T(name: str) -> float:
    """The effective value of a threshold: the portal's override, or the default.

    A stored value that is not a number, or falls outside the declared range, is
    ignored rather than clamped. Silently running at a bound nobody chose is
    worse than running at the default that was measured.
    """
    spec = THRESHOLDS[name]
    raw = _load_settings().get(f"threshold.{name}")
    if raw is None:
        return spec["default"]
    try:
        value = float(raw)
    except (TypeError, ValueError):
        logger.warning("Jev threshold %s is not a number (%r), using default", name, raw)
        return spec["default"]
    if not (spec["min"] <= value <= spec["max"]):
        logger.warning(
            "Jev threshold %s override %s is outside %s to %s, using default",
            name, value, spec["min"], spec["max"],
        )
        return spec["default"]
    return value


def threshold_report() -> list[dict]:
    """Every threshold with its default and its effective value, for the portal."""
    return [
        {
            "name": name,
            "area": spec["area"],
            "label": spec["label"],
            "effect": spec["effect"],
            "min": spec["min"],
            "max": spec["max"],
            "default": spec["default"],
            "value": T(name),
            "overridden": T(name) != spec["default"],
        }
        for name, spec in THRESHOLDS.items()
    ]


def _noul(answers: dict, key: str) -> float | None:
    v = (answers.get(key) or {}).get("noul")
    return float(v) if isinstance(v, (int, float)) else None


def _score(answers: dict, key: str) -> tuple[float | None, float, str]:
    a = answers.get(key) or {}
    v = a.get("score")
    if not isinstance(v, (int, float)):
        return None, 0.0, ""
    legend = a.get("legend") or {}
    nearest = legend.get(str(int(round(v))), "")
    return float(v), float(a.get("confidence", 0.0)), nearest


def _yn(p: float) -> str:
    return "yes" if p >= 0.5 else "no"


def _verdict_fr_triage(a: dict) -> list[str]:
    out = []
    label, conf = _choice(a, "category", T("FR_CATEGORY_PREFILL_ABOVE"))
    raw = (a.get("category") or {}).get("choice")
    if label:
        out.append(f"- Category: {label} ({conf:.2f}). Pre-fill the FR type field with it.")
    elif raw:
        out.append(f"- Category: best guess {raw} ({conf:.2f}), too weak to use. Ask the PM.")

    cr = _noul(a, "is_really_a_cr")
    if cr is not None:
        if cr >= T("IS_REALLY_A_CR_ABOVE"):
            out.append(
                f"- Really a change request: yes ({cr:.2f}). Say so and offer intake-cr "
                "instead of creating a new FR. Offer, do not switch on your own."
            )
        else:
            out.append(f"- Really a change request: no ({cr:.2f}). Continue as an FR.")

    sec = _noul(a, "touches_security")
    if sec is not None and sec >= T("TOUCHES_SECURITY_FLAG_ABOVE"):
        out.append(
            f"- Touches security, privacy, payments, or audit ({sec:.2f}). Record that in "
            "the FR so gate-review will require the Security section later."
        )

    clarity, _, nearest = _score(a, "clarity")
    if clarity is not None:
        if clarity < T("CLARITY_INTERVIEW_BELOW"):
            out.append(
                f"- Clarity: {clarity:.1f} of 2 ({nearest}). Run the clarifying "
                "interview before drafting anything."
            )
        else:
            out.append(f"- Clarity: {clarity:.1f} of 2 ({nearest}). Enough to draft.")
    return out


def _verdict_gate_review(a: dict) -> list[str]:
    out = []
    sec = _noul(a, "has_security_section")
    if sec is None:
        out.append("- Security section: no answer. Check it by hand.")
    elif sec < T("SECURITY_SECTION_BLOCKS_BELOW"):
        out.append(
            f"- Security section present: no ({sec:.2f}). This BLOCKS the gate. CLAUDE.md "
            "makes the security analysis mandatory. Tell the PM what is missing."
        )
    elif sec < T("SECURITY_SECTION_CONFIRM_BELOW"):
        out.append(
            f"- Security section present: unclear ({sec:.2f}). Do not block. Ask the PM "
            "to confirm the section is real before the gate proceeds."
        )
    else:
        out.append(f"- Security section present: yes ({sec:.2f}).")

    depth, _, nearest = _score(a, "research_depth")
    if depth is not None:
        if depth < T("RESEARCH_DEPTH_THIN_BELOW"):
            out.append(
                f"- Research depth: {depth:.1f} of 3 ({nearest}). Write out what is "
                "missing. Do not turn this into a pass or a fail on its own."
            )
        else:
            out.append(f"- Research depth: {depth:.1f} of 3 ({nearest}).")

    open_q = _noul(a, "open_questions_remain")
    if open_q is not None and open_q >= T("OPEN_QUESTIONS_ASK_ABOVE"):
        out.append(
            f"- Open questions remain: yes ({open_q:.2f}). Ask the PM to name the "
            "question before the gate proceeds."
        )

    out.append(
        "A clean result here does not pass the gate. It only removes the automated "
        "objections. The checklist and the PM still decide."
    )
    return out


def _verdict_cr_assessment(a: dict) -> list[str]:
    out = []
    area, conf = _choice(a, "affected_area", T("CLARIFICATION_ONLY_ABOVE"))
    raw = (a.get("affected_area") or {}).get("choice")
    if area == "clarification":
        out.append(
            f"- Affected area: clarification ({conf:.2f}). Suggest handling this as a PRD "
            "edit note rather than a full CR."
        )
    elif raw:
        rc = (a.get("affected_area") or {}).get("confidence", 0.0)
        out.append(f"- Affected area: {raw} ({rc:.2f}).")

    impact, _, nearest = _score(a, "scope_impact")
    if impact is not None:
        line = f"- Scope impact: {impact:.1f} of 3 ({nearest})."
        if impact >= T("SCOPE_IMPACT_OWN_FR_ABOVE"):
            line += " Large enough that it belongs in create-fr as its own FR. Suggest that."
        out.append(line)

    major = _noul(a, "needs_major_version")
    if major is not None:
        version = "v2.0" if major >= T("NEEDS_MAJOR_VERSION_ABOVE") else "v1.1"
        out.append(
            f"- Changes the intent of the PRD: {_yn(major)} ({major:.2f}). Suggest "
            f"{version}. The PM confirms the version number either way."
        )

    new_tag = _noul(a, "creates_new_tag")
    if new_tag is not None and new_tag >= T("CREATES_NEW_TAG_ABOVE"):
        out.append(
            f"- Pulls in a new module ({new_tag:.2f}). Offer a conflict scan for the "
            "current sprint before this is approved."
        )
    return out


def _verdict_conflict_pair(a: dict) -> list[str]:
    out = []
    real = _noul(a, "is_real_conflict")
    kind = (a.get("conflict_type") or {}).get("choice")
    sev, _, nearest = _score(a, "severity")
    levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    level = levels[min(int(round(sev)), 3)] if sev is not None else "UNKNOWN"

    if real is None:
        out.append("- No answer. Judge the pair by hand.")
    elif real >= T("CONFLICT_REAL_ABOVE"):
        out.append(
            f"- Real conflict: yes ({real:.2f}). Emit the CONFLICT block. Collision is "
            f"{kind}, risk level {level}."
        )
    elif real < T("CONFLICT_NOTE_BELOW"):
        out.append(
            f"- Real conflict: unlikely ({real:.2f}). Downgrade to a note, but still show "
            "it. The tag match found this pair, so the PM sees it either way."
        )
    else:
        out.append(
            f"- Real conflict: uncertain ({real:.2f}). Emit the block and label it "
            f"\"possible conflict, needs PM judgment\". Collision would be {kind}."
        )
    if sev is not None:
        out.append(f"- Severity: {sev:.1f} of 3, {level} ({nearest})")
    out.append(
        "Jev only ranks pairs the tag match already found. It never finds a conflict on "
        "its own, so never skip the tag scan."
    )
    return out


# Each band maps onto the scale score-feature already asks the PM about.
RICE_SCALES = {
    "reach_band": ("Reach", [1, 3, 7, 10], "of 10"),
    "impact_band": ("Impact", [0.25, 0.5, 1, 3], ""),
    "effort_band": ("Effort", [1, 2, 6, 10], "person-weeks"),
    "evidence_strength": ("Confidence", [20, 50, 80, 100], "percent"),
}


def _verdict_rice_bands(a: dict) -> list[str]:
    out = []
    for key, (name, scale, unit) in RICE_SCALES.items():
        value, conf, nearest = _score(a, key)
        if value is None:
            continue
        if conf < T("RICE_SUGGEST_ABOVE"):
            out.append(
                f"- {name}: no suggestion, confidence {conf:.2f} is too low. Ask the "
                "question with no number attached."
            )
            continue
        suggested = scale[min(int(round(value)), len(scale) - 1)]
        out.append(
            f"- {name}: suggest {suggested} {unit}".rstrip()
            + f" ({nearest}, confidence {conf:.2f})"
        )
    out.append(
        "These are suggestions to show inside the question, never answers. score-feature "
        "forbids assuming any RICE value. Ask all four questions, label each suggestion "
        "as suggested, and record what the PM actually chose."
    )
    return out


def _verdict_doc_routing(a: dict) -> list[str]:
    kind, conf = _choice(a, "doc_kind", T("DOC_ROUTING_ABOVE"))
    if not kind or kind == "other":
        return []
    where = {
        "feature_request": "discovery/inbox/ as an FR",
        "research": "discovery/research/ as a research document",
        "prd": "prd/ as a PRD",
        "stakeholder_notes": "stakeholders/, against the named person",
        "meeting_minutes": "decisions/ as a record",
    }[kind]
    return [
        f"- Document kind: {kind} ({conf:.2f}). Likely home: {where}.",
        "Suggest that destination and wait for the PM to confirm before writing.",
    ]


# name -> (questions, how to name the two inputs in the state, verdict builder)
QUESTION_SETS = {
    "fr_triage": (FR_TRIAGE_QUESTIONS, ("idea", "existing_work"), _verdict_fr_triage),
    "gate_review": (
        GATE_REVIEW_QUESTIONS, ("research_document", "feature_request"), _verdict_gate_review,
    ),
    "cr_assessment": (
        CR_ASSESSMENT_QUESTIONS, ("change_request", "current_prd"), _verdict_cr_assessment,
    ),
    "conflict_pair": (
        CONFLICT_PAIR_QUESTIONS, ("document_a", "document_b"), _verdict_conflict_pair,
    ),
    "rice_bands": (
        RICE_BAND_QUESTIONS, ("feature_request", "research_document"), _verdict_rice_bands,
    ),
    "doc_routing": (DOC_ROUTING_QUESTIONS, ("document", "context"), _verdict_doc_routing),
}


async def judge_async(question_set: str, content: str, context: str = "") -> str:
    """Judge a document. Returns text for the agent, never a decision."""
    spec = QUESTION_SETS.get(question_set)
    if not spec:
        return (
            f"Unknown question set '{question_set}'. Available: "
            + ", ".join(sorted(QUESTION_SETS))
        )
    questions, (primary, secondary), verdict = spec

    if not content or not content.strip():
        return f"Nothing to judge: {primary} was empty."

    state = {primary: content[:MAX_CONTENT_CHARS]}
    if context and context.strip():
        state[secondary] = context[:MAX_CONTENT_CHARS]

    answers = await _system_one(state, questions)
    if not answers:
        # Rule 5: never block a PM workflow on this API being up.
        return (
            "Jev is unavailable, so there is no automated judgment for this step. "
            "Continue with the manual checklist and say that the check was skipped."
        )

    lines = verdict(answers)
    if not lines:
        return f"Jev judgment ({question_set}): nothing confident enough to report."

    logger.info("jev judge %s -> %s", question_set, "; ".join(lines[:2]))
    header = (
        f"Jev judgment ({question_set}). Probabilistic, not fact. Record the answers you "
        "act on in the document's change log, and show the PM a draft before writing."
    )
    return header + "\n\n" + "\n".join(lines)


def judge(question_set: str, content: str, context: str = "") -> str:
    """Blocking wrapper for the agent tool loop, which runs tools in a thread."""
    try:
        return asyncio.run(judge_async(question_set, content, context))
    except Exception as e:
        logger.warning("Jev judge failed: %s", e)
        return (
            "Jev is unavailable, so there is no automated judgment for this step. "
            "Continue with the manual checklist and say that the check was skipped."
        )


async def route_document(content: str) -> str | None:
    """Suggest where an uploaded file belongs, or None when there is no clear answer.

    Unlike judge(), this runs in Python because handle_document already holds the
    converted text. None means stay quiet: an unsure guess in the prompt is worse
    than no guess, since the agent would repeat it to the PM as if it meant something.
    """
    if not content or not content.strip():
        return None

    answers = await _system_one(
        {"document": content[:MAX_CONTENT_CHARS]}, DOC_ROUTING_QUESTIONS
    )
    if not answers:
        return None

    lines = _verdict_doc_routing(answers)
    if not lines:
        return None

    logger.info("jev routing -> %s", lines[0])
    return (
        "\n## Jev routing for the uploaded file\n\n"
        "A classifier read the file before you did. This is a suggestion, not a\n"
        "decision, and it does not authorise writing anything.\n\n" + "\n".join(lines)
    )


async def ping(key: str, url: str = "") -> tuple[bool, str]:
    """Check one key against the API. Used by the portal before saving it.

    Takes the key as an argument rather than reading it back from the store, so
    a PM can test a key before committing to it.
    """
    if not key or not key.strip():
        return False, "No API key given."
    try:
        import httpx
    except ImportError:
        return False, "httpx is not installed, so Jev cannot be reached."

    question = {
        "reachable": {
            "type": "noul",
            "instructions": "Is `probe` the word yes?",
        }
    }
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS * 3) as client:
            resp = await client.post(
                f"{(url or base_url()).rstrip('/')}/v1/systemone",
                headers={"Authorization": f"Bearer {key.strip()}"},
                json={"model": MODEL, "state": {"probe": "yes"}, "questions": question},
            )
    except Exception as e:
        return False, f"Could not reach Jev: {e}"

    if resp.status_code == 401:
        return False, "That key was rejected."
    if resp.status_code == 403:
        return False, "That key exists but is not allowed to use this model."
    if resp.status_code >= 400:
        return False, f"Jev returned {resp.status_code}."
    try:
        model = resp.json().get("model", MODEL)
    except Exception:
        return False, "Jev replied with something this client cannot read."
    return True, f"Connected to {model}."
