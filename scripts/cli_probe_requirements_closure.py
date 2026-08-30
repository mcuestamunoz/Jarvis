#!/usr/bin/env python3
"""CLI probe — Requirements Closure IC (contract §4 Req-6).

Steps (contract table):
  1. Load a Fixture-2-shaped project (8/9 subsystems already PASS,
     restrictions="no") -> overall ASSEMBLY_READY (★3(b)).
  2. estado -> "PROJECT STATUS: ASSEMBLY READY".
  3. Real turn updates restrictions to an achievable autonomy constraint ->
     still PASS / ASSEMBLY_READY (proves the G26 write path, not just the
     ★3(b) baseline).
  4. Real turn updates restrictions to an unachievable autonomy constraint ->
     honest GAP-REQUIREMENTS-UNMET:autonomy, overall NOT ASSEMBLY READY.
  5. A direct derived-param write ("autonomia") is rejected; restrictions
     from step 4 stay unchanged.

Self-contained — does not depend on the workspace/ scratch directory.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


def _say(orch, text: str, llm: _RefuseLLM) -> dict:
    print(f"\nUser > {text}")
    result = orch.handle_user_text(text, llm)
    msg = result.get("message") or result.get("question") or ""
    if msg:
        print(f"Jarvis > {msg[:400]}")
    print(f"  [action={result.get('action')} status={result.get('status')}]")
    return result


def _spec(ComponentSpec, PropertyValue, key, component_type, *, catalog_ref=None, properties=None):
    return ComponentSpec(
        name=key, component_type=component_type, suggested_key=key,
        completeness="high", source="declared",
        properties=properties or {}, catalog_ref=catalog_ref,
    )


def _seed_assembly_ready_shape(orch, restrictions: str) -> None:
    """Direct state seeding for the "already complete" scaffolding — same
    precedent as scripts/cli_probe_impl_d_sku_bom.py's own direct
    parsed_constraints/current_parameters seed. The restrictions-update
    mechanism under test (steps 3-5) uses only real handle_user_text turns.
    """
    from jarvis.schemas.action_schema import CatalogRef, ComponentSpec, PropertyValue
    from jarvis.schemas.state_schema import DesignProperties

    ps = orch.state_manager.load_active_project(orch.workspace_manager)

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
    propellers = _spec(ComponentSpec, PropertyValue, "propellers", "propulsion_passive", properties={
        "diameter_in": PropertyValue(value=5.0, unit="in", source="declared"),
        "pitch_in": PropertyValue(value=4.5, unit="in", source="declared"),
    })
    esc = _spec(ComponentSpec, PropertyValue, "esc", "power_electronics")
    battery = _spec(ComponentSpec, PropertyValue, "battery", "energy_storage", properties={
        "battery_capacity_wh": PropertyValue(value=22.2, unit="Wh", source="declared"),
    })
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
    params = dict(ps.current_parameters or {})
    params.update({
        "vehicle_type": "dron",
        "restrictions": restrictions,
        "motor_count": 4,
        "per_motor_max_thrust_n": 9.7086,
        "motor_power_w": 400.0,
        "battery_capacity_wh": 22.2,
    })
    updated = ps.model_copy(update={
        "design_properties": dp,
        "current_parameters": params,
        "latest_results": {
            "simulation": {"status": "pass", "autonomy_min": 5.0455, "safety_margin_ratio": 1.2},
            "calculations": {"required_thrust_n": 20.0, "total_mass_kg": 1.72, "autonomy_min": 5.0455},
        },
    })
    orch.workspace_manager.save_state(updated)


def main() -> int:
    from jarvis.adapters.cli.main import render_startup_context
    from jarvis.core.engineering_readiness import build_engineering_readiness
    from jarvis.core.orchestrator import JarvisOrchestrator

    llm = _RefuseLLM()
    with tempfile.TemporaryDirectory(prefix="jarvis-probe-reqclosure-") as tmp:
        orch = JarvisOrchestrator(workspace_root=Path(tmp))
        orch.handle({
            "action": "create_project",
            "parameters": {
                "vehicle_type": "dron",
                "objective": "probe requirements closure",
                "payload_kg": 1.0,
                "restrictions": "no",
                "detail_level": "conceptual",
                "structure_mass_factor": 0.5,
                "safety_factor": 1.2,
            },
        })
        _seed_assembly_ready_shape(orch, "no")
        print("=== Setup: Fixture-2-shaped project seeded, restrictions='no' ===")

        # ── Step 1/2 ─────────────────────────────────────────────────────
        ps = orch.state_manager.load_active_project(orch.workspace_manager)
        readiness = build_engineering_readiness(ps)
        assert readiness.overall == "ASSEMBLY_READY", (
            f"step1 FAIL: overall={readiness.overall}, gaps={[g.gap_id for g in readiness.gaps]}"
        )
        print(f"✓ Step 1 PASS: overall={readiness.overall}")

        status = _say(orch, "estado", llm)
        text = render_startup_context(status.get("startup_context") or {})
        assert "PROJECT STATUS: ASSEMBLY READY" in text, f"step2 FAIL: {text[:300]!r}"
        print("✓ Step 2 PASS: estado shows PROJECT STATUS: ASSEMBLY READY")

        # ── Step 3: achievable constraint via real G26 write path ─────────
        result3 = _say(orch, "cambia restrictions a autonomia minima 3 min", llm)
        assert result3["status"] == "ok"
        ps3 = orch.state_manager.load_active_project(orch.workspace_manager)
        assert ps3.parsed_constraints.get("autonomy_min") == 3.0
        readiness3 = build_engineering_readiness(ps3)
        assert readiness3.overall == "ASSEMBLY_READY", (
            f"step3 FAIL: overall={readiness3.overall}, gaps={[g.gap_id for g in readiness3.gaps]}"
        )
        print(f"✓ Step 3 PASS: achievable constraint -> overall={readiness3.overall}")

        # ── Step 4: unachievable constraint -> honest gap ──────────────────
        result4 = _say(orch, "cambia restrictions a autonomia minima 15 min", llm)
        assert result4["status"] == "ok"
        ps4 = orch.state_manager.load_active_project(orch.workspace_manager)
        assert ps4.parsed_constraints.get("autonomy_min") == 15.0
        readiness4 = build_engineering_readiness(ps4)
        gap_ids4 = {g.gap_id for g in readiness4.gaps}
        assert "GAP-REQUIREMENTS-UNMET:autonomy" in gap_ids4, f"step4 FAIL: gaps={gap_ids4}"
        assert readiness4.overall == "NOT_ASSEMBLY_READY", f"step4 FAIL: overall={readiness4.overall}"
        print(f"✓ Step 4 PASS: unachievable constraint -> honest gap, overall={readiness4.overall}")

        # ── Step 5: direct derived-param write rejected ────────────────────
        before5 = orch.state_manager.load_active_project(orch.workspace_manager)
        result5 = orch.param_definition_session.apply_and_recalculate({"autonomia": 15.0})
        assert result5["status"] == "error", f"step5 FAIL: derived write not rejected: {result5}"
        after5 = orch.state_manager.load_active_project(orch.workspace_manager)
        assert after5.current_parameters == before5.current_parameters, "step5 FAIL: state mutated"
        assert "autonomia" not in after5.current_parameters
        assert after5.current_parameters["restrictions"] == before5.current_parameters["restrictions"]
        print("✓ Step 5 PASS: derived 'autonomia' write rejected, restrictions unchanged")

        print("\n=== SUMMARY: 5/5 PASS ===")
        return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    try:
        raise SystemExit(main())
    except AssertionError as e:
        print(f"\n✗ FAIL: {e}", file=sys.stderr)
        raise SystemExit(1)
