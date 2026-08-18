"""ERF-1 Slice 1 — Gap contract + rules (+ G9-B extract).

Covers .jes/artifacts/implementation_contract_erf1.md §7 Slice 1:
  - all six gap types emit correctly from fixture ProjectStates (trigger + non-trigger)
  - prioritize_gaps is deterministic
  - depends_on always explicit (empty in ERF-1)
  - no Continuity import
"""
from __future__ import annotations

import inspect
from types import SimpleNamespace

from jarvis.core.engineering_readiness import (
    Gap,
    GapEvidence,
    RecommendedNextStep,
    build_engineering_readiness,
    prioritize_gaps,
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


def _motor_spec(kv=None, catalog_ref=None):
    props = {}
    if kv is not None:
        props["kv_rating"] = PropertyValue(value=kv, unit="KV")
    return ComponentSpec(
        component_type="propulsion_active",
        suggested_key="motors",
        completeness="high",
        properties=props,
        source="declared",
        catalog_ref=catalog_ref,
    )


# ── No Continuity import (static smoke) ─────────────────────────────────────

def test_readiness_does_not_import_continuity():
    import jarvis.core.engineering_readiness as mod

    source = inspect.getsource(mod)
    assert "project_continuity" not in source


# ── GAP-MOTOR-CATALOG-UNRESOLVED ────────────────────────────────────────────

def test_gap_motor_catalog_unresolved_trigger():
    state = _project_state(
        current_parameters={
            "vehicle_type": "dron",
            "per_motor_max_thrust_n": 2.0,
            "propeller_diameter_in": 10.0,
        },
        latest_results={
            "simulation": {"status": "pass", "safety_margin_ratio": 1.0},
            "calculations": {"required_thrust_n": 19.8, "total_mass_kg": 1.5},
        },
        design_properties=_design_properties(
            components={"motors": _motor_spec(kv=2400)},
        ),
    )
    # motor_count=6 in current_parameters is required for thrust_per_motor_needed_n
    state.current_parameters["motor_count"] = 6
    result = build_engineering_readiness(state)
    catalog_gaps = [g for g in result.gaps if g.gap_type == "GAP-MOTOR-CATALOG-UNRESOLVED"]
    assert len(catalog_gaps) == 1
    gap = catalog_gaps[0]
    assert gap.gap_id == "GAP-MOTOR-CATALOG-UNRESOLVED"
    assert gap.severity == "MEDIUM"
    assert gap.domain == "catalog"
    assert set(gap.blocks) == {"catalog", "propulsion", "bom"}
    assert gap.depends_on == []
    assert gap.recommended_next_step.action == "list_motors"


def test_gap_motor_catalog_unresolved_absent_when_matches_found():
    state = _project_state(
        current_parameters={"vehicle_type": "dron", "motor_count": 4},
        latest_results={
            "simulation": {"status": "pass"},
            "calculations": {"required_thrust_n": 20.0},
        },
    )
    result = build_engineering_readiness(state)
    catalog_gaps = [g for g in result.gaps if g.gap_type == "GAP-MOTOR-CATALOG-UNRESOLVED"]
    assert catalog_gaps == []


# ── GAP-ARCH-BLOCK-INCOMPLETE ────────────────────────────────────────────────

def test_gap_arch_block_incomplete_trigger():
    state = _project_state(
        design_properties=_design_properties(
            system_blocks=["structure"], system_priority=["structure"],
        ),
    )
    result = build_engineering_readiness(state)
    arch_gaps = [g for g in result.gaps if g.gap_type == "GAP-ARCH-BLOCK-INCOMPLETE"]
    assert len(arch_gaps) == 1
    assert arch_gaps[0].blocks == ["architecture"]
    assert arch_gaps[0].recommended_next_step.action == "continue_architecture_block"


def test_gap_arch_block_incomplete_absent_when_complete():
    frame = ComponentSpec(suggested_key="frame", completeness="high", source="declared")
    state = _project_state(
        design_properties=_design_properties(
            components={"frame": frame},
            system_blocks=["structure"],
            system_priority=["structure"],
        ),
    )
    result = build_engineering_readiness(state)
    arch_gaps = [g for g in result.gaps if g.gap_type == "GAP-ARCH-BLOCK-INCOMPLETE"]
    assert arch_gaps == []


# ── GAP-BOM-MISSING-COMPONENT / GAP-BOM-INCOMPLETE-COMPONENT ────────────────

def test_gap_bom_missing_one_per_key():
    state = _project_state(
        design_properties=_design_properties(
            system_blocks=["structure", "control"],
            system_priority=["structure", "control"],
        ),
    )
    result = build_engineering_readiness(state)
    missing_gaps = {g.gap_id: g for g in result.gaps if g.gap_type == "GAP-BOM-MISSING-COMPONENT"}
    assert "GAP-BOM-MISSING-COMPONENT:frame" in missing_gaps
    assert "GAP-BOM-MISSING-COMPONENT:flight_controller" in missing_gaps
    assert missing_gaps["GAP-BOM-MISSING-COMPONENT:frame"].severity == "HIGH"
    assert missing_gaps["GAP-BOM-MISSING-COMPONENT:frame"].domain == "structure"
    assert missing_gaps["GAP-BOM-MISSING-COMPONENT:flight_controller"].domain == "control"


def test_gap_bom_incomplete_one_per_entry():
    stub_frame = ComponentSpec(suggested_key="frame", completeness="low", source="declared")
    state = _project_state(
        design_properties=_design_properties(
            components={"frame": stub_frame},
            system_blocks=["structure"],
            system_priority=["structure"],
        ),
    )
    result = build_engineering_readiness(state)
    incomplete_gaps = [g for g in result.gaps if g.gap_type == "GAP-BOM-INCOMPLETE-COMPONENT"]
    assert len(incomplete_gaps) == 1
    assert incomplete_gaps[0].gap_id == "GAP-BOM-INCOMPLETE-COMPONENT:frame"
    assert incomplete_gaps[0].severity == "MEDIUM"
    assert incomplete_gaps[0].recommended_next_step.action == "complete_component"


# ── GAP-SIM-NOT-PASS ─────────────────────────────────────────────────────────

def test_gap_sim_not_pass_when_fail():
    state = _project_state(
        latest_results={"simulation": {"status": "fail", "warnings": ["thrust too low"]}},
    )
    result = build_engineering_readiness(state)
    sim_gaps = [g for g in result.gaps if g.gap_type == "GAP-SIM-NOT-PASS"]
    assert len(sim_gaps) == 1
    assert sim_gaps[0].severity == "HIGH"
    assert sim_gaps[0].gap_id == "GAP-SIM-NOT-PASS"
    assert set(sim_gaps[0].blocks) == {"requirements", "propulsion", "energy"}


def test_gap_sim_not_pass_absent_when_pass():
    state = _project_state(latest_results={"simulation": {"status": "pass"}})
    result = build_engineering_readiness(state)
    sim_gaps = [g for g in result.gaps if g.gap_type == "GAP-SIM-NOT-PASS"]
    assert sim_gaps == []


def test_gap_sim_not_pass_triggers_on_blocking_with_no_sim_status():
    state = _project_state(
        latest_results={"simulation": {"physics_status": "missing_parameters"}},
    )
    result = build_engineering_readiness(state)
    sim_gaps = [g for g in result.gaps if g.gap_type == "GAP-SIM-NOT-PASS"]
    assert len(sim_gaps) == 1


# ── GAP-REQUIREMENTS-UNMET ───────────────────────────────────────────────────

def test_gap_requirements_mass_exceeded():
    state = _project_state(
        parsed_constraints={"max_weight_kg": 2.0},
        latest_results={
            "simulation": {"status": "pass"},
            "calculations": {"total_mass_kg": 3.5},
        },
    )
    result = build_engineering_readiness(state)
    req_gaps = [g for g in result.gaps if g.gap_type == "GAP-REQUIREMENTS-UNMET"]
    assert len(req_gaps) == 1
    assert req_gaps[0].gap_id == "GAP-REQUIREMENTS-UNMET:mass"
    assert req_gaps[0].severity == "HIGH"
    assert req_gaps[0].title == "Mass limit exceeded"


def test_gap_requirements_autonomy_not_met():
    state = _project_state(
        parsed_constraints={"autonomy_min": 30.0},
        latest_results={
            "simulation": {"status": "pass", "autonomy_min": 12.0},
            "calculations": {},
        },
    )
    result = build_engineering_readiness(state)
    req_gaps = [g for g in result.gaps if g.gap_type == "GAP-REQUIREMENTS-UNMET"]
    assert any(g.gap_id == "GAP-REQUIREMENTS-UNMET:autonomy" for g in req_gaps)


def test_gap_requirements_blocking_params_suppressed_when_sim_not_pass_also_fires():
    """When GAP-SIM-NOT-PASS already covers 'blocking, no sim status' for the
    same root cause, GAP-REQUIREMENTS-UNMET's (c) must not double-emit."""
    state = _project_state(
        latest_results={"simulation": {"physics_status": "missing_parameters"}},
    )
    result = build_engineering_readiness(state)
    blocking_params_gaps = [
        g for g in result.gaps
        if g.gap_type == "GAP-REQUIREMENTS-UNMET" and g.instance_key == "blocking_params"
    ]
    assert blocking_params_gaps == []
    assert any(g.gap_type == "GAP-SIM-NOT-PASS" for g in result.gaps)


def test_gap_requirements_blocking_params_fires_when_sim_status_stale_pass():
    """Blocking physics_status alongside a stale prior sim_status=='pass' (not
    re-cleared) is the one case (c) legitimately fires standalone."""
    state = _project_state(
        latest_results={
            "simulation": {"physics_status": "missing_parameters", "status": "pass"},
        },
    )
    result = build_engineering_readiness(state)
    blocking_params_gaps = [
        g for g in result.gaps
        if g.gap_type == "GAP-REQUIREMENTS-UNMET" and g.instance_key == "blocking_params"
    ]
    assert len(blocking_params_gaps) == 1
    assert blocking_params_gaps[0].severity == "MEDIUM"
    assert not any(g.gap_type == "GAP-SIM-NOT-PASS" for g in result.gaps)


# ── depends_on always explicit (empty in ERF-1) ─────────────────────────────

def test_all_emitted_gaps_have_explicit_empty_depends_on():
    state = _project_state(
        parsed_constraints={"max_weight_kg": 1.0},
        current_parameters={"vehicle_type": "dron", "per_motor_max_thrust_n": 2.0, "motor_count": 6},
        latest_results={
            "simulation": {"status": "pass"},
            "calculations": {"required_thrust_n": 19.8, "total_mass_kg": 2.5},
        },
        design_properties=_design_properties(
            components={"motors": _motor_spec(kv=2400)},
            system_blocks=["structure"],
            system_priority=["structure"],
        ),
    )
    result = build_engineering_readiness(state)
    assert result.gaps  # sanity: this fixture produces several gaps
    for g in result.gaps:
        assert g.depends_on == []


# ── prioritize_gaps determinism / ordering ──────────────────────────────────

def _gap(gap_id, severity, blocks):
    return Gap(
        gap_id=gap_id,
        gap_type=gap_id,
        instance_key=None,
        title=gap_id,
        severity=severity,
        domain="bom",
        blocks=blocks,
        depends_on=[],
        evidence=[GapEvidence(source="test", fact="x")],
        recommended_next_step=RecommendedNextStep(action="noop", params={}),
    )


def test_prioritize_gaps_severity_then_unblock_then_id():
    gaps = [
        _gap("GAP-C", "MEDIUM", ["bom"]),
        _gap("GAP-A", "HIGH", ["bom"]),
        _gap("GAP-B", "HIGH", ["bom", "structure"]),
        _gap("GAP-D", "LOW", ["bom"]),
    ]
    ranked = prioritize_gaps(gaps)
    # HIGH before MEDIUM before LOW; among HIGH, more blocks() unblocked wins;
    # stable gap_id tiebreak otherwise.
    assert [g.gap_id for g in ranked] == ["GAP-B", "GAP-A", "GAP-C", "GAP-D"]


def test_prioritize_gaps_deterministic_across_calls():
    gaps = [
        _gap("GAP-Z", "HIGH", ["bom"]),
        _gap("GAP-Y", "HIGH", ["bom"]),
    ]
    first = [g.gap_id for g in prioritize_gaps(gaps)]
    second = [g.gap_id for g in prioritize_gaps(gaps)]
    assert first == second == ["GAP-Y", "GAP-Z"]
