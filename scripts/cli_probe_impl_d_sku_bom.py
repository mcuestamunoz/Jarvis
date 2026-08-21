#!/usr/bin/env python3
"""CLI probe — Impl D Create -> BOM / SKU BOM (contract §4.3 / §9).

Steps:
  1. Bind a real motor SKU via the component wizard (G21 path).
  2. estado -> BOM line shows [sku] + qty=N (D1/D2), and the BOM section
     actually renders even though Continuity has evidence queued (D4/★6 —
     before this IC, the section would have been silently suppressed).
  3. Force a G5 divergence (frankenstein: catalog_ref cleared, .name kept)
     -> estado BOM line no longer shows [sku] (Scenario D honesty).
  4. Confirm no new gap type was introduced (★4) and readiness is otherwise
     unaffected.
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
    from jarvis.core.catalog_bind import invalidate_diverged_catalog_refs
    from jarvis.core.engineering_readiness import build_engineering_readiness
    from jarvis.core.orchestrator import JarvisOrchestrator
    from jarvis.knowledge.library import default_library

    llm = _RefuseLLM()
    with tempfile.TemporaryDirectory(prefix="jarvis-probe-impld-") as tmp:
        orch = JarvisOrchestrator(workspace_root=Path(tmp))
        orch.handle({
            "action": "create_project",
            "parameters": {
                "vehicle_type": "dron",
                "objective": "probe Impl D SKU BOM",
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

        _say(orch, "definir propulsion", llm)
        choose = _say(orch, "ayúdame a elegir", llm)
        assert choose.get("motor_suggestions"), "step1: motor_suggestions empty"
        pick = _say(orch, "1", llm)
        assert pick.get("status") == "ok"

        project = orch.state_manager.load_active_project(orch.workspace_manager)
        motors = project.design_properties.components.get("motors")
        assert motors is not None and motors.catalog_ref is not None
        sku = motors.catalog_ref.sku
        print(f"\n✓ Step 1 PASS: bound {sku}")

        # Autonomy constraint -> energy_model_honesty_note fires -> Continuity
        # evidence is non-empty -> pre-D4 this would have hidden the BOM
        # section entirely.
        project = project.model_copy(update={
            "parsed_constraints": {**project.parsed_constraints, "autonomy_min": 20.0},
            "current_parameters": {**project.current_parameters, "motor_count": 6, "propeller_diameter_in": 5.0},
        })
        orch.workspace_manager.save_state(project)

        status = _say(orch, "estado", llm)
        ctx = status.get("startup_context") or {}
        continuity = ctx.get("continuity") or {}
        bom_lines = ctx.get("component_bom_lines") or []
        assert continuity.get("evidence"), "step2 precondition: Continuity evidence must be non-empty"
        motor_line = next((l for l in bom_lines if l.startswith("✓ motors")), None)
        assert motor_line is not None, "step2: no motors BOM line found"
        assert f"[{sku}]" in motor_line, f"step2: BOM line missing [sku]: {motor_line!r}"
        assert "qty=6" in motor_line, f"step2: BOM line missing qty: {motor_line!r}"

        rendered = render_startup_context(ctx)
        assert "Componentes / gaps:" in rendered, (
            "step2 FAIL (★6/D4): BOM section suppressed despite Continuity evidence being present"
        )
        assert f"[{sku}]" in rendered
        print(f"✓ Step 2 PASS: estado shows '[{sku}] qty=6' even with Continuity evidence present (D4)")

        # ── Step 3: frankenstein via real G5 divergence ─────────────────────
        diverged_params = dict(project.current_parameters)
        diverged_params["per_motor_max_thrust_n"] = default_library.get_motor(sku).thrust_n * 2
        updated_components, updated_params = invalidate_diverged_catalog_refs(
            project.design_properties.components, diverged_params
        )
        project2 = project.model_copy(update={
            "current_parameters": updated_params,
            "design_properties": project.design_properties.model_copy(update={"components": updated_components}),
        })
        orch.workspace_manager.save_state(project2)

        frankenstein = project2.design_properties.components["motors"]
        assert frankenstein.catalog_ref is None
        assert frankenstein.name == sku  # .name still looks like a SKU

        status2 = _say(orch, "estado", llm)
        ctx2 = status2.get("startup_context") or {}
        bom_lines2 = ctx2.get("component_bom_lines") or []
        motor_line2 = next((l for l in bom_lines2 if l.startswith("✓ motors")), None)
        assert motor_line2 is not None
        assert f"[{sku}]" not in motor_line2, (
            f"step3 FAIL: frankenstein presented as resolved SKU: {motor_line2!r}"
        )
        print(f"✓ Step 3 PASS: frankenstein motor line does not claim a resolved SKU: {motor_line2!r}")

        # ── Step 4: no new gap type, readiness otherwise unaffected ────────
        readiness = build_engineering_readiness(project2)
        gap_types = {g.gap_type for g in readiness.gaps}
        assert "GAP-BOM-SKU-UNRESOLVED" not in gap_types
        print("✓ Step 4 PASS: no new gap type introduced (★4)")

        print("\n=== SUMMARY: 4/4 PASS ===")
        return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    try:
        raise SystemExit(main())
    except AssertionError as e:
        print(f"\n✗ FAIL: {e}", file=sys.stderr)
        raise SystemExit(1)
