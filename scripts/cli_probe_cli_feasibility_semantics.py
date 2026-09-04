#!/usr/bin/env python3
"""CLI probe — CLI feasibility vs readiness semantics.

implementation_contract_cli_feasibility_semantics.md §3 (optional probe;
not a substitute for tests/test_cli_feasibility_semantics.py).

Deterministic, no LLM. Reproduces the field fixture
(workspace/autonomía-de-5min-c09442c25db0): emax_rs2205s_2300 (catalog,
no nameplate max_watts) + hq_5045_bn propeller (catalog) + a 4S battery +
an autonomy_min=5 constraint the energy model cannot evaluate.

Steps:
  1. Bind motor/propeller/battery, set the autonomy constraint.
  2. calcular -> named-negative autonomía, not silent, not a fake minute.
  3. simular -> thrust feasibility PASS unchanged; same named negative.
  4. estado -> no "Declarar motor_power_w", situation is thrust-feasibility
     scoped (not "Diseño validado"), fallback suffix reflects BOM identity
     (propeller IS catalog-bound), ERF Energy still PASS (untouched, §4).
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


def main() -> int:
    from jarvis.adapters.cli.main import render_response, render_startup_context
    from jarvis.core.catalog_bind import bind_battery_from_catalog, bind_motor_from_catalog, bind_propeller_from_catalog
    from jarvis.core.component_writers import set_battery_component, set_motor_component, set_propeller_component
    from jarvis.core.orchestrator import JarvisOrchestrator
    from jarvis.knowledge.library import default_library

    with tempfile.TemporaryDirectory(prefix="jarvis-probe-cli-feasibility-") as tmp:
        orch = JarvisOrchestrator(workspace_root=Path(tmp))
        orch.handle({
            "action": "create_project",
            "parameters": {
                "vehicle_type": "dron", "objective": "autonomía de 5 min", "payload_kg": 1.0,
                "restrictions": "no", "detail_level": "conceptual", "motors": 4,
                "structure_mass_factor": 0.6, "safety_factor": 1.2,
            },
        })
        ps = orch.state_manager.load_active_project(orch.workspace_manager)

        ps = set_propeller_component(ps, bind_propeller_from_catalog("hq_5045_bn"))
        m = default_library.get_motor("emax_rs2205s_2300")
        assert m.max_watts is None, "fixture assumes this SKU has no nameplate wattage"
        motor_spec = bind_motor_from_catalog({
            "name": m.name, "max_watts": m.max_watts, "thrust_n": m.thrust_n,
            "kv_rating": m.kv_rating, "weight_g": m.weight_g, "is_generic": m.is_generic,
        })
        ps = set_motor_component(ps, motor_spec, m.max_watts)
        battery_spec = bind_battery_from_catalog("lipo_4s_10000mah")
        ps = set_battery_component(
            ps, battery_spec, battery_spec.properties["battery_capacity_wh"].value
        )
        ps = ps.model_copy(update={"parsed_constraints": {"autonomy_min": 5.0}})
        orch.workspace_manager.save_state(ps)
        print("✓ Step 1 PASS: emax_rs2205s_2300 (no W) + hq_5045_bn + 4S battery bound, autonomy_min=5 constraint set")

        llm = _RefuseLLM()

        calc_result = orch.handle_user_text("calcular", llm)
        assert calc_result["status"] == "ok", calc_result
        assert calc_result["calculations"]["autonomy_min"] is None
        calc_rendered = render_response(calc_result)
        assert "autonomía=no calculada" in calc_rendered, calc_rendered
        assert "autonomía real" not in calc_rendered.lower()
        print("✓ Step 2 PASS: calcular names the energy gap — not silent, not a fake minute")

        sim_result = orch.handle_user_text("simular", llm)
        assert sim_result["status"] == "ok", sim_result
        assert sim_result["simulation"]["status"] == "pass"
        assert sim_result["simulation"]["autonomy_min"] is None
        sim_rendered = render_response(sim_result)
        assert "autonomía=no calculada" in sim_rendered, sim_rendered
        print(f"✓ Step 3 PASS: simular status=pass (thrust feasibility unchanged), autonomía named-negative")

        ctx = orch.build_startup_context()
        estado_rendered = render_startup_context(ctx)

        assert "Declarar motor_power_w" not in estado_rendered
        continuity = ctx.get("continuity") or {}
        situation = continuity.get("situation", "")
        assert "Diseño validado en simulación (PASS)" not in situation
        assert "Comprobación de empuje" in situation, situation
        assert "(sin hélice de catálogo)" not in estado_rendered
        assert "fallback de fabricante" in estado_rendered

        readiness = ctx.get("readiness") or {}
        energy_verdict = ((readiness.get("subsystems") or {}).get("energy") or {}).get("verdict")
        assert energy_verdict == "PASS", energy_verdict
        print("✓ Step 4 PASS: estado — no invented-W CTA, thrust-feasibility situation, BOM-aware suffix, ERF Energy PASS untouched")

    print("\n=== SUMMARY: 4/4 CLI FEASIBILITY SEMANTICS PROBES PASS ===")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    try:
        raise SystemExit(main())
    except AssertionError as e:
        print(f"\n✗ FAIL: {e}", file=sys.stderr)
        raise SystemExit(1)
