#!/usr/bin/env python3
"""CLI probe — Frankenstein .name Clear (IC D, contract §3 G24D-4).

Steps (investigation_report_deferred_queue_post_v031.md §6.1 repro):
  1. Bind motor -> "optimiza para aumentar payload" -> "aplica la mejor"
     (abstract #1, diverges per_motor_max_thrust_n/motor_count).
  2. catalog_ref is None (G5, unchanged).
  3. Motor .name != original SKU string.
  4. estado / format_bom_lines motor line does not display the old SKU
     as the name.
  5. sku_resolved still False; no [sku] bracket either.
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


_BOUND_SKU = "sunnysky_r2305_2500"


def main() -> int:
    from jarvis.adapters.cli.main import render_startup_context
    from jarvis.core.catalog_bind import bind_motor_from_catalog
    from jarvis.core.component_writers import set_motor_component
    from jarvis.core.orchestrator import JarvisOrchestrator
    from jarvis.core.project_closure import build_component_bom, format_bom_lines
    from jarvis.knowledge.library import default_library

    llm = _RefuseLLM()
    with tempfile.TemporaryDirectory(prefix="jarvis-probe-g24d-") as tmp:
        orch = JarvisOrchestrator(workspace_root=Path(tmp))
        orch.handle({
            "action": "create_project",
            "parameters": {
                "vehicle_type": "dron",
                "objective": "probe frankenstein name clear",
                "payload_kg": 1.0,
                "restrictions": "no",
                "detail_level": "conceptual",
                "motors": 4,
                "structure_mass_factor": 0.5,
                "safety_factor": 1.2,
            },
        })
        ps = orch.state_manager.load_active_project(orch.workspace_manager)
        bound_motor = default_library.get_motor(_BOUND_SKU)
        spec = bind_motor_from_catalog({
            "idx": 1, "name": _BOUND_SKU, "thrust_n": bound_motor.thrust_n,
            "kv_rating": bound_motor.kv_rating, "weight_g": bound_motor.weight_g,
            "max_watts": bound_motor.max_watts, "is_generic": bound_motor.is_generic,
        })
        ps = set_motor_component(ps, spec, bound_motor.max_watts)
        orch.workspace_manager.save_state(ps)
        print(f"=== Setup: motor bound to {_BOUND_SKU} ===")

        # ── Step 1 ───────────────────────────────────────────────────────
        explore_result = _say(orch, "optimiza para aumentar payload", llm)
        assert explore_result["status"] == "ok"
        apply_result = _say(orch, "aplica la mejor", llm)
        assert apply_result["status"] == "ok"
        print("✓ Step 1 PASS: abstract #1 applied")

        saved = orch.state_manager.load_active_project(orch.workspace_manager)
        motors = saved.design_properties.components["motors"]

        # ── Step 2 ───────────────────────────────────────────────────────
        assert motors.catalog_ref is None, f"step2 FAIL: catalog_ref={motors.catalog_ref}"
        print("✓ Step 2 PASS: catalog_ref cleared (G5, unchanged)")

        # ── Step 3 ───────────────────────────────────────────────────────
        assert motors.name != _BOUND_SKU, f"step3 FAIL: .name still the old SKU: {motors.name!r}"
        assert not default_library.has_motor(motors.name), (
            f"step3 FAIL: new .name is itself a real SKU: {motors.name!r}"
        )
        print(f"✓ Step 3 PASS: motor.name={motors.name!r} (not the old SKU, not any real SKU)")

        # ── Step 4 ───────────────────────────────────────────────────────
        # Scope note (contract §5 non-goal): Continuity's own "Catálogo:
        # candidatos ..." evidence line is a SEPARATE, unrelated surface
        # (resolve_motor_catalog_surface's fresh design-space search) — it
        # may legitimately re-suggest the same SKU as a *new* pick candidate
        # after divergence, which is correct and untouched by this IC. This
        # step checks only the motor component's own identity line, in both
        # the direct BOM projection and the estado "Componentes / gaps"
        # section that renders it.
        bom = build_component_bom(saved)
        lines = format_bom_lines(bom)
        motor_line = next(l for l in lines if l.startswith("✓ motors"))
        assert _BOUND_SKU not in motor_line, f"step4 FAIL: old SKU string leaked into BOM line: {motor_line!r}"
        ctx = orch.build_startup_context()
        rendered = render_startup_context(ctx)
        rendered_motor_line = next(
            l for l in rendered.splitlines() if l.strip().startswith("✓ motors")
        )
        assert _BOUND_SKU not in rendered_motor_line, (
            f"step4 FAIL: old SKU string leaked into estado's motor line: {rendered_motor_line!r}"
        )
        print(f"✓ Step 4 PASS: motor's own BOM/estado line honest: {motor_line!r}")

        # ── Step 5 ───────────────────────────────────────────────────────
        entry = next(e for e in bom["defined"] if e["key"] == "motors")
        assert entry["sku_resolved"] is False, f"step5 FAIL: sku_resolved={entry['sku_resolved']}"
        assert "[" not in motor_line, f"step5 FAIL: bracketed SKU claim present: {motor_line!r}"
        print("✓ Step 5 PASS: sku_resolved=False, no [sku] bracket")

        print("\n=== SUMMARY: 5/5 PASS ===")
        return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    try:
        raise SystemExit(main())
    except AssertionError as e:
        print(f"\n✗ FAIL: {e}", file=sys.stderr)
        raise SystemExit(1)
