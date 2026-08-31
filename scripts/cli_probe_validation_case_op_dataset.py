#!/usr/bin/env python3
"""CLI probe — Validation Case ★6 Regression Gate (contract §3 VC-1).

Locks the already-shipped ★6 operating-point dataset (phase2_star6_
operating_point_validation_case.md) as a permanent end-to-end regression
gate: real production bind path -> resolve_operating_point -> P2-2 bridge
-> the two EXISTING estado lines. Adds zero new capability, zero new
estado UI, zero src/ diff — see the implementation report's
`git diff --stat -- src/` confirmation.

Steps:
  1. OP-2: emax_rs2205s_2300 + hq_5045_bn @ ~16.0V -> full tuple matches
     the ★6 doc's OP-2 row exactly.
  2. OP-3: sunnysky_r2205_2500 + gf_5045x3 @ 14.8V -> full tuple matches
     the ★6 doc's OP-3 row exactly.
  3. OP-0: emax_rs2205s_2300, no propeller bound -> fallback_operating_point,
     thrust_n=10.0420, no OP-electrical tuple (all fields absent/None).
  4. estado (OP-2 case) -> the two EXISTING propulsion lines are present
     with the expected values -- no new line, no new UI.
  5. Rating vs OP lock: motor_power_w=400.0 and motor_op_power_w=432.0
     coexist on the OP-2 path (P2-2, already shipped).
  6. Regression: cli_probe_p2_2_operating_point_bridge.py still 6/6.
"""
from __future__ import annotations

import subprocess
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


def _bind_motor_propeller(orch, *, motor_sku, propeller_sku=None, battery_cell_count=None):
    from jarvis.core.catalog_bind import bind_motor_from_catalog, bind_propeller_from_catalog
    from jarvis.core.component_writers import set_motor_component, set_propeller_component
    from jarvis.knowledge.library import default_library

    ps = orch.state_manager.load_active_project(orch.workspace_manager)

    if propeller_sku is not None:
        prop_spec = bind_propeller_from_catalog(propeller_sku)
        ps = set_propeller_component(ps, prop_spec)

    if battery_cell_count is not None:
        ps = ps.model_copy(update={
            "current_parameters": {**ps.current_parameters, "battery_cell_count": battery_cell_count},
        })

    m = default_library.get_motor(motor_sku)
    motor_spec = bind_motor_from_catalog({
        "name": m.name, "max_watts": m.max_watts, "thrust_n": m.thrust_n,
        "kv_rating": m.kv_rating, "weight_g": m.weight_g,
    })
    ps = set_motor_component(ps, motor_spec, m.max_watts)
    orch.workspace_manager.save_state(ps)
    return orch.state_manager.load_active_project(orch.workspace_manager)


def _fresh_orchestrator(tmp_root: Path, name: str):
    from jarvis.core.orchestrator import JarvisOrchestrator

    orch = JarvisOrchestrator(workspace_root=tmp_root / name)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": f"probe validation case {name}",
            "payload_kg": 1.0, "restrictions": "no", "detail_level": "conceptual",
            "motors": 4, "structure_mass_factor": 0.5, "safety_factor": 1.2,
        },
    })
    return orch


def _assert_close(actual, expected, label, tol=1e-6):
    assert actual is not None, f"{label} FAIL: got None, expected {expected}"
    assert abs(float(actual) - float(expected)) <= tol, f"{label} FAIL: got {actual}, expected {expected}"


def main() -> int:
    import json as _json

    from jarvis.adapters.cli.main import render_startup_context

    with tempfile.TemporaryDirectory(prefix="jarvis-probe-validation-case-") as tmp:
        tmp_root = Path(tmp)

        # ── Step 1: OP-2 ─────────────────────────────────────────────────
        orch2 = _fresh_orchestrator(tmp_root, "op2")
        ps2 = _bind_motor_propeller(
            orch2, motor_sku="emax_rs2205s_2300", propeller_sku="hq_5045_bn",
            battery_cell_count=4.32,  # 4.32 * 3.7 ~= 16.0 V
        )
        res2 = _json.loads(ps2.current_parameters["propulsion_resolution"])
        assert res2["resolution_type"] == "exact_operating_point", f"step1 FAIL: {res2}"
        _assert_close(res2["thrust_n"], 9.7086, "step1 thrust_n")
        _assert_close(ps2.current_parameters.get("motor_op_power_w"), 432.0, "step1 motor_op_power_w")
        _assert_close(ps2.current_parameters.get("motor_op_current_a"), 27.0, "step1 motor_op_current_a")
        _assert_close(ps2.current_parameters.get("motor_op_rpm"), 23560.0, "step1 motor_op_rpm")
        assert res2["source_type"] == "manufacturer_test", f"step1 FAIL: source_type={res2['source_type']}"
        _assert_close(res2["confidence"], 0.98, "step1 confidence")
        print("✓ Step 1 PASS: OP-2 (emax_rs2205s_2300 + hq_5045_bn @ ~16.0V) matches ★6 exactly")

        # ── Step 2: OP-3 ─────────────────────────────────────────────────
        orch3 = _fresh_orchestrator(tmp_root, "op3")
        ps3 = _bind_motor_propeller(
            orch3, motor_sku="sunnysky_r2205_2500", propeller_sku="gf_5045x3",
            battery_cell_count=4,  # 4 * 3.7 = 14.8 V
        )
        res3 = _json.loads(ps3.current_parameters["propulsion_resolution"])
        assert res3["resolution_type"] == "exact_operating_point", f"step2 FAIL: {res3}"
        _assert_close(res3["thrust_n"], 12.5525, "step2 thrust_n")
        _assert_close(ps3.current_parameters.get("motor_op_power_w"), 592.0, "step2 motor_op_power_w")
        _assert_close(ps3.current_parameters.get("motor_op_current_a"), 40.0, "step2 motor_op_current_a")
        _assert_close(ps3.current_parameters.get("motor_op_rpm"), 27082.0, "step2 motor_op_rpm")
        assert res3["source_type"] == "manufacturer_test", f"step2 FAIL: source_type={res3['source_type']}"
        _assert_close(res3["confidence"], 0.97, "step2 confidence")
        print("✓ Step 2 PASS: OP-3 (sunnysky_r2205_2500 + gf_5045x3 @ 14.8V) matches ★6 exactly")

        # ── Step 3: OP-0 fallback ────────────────────────────────────────
        orch0 = _fresh_orchestrator(tmp_root, "op0")
        ps0 = _bind_motor_propeller(orch0, motor_sku="emax_rs2205s_2300")  # no propeller bound
        res0 = _json.loads(ps0.current_parameters["propulsion_resolution"])
        assert res0["resolution_type"] == "fallback_operating_point", f"step3 FAIL: {res0}"
        _assert_close(res0["thrust_n"], 10.0420, "step3 thrust_n")
        assert ps0.current_parameters.get("motor_op_power_w") is None, (
            f"step3 FAIL: motor_op_power_w should be absent, got {ps0.current_parameters.get('motor_op_power_w')}"
        )
        assert ps0.current_parameters.get("motor_op_current_a") is None
        assert ps0.current_parameters.get("motor_op_rpm") is None
        print("✓ Step 3 PASS: OP-0 fallback (emax_rs2205s_2300, no propeller) -> "
              "fallback_operating_point, thrust_n=10.0420, no OP electrical tuple")

        # ── Step 4: estado regression (existing lines only) ─────────────
        ctx2 = orch2.build_startup_context()
        rendered2 = render_startup_context(ctx2)
        assert "Propulsión (evidencia): exact_operating_point · manufacturer_test · 9.7086 N" in rendered2, (
            f"step4 FAIL: evidencia line missing/changed: {rendered2[:800]!r}"
        )
        assert "Propulsión (OP eléctrico): power=432.0 W · current=27.0 A · rpm=23560.0" in rendered2, (
            f"step4 FAIL: OP electrical line missing/changed: {rendered2[:800]!r}"
        )
        assert "Validation" not in rendered2 and "Confianza" not in rendered2, (
            "step4 FAIL: a new validation-summary line was added — forbidden by contract §2.3"
        )
        print("✓ Step 4 PASS: estado shows only the two existing propulsion lines, no new UI")

        # ── Step 5: rating vs OP coexistence ─────────────────────────────
        _assert_close(ps2.current_parameters.get("motor_power_w"), 400.0, "step5 motor_power_w")
        _assert_close(ps2.current_parameters.get("motor_op_power_w"), 432.0, "step5 motor_op_power_w")
        print("✓ Step 5 PASS: motor_power_w=400.0 (rating) and motor_op_power_w=432.0 (OP) coexist")

        # ── Step 6: P2-2 probe regression ───────────────────────────────
        result = subprocess.run(
            [sys.executable, "scripts/cli_probe_p2_2_operating_point_bridge.py"],
            capture_output=True, text=True, cwd=str(Path(__file__).resolve().parents[1]),
        )
        assert "6/6 PASS" in result.stdout, (
            f"step6 FAIL: cli_probe_p2_2_operating_point_bridge.py did not report 6/6:\n"
            f"{result.stdout[-1000:]}\n{result.stderr[-500:]}"
        )
        print("✓ Step 6 PASS: cli_probe_p2_2_operating_point_bridge.py still 6/6")

        print("\n=== SUMMARY: 6/6 PASS ===")
        return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    try:
        raise SystemExit(main())
    except AssertionError as e:
        print(f"\n✗ FAIL: {e}", file=sys.stderr)
        raise SystemExit(1)
