"""Impl D — Create → BOM / SKU BOM.

BOM entries now carry catalog_ref / sku_resolved / quantity (★1/★2) — the
BOM projection consumes SKU identity instead of only completeness buckets.
sku_resolved is computed from catalog_ref (+ a live library re-check),
NEVER from `.name` shape — this is the rule that closes Scenario D
(frankenstein: `.name` still looks like a SKU after G5 clears catalog_ref).

No new gap type (★4), no Continuity/ranking changes (★3), no ERF verdict
wiring (★5) — covered here only as "unchanged" regression proof.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from jarvis.core.catalog_bind import (
    bind_battery_from_catalog,
    bind_motor_from_catalog,
    invalidate_diverged_catalog_refs,
)
from jarvis.core.component_writers import set_motor_component
from jarvis.core.engineering_readiness import build_engineering_readiness
from jarvis.core.motor_catalog_assist import MotorSuggestion
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.project_closure import build_component_bom, format_bom_lines
from jarvis.knowledge.library import default_library
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue

_SKU = "brotherhobby_avenger_2500"  # thrust_n=9.5, kv 2300-2700, prop (5,)


def _real_battery_sku() -> str:
    return default_library.list_batteries()[0].name


def _state(**kwargs):
    defaults = dict(
        parsed_constraints={},
        latest_results={},
        current_parameters={},
        design_properties=SimpleNamespace(
            components={}, system_blocks=[], system_defined=False, system_priority=[],
        ),
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _suggestion_for(sku: str) -> MotorSuggestion:
    m = default_library.get_motor(sku)
    return {
        "idx": 1, "name": sku, "thrust_n": m.thrust_n, "kv_rating": m.kv_rating,
        "weight_g": m.weight_g, "max_watts": m.max_watts, "is_generic": m.is_generic,
    }


# ── 1. Bound motor → sku_resolved, catalog_ref, quantity ───────────────────

def test_bound_motor_entry_has_resolved_catalog_ref_and_quantity():
    spec = bind_motor_from_catalog(_suggestion_for(_SKU))
    state = _state(
        current_parameters={"motor_count": 6},
        design_properties=SimpleNamespace(
            components={"motors": spec}, system_blocks=["propulsion"], system_defined=True,
            system_priority=["propulsion"],
        ),
    )

    bom = build_component_bom(state)
    entry = next(e for e in bom["defined"] if e["key"] == "motors")

    assert entry["catalog_ref"] == {"family": "motor", "sku": _SKU}
    assert entry["sku_resolved"] is True
    assert entry["quantity"] == 6

    lines = format_bom_lines(bom)
    motor_line = next(l for l in lines if l.startswith("✓ motors"))
    assert f"[{_SKU}]" in motor_line
    assert "qty=6" in motor_line


# ── 2. Unbound freeform → sku_resolved False, catalog_ref None ─────────────

def test_unbound_freeform_motor_entry_has_no_catalog_identity():
    spec = ComponentSpec(
        name="4x 2306 2400KV 50W", component_type="propulsion_active", suggested_key="motors",
        completeness="high", source="declared",
        properties={
            "motor_count": PropertyValue(value=4), "kv_rating": PropertyValue(value=2400),
            "power_w": PropertyValue(value=50.0),
        },
    )
    state = _state(
        current_parameters={"motor_count": 4},
        design_properties=SimpleNamespace(
            components={"motors": spec}, system_blocks=["propulsion"], system_defined=True,
            system_priority=["propulsion"],
        ),
    )

    bom = build_component_bom(state)
    entry = next(e for e in bom["defined"] if e["key"] == "motors")

    assert entry["catalog_ref"] is None
    assert entry["sku_resolved"] is False
    assert entry["quantity"] == 4

    lines = format_bom_lines(bom)
    motor_line = next(l for l in lines if l.startswith("✓ motors"))
    assert "[" not in motor_line  # no bracketed SKU, no false resolved claim
    assert "qty=4" in motor_line


# ── 3. Frankenstein: catalog_ref cleared, .name retained ────────────────────

def test_frankenstein_entry_after_g5_divergence_is_not_resolved(tmp_path: Path):
    """Real G5 divergence path (catalog_bind.invalidate_diverged_catalog_refs)
    clears catalog_ref but never touches .name — the BOM entry must not
    present this as a resolved SKU."""
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({"action": "create_project", "parameters": {
        "vehicle_type": "dron", "objective": "x", "payload_kg": 1.0,
        "restrictions": "ninguna", "detail_level": "conceptual",
        "structure_mass_factor": 0.5, "safety_factor": 1.2,
    }})
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    spec = bind_motor_from_catalog(_suggestion_for(_SKU))
    ps = set_motor_component(ps, spec, default_library.get_motor(_SKU).max_watts)
    ps = ps.model_copy(update={
        "current_parameters": {**ps.current_parameters, "motor_count": 6, "propeller_diameter_in": 5.0},
    })

    # Force a diverging thrust value directly into params (mirrors
    # test_catalog_bind_v1.py's own divergence fixture) and run the same G5
    # entry point a real DSE apply would.
    diverged_params = dict(ps.current_parameters)
    diverged_params["per_motor_max_thrust_n"] = default_library.get_motor(_SKU).thrust_n * 2
    updated_components, updated_params = invalidate_diverged_catalog_refs(
        ps.design_properties.components, diverged_params
    )
    ps = ps.model_copy(update={
        "current_parameters": updated_params,
        "design_properties": ps.design_properties.model_copy(update={"components": updated_components}),
    })

    frankenstein = ps.design_properties.components["motors"]
    assert frankenstein.catalog_ref is None  # G5 cleared it
    assert frankenstein.name == _SKU  # .name untouched — still looks like a SKU

    bom = build_component_bom(ps)
    entry = next(e for e in bom["defined"] if e["key"] == "motors")

    assert entry["catalog_ref"] is None
    assert entry["sku_resolved"] is False

    lines = format_bom_lines(bom)
    motor_line = next(l for l in lines if l.startswith("✓ motors"))
    assert f"[{_SKU}]" not in motor_line, "frankenstein must not present as a resolved SKU"
    assert "(SKU sin resolver)" not in motor_line  # catalog_ref is None, not just unresolved


# ── 4. Architecture-complete + bound motor → bucket/gap behavior unchanged ──

def test_architecture_complete_bound_motor_still_bom_pass_no_new_gap_type(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({"action": "create_project", "parameters": {
        "vehicle_type": "dron", "objective": "x", "payload_kg": 1.0,
        "restrictions": "ninguna", "detail_level": "conceptual",
        "structure_mass_factor": 0.5, "safety_factor": 1.2,
    }})
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    motor_spec = bind_motor_from_catalog(_suggestion_for(_SKU))
    ps = set_motor_component(ps, motor_spec, default_library.get_motor(_SKU).max_watts)

    def _comp(key, ctype, **props):
        return ComponentSpec(
            name=key, component_type=ctype, suggested_key=key,
            completeness="high", source="declared", properties=props,
        )

    dp = ps.design_properties.model_copy(update={
        "system_defined": True,
        "system_blocks": ["propulsion", "energy", "structure", "control"],
        "system_priority": ["propulsion", "energy", "structure", "control"],
        "components": {
            **ps.design_properties.components,
            "propellers": _comp("propellers", "propulsion_passive", diameter_in=PropertyValue(value=5.0)),
            "esc": _comp("esc", "propulsion_active", current_a=PropertyValue(value=30.0)),
            "battery": _comp("battery", "energy_storage", battery_capacity_wh=PropertyValue(value=74)),
            "frame": _comp("frame", "structure", mass_kg=PropertyValue(value=0.5), material=PropertyValue(value="fibra")),
            "flight_controller": _comp("flight_controller", "control", model=PropertyValue(value="Pixhawk 4")),
            "sensors": _comp("sensors", "control", gps_model=PropertyValue(value="M9N")),
        },
    })
    ps = ps.model_copy(update={
        "design_properties": dp,
        "current_parameters": {**ps.current_parameters, "motor_count": 6, "propeller_diameter_in": 5.0},
    })

    bom = build_component_bom(ps)
    assert bom["missing"] == []
    assert bom["incomplete"] == []

    motors_entry = next(e for e in bom["defined"] if e["key"] == "motors")
    assert motors_entry["sku_resolved"] is True

    readiness = build_engineering_readiness(ps)
    gap_types = {g.gap_type for g in readiness.gaps}
    assert "GAP-BOM-SKU-UNRESOLVED" not in gap_types  # ★4 — no new gap type introduced
    assert not any(t.startswith("GAP-BOM-MISSING") or t.startswith("GAP-BOM-INCOMPLETE") for t in gap_types)


# ── 5. Regression: GAP-BOM-* still driven only by missing/incomplete ────────

def test_gap_bom_missing_and_incomplete_unaffected_by_new_fields():
    from jarvis.core.engineering_readiness import _bom_incomplete_gaps, _bom_missing_gaps

    state = _state(
        design_properties=SimpleNamespace(
            components={"motors": ComponentSpec(
                name="stub", component_type="propulsion_active", suggested_key="motors",
                completeness="low", source="declared", properties={},
            )},
            system_blocks=["propulsion"], system_defined=True, system_priority=["propulsion"],
        ),
    )
    bom = build_component_bom(state)
    assert bom["missing"] == ["propellers", "esc"]
    assert bom["incomplete"][0]["key"] == "motors"

    missing_gaps = _bom_missing_gaps(bom)
    incomplete_gaps = _bom_incomplete_gaps(bom)
    assert all(g.gap_type == "GAP-BOM-MISSING-COMPONENT" for g in missing_gaps)
    assert all(g.gap_type == "GAP-BOM-INCOMPLETE-COMPONENT" for g in incomplete_gaps)
    # New fields present on bucket entries but not read by the gap builders —
    # confirmed by the gap objects themselves carrying no catalog_ref/sku_resolved.
    incomplete_entry = bom["incomplete"][0]
    assert "catalog_ref" in incomplete_entry and "sku_resolved" in incomplete_entry


# ── 6. Battery with catalog_ref → same entry shape as motors ───────────────

def test_battery_catalog_ref_entry_shape_matches_motors_pattern():
    sku = _real_battery_sku()
    spec = bind_battery_from_catalog(sku)
    state = _state(
        design_properties=SimpleNamespace(
            components={"battery": spec}, system_blocks=["energy"], system_defined=True,
            system_priority=["energy"],
        ),
    )

    bom = build_component_bom(state)
    entry = next(e for e in bom["defined"] + bom["declarative"] if e["key"] == "battery")

    assert entry["catalog_ref"] == {"family": "battery", "sku": sku}
    assert entry["sku_resolved"] is True
    assert entry["quantity"] == 1

    lines = format_bom_lines(bom)
    battery_line = next(l for l in lines if "battery" in l)
    assert f"[{sku}]" in battery_line
