"""Tests for v1 project closure: requirements, BOM, D8 catalog, energy honesty, D7."""
from __future__ import annotations

from types import SimpleNamespace

from jarvis.core.component_inference import infer_component, infer_components
from jarvis.core.project_closure import (
    build_component_bom,
    derive_physical_requirements,
    energy_model_honesty_note,
    format_bom_lines,
    format_requirements_lines,
)
from jarvis.domains.aerial import aerial_registry
from jarvis.knowledge.library import ComponentLibrary
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue


def _state(**kwargs):
    defaults = dict(
        parsed_constraints={},
        latest_results={},
        current_parameters={},
        design_properties=SimpleNamespace(
            components={},
            system_blocks=[],
            system_defined=False,
            system_priority=[],
        ),
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# ── Physical requirements ─────────────────────────────────────────────────────

def test_derive_physical_requirements_from_calc_and_constraints():
    state = _state(
        parsed_constraints={"autonomy_min": 20.0, "max_weight_kg": 3.0},
        latest_results={
            "calculations": {
                "required_thrust_n": 40.0,
                "total_mass_kg": 2.5,
                "autonomy_min": 18.0,
            },
            "simulation": {"safety_margin_ratio": 1.4},
        },
        current_parameters={"motor_count": 4},
    )
    req = derive_physical_requirements(state)
    assert req["autonomy_target_min"] == 20.0
    assert req["max_mass_kg"] == 3.0
    assert req["thrust_needed_n"] == 40.0
    assert req["thrust_per_motor_needed_n"] == 10.0
    assert req["current_mass_kg"] == 2.5
    assert req["safety_margin_ratio"] == 1.4
    lines = format_requirements_lines(req)
    assert any("Empuje" in line for line in lines)


def test_energy_honesty_only_when_autonomy_constrained():
    # No constraint at all -> no note, regardless of calc state.
    assert energy_model_honesty_note(_state()) is None

    # CLI feasibility vs readiness semantics IC (§2.5): constraint set but no
    # autonomy was actually calculated -> honest "not calculated" sentence,
    # never the L0 (Wh/W)x60 disclosure (that would imply a number exists).
    note_uncalculated = energy_model_honesty_note(
        _state(parsed_constraints={"autonomy_min": 15})
    )
    assert note_uncalculated is not None
    assert "no calculada" in note_uncalculated.lower()
    assert "Wh" not in note_uncalculated

    # Constraint set AND autonomy actually calculated -> keep the original
    # L0 disclosure sentence, unchanged.
    note_calculated = energy_model_honesty_note(
        _state(
            parsed_constraints={"autonomy_min": 15},
            latest_results={"calculations": {"autonomy_min": 12.5}},
        )
    )
    assert note_calculated is not None
    assert "Wh" in note_calculated or "simplificado" in note_calculated.lower()


def test_build_component_bom_classifies_gaps():
    motors = ComponentSpec(
        name="4x 920KV",
        suggested_key="motors",
        component_type="propulsion_active",
        completeness="high",
        properties={"thrust_n": PropertyValue(value=12.0, unit="N")},
    )
    props = ComponentSpec(
        name="hélices",
        suggested_key="propellers",
        component_type="propulsion_passive",
        completeness="low",
        missing_fields=["diámetro"],
    )
    state = _state(
        design_properties=SimpleNamespace(
            system_blocks=["propulsion"],
            system_defined=True,
            system_priority=["propulsion"],
            components={"motors": motors, "propellers": props},
        )
    )
    bom = build_component_bom(state)
    assert any(e["key"] == "motors" for e in bom["defined"])
    assert any(e["key"] == "propellers" for e in bom["incomplete"])
    lines = format_bom_lines(bom)
    assert any("motors" in line for line in lines)


def test_bom_flight_controller_defined_gets_identity_suffix():
    """Control parity IC §2.2: flight_controller reaching the ``defined``
    bucket via brand/model name recognition (e.g. "Pixhawk 4") gets an
    identity-only suffix — it never carries a measured engineering value,
    unlike motors/battery/propellers/frame in the same bucket."""
    fc = ComponentSpec(
        name="pixhawk_4",
        suggested_key="flight_controller",
        component_type="flight_controller",
        completeness="high",
        properties={"model": PropertyValue(value="pixhawk_4", confidence=0.9)},
    )
    motors = ComponentSpec(
        name="4x 920KV",
        suggested_key="motors",
        component_type="propulsion_active",
        completeness="high",
        properties={"thrust_n": PropertyValue(value=12.0, unit="N")},
    )
    state = _state(
        design_properties=SimpleNamespace(
            system_blocks=["control", "propulsion"],
            system_defined=True,
            system_priority=["control", "propulsion"],
            components={"flight_controller": fc, "motors": motors},
        )
    )
    bom = build_component_bom(state)
    assert any(e["key"] == "flight_controller" for e in bom["defined"])
    lines = format_bom_lines(bom)
    fc_line = next(line for line in lines if line.startswith("✓ flight_controller"))
    motors_line = next(line for line in lines if line.startswith("✓ motors"))
    assert "identidad, sin dato físico" in fc_line
    assert "identidad, sin dato físico" not in motors_line
    assert motors_line.endswith("(high)")


def test_bom_sensors_declarative_unaffected_by_control_suffix():
    """Sensors stay in the declarative bucket (never "defined") and never
    get the flight_controller-only identity suffix."""
    sensors = ComponentSpec(
        name="gps_m9n",
        suggested_key="sensors",
        component_type="sensors",
        completeness="medium",
        properties={"gps_model": PropertyValue(value="ublox_m9n")},
    )
    state = _state(
        design_properties=SimpleNamespace(
            system_blocks=["control"],
            system_defined=True,
            system_priority=["control"],
            components={"sensors": sensors},
        )
    )
    bom = build_component_bom(state)
    assert any(e["key"] == "sensors" for e in bom["declarative"])
    lines = format_bom_lines(bom)
    sensors_line = next(line for line in lines if "sensors" in line)
    assert sensors_line.startswith("◇")
    assert "(declarativo)" in sensors_line
    assert "identidad, sin dato físico" not in sensors_line


def _frame_and_motors(size_class_inch=None):
    frame_props = {
        "mass_kg": PropertyValue(value=0.4),
        "material": PropertyValue(value="fibra de carbono"),
    }
    if size_class_inch is not None:
        frame_props["size_class_inch"] = PropertyValue(value=size_class_inch, unit="in")
    frame = ComponentSpec(
        name="frame", suggested_key="frame", component_type="structure",
        completeness="high", properties=frame_props,
    )
    motors = ComponentSpec(
        name="4x 920KV", suggested_key="motors", component_type="propulsion_active",
        completeness="high", properties={"thrust_n": PropertyValue(value=12.0, unit="N")},
    )
    propellers = ComponentSpec(
        name="propellers", suggested_key="propellers", component_type="propulsion_passive",
        completeness="high", properties={"diameter_in": PropertyValue(value=10.0)},
    )
    return frame, motors, propellers


def _structure_state(frame, motors, propellers):
    return _state(
        design_properties=SimpleNamespace(
            system_blocks=["structure", "propulsion"],
            system_defined=True,
            system_priority=["structure", "propulsion"],
            components={"frame": frame, "motors": motors, "propellers": propellers},
        )
    )


def test_bom_frame_class_missing_gets_pending_suffix():
    """Structure Foundations IC §2.1: frame reaches "defined" (mass+material)
    without ever declaring size_class_inch — with the propeller diameter
    known, the BOM line must not look fully settled."""
    frame, motors, propellers = _frame_and_motors(size_class_inch=None)
    state = _structure_state(frame, motors, propellers)
    bom = build_component_bom(state)
    assert any(e["key"] == "frame" for e in bom["defined"])
    lines = format_bom_lines(bom, state)
    frame_line = next(line for line in lines if line.startswith("✓ frame"))
    motors_line = next(line for line in lines if line.startswith("✓ motors"))
    assert "compatibilidad de clase nivel A pendiente" in frame_line
    assert "clase incompatible" not in frame_line
    assert motors_line.endswith("(high)")


def test_bom_frame_class_incompatible_gets_incompatible_suffix():
    frame, motors, propellers = _frame_and_motors(size_class_inch=5.0)  # < 10 in prop
    state = _structure_state(frame, motors, propellers)
    lines = format_bom_lines(build_component_bom(state), state)
    frame_line = next(line for line in lines if line.startswith("✓ frame"))
    assert "clase incompatible nivel A" in frame_line
    assert "pendiente" not in frame_line


def test_bom_frame_class_compatible_stays_plain():
    frame, motors, propellers = _frame_and_motors(size_class_inch=12.0)  # >= 10 in prop
    state = _structure_state(frame, motors, propellers)
    lines = format_bom_lines(build_component_bom(state), state)
    frame_line = next(line for line in lines if line.startswith("✓ frame"))
    assert frame_line.endswith("(high)")
    assert "pendiente" not in frame_line
    assert "incompatible" not in frame_line


def test_bom_frame_suffix_absent_without_project_state():
    """Backward compatibility: omitting project_state keeps the plain tail
    (existing callers that never pass it are unaffected)."""
    frame, motors, propellers = _frame_and_motors(size_class_inch=None)
    state = _structure_state(frame, motors, propellers)
    lines = format_bom_lines(build_component_bom(state))
    frame_line = next(line for line in lines if line.startswith("✓ frame"))
    assert frame_line.endswith("(high)")


# ── D8 design-space catalog ───────────────────────────────────────────────────

def test_find_motors_for_requirements_matches_thrust_band():
    lib = ComponentLibrary()
    matches = lib.find_motors_for_requirements(min_thrust_n=12.0, kv=1100)
    assert matches
    assert all(not (m.max_thrust_n < 12.0 and m.thrust_n < 12.0) for m in matches)
    # Generics sort last among equal thrust distance
    if any(m.is_generic for m in matches) and any(not m.is_generic for m in matches):
        first_generic = next(i for i, m in enumerate(matches) if m.is_generic)
        last_real = max(i for i, m in enumerate(matches) if not m.is_generic)
        assert last_real < first_generic


def test_find_motors_for_requirements_empty_is_honest_gap():
    lib = ComponentLibrary()
    matches = lib.find_motors_for_requirements(min_thrust_n=200.0, kv=6000)
    assert matches == []


def test_motor_catalog_has_design_space_and_enough_refs():
    lib = ComponentLibrary()
    motors = lib.list_motors()
    assert len(motors) >= 18
    sample = lib.get_motor("sunnysky_x2216_11")
    assert sample.min_thrust_n > 0
    assert sample.kv_max >= sample.kv_rating


# ── D7 multi-component ────────────────────────────────────────────────────────

def test_infer_components_splits_motors_and_propellers():
    specs = infer_components(
        "4 motores 920KV, hélices 10x4.5",
        registry=aerial_registry,
    )
    keys = [s.suggested_key for s in specs]
    assert "motors" in keys
    assert "propellers" in keys


def test_infer_components_recovers_kv_without_motor_word():
    specs = infer_components(
        "4x 2306 2400KV, hélices 10x4.5",
        registry=aerial_registry,
    )
    keys = [s.suggested_key for s in specs]
    assert "motors" in keys
    assert "propellers" in keys


def test_infer_components_merges_same_key_thrust_after_split():
    """P1 regression: '4 motores 920KV y 15N' must keep thrust, not drop it on split."""
    for text in ("4 motores 920KV y 15N", "4 motores 920KV, 15N de empuje"):
        specs = infer_components(text, registry=aerial_registry)
        assert len(specs) == 1
        assert specs[0].suggested_key == "motors"
        props = specs[0].properties or {}
        assert "kv_rating" in props
        assert "thrust_n" in props
        assert float(props["thrust_n"].value) == 15.0


def test_infer_component_single_unchanged():
    spec = infer_component("4 motores 920KV", registry=aerial_registry)
    assert spec.suggested_key == "motors"


def test_bom_kv_motor_is_declared_not_stub():
    """FN-020: a 'medium' completeness component with measurable signal and no
    outstanding missing_fields is architecture-present (same threshold as
    _component_is_low/_block_progress_status, via classify_component) — it
    must land in 'declarative' (declared, enrichment optional), never in the
    strong-gap 'incomplete' (stub) bucket that BOM/Continuity treat as a real
    acquisition target.

    Superseded assertion (pre-FN-020: medium ⇒ 'incomplete' unconditionally)
    was the exact dual-threshold contradiction FN-020 removes: architecture
    progress already counted this same component as present (completeness !=
    'low'), while BOM called it a gap — see docs/PROJECT_CONTINUITY.md FN-020.
    """
    motors = ComponentSpec(
        name="4x 920KV",
        suggested_key="motors",
        component_type="propulsion_active",
        completeness="medium",
        missing_fields=[],
        properties={
            "kv_rating": PropertyValue(value=920.0, unit="KV"),
            "motor_count": PropertyValue(value=4),
        },
    )
    state = _state(
        design_properties=SimpleNamespace(
            system_blocks=["propulsion"],
            system_defined=True,
            system_priority=["propulsion"],
            components={"motors": motors},
        )
    )
    bom = build_component_bom(state)
    assert any(e["key"] == "motors" for e in bom["declarative"])
    assert not any(e["key"] == "motors" for e in bom["incomplete"])


def test_bom_extra_low_completeness_not_defined():
    """Extras outside architecture use the same classification (not always defined)."""
    orphan = ComponentSpec(
        name="sensor suelto",
        suggested_key="sensors",
        component_type="sensor",
        completeness="low",
        missing_fields=["modelo"],
        properties={},
    )
    state = _state(
        design_properties=SimpleNamespace(
            system_blocks=["propulsion"],
            system_defined=True,
            system_priority=["propulsion"],
            components={"sensors": orphan},
        )
    )
    bom = build_component_bom(state)
    assert any(e["key"] == "sensors" for e in bom["incomplete"])
    assert not any(e["key"] == "sensors" for e in bom["defined"])
