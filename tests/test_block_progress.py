"""Tests G2 — BLOCK_TYPE catalog + composite branch in _block_progress_status.

Validates:
1. BLOCK_TYPE catalog: correct types for all known blocks + fallback for custom blocks.
2. get_block_type() public API.
3. _block_progress_status with block_type="composite" (mocked via patch).
4. Edge case: composite block with no param_reason (params_ok trivially True).
5. Existing param and component branches still work correctly after refactor.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from jarvis.core.system_architecture_catalog import (
    BLOCK_TYPE,
    get_block_type,
)
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_component(completeness: str) -> ComponentSpec:
    return ComponentSpec(
        name="test",
        suggested_key="test",
        completeness=completeness,
        properties={"x": PropertyValue(value=1.0)},
    )


class _FakeDP:
    """Minimal DesignProperties stub for _block_progress_status tests."""
    def __init__(self, components: dict):
        self.components = components


# ── Commit 1: BLOCK_TYPE catalog ──────────────────────────────────────────────

class TestBlockTypeCatalog:

    def test_param_blocks(self):
        assert BLOCK_TYPE["actuation"] == "param"
        assert BLOCK_TYPE["transmission"] == "param"

    def test_composite_blocks(self):
        assert BLOCK_TYPE["energy"] == "composite"    # Fase 4: battery + motors
        assert BLOCK_TYPE["propulsion"] == "composite"  # Fase 6: motors + propellers

    def test_component_blocks(self):
        assert BLOCK_TYPE["structure"] == "component"
        assert BLOCK_TYPE["control"] == "component"
        assert BLOCK_TYPE["perception"] == "component"
        assert BLOCK_TYPE["communication"] == "component"
        assert BLOCK_TYPE["payload"] == "component"
        assert BLOCK_TYPE["manipulation"] == "component"

    def test_all_blocks_have_valid_type(self):
        valid = {"param", "component", "composite"}
        for block, btype in BLOCK_TYPE.items():
            assert btype in valid, f"Block '{block}' has invalid type '{btype}'"

    def test_get_block_type_known(self):
        assert get_block_type("structure") == "component"
        assert get_block_type("energy") == "composite"  # Fase 4

    def test_get_block_type_custom_fallback(self):
        """Custom/unknown blocks default to 'component' — prevents silent None crash."""
        assert get_block_type("custom_unknown_block") == "component"
        assert get_block_type("") == "component"


# ── Commit 2: composite branch in _block_progress_status ─────────────────────

class TestBlockProgressComposite:
    """Tests the composite branch using patch to avoid touching the production catalog.

    Strategy: mock BLOCK_TYPE inside orchestrator to treat 'energy' as 'composite'.
    This validates the logic without adding composite entries to production.
    """

    def _status(self, block, components, params):
        from jarvis.core.orchestrator import JarvisOrchestrator
        dp = _FakeDP(components)
        return JarvisOrchestrator._block_progress_status(block, dp, params)

    def _with_composite_energy(self):
        """Context manager: patch BLOCK_TYPE so 'energy' is 'composite' in tests only."""
        patched = {**BLOCK_TYPE, "energy": "composite"}
        return patch("jarvis.core.orchestrator.BLOCK_TYPE", patched), \
               patch("jarvis.core.system_architecture_catalog.BLOCK_TYPE", patched)

    def test_composite_complete_when_both_ok(self):
        """composite → 'complete' when params AND all components are defined."""
        params = {"battery_capacity_wh": 111.0, "motor_power_w": 200.0}
        components = {
            "battery": _make_component("high"),
            "motors": _make_component("high"),  # energy needs both battery AND motors
        }
        with patch("jarvis.core.orchestrator.get_block_type", return_value="composite"):
            status = self._status("energy", components, params)
        assert status == "complete"

    def test_composite_in_progress_only_params_ok(self):
        """composite → 'in_progress' when params OK but components missing."""
        params = {"battery_capacity_wh": 111.0, "motor_power_w": 200.0}
        components = {}  # no battery defined
        with patch("jarvis.core.orchestrator.get_block_type", return_value="composite"):
            status = self._status("energy", components, params)
        assert status == "in_progress"

    def test_composite_in_progress_only_components_ok(self):
        """composite → 'in_progress' when components OK but params missing."""
        params = {}  # no energy params
        components = {
            "battery": _make_component("high"),
            "motors": _make_component("high"),  # both components ok → components_ok=True
        }
        with patch("jarvis.core.orchestrator.get_block_type", return_value="composite"):
            status = self._status("energy", components, params)
        assert status == "in_progress"

    def test_composite_not_started_when_nothing_ok(self):
        """composite → 'not_started' when neither params nor components are defined."""
        params = {}
        components = {}
        with patch("jarvis.core.orchestrator.get_block_type", return_value="composite"):
            status = self._status("energy", components, params)
        assert status == "not_started"

    def test_composite_no_param_reason_params_trivially_ok(self):
        """Edge case: composite block with no param_reason → params_ok=True trivially.
        Completion depends only on components.
        """
        params = {}  # no params at all
        components = {"battery": _make_component("high")}
        # Mock a custom composite block with no param_reason
        custom_block = "custom_composite"
        patched_block_to_components = {"custom_composite": ["battery"]}
        with patch("jarvis.core.orchestrator.get_block_type", return_value="composite"), \
             patch("jarvis.core.orchestrator.get_param_reason_for_block", return_value=None), \
             patch("jarvis.core.orchestrator.BLOCK_TO_COMPONENTS", patched_block_to_components):
            status = self._status(custom_block, components, params)
        assert status == "complete"

    def test_composite_no_param_reason_not_started_when_no_components(self):
        """Composite block with no param_reason and no components defined.
        params_ok=True trivially, components_ok=False → 'in_progress'.
        (Not 'not_started' because the params criterion is already satisfied.)
        """
        params = {}
        components = {}
        patched_block_to_components = {"custom_composite": ["battery"]}
        with patch("jarvis.core.orchestrator.get_block_type", return_value="composite"), \
             patch("jarvis.core.orchestrator.get_param_reason_for_block", return_value=None), \
             patch("jarvis.core.orchestrator.BLOCK_TO_COMPONENTS", patched_block_to_components):
            status = self._status("custom_composite", components, params)
        assert status == "in_progress"


# ── Regression: existing param and component branches still work ──────────────

class TestBlockProgressRegressionAfterRefactor:
    """Existing param and component branches must behave identically after refactor."""

    def _status(self, block, components, params):
        from jarvis.core.orchestrator import JarvisOrchestrator
        dp = _FakeDP(components)
        return JarvisOrchestrator._block_progress_status(block, dp, params)

    def test_param_block_not_started(self):
        assert self._status("energy", {}, {}) == "not_started"

    def test_param_block_in_progress(self):
        # propulsion is now composite: params_ok but no components → in_progress
        params = {"motor_count": 4, "per_motor_max_thrust_n": 20.0}
        assert self._status("propulsion", {}, params) == "in_progress"

    def test_param_block_complete(self):
        params = {"motor_count": 4, "per_motor_max_thrust_n": 20.0}
        components = {"motors": _make_component("medium"), "propellers": _make_component("medium")}
        assert self._status("propulsion", components, params) == "complete"

    def test_component_block_not_started(self):
        assert self._status("structure", {}, {}) == "not_started"

    def test_component_block_not_started_when_all_low(self):
        components = {"frame": _make_component("low")}
        assert self._status("structure", components, {}) == "not_started"

    def test_component_block_complete(self):
        components = {"frame": _make_component("high")}
        assert self._status("structure", components, {}) == "complete"

    def test_unknown_block_not_started(self):
        """Unknown block with no component keys → not_started."""
        assert self._status("unknown_block_xyz", {}, {}) == "not_started"
