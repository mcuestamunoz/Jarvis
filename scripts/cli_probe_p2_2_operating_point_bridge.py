#!/usr/bin/env python3
"""CLI probe — P2-2 Operating Point Bridge (contract §3 P2-6).

Steps:
  1. Bind motor emax_rs2205s_2300 + propeller hq_5045_bn + ~16V (battery
     cell count) -> motor_power_w == 400.0 (catalog rating, unchanged).
  2. Inspect current_parameters -> motor_op_power_w == 432.0,
     motor_op_current_a == 27.0 (the resolved operating point).
  3. "calcular" -> autonomy_min reflects the OP power (lower than a
     rating-only calc would give).
  4. "estado" -> shows a distinct OP-electrical line, never conflated with
     the catalog rating line.
  5. Bind a legacy-estimate SKU (emax_rs2205_2300, no operating_points
     data) -> zero motor_op_* keys, motor_power_w unchanged/honest.
  6. Closure smoke: cli_probe_requirements_closure.py still 5/5.

Real production wiring, no LLM where avoidable.
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


def _say(orch, text: str, llm: _RefuseLLM) -> dict:
    print(f"\nUser > {text}")
    result = orch.handle_user_text(text, llm)
    msg = result.get("message") or result.get("question") or ""
    if msg:
        print(f"Jarvis > {msg[:400]}")
    print(f"  [action={result.get('action')} status={result.get('status')}]")
    return result


def main() -> int:
    from jarvis.adapters.cli.main import render_startup_context
    from jarvis.core.catalog_bind import bind_motor_from_catalog, bind_propeller_from_catalog
    from jarvis.core.component_writers import set_motor_component, set_propeller_component
    from jarvis.core.orchestrator import JarvisOrchestrator
    from jarvis.knowledge.library import default_library

    llm = _RefuseLLM()
    with tempfile.TemporaryDirectory(prefix="jarvis-probe-p2-2-") as tmp:
        orch = JarvisOrchestrator(workspace_root=Path(tmp))
        orch.handle({
            "action": "create_project",
            "parameters": {
                "vehicle_type": "dron",
                "objective": "probe p2-2 operating point bridge",
                "payload_kg": 1.0,
                "restrictions": "no",
                "detail_level": "conceptual",
                "motors": 4,
                "structure_mass_factor": 0.5,
                "safety_factor": 1.2,
            },
        })
        ps = orch.state_manager.load_active_project(orch.workspace_manager)

        prop_spec = bind_propeller_from_catalog("hq_5045_bn")
        ps = set_propeller_component(ps, prop_spec)
        ps = ps.model_copy(update={
            "current_parameters": {**ps.current_parameters, "battery_cell_count": 4.32},  # ~16.0V
        })
        m = default_library.get_motor("emax_rs2205s_2300")
        motor_spec = bind_motor_from_catalog({
            "name": m.name, "max_watts": m.max_watts, "thrust_n": m.thrust_n,
            "kv_rating": m.kv_rating, "weight_g": m.weight_g,
        })
        ps = set_motor_component(ps, motor_spec, m.max_watts)
        ps = ps.model_copy(update={
            "current_parameters": {**ps.current_parameters, "battery_capacity_wh": 100.0},
        })
        orch.workspace_manager.save_state(ps)

        # ── Step 1 ───────────────────────────────────────────────────────
        ps = orch.state_manager.load_active_project(orch.workspace_manager)
        assert ps.current_parameters.get("motor_power_w") == 400.0, (
            f"step1 FAIL: motor_power_w={ps.current_parameters.get('motor_power_w')}"
        )
        print(f"✓ Step 1 PASS: motor_power_w={ps.current_parameters['motor_power_w']} (catalog rating, unchanged)")

        # ── Step 2 ───────────────────────────────────────────────────────
        op_power = ps.current_parameters.get("motor_op_power_w")
        op_current = ps.current_parameters.get("motor_op_current_a")
        assert op_power == 432.0, f"step2 FAIL: motor_op_power_w={op_power}"
        assert op_current == 27.0, f"step2 FAIL: motor_op_current_a={op_current}"
        print(f"✓ Step 2 PASS: motor_op_power_w={op_power}, motor_op_current_a={op_current}")

        # ── Step 3 ───────────────────────────────────────────────────────
        calc = _say(orch, "calcular", llm)
        assert calc["status"] == "ok"
        ps3 = orch.state_manager.load_active_project(orch.workspace_manager)
        autonomy_with_op = ps3.latest_results["calculations"]["autonomy_min"]

        from jarvis.core.calculation_engine import CalculationEngine
        params_rating_only = dict(ps3.current_parameters)
        params_rating_only.pop("motor_op_power_w", None)
        bundle_rating_only = CalculationEngine().build(params_rating_only)
        assert autonomy_with_op < bundle_rating_only.autonomy_min, (
            f"step3 FAIL: OP autonomy {autonomy_with_op} not lower than rating-only {bundle_rating_only.autonomy_min}"
        )
        print(f"✓ Step 3 PASS: autonomy_min={autonomy_with_op} (< rating-only {bundle_rating_only.autonomy_min})")

        # ── Step 4 ───────────────────────────────────────────────────────
        status = _say(orch, "estado", llm)
        text = render_startup_context(status.get("startup_context") or {})
        assert "Propulsión (OP eléctrico): power=432.0 W · current=27.0 A" in text, (
            f"step4 FAIL: OP electrical line missing: {text[:800]!r}"
        )
        assert "Propulsión (evidencia): exact_operating_point" in text
        print("✓ Step 4 PASS: estado shows distinct OP-electrical line")

        # ── Step 5: legacy SKU ──────────────────────────────────────────
        orch5 = JarvisOrchestrator(workspace_root=Path(tempfile.mkdtemp(prefix="jarvis-probe-p2-2-legacy-")))
        orch5.handle({
            "action": "create_project",
            "parameters": {
                "vehicle_type": "dron", "objective": "legacy smoke", "payload_kg": 1.0,
                "restrictions": "no", "detail_level": "conceptual", "motors": 4,
                "structure_mass_factor": 0.5, "safety_factor": 1.2,
            },
        })
        ps5 = orch5.state_manager.load_active_project(orch5.workspace_manager)
        m5 = default_library.get_motor("emax_rs2205_2300")
        legacy_spec = bind_motor_from_catalog({
            "name": m5.name, "max_watts": m5.max_watts, "thrust_n": m5.thrust_n,
            "kv_rating": m5.kv_rating, "weight_g": m5.weight_g,
        })
        ps5 = set_motor_component(ps5, legacy_spec, m5.max_watts)
        assert "motor_op_power_w" not in ps5.current_parameters
        assert "motor_op_current_a" not in ps5.current_parameters
        assert "motor_op_rpm" not in ps5.current_parameters
        assert ps5.current_parameters["motor_power_w"] == m5.max_watts
        print(f"✓ Step 5 PASS: legacy SKU {m5.name} -> zero motor_op_* keys, motor_power_w honest")

        # ── Step 6: closure smoke ───────────────────────────────────────
        result = subprocess.run(
            [sys.executable, "scripts/cli_probe_requirements_closure.py"],
            capture_output=True, text=True, cwd=str(Path(__file__).resolve().parents[1]),
        )
        assert "5/5 PASS" in result.stdout, (
            f"step6 FAIL: closure probe did not report 5/5 PASS:\n{result.stdout[-1000:]}\n{result.stderr[-500:]}"
        )
        print("✓ Step 6 PASS: cli_probe_requirements_closure.py still 5/5")

        print("\n=== SUMMARY: 6/6 PASS ===")
        return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    try:
        raise SystemExit(main())
    except AssertionError as e:
        print(f"\n✗ FAIL: {e}", file=sys.stderr)
        raise SystemExit(1)
