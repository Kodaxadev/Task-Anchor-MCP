"""
drift.py — Drift detection scoring engine and history logging.
Single responsibility: analyse user input for ADHD context-switching signals.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Tuple

from .models import (
    DRIFT_GAP_MAX_OVERLAP,
    DRIFT_GAP_MIN_LENGTH,
    DRIFT_GAP_PENALTY,
    DRIFT_SCORE_CAP,
    DRIFT_SIGNALS,
    DRIFT_THRESHOLD,
)
from .storage import read_json, write_json


# ---------------------------------------------------------------------------
# Phrase matching — whole-word boundary so "instead" doesn't fire inside
# "instantiate", and "rewrite" doesn't fire inside "overwrite".
# Multi-word phrases (e.g. "while we're at it") are matched literally with
# word boundaries only on the outer edges.
# ---------------------------------------------------------------------------

def _build_pattern(phrase: str) -> re.Pattern:
    escaped = re.escape(phrase)
    return re.compile(rf"\b{escaped}\b", re.IGNORECASE)


# Compiled once at import time — avoids re-compiling on every message.
_COMPILED_SIGNALS: list[tuple[re.Pattern, int]] = [
    (_build_pattern(phrase), weight)
    for phrase, weight in DRIFT_SIGNALS.items()
]


# ---------------------------------------------------------------------------
# Scoring engine
# ---------------------------------------------------------------------------

def score_input(user_input: str, current_context: str) -> Tuple[int, int]:
    """
    Returns (raw_score, keyword_overlap).

    raw_score       — sum of matched signal weights + optional gap penalty
    keyword_overlap — shared meaningful words between input and context
    """
    # Signal matching — whole-phrase, word-boundary aware
    signal_score = sum(
        weight
        for pattern, weight in _COMPILED_SIGNALS
        if pattern.search(user_input)
    )

    # Context gap penalty — only applied to substantive messages where the
    # input shares almost no vocabulary with the active task context.
    # Short messages (questions, confirmations) are exempt.
    context_words = _meaningful_words(current_context)
    input_words   = _meaningful_words(user_input)
    overlap       = len(context_words & input_words)

    gap_penalty = 0
    if (
        len(user_input) >= DRIFT_GAP_MIN_LENGTH
        and overlap < DRIFT_GAP_MAX_OVERLAP
    ):
        gap_penalty = DRIFT_GAP_PENALTY

    return signal_score + gap_penalty, overlap


def _meaningful_words(text: str) -> set[str]:
    """
    Returns lowercase words longer than 3 chars, stripping noise words that
    appear in almost every message and pollute the overlap calculation.
    """
    _STOP = {
        "this", "that", "with", "from", "have", "will", "just", "been",
        "also", "when", "what", "they", "your", "here", "there", "then",
        "than", "into", "some", "like", "more", "make", "want",
    }
    words = re.findall(r"[a-z]{4,}", text.lower())
    return {w for w in words if w not in _STOP}


def is_drift(score: int) -> bool:
    return score >= DRIFT_THRESHOLD


def capped_score(score: int) -> int:
    """Display-safe score — prevents misleading label in UI output."""
    return min(score, DRIFT_SCORE_CAP)


# ---------------------------------------------------------------------------
# Formatted output
# ---------------------------------------------------------------------------

def format_drift_response(
    user_input: str,
    current_context: str,
    score: int,
    overlap: int,
) -> str:
    display = capped_score(score)
    return (
        f"⚓ DRIFT DETECTED (Score: {display}/{DRIFT_SCORE_CAP})\n\n"
        f'DETECTED: "{user_input[:60]}{"..." if len(user_input) > 60 else ""}"\n\n'
        f"ANALYSIS:\n"
        f"- Signal match: Probable context switch\n"
        f"- Context overlap: {overlap} shared keyword(s)\n"
        f"- Suggestion: PARK immediately\n\n"
        f"ACTION REQUIRED:\n"
        f"Call parked_add to capture this idea, then return to:\n"
        f"{current_context}\n\n"
        f"BINARY CHOICE:\n"
        f"[1] Park this idea and continue current task\n"
        f"[2] Mark current complete and switch (requires validation)"
    )


def format_clear_response(score: int) -> str:
    return (
        f"✓ No drift detected (score: {capped_score(score)}/{DRIFT_SCORE_CAP}). "
        f"Proceed with current task."
    )


# ---------------------------------------------------------------------------
# Drift history logging
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Completion validation — reuses _meaningful_words for consistent filtering.
# Applies naive suffix stripping so "returns" matches "return", etc.
# ---------------------------------------------------------------------------

def _stem(word: str) -> str:
    """Naive suffix strip — handles the most common English inflections.

    Not a real stemmer; just enough to prevent false negatives like
    'tested' vs 'test' or 'returns' vs 'return'.
    """
    for suffix in ("ing", "tion", "ed", "es", "ly", "er", "est", "ment", "ness"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)]
    if word.endswith("s") and len(word) > 4:
        return word[:-1]
    return word


def score_completion(exit_condition: str, evidence: str) -> float:
    """Return 0.0–1.0 ratio of exit-condition keywords matched by evidence.

    Uses meaningful-word extraction (stop-word removal) + naive stemming
    so that 'test passes' is NOT matched by random mentions of 'test'.
    """
    exit_stems = {_stem(w) for w in _meaningful_words(exit_condition)}
    evidence_stems = {_stem(w) for w in _meaningful_words(evidence)}

    if not exit_stems:
        return 1.0  # vacuously true — empty exit condition

    return len(exit_stems & evidence_stems) / len(exit_stems)


def log_drift_event(
    drift_history_path: Path,
    event_type: str,
    intervention_successful: bool,
) -> None:
    """Reads, increments, and atomically writes drift stats."""
    stats = read_json(
        drift_history_path,
        default={"total_drifts": 0, "successful_interventions": 0},
    )
    stats["total_drifts"] += 1
    if intervention_successful:
        stats["successful_interventions"] += 1
    write_json(drift_history_path, stats)
