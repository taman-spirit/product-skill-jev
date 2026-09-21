"""
Unit tests for the Jev integration.
Run without Docker: pytest tests/test_jev.py -v

These cover the two things that decide whether the bot degrades safely: the
fail open paths, and the confidence thresholds that gate every answer.
"""
import asyncio
import os
import sys
from pathlib import Path

import pytest

BOT_PATH = Path(__file__).parent.parent / "bot"
sys.path.insert(0, str(BOT_PATH))

import jev  # noqa: E402


def run(coro):
    return asyncio.run(coro)


@pytest.fixture
def api_key(monkeypatch):
    monkeypatch.setenv(jev.API_KEY_ENV, "test-key-not-real")


def answers(intent=None, intent_conf=1.0, feedback=None, feedback_conf=1.0, urgency=None):
    out = {}
    if intent:
        out["intent"] = {"type": "choice", "choice": intent, "confidence": intent_conf}
    if feedback:
        out["feedback_type"] = {
            "type": "choice", "choice": feedback, "confidence": feedback_conf,
        }
    if urgency is not None:
        out["feedback_urgency"] = {"type": "score", "score": urgency}
    return out


def stub(monkeypatch, result):
    async def _fake(state, questions):
        return result
    monkeypatch.setattr(jev, "_system_one", _fake)


# ── Fail open ─────────────────────────────────────────────────────

class TestFailsOpen:
    def test_no_api_key_returns_none(self, monkeypatch):
        monkeypatch.delenv(jev.API_KEY_ENV, raising=False)
        assert run(jev.analyze_message("create a project")) is None

    def test_error_status_returns_none(self, monkeypatch, api_key):
        import httpx

        class Unauthorised:
            def __init__(self, *a, **k): pass
            async def __aenter__(self): return self
            async def __aexit__(self, *a): return False
            async def post(self, url, **k):
                return httpx.Response(
                    401, request=httpx.Request("POST", url), json={"detail": "bad key"},
                )

        monkeypatch.setattr(httpx, "AsyncClient", Unauthorised)
        assert run(jev.analyze_message("hello")) is None

    def test_transport_error_is_swallowed(self, monkeypatch, api_key):
        """_system_one itself must never propagate an exception."""
        import httpx

        class Boom:
            def __init__(self, *a, **k): pass
            async def __aenter__(self): return self
            async def __aexit__(self, *a): return False
            async def post(self, *a, **k):
                raise httpx.ConnectTimeout("timed out")

        monkeypatch.setattr(httpx, "AsyncClient", Boom)
        assert run(jev._system_one({"message": "x"}, jev.MESSAGE_QUESTIONS)) is None

    def test_empty_answers_returns_none(self, monkeypatch, api_key):
        stub(monkeypatch, {})
        assert run(jev.analyze_message("hello")) is None

    def test_blank_message_is_not_sent(self, monkeypatch, api_key):
        def _explode(state, questions):
            raise AssertionError("should not call the API for a blank message")
        monkeypatch.setattr(jev, "_system_one", _explode)
        assert run(jev.analyze_message("   ")) is None


# ── Intent thresholds ─────────────────────────────────────────────

class TestIntent:
    def test_confident_intent_is_used(self, monkeypatch, api_key):
        stub(monkeypatch, answers(intent="prd", intent_conf=0.93))
        s = run(jev.analyze_message("write the requirements doc"))
        assert s.intent == "prd"
        assert s.intent_confidence == 0.93

    def test_low_confidence_intent_is_dropped(self, monkeypatch, api_key):
        below = jev.INTENT_MIN_CONFIDENCE - 0.01
        stub(monkeypatch, answers(intent="prd", intent_conf=below))
        assert run(jev.analyze_message("hmm")).intent is None

    def test_other_label_is_not_an_intent(self, monkeypatch, api_key):
        stub(monkeypatch, answers(intent="other", intent_conf=0.99))
        assert run(jev.analyze_message("what is the weather")).intent is None


# ── Feedback thresholds ───────────────────────────────────────────

class TestFeedback:
    def test_confident_blocker_is_captured(self, monkeypatch, api_key):
        stub(monkeypatch, answers(
            intent="stakeholder", feedback="blocker", feedback_conf=0.91, urgency=2.0,
        ))
        s = run(jev.analyze_message("Robert says we cannot ship without the audit log"))
        assert s.feedback_type == "blocker"
        assert s.urgency == 2.0
        assert s.is_blocking_feedback

    def test_low_confidence_feedback_is_dropped(self, monkeypatch, api_key):
        below = jev.FEEDBACK_TYPE_MIN_CONFIDENCE - 0.01
        stub(monkeypatch, answers(feedback="blocker", feedback_conf=below, urgency=2.0))
        s = run(jev.analyze_message("Robert mentioned something"))
        assert s.feedback_type is None
        assert s.urgency is None

    def test_none_label_is_not_feedback(self, monkeypatch, api_key):
        stub(monkeypatch, answers(feedback="none", feedback_conf=0.99, urgency=0.0))
        s = run(jev.analyze_message("list all projects"))
        assert s.feedback_type is None
        assert s.urgency is None

    def test_calm_feedback_is_not_blocking(self, monkeypatch, api_key):
        stub(monkeypatch, answers(feedback="suggestion", feedback_conf=0.9, urgency=0.4))
        assert not run(jev.analyze_message("Mai suggested a tweak")).is_blocking_feedback

    def test_urgent_non_blocker_still_counts_as_blocking(self, monkeypatch, api_key):
        stub(monkeypatch, answers(feedback="concern", feedback_conf=0.9, urgency=2.0))
        assert run(jev.analyze_message("Mai is worried")).is_blocking_feedback


# ── Prompt note ───────────────────────────────────────────────────

class TestPromptNote:
    def test_empty_signals_produce_no_note(self):
        assert jev.Signals().as_prompt_note() is None

    def test_note_reports_the_judgment_and_withholds_authority(self, monkeypatch, api_key):
        stub(monkeypatch, answers(
            intent="stakeholder", intent_conf=0.9,
            feedback="blocker", feedback_conf=0.95, urgency=2.0,
        ))
        note = run(jev.analyze_message("Robert is blocking on the audit log")).as_prompt_note()
        flat = " ".join(note.split())
        assert "stakeholder" in flat and "blocker" in flat
        assert "Blocking" in flat                      # maps to the Sentiment field
        assert "do not create one" in flat             # offers a CR, never creates it
        assert "not authorise writing a file" in flat  # CLAUDE.md draft-first rule

    def test_audit_line_records_confidence(self, monkeypatch, api_key):
        stub(monkeypatch, answers(intent="feature", intent_conf=0.88))
        assert "intent=feature@0.88" in run(jev.analyze_message("new idea")).audit_line()


# ── Router integration ────────────────────────────────────────────

class TestSmartFallback:
    @pytest.fixture
    def bot(self, monkeypatch):
        # bot.py evaluates `X | None` annotations at import time, so it needs 3.10.
        # The Docker image is 3.12, a dev machine may be older.
        if sys.version_info < (3, 10):
            pytest.skip("bot/bot.py requires Python 3.10 or newer")
        pytest.importorskip("telegram")
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
        import bot as bot_module
        return bot_module

    def test_signals_beat_the_keyword_table(self, bot):
        # No keyword in this text matches the "change" branch.
        s = jev.Signals(intent="change", intent_confidence=0.9)
        out = bot._smart_fallback("khach hang muon sua lai pham vi", [], "", s)
        assert "Create CR for PRD-001" in out

    def test_keywords_still_work_without_signals(self, bot):
        out = bot._smart_fallback("show me the project", [], "", None)
        assert "Show all projects" in out

    def test_unconfident_signals_fall_back_to_keywords(self, bot):
        out = bot._smart_fallback("show me the project", [], "", jev.Signals())
        assert "Show all projects" in out


# ── Document judgments ────────────────────────────────────────────

def doc_stub(monkeypatch, result):
    async def _fake(state, questions):
        return result
    monkeypatch.setattr(jev, "_system_one", _fake)


def noul(p):
    return {"type": "noul", "noul": p}


def score(v, conf=1.0, legend=None):
    return {"type": "score", "score": v, "confidence": conf, "legend": legend or {}}


class TestJudgeContract:
    def test_unknown_question_set_lists_the_real_ones(self, api_key):
        out = jev.judge("not_a_set", "text")
        assert "Unknown question set" in out and "gate_review" in out

    def test_empty_content_is_not_sent(self, monkeypatch, api_key):
        def _explode(state, questions):
            raise AssertionError("should not call the API for empty content")
        monkeypatch.setattr(jev, "_system_one", _explode)
        assert "Nothing to judge" in jev.judge("gate_review", "   ")

    def test_api_down_tells_the_agent_to_continue_manually(self, monkeypatch, api_key):
        doc_stub(monkeypatch, None)
        out = jev.judge("gate_review", "some research")
        assert "unavailable" in out and "manual checklist" in out

    def test_content_is_truncated(self, monkeypatch, api_key):
        seen = {}

        async def _capture(state, questions):
            seen.update(state)
            return {"has_security_section": noul(0.9)}

        monkeypatch.setattr(jev, "_system_one", _capture)
        jev.judge("gate_review", "x" * (jev.MAX_CONTENT_CHARS + 5000))
        assert len(seen["research_document"]) == jev.MAX_CONTENT_CHARS

    def test_every_set_names_two_state_keys(self):
        for name, (questions, keys, verdict) in jev.QUESTION_SETS.items():
            assert len(keys) == 2, name
            assert questions and callable(verdict), name


class TestGateReview:
    def test_missing_security_section_blocks(self, monkeypatch, api_key):
        doc_stub(monkeypatch, {
            "has_security_section": noul(0.12),
            "research_depth": score(2.4, legend={"2": "Alternatives considered."}),
        })
        out = jev.judge("gate_review", "research text")
        assert "BLOCKS the gate" in out

    def test_unclear_security_section_asks_instead_of_blocking(self, monkeypatch, api_key):
        doc_stub(monkeypatch, {"has_security_section": noul(0.7)})
        out = jev.judge("gate_review", "research text")
        assert "BLOCKS" not in out
        assert "Ask the PM to confirm" in out

    def test_clean_result_still_does_not_pass_the_gate(self, monkeypatch, api_key):
        doc_stub(monkeypatch, {
            "has_security_section": noul(0.97),
            "research_depth": score(3.0, legend={"3": "Alternatives, risks, evidence."}),
            "open_questions_remain": noul(0.05),
        })
        out = jev.judge("gate_review", "research text")
        assert "does not pass the gate" in out


class TestRiceBands:
    def test_low_confidence_shows_no_number(self, monkeypatch, api_key):
        below = jev.RICE_SUGGEST_ABOVE - 0.01
        doc_stub(monkeypatch, {"reach_band": score(2.0, conf=below)})
        out = jev.judge("rice_bands", "fr text")
        assert "no suggestion" in out
        assert "suggest 7" not in out

    def test_bands_map_onto_the_score_feature_scale(self, monkeypatch, api_key):
        doc_stub(monkeypatch, {
            "reach_band": score(2.0, conf=0.9),          # -> 7 of 10
            "impact_band": score(3.0, conf=0.9),         # -> 3
            "effort_band": score(1.0, conf=0.9),         # -> 2 person-weeks
            "evidence_strength": score(2.0, conf=0.9),   # -> 80 percent
        })
        out = jev.judge("rice_bands", "fr text")
        assert "Reach: suggest 7 of 10" in out
        assert "Impact: suggest 3" in out
        assert "Effort: suggest 2 person-weeks" in out
        assert "Confidence: suggest 80 percent" in out

    def test_always_repeats_that_these_are_not_answers(self, monkeypatch, api_key):
        doc_stub(monkeypatch, {"reach_band": score(1.0, conf=0.95)})
        out = jev.judge("rice_bands", "fr text")
        assert "forbids assuming any RICE value" in out


class TestConflictPair:
    def test_unlikely_conflict_is_downgraded_but_still_shown(self, monkeypatch, api_key):
        doc_stub(monkeypatch, {
            "is_real_conflict": noul(0.1),
            "conflict_type": {"type": "choice", "choice": "none", "confidence": 0.9},
            "severity": score(0.0, legend={"0": "No shared work."}),
        })
        out = jev.judge("conflict_pair", "prd a", "prd b")
        assert "Downgrade to a note" in out
        assert "still show" in out

    def test_uncertain_conflict_is_labelled_for_the_pm(self, monkeypatch, api_key):
        doc_stub(monkeypatch, {"is_real_conflict": noul(0.5)})
        assert "needs PM judgment" in jev.judge("conflict_pair", "prd a", "prd b")

    def test_severity_maps_to_the_claude_md_risk_levels(self, monkeypatch, api_key):
        doc_stub(monkeypatch, {
            "is_real_conflict": noul(0.9),
            "conflict_type": {"type": "choice", "choice": "api_contract", "confidence": 0.9},
            "severity": score(3.0, legend={"3": "A release is blocked."}),
        })
        out = jev.judge("conflict_pair", "prd a", "prd b")
        assert "CRITICAL" in out and "api_contract" in out

    def test_never_claims_to_find_conflicts_itself(self, monkeypatch, api_key):
        doc_stub(monkeypatch, {"is_real_conflict": noul(0.9)})
        assert "never skip the tag scan" in jev.judge("conflict_pair", "a", "b")


class TestFrTriage:
    def test_change_request_is_offered_not_taken(self, monkeypatch, api_key):
        doc_stub(monkeypatch, {
            "category": {"type": "choice", "choice": "improvement", "confidence": 0.9},
            "is_really_a_cr": noul(0.92),
        })
        out = jev.judge("fr_triage", "idea text", "PRD-001 Billing")
        assert "offer intake-cr" in out
        assert "Offer, do not switch on your own" in out

    def test_weak_category_is_reported_as_unusable(self, monkeypatch, api_key):
        doc_stub(monkeypatch, {
            "category": {"type": "choice", "choice": "improvement", "confidence": 0.4},
        })
        out = jev.judge("fr_triage", "idea text")
        assert "too weak to use" in out

    def test_security_flag_uses_the_generous_threshold(self, monkeypatch, api_key):
        assert jev.TOUCHES_SECURITY_FLAG_ABOVE < 0.7
        doc_stub(monkeypatch, {"touches_security": noul(0.65)})
        assert "gate-review will require the Security section" in jev.judge("fr_triage", "idea")


class TestDocumentRouting:
    def test_confident_kind_suggests_a_folder(self, monkeypatch, api_key):
        doc_stub(monkeypatch, {
            "doc_kind": {"type": "choice", "choice": "research", "confidence": 0.93},
        })
        out = run(jev.route_document("a long research document"))
        assert "discovery/research/" in out
        assert "wait for the PM to confirm" in out

    def test_unsure_stays_quiet(self, monkeypatch, api_key):
        below = jev.DOC_ROUTING_ABOVE - 0.05
        doc_stub(monkeypatch, {
            "doc_kind": {"type": "choice", "choice": "research", "confidence": below},
        })
        assert run(jev.route_document("ambiguous text")) is None

    def test_other_stays_quiet(self, monkeypatch, api_key):
        doc_stub(monkeypatch, {
            "doc_kind": {"type": "choice", "choice": "other", "confidence": 0.99},
        })
        assert run(jev.route_document("???")) is None

    def test_api_down_stays_quiet(self, monkeypatch, api_key):
        doc_stub(monkeypatch, None)
        assert run(jev.route_document("text")) is None


class TestToolWiring:
    """The prompt describes judge(), so every runtime that loads it must have it."""

    def _tool_names(self, path):
        import ast
        tree = ast.parse(Path(path).read_text())
        for node in tree.body:
            if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "TOOLS":
                return {
                    v.value for d in node.value.elts for k, v in zip(d.keys, d.values)
                    if getattr(k, "value", "") == "name"
                }
        return set()

    def test_bot_and_backend_expose_the_same_tools(self):
        root = Path(__file__).parent.parent
        bot_tools = self._tool_names(root / "bot" / "agent.py")
        backend_tools = self._tool_names(root / "apps" / "backend" / "agent_bridge.py")
        assert "judge" in bot_tools
        assert bot_tools == backend_tools, "TOOLS drifted between bot and backend"

    def test_declared_sets_match_the_implemented_ones(self):
        import ast
        root = Path(__file__).parent.parent
        tree = ast.parse((root / "bot" / "agent.py").read_text())
        declared = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.List) and node.elts:
                vals = [getattr(e, "value", None) for e in node.elts]
                if "fr_triage" in vals:
                    declared = set(v for v in vals if v)
        assert declared, "could not find the question_set enum in bot/agent.py"
        # doc_routing runs in Python, not through the tool, so it is not declared.
        assert declared == set(jev.QUESTION_SETS) - {"doc_routing"}


# ── Settings store ────────────────────────────────────────────────

@pytest.fixture
def store(tmp_path, monkeypatch):
    """A workspace whose settings.db the portal would write to."""
    import sqlite3
    monkeypatch.setenv("WORKSPACE_PATH", str(tmp_path))
    (tmp_path / "_system").mkdir()

    def write(**rows):
        conn = sqlite3.connect(tmp_path / "_system" / "settings.db")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS jev_settings "
            "(name TEXT PRIMARY KEY, value TEXT, updated_at TEXT)"
        )
        for name, value in rows.items():
            conn.execute(
                "INSERT OR REPLACE INTO jev_settings VALUES (?,?,'t')",
                (name.replace("__", "."), str(value)),
            )
        conn.commit()
        conn.close()
        jev.reset_settings_cache()

    jev.reset_settings_cache()
    yield write
    jev.reset_settings_cache()


class TestSettingsStore:
    def test_no_database_falls_back_to_the_environment(self, monkeypatch, tmp_path):
        monkeypatch.setenv("WORKSPACE_PATH", str(tmp_path))
        monkeypatch.setenv(jev.API_KEY_ENV, "env-key")
        jev.reset_settings_cache()
        assert jev.api_key() == "env-key"
        assert jev.is_enabled()
        assert jev.base_url() == jev.DEFAULT_BASE_URL

    def test_cache_is_cold_at_process_start(self, store, monkeypatch):
        """time.monotonic() starts near zero, so a 0.0 sentinel would serve an
        empty cache for the first seconds of every run."""
        store(api_key="portal-key")
        assert jev._settings_cache[0] == jev._NEVER_LOADED
        assert jev.api_key() == "portal-key"

    def test_portal_key_beats_the_environment(self, store, monkeypatch):
        monkeypatch.setenv(jev.API_KEY_ENV, "env-key")
        store(api_key="portal-key")
        assert jev.api_key() == "portal-key"

    def test_disabled_stops_every_call(self, store, monkeypatch, api_key):
        store(enabled=0)

        def _explode(state, questions):
            raise AssertionError("must not reach the API while disabled")

        monkeypatch.setattr(jev, "_system_one", jev._system_one)
        assert not jev.is_enabled()
        assert run(jev.analyze_message("Robert is blocking")) is None
        assert run(jev.route_document("some document")) is None

    def test_unreadable_database_is_not_fatal(self, tmp_path, monkeypatch):
        monkeypatch.setenv("WORKSPACE_PATH", str(tmp_path))
        (tmp_path / "_system").mkdir()
        (tmp_path / "_system" / "settings.db").write_text("this is not sqlite")
        jev.reset_settings_cache()
        assert jev._load_settings() == {}
        assert jev.is_enabled()


# ── Threshold overrides ───────────────────────────────────────────

class TestThresholdOverrides:
    def test_default_is_used_when_nothing_is_stored(self, store):
        store()
        assert jev.T("CONFLICT_REAL_ABOVE") == jev.CONFLICT_REAL_ABOVE

    def test_override_is_applied(self, store):
        store(threshold__CONFLICT_REAL_ABOVE=0.6)
        assert jev.T("CONFLICT_REAL_ABOVE") == 0.6

    def test_override_changes_the_verdict(self, store, monkeypatch, api_key):
        store(threshold__CONFLICT_REAL_ABOVE=0.6)
        doc_stub(monkeypatch, {"is_real_conflict": noul(0.65)})
        assert "Real conflict: yes" in jev.judge("conflict_pair", "a", "b")

    def test_out_of_range_override_is_ignored_not_clamped(self, store):
        store(threshold__RICE_SUGGEST_ABOVE=9)
        assert jev.T("RICE_SUGGEST_ABOVE") == jev.RICE_SUGGEST_ABOVE

    def test_non_numeric_override_is_ignored(self, store):
        store(threshold__RICE_SUGGEST_ABOVE="high")
        assert jev.T("RICE_SUGGEST_ABOVE") == jev.RICE_SUGGEST_ABOVE

    def test_report_marks_what_deviates(self, store):
        store(threshold__DOC_ROUTING_ABOVE=0.9)
        report = {r["name"]: r for r in jev.threshold_report()}
        assert report["DOC_ROUTING_ABOVE"]["value"] == 0.9
        assert report["DOC_ROUTING_ABOVE"]["overridden"]
        assert report["DOC_ROUTING_ABOVE"]["default"] == jev.DOC_ROUTING_ABOVE
        assert not report["CONFLICT_REAL_ABOVE"]["overridden"]

    def test_every_entry_declares_a_usable_range(self):
        for name, spec in jev.THRESHOLDS.items():
            assert spec["min"] < spec["max"], name
            assert spec["min"] <= spec["default"] <= spec["max"], name
            assert spec["area"] and spec["label"] and spec["effect"], name

    def test_registry_covers_every_call_site(self):
        """A T("NAME") with no entry would raise KeyError at runtime."""
        import re
        source = (Path(__file__).parent.parent / "bot" / "jev.py").read_text()
        used = set(re.findall(r'\bT\("([A-Z_]+)"\)', source))
        assert used, "found no T() call sites to check"
        assert used <= set(jev.THRESHOLDS), used - set(jev.THRESHOLDS)

    def test_paired_thresholds_keep_their_order(self):
        """Some pairs only make sense in order. The portal validates a value
        against its own range, not against its partner, so this documents it."""
        assert jev.CONFLICT_NOTE_BELOW < jev.CONFLICT_REAL_ABOVE
        assert jev.SECURITY_SECTION_BLOCKS_BELOW < jev.SECURITY_SECTION_CONFIRM_BELOW


# ── Backend storage ───────────────────────────────────────────────

class TestKeystoreJevSettings:
    @pytest.fixture
    def keystore(self, tmp_path, monkeypatch):
        monkeypatch.setenv("WORKSPACE_PATH", str(tmp_path))
        sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "backend"))
        from core import keystore
        return keystore

    def test_round_trip(self, keystore):
        keystore.set_jev_settings({"api_key": "k", "threshold.DOC_ROUTING_ABOVE": 0.9})
        stored = keystore.get_jev_settings()
        assert stored["api_key"] == "k"
        assert stored["threshold.DOC_ROUTING_ABOVE"] == "0.9"

    def test_none_removes_a_row(self, keystore):
        keystore.set_jev_settings({"api_key": "k"})
        keystore.set_jev_settings({"api_key": None})
        assert "api_key" not in keystore.get_jev_settings()

    def test_reset_drops_only_thresholds(self, keystore):
        keystore.set_jev_settings({
            "api_key": "k", "enabled": "0",
            "threshold.DOC_ROUTING_ABOVE": 0.9, "threshold.RICE_SUGGEST_ABOVE": 0.8,
        })
        assert keystore.clear_jev_thresholds() == 2
        left = keystore.get_jev_settings()
        assert set(left) == {"api_key", "enabled"}

    def test_jev_never_enters_the_active_key_rotation(self, keystore):
        """activate_key clears is_active on every api_keys row, which is why Jev
        lives in its own table instead."""
        keystore.add_key("anthropic", "Claude", "sk-a", set_active=True)
        keystore.set_jev_settings({"api_key": "jev-key", "enabled": "1"})
        other = keystore.add_key("google", "Gemini", "sk-g", set_active=True)
        keystore.activate_key(other["id"])
        assert keystore.get_jev_settings()["enabled"] == "1"
        assert keystore.get_jev_settings()["api_key"] == "jev-key"
