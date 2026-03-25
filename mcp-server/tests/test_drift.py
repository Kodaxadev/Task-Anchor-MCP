"""
test_drift.py — Unit tests for the drift scoring engine.
Tests: signal matching, substring immunity, gap penalty, threshold, logging.
"""

import pytest
from pathlib import Path

from task_anchor.drift import (
    capped_score,
    format_clear_response,
    format_drift_response,
    is_drift,
    log_drift_event,
    score_input,
)
from task_anchor.models import DRIFT_SCORE_CAP, DRIFT_THRESHOLD


CONTEXT = "building the auth handler for the login endpoint"


# ---------------------------------------------------------------------------
# Substring immunity — signals must not fire inside longer words
# ---------------------------------------------------------------------------

class TestSubstringImmunity:

    def test_overwrite_does_not_trigger_rewrite_the(self):
        score, _ = score_input("can you overwrite the config file", CONTEXT)
        assert not is_drift(score)

    def test_instantiate_does_not_trigger_instead_of(self):
        score, _ = score_input("instantiate the DatabaseManager", CONTEXT)
        assert not is_drift(score)

    def test_reinstantiate_is_clean(self):
        score, _ = score_input("reinstantiate the connection pool after failure", CONTEXT)
        assert not is_drift(score)

    def test_insteadof_no_space_is_clean(self):
        # PHP/interface keyword — no word boundary match
        score, _ = score_input("use insteadof for interface override in PHP", CONTEXT)
        assert not is_drift(score)


# ---------------------------------------------------------------------------
# True drift signals — should fire
# ---------------------------------------------------------------------------

class TestDriftSignals:

    def test_while_were_at_it(self):
        score, _ = score_input("while we're at it, add rate limiting", CONTEXT)
        assert is_drift(score)

    def test_might_as_well(self):
        score, _ = score_input("might as well refactor the whole service layer", CONTEXT)
        assert is_drift(score)

    def test_different_approach(self):
        score, _ = score_input("different approach — use OAuth instead", CONTEXT)
        assert is_drift(score)

    def test_instead_of_phrase(self):
        score, _ = score_input("instead of JWT, use session cookies", CONTEXT)
        assert is_drift(score)

    def test_scrap_that(self):
        score, _ = score_input("scrap that, let's start from scratch", CONTEXT)
        assert is_drift(score)

    def test_can_you_also(self):
        score, _ = score_input("can you also add a dark mode toggle", CONTEXT)
        assert is_drift(score)

    def test_lets_switch(self):
        score, _ = score_input("let's switch to a Redis-based session store", CONTEXT)
        assert is_drift(score)

    def test_new_library(self):
        score, _ = score_input("new library — passlib handles this better", CONTEXT)
        assert is_drift(score)

    def test_what_if_we(self):
        score, _ = score_input("what if we rewrote this in Go instead", CONTEXT)
        assert is_drift(score)


# ---------------------------------------------------------------------------
# Safe messages — should NOT drift
# ---------------------------------------------------------------------------

class TestNoDriftOnSafeMessages:

    def test_normal_progress_update(self):
        score, _ = score_input("the handler is returning 200 now", CONTEXT)
        assert not is_drift(score)

    def test_short_question(self):
        score, _ = score_input("does this handle unicode?", CONTEXT)
        assert not is_drift(score)

    def test_in_context_technical_statement(self):
        score, _ = score_input("added the JWT validation middleware to the handler", CONTEXT)
        assert not is_drift(score)

    def test_bug_report(self):
        score, _ = score_input("the login endpoint is returning a 500 on null password", CONTEXT)
        assert not is_drift(score)

    def test_actually_alone_does_not_drift(self):
        # "actually" is weight 2, below threshold of 4 on its own
        score, _ = score_input("actually that fixed the issue", CONTEXT)
        assert not is_drift(score)


# ---------------------------------------------------------------------------
# Gap penalty behaviour
# ---------------------------------------------------------------------------

class TestGapPenalty:

    def test_short_input_exempt_from_gap_penalty(self):
        # Under 40 chars, gap penalty must not fire even with zero overlap
        short_input = "add caching layer"  # 17 chars, no context overlap
        score, overlap = score_input(short_input, CONTEXT)
        assert overlap == 0
        assert not is_drift(score)

    def test_long_off_topic_input_gets_gap_penalty(self):
        # Long input with zero overlap with context should attract penalty
        off_topic = "can you explain how kubernetes horizontal pod autoscaling works in production"
        score, overlap = score_input(off_topic, CONTEXT)
        # Not asserting drift — just that penalty was applied (score > 0 without signals)
        assert score > 0

    def test_long_in_context_input_no_gap_penalty(self):
        in_context = "the login endpoint auth handler is returning the correct JWT token now"
        score, overlap = score_input(in_context, CONTEXT)
        assert overlap >= 2


# ---------------------------------------------------------------------------
# Score helpers
# ---------------------------------------------------------------------------

class TestScoreHelpers:

    def test_capped_score_does_not_exceed_cap(self):
        assert capped_score(999) == DRIFT_SCORE_CAP

    def test_capped_score_below_cap_unchanged(self):
        assert capped_score(3) == 3

    def test_is_drift_at_threshold(self):
        assert is_drift(DRIFT_THRESHOLD) is True

    def test_is_drift_below_threshold(self):
        assert is_drift(DRIFT_THRESHOLD - 1) is False


# ---------------------------------------------------------------------------
# Response formatting
# ---------------------------------------------------------------------------

class TestFormatting:

    def test_drift_response_contains_binary_choice(self):
        result = format_drift_response("let's switch to redis", CONTEXT, 4, 0)
        assert "[1]" in result
        assert "[2]" in result

    def test_drift_response_truncates_long_input(self):
        long_input = "x" * 100
        result = format_drift_response(long_input, CONTEXT, 4, 0)
        assert "..." in result

    def test_clear_response_shows_score(self):
        result = format_clear_response(2)
        assert "2" in result
        assert "✓" in result


# ---------------------------------------------------------------------------
# Drift history logging
# ---------------------------------------------------------------------------

class TestDriftHistoryLogging:

    def test_creates_file_if_missing(self, tmp_path):
        path = tmp_path / "DRIFT_HISTORY.json"
        log_drift_event(path, "signal_match", True)
        assert path.exists()

    def test_increments_total_drifts(self, tmp_path):
        path = tmp_path / "DRIFT_HISTORY.json"
        log_drift_event(path, "signal_match", True)
        log_drift_event(path, "signal_match", True)
        import json
        data = json.loads(path.read_text())
        assert data["total_drifts"] == 2

    def test_increments_successful_interventions(self, tmp_path):
        path = tmp_path / "DRIFT_HISTORY.json"
        log_drift_event(path, "signal_match", True)
        log_drift_event(path, "signal_match", False)
        import json
        data = json.loads(path.read_text())
        assert data["successful_interventions"] == 1

    def test_does_not_corrupt_existing_data(self, tmp_path):
        import json
        path = tmp_path / "DRIFT_HISTORY.json"
        path.write_text(json.dumps({"total_drifts": 5, "successful_interventions": 3}))
        log_drift_event(path, "signal_match", True)
        data = json.loads(path.read_text())
        assert data["total_drifts"] == 6
        assert data["successful_interventions"] == 4


# ---------------------------------------------------------------------------
# score_completion — stop-word removal + naive stemming
# ---------------------------------------------------------------------------

class TestScoreCompletion:

    def test_exact_match_returns_one(self):
        from task_anchor.drift import score_completion
        ratio = score_completion(
            "endpoint returns 200 in manual test",
            "endpoint returns 200 in manual test"
        )
        assert ratio == 1.0

    def test_empty_exit_condition_is_vacuously_true(self):
        from task_anchor.drift import score_completion
        assert score_completion("", "anything here") == 1.0

    def test_no_overlap_returns_zero(self):
        from task_anchor.drift import score_completion
        ratio = score_completion(
            "endpoint returns 200 in manual test",
            "the weather is nice today"
        )
        assert ratio == 0.0

    def test_stemming_matches_inflected_forms(self):
        from task_anchor.drift import score_completion
        # "returned" stems to "return", "testing" stems to "test"
        ratio = score_completion(
            "endpoint returns 200 in manual test",
            "endpoint returned 200 when testing manually"
        )
        assert ratio >= 0.5

    def test_stop_words_excluded_from_matching(self):
        from task_anchor.drift import score_completion
        # "this", "that", "with" are stop words — shouldn't inflate score
        ratio = score_completion(
            "deploy the migration script with rollback",
            "this that with from have will just"
        )
        assert ratio == 0.0

    def test_partial_match_below_threshold(self):
        from task_anchor.drift import score_completion
        ratio = score_completion(
            "endpoint returns 200 in manual test",
            "I tested things and it seemed fine"
        )
        assert ratio < 0.5
