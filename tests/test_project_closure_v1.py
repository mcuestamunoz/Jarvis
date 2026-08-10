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
    assert energy_model_honesty_note(_state()) is None
    note = energy_model_honesty_note(_state(parsed_constraints={"autonomy_min": 15}))
    assert note is not None
    assert "Wh" in note or "simplificado" in note.lower()


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
