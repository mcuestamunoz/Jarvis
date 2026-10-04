"""Tests T1-T3 for `B1-orchestrator-fulfill-docstring-honesty` (T18).

Comment/docstring honesty only — zero runtime behavior change. After T14
(`B1-assistant-vehicle-allowlist-widen`), `ArmedAllowlistSafetyGate`'s
allow-list covers all seven chat `AutonomyVerb` values, so the four
fulfill methods for TAKEOFF/RETURN_HOME/FOLLOW/PATROL must no longer
claim `verb_not_allowed`/"allow-list excludes" in their own docstrings.
"""

from __future__ import annotations

import inspect

from jarvis.core.orchestrator import JarvisOrchestrator

_FULFILL_METHOD_NAMES = (
    "_handle_vehicle_takeoff",
    "_handle_vehicle_return_home",
    "_handle_vehicle_follow",
    "_handle_vehicle_patrol",
)

_STALE_SUBSTRINGS = (
    "verb_not_allowed",
    "allow-list excludes",
    "allow-list still",
)


def test_t1_fulfill_docstrings_do_not_claim_stale_allowlist_exclusion():
    for name in _FULFILL_METHOD_NAMES:
        method = getattr(JarvisOrchestrator, name)
        docstring = inspect.getdoc(method) or ""
        for stale in _STALE_SUBSTRINGS:
            assert stale not in docstring, (
                f"{name}'s docstring still claims {stale!r} — stale after T14's "
                "seven-verb allow-list widen"
            )


def test_t2_armed_e2e_still_allow_not_implemented_for_all_four():
    orch = JarvisOrchestrator()

    class _ExplodingLLMInterface:
        def interpret(self, *args, **kwargs):
            raise AssertionError("llm must not be called")

        def analyze(self, *args, **kwargs):
            raise AssertionError("llm must not be called")

        def complete(self, *args, **kwargs):
            raise AssertionError("llm must not be called")

    exploding = _ExplodingLLMInterface()
    assert orch.handle_user_text("armar", exploding)["action"] == "vehicle_arm_policy"

    for raw, action in (
        ("takeoff", "vehicle_takeoff"),
        ("rtl", "vehicle_return_home"),
        ("follow", "vehicle_follow"),
        ("patrol", "vehicle_patrol"),
    ):
        result = orch.handle_user_text(raw, exploding)
        assert result["action"] == action
        assert "allow" in result["message"]
        assert "not_implemented" in result["message"]
        assert "verb_not_allowed" not in result["message"]
        assert "executed" not in result["message"].lower()


def test_t3_intercept_comments_also_clean():
    """Same honesty check as T1, extended to the `_handle_global_commands`
    intercept comments that wire TAKEOFF/RETURN_HOME/FOLLOW/PATROL — the
    other stale-claim location this Buy's DC calls out. (This Buy adds
    no tip-version pin test, consistent with the T17 guardrail
    `test_suite_no_tip_version_pins_b1.py`, which already scans this
    file too.)"""
    source = inspect.getsource(JarvisOrchestrator._handle_global_commands)
    for stale in _STALE_SUBSTRINGS:
        assert stale not in source, (
            f"_handle_global_commands still contains {stale!r} — stale after "
            "T14's seven-verb allow-list widen"
        )
