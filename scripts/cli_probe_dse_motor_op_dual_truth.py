#!/usr/bin/env python3
"""CLI probe — Motor OP Voltage Coherence (contract §3 MOP-6).

Deterministic, no LLM. Mirrors the field-walk sequence that originally
exposed the DSE <-> motor_op_power_w dual-truth bug (investigation_report_
dse_motor_op_dual_truth.md): motor+propeller bound before any battery,
then a real 6S/22.2V battery bound afterward — the exact shape that used
to lock in a stale, voltage-incoherent exact_operating_point (432W) that
explore's honest re-normalization disagreed with, producing an autonomy
cliff (explore promised more than apply/calcular delivered).

Post-catalog-foundation hygiene: EMAX carries no nominal max_watts and no
22.2V exact row, so steps 3-4 assert honest None-agreement (CASE A) rather
than a motor_power_w formula. Step 5 uses the sunnysky exact-OP fixture
(CASE B) for explore/apply promise coherence.

Steps:
  1. Bind motor emax_rs2205s_2300 + propeller hq_5045_bn, NO battery yet ->
     no motor_op_power_w lock-in (MOP-1: voltage_v=None never matches
     an exact row).
  2. Bind lipo_6s_10000mah (6S/22.2V) -> MOP-2 conditional revalidation
     confirms honestly at 22.2V; still no stale 432W anywhere.
  3. calcular -> autonomy_min honestly None (no power model on this combo).
  4. "optimiza para mejorar autonomia" -> explore baseline autonomy equals
     step 3's calc autonomy (MOP-3: explore uses live params, not a
     re-normalized copy) — both None here.
  5. Separate sunnysky exact-OP fixture -> "aplica la mejor" delivers
     explore's own promise for the applied candidate (CASE B).
  6. estado -> honest fallback evidence line, no OP-electrical line (no
     motor_op_* data to show), no contradiction with step 1/2.
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


def _assert_close(actual, expected, label, tol=0.01):
    assert actual is not None, f"{label} FAIL: got None, expected {expected}"
    assert abs(float(actual) - float(expected)) <= tol, f"{label} FAIL: got {actual}, expected {expected}"


def _sunnysky_exact_op_orch(root: Path):
    from jarvis.core.catalog_bind import bind_battery_from_catalog, bind_motor_from_catalog, bind_propeller_from_catalog
    from jarvis.core.component_writers import set_battery_component, set_motor_component, set_propeller_component
    from jarvis.core.orchestrator import JarvisOrchestrator
    from jarvis.knowledge.library import default_library

    orch = JarvisOrchestrator(workspace_root=root)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": "probe dse case b",
            "payload_kg": 1.0, "restrictions": "autonomia minima 15 min",
            "detail_level": "conceptual", "motors": 4,
            "structure_mass_factor": 0.5, "safety_factor": 1.2,
        },
    })
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    ps = set_propeller_component(ps, bind_propeller_from_catalog("gf_5045x3"))
    m = default_library.get_motor("sunnysky_r2205_2500")
    motor_spec = bind_motor_from_catalog({
        "name": m.name, "max_watts": m.max_watts, "thrust_n": m.thrust_n,
        "kv_rating": m.kv_rating, "weight_g": m.weight_g,
    })
    ps = set_motor_component(ps, motor_spec, m.max_watts)
    battery_spec = bind_battery_from_catalog("lipo_4s_1500mah")
    ps = set_battery_component(
        ps, battery_spec, battery_spec.properties["battery_capacity_wh"].value,
    )
    orch.workspace_manager.save_state(ps)
    return orch


def main() -> int:
    import json as _json

    from jarvis.adapters.cli.main import render_startup_context
    from jarvis.core.catalog_bind import bind_battery_from_catalog, bind_motor_from_catalog, bind_propeller_from_catalog
    from jarvis.core.component_writers import set_battery_component, set_motor_component, set_propeller_component
    from jarvis.core.orchestrator import JarvisOrchestrator
    from jarvis.knowledge.library import default_library

    with tempfile.TemporaryDirectory(prefix="jarvis-probe-motor-op-voltage-coherence-") as tmp:
        orch = JarvisOrchestrator(workspace_root=Path(tmp))
        orch.handle({
            "action": "create_project",
            "parameters": {
                "vehicle_type": "dron", "objective": "probe motor op voltage coherence",
                "payload_kg": 1.0, "restrictions": "no", "detail_level": "conceptual",
                "motors": 4, "structure_mass_factor": 0.5, "safety_factor": 1.2,
            },
        })
        llm = _RefuseLLM()

        # ── Step 1: motor + propeller, NO battery ───────────────────────
        ps = orch.state_manager.load_active_project(orch.workspace_manager)
        prop_spec = bind_propeller_from_catalog("hq_5045_bn")
        ps = set_propeller_component(ps, prop_spec)
        m = default_library.get_motor("emax_rs2205s_2300")
        motor_spec = bind_motor_from_catalog({
            "name": m.name, "max_watts": m.max_watts, "thrust_n": m.thrust_n,
            "kv_rating": m.kv_rating, "weight_g": m.weight_g,
        })
        ps = set_motor_component(ps, motor_spec, m.max_watts)
        res1 = _json.loads(ps.current_parameters["propulsion_resolution"])
        assert res1["resolution_type"] != "exact_operating_point", f"step1 FAIL: {res1}"
        assert res1["voltage_validated"] is False, f"step1 FAIL: {res1}"
        assert ps.current_parameters.get("motor_op_power_w") is None, (
            f"step1 FAIL: stale motor_op_power_w={ps.current_parameters.get('motor_op_power_w')}"
        )
        print("✓ Step 1 PASS: motor+propeller bound with no battery -> no exact lock-in, no stale motor_op_power_w")

        # ── Step 2: bind lipo_6s_10000mah (6S/22.2V) ────────────────────
        battery_spec = bind_battery_from_catalog("lipo_6s_10000mah")
        ps = set_battery_component(ps, battery_spec, battery_spec.properties["battery_capacity_wh"].value)
        orch.workspace_manager.save_state(ps)
        res2 = _json.loads(ps.current_parameters["propulsion_resolution"])
        assert res2["voltage_validated"] is True, f"step2 FAIL: {res2}"
        _assert_close(res2["resolved_at_voltage_v"], 22.2, "step2 resolved_at_voltage_v")
        assert ps.current_parameters.get("motor_op_power_w") is None, (
            f"step2 FAIL: stale motor_op_power_w={ps.current_parameters.get('motor_op_power_w')} "
            "survived a 22.2V battery bind"
        )
        _assert_close(ps.current_parameters.get("per_motor_max_thrust_n"), 10.042, "step2 thrust_n")
        capacity_wh = ps.current_parameters["battery_capacity_wh"]
        print(f"✓ Step 2 PASS: lipo_6s_10000mah bound ({capacity_wh}Wh) -> honest 22.2V resolution, no stale 432W")

        # ── Step 3: calcular (CASE A — honest None, no EMAX power model) ─
        result3 = orch.handle_user_text("calcular", llm)
        assert result3["status"] == "ok", f"step3 FAIL: {result3}"
        saved3 = orch.state_manager.load_active_project(orch.workspace_manager)
        autonomy3 = saved3.latest_results["calculations"]["autonomy_min"]
        assert autonomy3 is None, f"step3 FAIL: expected honest None autonomy, got {autonomy3}"
        print("✓ Step 3 PASS: autonomy_min=None (no nominal/OP power on EMAX @ 22.2V fallback)")

        # ── Step 4: optimiza para mejorar autonomia (CASE A baseline) ───
        result4 = orch.handle_user_text("optimiza para mejorar autonomia", llm)
        assert result4["status"] == "ok", f"step4 FAIL: {result4}"
        exploration = orch.state_manager.get_runtime_session().last_exploration_result
        assert exploration is not None, "step4 FAIL: no exploration result"
        baseline_autonomy = exploration.baseline_simulation.autonomy_min
        assert baseline_autonomy is None, f"step4 FAIL: baseline={baseline_autonomy}, expected None"
        assert baseline_autonomy == autonomy3, "step4 explore baseline vs calcular"
        print("✓ Step 4 PASS: explore baseline autonomy=None == calcular autonomy=None (MOP-3 live-params)")

        # ── Step 5: CASE B — sunnysky exact OP apply promise ─────────────
        orch5 = _sunnysky_exact_op_orch(Path(tempfile.mkdtemp(prefix="jarvis-probe-dse-case-b-")))
        ps5 = orch5.state_manager.load_active_project(orch5.workspace_manager)
        exploration5 = orch5.design_explorer.explore(ps5, "mejorar_autonomia")
        assert exploration5.viable, "step5 FAIL: need at least one viable candidate"
        promised = exploration5.viable[0].simulation.autonomy_min
        assert promised is not None, "step5 FAIL: candidate must have a real autonomy prediction"
        session5 = orch5.state_manager.get_runtime_session()
        orch5.state_manager.set_runtime_session(
            session5.model_copy(update={"last_exploration_result": exploration5})
        )
        result5 = orch5.handle_user_text("aplica la mejor", llm)
        assert result5["status"] == "ok", f"step5 FAIL: {result5}"
        saved5 = orch5.state_manager.load_active_project(orch5.workspace_manager)
        actual5 = saved5.latest_results["calculations"]["autonomy_min"]
        _assert_close(actual5, promised, "step5 apply vs explore promise")
        print(f"✓ Step 5 PASS: post-apply autonomy={actual5} == explore promise={promised} (sunnysky CASE B)")

        # ── Step 6: estado ────────────────────────────────────────────────
        ctx = orch.build_startup_context()
        rendered = render_startup_context(ctx)
        assert "Propulsión (evidencia)" in rendered, f"step6 FAIL: no evidencia line: {rendered[:800]!r}"
        assert "432.0" not in rendered, f"step6 FAIL: stale 432W value leaked into estado: {rendered[:800]!r}"
        print("✓ Step 6 PASS: estado shows honest evidence, no contradictory/stale OP data")

        print("\n=== SUMMARY: 6/6 PASS ===")
        return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    try:
        raise SystemExit(main())
    except AssertionError as e:
        print(f"\n✗ FAIL: {e}", file=sys.stderr)
        raise SystemExit(1)
