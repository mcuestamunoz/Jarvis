#!/usr/bin/env python3
"""CLI probe — Phase 2 P2-1 Lookup Operating Point (IC §7).

Steps:
  1. Create project, bind emax_rs2205s_2300 via the real component wizard
     ("ayúdame a elegir" -> pick by number, G21 path, unmodified).
  2. estado -> fallback resolution visible (no propeller bound yet);
     thrust ~= 10.042 N, labeled fallback_operating_point / manufacturer_test.
  3. Bind propeller hq_5045_bn (real bind path — bind_propeller_from_catalog
     has no live wizard UX yet per docs/PHYSICAL_COMPONENT_CATALOG_V1.md
     §6/Impl B scope, so this step uses the same test-callable API the
     Impl C/D probes already rely on for battery binds — documented here,
     not a UX gap introduced by this IC).
  4. estado -> exact resolution, thrust in {9.1986, 9.7086} with v1
     max-thrust policy -> 9.7086.
  5. Confirm sunnysky_r2305_2500 still bindable as legacy (untouched SKU).
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
        print(f"Jarvis > {msg[:800]}")
    print(f"  [action={result.get('action')} status={result.get('status')}]")
    return result


def main() -> int:
    from jarvis.adapters.cli.main import render_startup_context
    from jarvis.core.catalog_bind import bind_motor_from_catalog, bind_propeller_from_catalog
    from jarvis.core.component_writers import set_motor_component, set_propeller_component
    from jarvis.core.orchestrator import JarvisOrchestrator
    from jarvis.knowledge.library import default_library

    llm = _RefuseLLM()
    with tempfile.TemporaryDirectory(prefix="jarvis-probe-phase2op-") as tmp:
        orch = JarvisOrchestrator(workspace_root=Path(tmp))
        orch.handle({
            "action": "create_project",
            "parameters": {
                "vehicle_type": "dron",
                "objective": "probe Phase 2 P2-1 lookup operating point",
                "payload_kg": 1.0,
                "restrictions": "ninguna",
                "detail_level": "conceptual",
                "structure_mass_factor": 0.5,
                "safety_factor": 1.2,
            },
        })
        ps = orch.state_manager.load_active_project(orch.workspace_manager)
        orch.system_definition_session.start("dron", ps)
        orch.system_definition_session.answer("A")
        print("=== Setup: project created, architecture A applied ===")

        # ── Step 1: bind emax_rs2205s_2300 via the real wizard ─────────────
        _say(orch, "definir propulsion", llm)
        choose = _say(orch, "ayúdame a elegir", llm)
        suggestions = choose.get("motor_suggestions") or []
        assert suggestions, "step1: motor_suggestions empty"
        idx = next((s["idx"] for s in suggestions if s["name"] == "emax_rs2205s_2300"), None)
        assert idx is not None, (
            f"step1 FAIL: emax_rs2205s_2300 not in wizard suggestions: "
            f"{[s['name'] for s in suggestions]}"
        )
        pick = _say(orch, str(idx), llm)
        assert pick.get("status") == "ok"

        project = orch.state_manager.load_active_project(orch.workspace_manager)
        motors = project.design_properties.components.get("motors")
        assert motors is not None and motors.catalog_ref is not None
        assert motors.catalog_ref.sku == "emax_rs2205s_2300"
        print(f"\n✓ Step 1 PASS: bound emax_rs2205s_2300 (wizard idx={idx})")

        # ── Step 2: estado -> fallback resolution (no propeller bound) ─────
        status = _say(orch, "estado", llm)
        ctx = status.get("startup_context") or {}
        rendered = render_startup_context(ctx)
        assert "fallback_operating_point" in rendered, (
            f"step2 FAIL: expected fallback_operating_point in estado, got:\n{rendered}"
        )
        assert "10.042" in rendered
        assert "manufacturer_test" in rendered
        assert "(sin hélice de catálogo)" in rendered
        print("✓ Step 2 PASS: estado shows fallback_operating_point / manufacturer_test / 10.042 N")

        # ── Step 3: bind propeller hq_5045_bn (test-callable API) ──────────
        project = orch.state_manager.load_active_project(orch.workspace_manager)
        prop_spec = bind_propeller_from_catalog("hq_5045_bn")
        project = set_propeller_component(project, prop_spec)
        # Re-apply the motor bind so the bridge re-resolves now that a
        # propeller catalog_ref exists (mirrors what a real re-declare turn
        # would trigger via apply_and_recalculate).
        motor_spec = bind_motor_from_catalog(
            {
                "idx": 1, "name": "emax_rs2205s_2300",
                "thrust_n": default_library.get_motor("emax_rs2205s_2300").thrust_n,
                "kv_rating": default_library.get_motor("emax_rs2205s_2300").kv_rating,
                "weight_g": default_library.get_motor("emax_rs2205s_2300").weight_g,
                "max_watts": default_library.get_motor("emax_rs2205s_2300").max_watts,
                "is_generic": False,
            }
        )
        project = project.model_copy(update={
            "current_parameters": {**project.current_parameters, "battery_cell_count": 4.32},  # ~16.0V
        })
        project = set_motor_component(project, motor_spec, default_library.get_motor("emax_rs2205s_2300").max_watts)
        orch.workspace_manager.save_state(project)
        print("✓ Step 3: propeller hq_5045_bn bound, motor re-resolved with propeller + ~16V context")

        # ── Step 4: estado -> exact resolution, max-thrust policy ──────────
        status2 = _say(orch, "estado", llm)
        ctx2 = status2.get("startup_context") or {}
        rendered2 = render_startup_context(ctx2)
        assert "exact_operating_point" in rendered2, (
            f"step4 FAIL: expected exact_operating_point in estado, got:\n{rendered2}"
        )
        assert "9.7086" in rendered2, f"step4 FAIL: expected max-thrust 9.7086 N, got:\n{rendered2}"
        assert project.current_parameters["per_motor_max_thrust_n"] in (9.1986, 9.7086)
        assert project.current_parameters["per_motor_max_thrust_n"] == 9.7086
        print("✓ Step 4 PASS: estado shows exact_operating_point, v1_max_thrust -> 9.7086 N")

        # ── Step 5: sunnysky_r2305_2500 still bindable as legacy ───────────
        legacy_spec = bind_motor_from_catalog({
            "idx": 1, "name": "sunnysky_r2305_2500",
            "thrust_n": default_library.get_motor("sunnysky_r2305_2500").thrust_n,
            "kv_rating": default_library.get_motor("sunnysky_r2305_2500").kv_rating,
            "weight_g": default_library.get_motor("sunnysky_r2305_2500").weight_g,
            "max_watts": default_library.get_motor("sunnysky_r2305_2500").max_watts,
            "is_generic": False,
        })
        legacy_ps = set_motor_component(project, legacy_spec, default_library.get_motor("sunnysky_r2305_2500").max_watts)
        assert legacy_ps.current_parameters["per_motor_max_thrust_n"] == 7.5
        print("✓ Step 5 PASS: sunnysky_r2305_2500 unchanged, still resolves as legacy 7.5 N")

        print("\n=== SUMMARY: 5/5 PASS ===")
        return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    try:
        raise SystemExit(main())
    except AssertionError as e:
        print(f"\n✗ FAIL: {e}", file=sys.stderr)
        raise SystemExit(1)
