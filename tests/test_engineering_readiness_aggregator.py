"""ERF-1 Slice 3 — Readiness aggregator.

Covers .jes/artifacts/implementation_contract_erf1.md §7 Slice 3:
  - build_engineering_readiness composes authorities end-to-end
  - derived on read, no persistence
  - same ProjectState -> identical JSON twice
  - signature guard: no continuity argument accepted
"""
from __future__ import annotations

import dataclasses
import inspect
import json
from types import SimpleNamespace

from jarvis.core.engineering_readiness import (
    EngineeringReadinessResult,
    build_engineering_readiness,
)
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue


def _design_properties(**kwargs):
    defaults = dict(components={}, system_blocks=[], system_priority=[])
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _project_state(**kwargs):
    defaults = dict(
        current_parameters={"vehicle_type": "dron"},
        parsed_constraints={},
        latest_results={"simulation": {}, "calculations": {}},
        design_properties=_design_properties(),
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_build_engineering_readiness_no_continuity_param():
    sig = inspect.signature(build_engineering_readiness)
    params = list(sig.parameters)
    assert params == ["project_state"]
    assert "readiness" not in params
    assert "continuity" not in params


def test_readiness_returns_dataclass_result():
    result = build_engineering_readiness(_project_state())
    assert isinstance(result, EngineeringReadinessResult)


def test_readiness_deterministic_twice():
    motors = ComponentSpec(
        suggested_key="motors",
        completeness="high",
        source="declared",
        properties={"kv_rating": PropertyValue(value=2400.0, unit="KV")},
    )
    state = _project_state(
        current_parameters={
            "vehicle_type": "dron",
            "per_motor_max_thrust_n": 2.0,
            "motor_count": 6,
            "propeller_diameter_in": 10.0,
        },
        latest_results={
            "simulation": {"status": "pass", "safety_margin_ratio": 1.0},
            "calculations": {"required_thrust_n": 19.8, "total_mass_kg": 1.5},
        },
        design_properties=_design_properties(
            components={"motors": motors},
            system_blocks=["structure", "propulsion"],
            system_priority=["structure", "propulsion"],
        ),
    )

    first = build_engineering_readiness(state)
    second = build_engineering_readiness(state)

    first_json = json.dumps(dataclasses.asdict(first), sort_keys=True)
    second_json = json.dumps(dataclasses.asdict(second), sort_keys=True)
    assert first_json == second_json


def test_readiness_no_disk_io(tmp_path, monkeypatch):
    """Derived on read — no readiness.json or any other file write."""
    import os

    monkeypatch.chdir(tmp_path)
    before = set(os.listdir(tmp_path))
    build_engineering_readiness(_project_state())
    after = set(os.listdir(tmp_path))
    assert before == after


def test_readiness_composes_across_authorities():
    """End-to-end smoke: architecture + BOM + requirements + catalog + sim all
    feed the same result without any one authority's logic being forked."""
    state = _project_state(
        parsed_constraints={"max_weight_kg": 2.0},
        current_parameters={"vehicle_type": "dron"},
        latest_results={
            "simulation": {"status": "fail", "warnings": ["margen insuficiente"]},
            "calculations": {"total_mass_kg": 3.0},
        },
        design_properties=_design_properties(
            system_blocks=["structure"], system_priority=["structure"],
        ),
    )
    result = build_engineering_readiness(state)
    gap_types = {g.gap_type for g in result.gaps}
    assert "GAP-SIM-NOT-PASS" in gap_types
    assert "GAP-REQUIREMENTS-UNMET" in gap_types
    assert "GAP-ARCH-BLOCK-INCOMPLETE" in gap_types
    assert "GAP-BOM-MISSING-COMPONENT" in gap_types
    assert result.overall == "NOT_ASSEMBLY_READY"
    assert result.top_gap is not None
    assert result.top_gap.severity == "HIGH"
