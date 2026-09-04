"""FN-020 — Completeness coherence: one classifier for architecture progress,
BOM, and Continuity.

Root contradiction (live project `construir-dron-6ac77f21daf5`): battery and
sensors sit at completeness='medium' with real measurable properties
(battery_capacity_wh / gps_model). Architecture progress (_block_progress_status)
already counted them as present (non-low), giving 4/4 — but build_component_bom
called any 'medium' component 'incomplete' regardless, so Continuity said the
system "aún tiene gaps de componentes" in the same breath as "architecture
complete". Same ProjectState, two truths.

Fix: project_closure.classify_component (missing/stub/declared/defined) is now
the single presence/completeness classifier, consumed by both
orchestrator._component_is_low (via component_presence_tier) and
build_component_bom — Continuity's existing situation/evidence/next_step logic
already reads bom['incomplete']/['missing'] as the strong-gap signal, so once
those buckets stop misclassifying medium+measurable as a gap, Continuity
becomes coherent with no changes of its own required.
"""
from __future__ import annotations

from types import SimpleNamespace

from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.project_closure import build_component_bom, classify_component, component_presence_tier
from jarvis.core.project_continuity import build_project_continuity
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue

_PRIORITY = ["propulsion", "energy", "structure", "control"]


def _full_dron_state(*, battery_completeness="medium", sensors_completeness="medium",
                      include_flight_controller=True) -> SimpleNamespace:
    components = {
        "motors": ComponentSpec(
            name="motores", suggested_key="motors", component_type="propulsion_active",
            completeness="high",
            properties={"kv_rating": PropertyValue(value=2400), "thrust_n": PropertyValue(value=12.0)},
        ),
        "propellers": ComponentSpec(
            name="hélices", suggested_key="propellers", component_type="propulsion_passive",
            completeness="high", properties={"diameter_in": PropertyValue(value=10.0)},
        ),
        # ERF-2 ★5: esc is now part of BLOCK_TO_COMPONENTS["propulsion"].
        "esc": ComponentSpec(
            name="ESC 30A", suggested_key="esc", component_type="propulsion_active",
            completeness="high", properties={"current_a": PropertyValue(value=30.0)},
        ),
        "battery": ComponentSpec(
            name="batería", suggested_key="battery", component_type="energy",
            completeness=battery_completeness, missing_fields=[],
            properties={"battery_capacity_wh": PropertyValue(value=74.0)},
        ),
        "frame": ComponentSpec(
            name="frame", suggested_key="frame", component_type="structure",
            completeness="high",
            # Structure A (implementation_contract_structure_a.md §2.2): the
            # propeller above declares diameter_in=10.0, so this "fully
            # closed" fixture must also declare a compatible size_class_inch.
            properties={
                "mass_kg": PropertyValue(value=0.5),
                "material": PropertyValue(value="fibra"),
                "size_class_inch": PropertyValue(value=10.0, unit="in"),
            },
        ),
        "sensors": ComponentSpec(
            name="GPS", suggested_key="sensors", component_type="control",
            completeness=sensors_completeness, missing_fields=[],
            properties={"gps_model": PropertyValue(value="M9N")},
        ),
    }
    if include_flight_controller:
        components["flight_controller"] = ComponentSpec(
            name="Pixhawk 4", suggested_key="flight_controller", component_type="control",
            completeness="high", properties={"model": PropertyValue(value="Pixhawk 4")},
        )
    return SimpleNamespace(
        current_parameters={
            "motor_count": 4, "per_motor_max_thrust_n": 3.0,
            "battery_capacity_wh": 74.0, "motor_power_w": 50.0,
        },
        parsed_constraints={},
        latest_results={
            "simulation": {"status": "pass", "can_fly": True, "safety_margin_ratio": 1.4},
            "calculations": {},
        },
        design_properties=SimpleNamespace(
            system_defined=True,
            system_blocks=list(_PRIORITY),
            system_priority=list(_PRIORITY),
            components=components,
        ),
    )


def _continuity_for(state) -> dict:
    bom = build_component_bom(state)
    return build_project_continuity(
        project_state=state, status_type="nominal", status_reason=None, phase="complete",
        architecture_progress="4/4", next_architecture_label=None, next_block_status=None,
        proactive_question="Arquitectura completa (4/4) — puedes optimizar o simular.",
        suggested_action=None, physical_requirements={}, component_bom=bom,
        energy_model_note=None, motor_catalog_gap=None, motor_catalog_matches=None,
    )


# 1. Architecture stays complete with medium+measurable battery/sensors ────

def test_medium_battery_sensors_architecture_complete():
    state = _full_dron_state()
    dp = state.design_properties
    params = state.current_parameters
    for block in _PRIORITY:
        status = JarvisOrchestrator._block_progress_status(block, dp, params)
        assert status == "complete", f"{block} expected complete, got {status}"


# 2. Continuity does not claim component gaps when architecture is closed ──

def test_continuity_no_strong_gaps_when_architecture_complete_medium_only():
    state = _full_dron_state()
    bom = build_component_bom(state)
    assert bom["incomplete"] == []
    assert bom["missing"] == []

    continuity = _continuity_for(state)
    assert "gaps de componentes" not in continuity["situation"]
    assert not any(line.startswith("Gap:") for line in continuity["evidence"])
    assert not any(line.startswith("Falta definir:") for line in continuity["evidence"])


# 3. next_useful_step prefers PASS/optimize family, not "completa battery" ─

def test_continuity_next_step_not_complete_battery_when_arch_closed():
    state = _full_dron_state()
    continuity = _continuity_for(state)
    next_step = continuity["next_useful_step"]
    assert "battery" not in next_step.lower()
    assert "completa" not in next_step.lower()
    assert "pass" in next_step.lower() or "optimiz" in next_step.lower() or "simular" in next_step.lower()


# 4. Real stub / missing components still produce strong gap language ──────

def test_stub_or_missing_still_strong_gap():
    # Stub: sensors genuinely low completeness.
    stub_state = _full_dron_state(sensors_completeness="low")
    bom = build_component_bom(stub_state)
    assert any(e["key"] == "sensors" for e in bom["incomplete"])
    continuity = _continuity_for(stub_state)
    assert any("sensors" in line for line in continuity["evidence"])

    # Missing: flight_controller entirely absent.
    missing_state = _full_dron_state(include_flight_controller=False)
    bom2 = build_component_bom(missing_state)
    assert "flight_controller" in bom2["missing"]
    continuity2 = _continuity_for(missing_state)
    assert "flight_controller" in continuity2["next_useful_step"]


# 5. classify_component agrees with architecture's presence check ──────────

def test_classifier_shared_bom_and_architecture():
    state = _full_dron_state()
    cases = [
        ComponentSpec(suggested_key="x", completeness="low", properties={}),
        ComponentSpec(suggested_key="battery", completeness="medium", missing_fields=[],
                      properties={"battery_capacity_wh": PropertyValue(value=50.0)}),
        ComponentSpec(suggested_key="frame", completeness="high",
                      properties={"mass_kg": PropertyValue(value=0.4)}),
        ComponentSpec(suggested_key="flight_controller", completeness="medium",
                      properties={}),  # non-low, no measurable signal (name-only)
    ]
    for spec in cases:
        tier = classify_component(spec.suggested_key, spec, state)
        arch_low = JarvisOrchestrator._component_is_low(spec)
        presence_low = component_presence_tier(spec) == "stub"
        assert arch_low == presence_low
        assert (tier == "stub") == arch_low, (spec.completeness, tier, arch_low)


# ── E (acceptance): propulsion still incomplete when propellers missing ────

def test_propulsion_incomplete_when_propellers_missing_unaffected():
    components = {
        "motors": ComponentSpec(
            name="motores", suggested_key="motors", component_type="propulsion_active",
            completeness="high", properties={"kv_rating": PropertyValue(value=2400)},
        ),
    }
    state = SimpleNamespace(
        current_parameters={"motor_count": 4, "per_motor_max_thrust_n": 3.0},
        parsed_constraints={},
        latest_results={"simulation": {}, "calculations": {}},
        design_properties=SimpleNamespace(
            system_defined=True,
            system_blocks=["propulsion"],
            system_priority=["propulsion"],
            components=components,
        ),
    )
    status = JarvisOrchestrator._block_progress_status(
        "propulsion", state.design_properties, state.current_parameters
    )
    assert status != "complete"
    bom = build_component_bom(state)
    assert "propellers" in bom["missing"]
