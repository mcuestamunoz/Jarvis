#!/usr/bin/env python3
"""CLI probe — Closure Policy + Propeller sku_resolved (IC 3, contract Pol-5).

Steps:
  1. Minimal state: motor + propeller catalog-bound (hq_5045_bn) ->
     build_component_bom -> propellers entry sku_resolved is True.
  2. format_bom_lines on the same state -> line shows [hq_5045_bn], never
     "(SKU sin resolver)" — the live bug from investigation §6.1, now fixed.
  3. Snapshot A shape (freeform battery, explicit-no requirements, every
     other subsystem crafted PASS) -> build_engineering_readiness ->
     PROJECT STATUS: ASSEMBLY READY.
  4. Snapshot B shape (motor + propeller + battery all catalog-bound,
     freeform esc/frame/FC/sensors) -> readiness summary shows [sku] on all
     three catalog families; propeller line not marked unresolved; overall
     still ASSEMBLY READY.

Self-contained (no dependency on the workspace/ scratch directory) — same
discipline as the IC 1/2 probes.
"""
from __future__ import annotations

import sys
from pathlib import Path


def _spec(ComponentSpec, PropertyValue, key, component_type, *, catalog_ref=None, properties=None):
    return ComponentSpec(
        name=key, component_type=component_type, suggested_key=key,
        completeness="high", source="declared",
        properties=properties or {}, catalog_ref=catalog_ref,
    )


def _assembly_ready_shape_state(restrictions: str, *, battery_catalog_ref=None, autonomy_min: float = 5.0455):
    from jarvis.schemas.action_schema import CatalogRef, ComponentSpec, PropertyValue
    from jarvis.schemas.state_schema import DesignProperties, ProjectState

    motors = _spec(
        ComponentSpec, PropertyValue, "motors", "propulsion_active",
        catalog_ref=CatalogRef(family="motor", sku="emax_rs2205s_2300"),
        properties={
            "thrust_n": PropertyValue(value=9.7086, unit="N", confidence=0.98, source="declared"),
            "kv_rating": PropertyValue(value=2300, source="declared"),
            "power_w": PropertyValue(value=400.0, unit="W", source="declared"),
            "motor_count": PropertyValue(value=4, source="declared"),
        },
    )
    propellers = _spec(
        ComponentSpec, PropertyValue, "propellers", "propulsion_passive",
        catalog_ref=CatalogRef(family="propeller", sku="hq_5045_bn"),
        properties={
            "diameter_in": PropertyValue(value=5.0, unit="in", source="declared"),
            "pitch_in": PropertyValue(value=4.5, unit="in", source="declared"),
        },
    )
    esc = _spec(ComponentSpec, PropertyValue, "esc", "power_electronics")
    battery_props = {"battery_capacity_wh": PropertyValue(value=22.2, unit="Wh", source="declared")}
    battery = _spec(
        ComponentSpec, PropertyValue, "battery", "energy_storage",
        catalog_ref=battery_catalog_ref, properties=battery_props,
    )
    frame = _spec(ComponentSpec, PropertyValue, "frame", "structure", properties={
        "material": PropertyValue(value="carbono", source="declared"),
    })
    flight_controller = _spec(ComponentSpec, PropertyValue, "flight_controller", "control")
    sensors = _spec(ComponentSpec, PropertyValue, "sensors", "control")

    dp = DesignProperties(
        components={
            "motors": motors, "propellers": propellers, "esc": esc, "battery": battery,
            "frame": frame, "flight_controller": flight_controller, "sensors": sensors,
        },
        system_defined=True,
        system_blocks=["propulsion", "energy", "structure", "control"],
        system_priority=["propulsion", "energy", "structure", "control"],
    )

    return ProjectState(
        project_id="closure-policy-probe", project_slug="closure-policy-probe",
        objective="probe closure policy + propeller sku_resolved",
        workspace_path="/tmp/closure-policy-probe",
        current_parameters={
            "vehicle_type": "dron", "restrictions": restrictions,
            "motor_count": 4, "per_motor_max_thrust_n": 9.7086,
            "motor_power_w": 400.0, "battery_capacity_wh": 22.2,
        },
        design_properties=dp,
        latest_results={
            "simulation": {"status": "pass", "autonomy_min": autonomy_min, "safety_margin_ratio": 1.2},
            "calculations": {"required_thrust_n": 20.0, "total_mass_kg": 1.72, "autonomy_min": autonomy_min},
        },
    )


def main() -> int:
    from jarvis.core.engineering_readiness import build_engineering_readiness
    from jarvis.core.project_closure import build_component_bom, format_bom_lines
    from jarvis.schemas.action_schema import CatalogRef
    from jarvis.schemas.state_schema import ProjectState

    # ── Step 1/2: minimal motor + propeller bound state -> BOM ─────────────
    minimal_state = _assembly_ready_shape_state("no")  # builder binds motor+propeller internally
    bom = build_component_bom(minimal_state)
    prop_entry = next(e for e in bom["defined"] if e["key"] == "propellers")
    assert prop_entry["sku_resolved"] is True, f"step1 FAIL: sku_resolved={prop_entry['sku_resolved']}"
    print(f"✓ Step 1 PASS: propellers entry sku_resolved={prop_entry['sku_resolved']}")

    lines = format_bom_lines(bom)
    propeller_line = next(l for l in lines if l.startswith("✓ propellers"))
    assert "[hq_5045_bn]" in propeller_line, f"step2 FAIL: {propeller_line!r}"
    assert "SKU sin resolver" not in propeller_line, f"step2 FAIL (live bug not fixed): {propeller_line!r}"
    print(f"✓ Step 2 PASS: {propeller_line!r}")

    # ── Step 3: Snapshot A — freeform battery, explicit-no requirements ────
    snapshot_a = _assembly_ready_shape_state("no", battery_catalog_ref=None)
    readiness_a = build_engineering_readiness(snapshot_a)
    assert readiness_a.overall == "ASSEMBLY_READY", (
        f"step3 FAIL: overall={readiness_a.overall}, gaps={[g.gap_id for g in readiness_a.gaps]}"
    )
    assert snapshot_a.design_properties.components["battery"].catalog_ref is None
    print(f"✓ Step 3 PASS: Snapshot A (freeform battery) -> overall={readiness_a.overall}")

    # ── Step 4: Snapshot B — motor+propeller+battery all catalog-bound ─────
    snapshot_b = _assembly_ready_shape_state(
        "no", battery_catalog_ref=CatalogRef(family="battery", sku="lipo_6s_10000mah")
    )
    readiness_b = build_engineering_readiness(snapshot_b)
    assert readiness_b.overall == "ASSEMBLY_READY", (
        f"step4 FAIL: overall={readiness_b.overall}, gaps={[g.gap_id for g in readiness_b.gaps]}"
    )
    bom_b = build_component_bom(snapshot_b)
    lines_b = format_bom_lines(bom_b)
    for key, sku in (("motors", "emax_rs2205s_2300"), ("propellers", "hq_5045_bn"), ("battery", "lipo_6s_10000mah")):
        line = next(l for l in lines_b if key in l)
        assert f"[{sku}]" in line, f"step4 FAIL: {key} line missing [sku]: {line!r}"
        assert "SKU sin resolver" not in line, f"step4 FAIL: {key} line unresolved: {line!r}"
    print(f"✓ Step 4 PASS: Snapshot B (motor+propeller+battery bound) -> overall={readiness_b.overall}, "
          f"all three families show [sku] resolved")

    # ── Step 5 (optional): a real on-disk fixture, if present ──────────────
    import json as _json
    candidate = (
        Path(__file__).resolve().parents[1]
        / "workspace" / "crear-un-dron-de-autonomia-con-payload-1kg-184eac8b7789" / "state.json"
    )
    if candidate.exists():
        data = _json.loads(candidate.read_text())
        state = ProjectState.model_validate(data)
        bom5 = build_component_bom(state)
        lines5 = format_bom_lines(bom5)
        prop_line5 = next(l for l in lines5 if l.startswith("✓ propellers"))
        assert "SKU sin resolver" not in prop_line5, f"step5 FAIL: {prop_line5!r}"
        print(f"✓ Step 5 PASS (optional, real fixture): {prop_line5!r}")
    else:
        print("… Step 5 SKIPPED (optional): no on-disk workspace fixture found")

    print("\n=== SUMMARY: 4/4 PASS (+ optional step 5) ===")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    try:
        raise SystemExit(main())
    except AssertionError as e:
        print(f"\n✗ FAIL: {e}", file=sys.stderr)
        raise SystemExit(1)
