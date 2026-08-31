#!/usr/bin/env python3
"""CLI probe — Battery Catalog UX + G27 Hardening (IC 2, contract §9).

Steps (contract table):
  1. Create/minimal project, drive propulsion to bound (motor+propeller
     catalog pick), ESC declared -> baseline, battery still stub.
  2. Open energy gap -> "ayúdame a elegir" -> list includes lipo_6s_10000mah.
  3. Pick that SKU -> catalog_ref, battery_capacity_wh=222.0 (seed value).
  4. "calcular" -> autonomía_min coherent with 222 Wh (not 6 Wh, not None).
  5. "estado" -> battery line shows [lipo_6s_10000mah] resolved.
  6. G27 phrase on a freeform (unbound) project's semantic adapter ->
     battery_capacity_wh != 6.0.

Real handle_user_text turns throughout (no state-patch bind shortcuts for
the mechanism under test) — matches the propeller/Impl D probe precedent.
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


def main() -> int:
    from jarvis.adapters.cli.main import render_startup_context
    from jarvis.core.orchestrator import JarvisOrchestrator
    from jarvis.knowledge.library import default_library
    from jarvis.llm.semantic_intent_adapter import SemanticIntentAdapter

    llm = _RefuseLLM()
    with tempfile.TemporaryDirectory(prefix="jarvis-probe-battery-") as tmp:
        orch = JarvisOrchestrator(workspace_root=Path(tmp))
        orch.handle({
            "action": "create_project",
            "parameters": {
                "vehicle_type": "dron",
                "objective": "probe battery catalog bind ux",
                "payload_kg": 1.0,
                "restrictions": "no",
                "detail_level": "conceptual",
                "motors": 4,
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

        prop_choose = _say(orch, "ayúdame a elegir", llm)
        assert prop_choose.get("propeller_suggestions"), "step1: propeller_suggestions empty"
        prop_pick = _say(orch, "1", llm)
        assert prop_pick.get("status") == "ok"

        esc_result = _say(orch, "ESC 30A", llm)
        assert esc_result.get("status") == "ok"

        project = orch.state_manager.load_active_project(orch.workspace_manager)
        battery = project.design_properties.components.get("battery")
        assert battery is None or battery.catalog_ref is None, "step1 precondition: battery not yet bound"
        print("✓ Step 1 PASS: propulsion bound (motor+propeller+ESC), battery still stub")

        # ── Step 2 ───────────────────────────────────────────────────────
        battery_choose = _say(orch, "ayúdame a elegir", llm)
        suggestions = battery_choose.get("battery_suggestions") or []
        assert suggestions, "step2: battery_suggestions empty"
        names = {s["name"] for s in suggestions}
        assert "lipo_6s_10000mah" in names, f"step2 FAIL: lipo_6s_10000mah not in list: {names}"
        print(f"✓ Step 2 PASS: battery list includes lipo_6s_10000mah ({len(suggestions)} candidates)")

        # ── Step 3 ───────────────────────────────────────────────────────
        target_idx = next(s["idx"] for s in suggestions if s["name"] == "lipo_6s_10000mah")
        pick3 = _say(orch, str(target_idx), llm)
        assert pick3.get("status") == "ok"
        project = orch.state_manager.load_active_project(orch.workspace_manager)
        battery = project.design_properties.components.get("battery")
        assert battery is not None and battery.catalog_ref is not None
        assert battery.catalog_ref.sku == "lipo_6s_10000mah"
        assert project.current_parameters.get("battery_capacity_wh") == 222.0, (
            f"step3 FAIL: battery_capacity_wh={project.current_parameters.get('battery_capacity_wh')}"
        )
        assert project.current_parameters.get("battery_cell_count") == 6
        print(f"✓ Step 3 PASS: catalog_ref={battery.catalog_ref}, "
              f"battery_capacity_wh={project.current_parameters['battery_capacity_wh']}")

        # ── Step 4 ───────────────────────────────────────────────────────
        calc = _say(orch, "calcular", llm)
        assert calc.get("status") == "ok"
        project = orch.state_manager.load_active_project(orch.workspace_manager)
        autonomy = project.latest_results.get("calculations", {}).get("autonomy_min")
        assert autonomy is not None, "step4 FAIL: autonomy_min is None"
        assert autonomy > 5.0, f"step4 FAIL: autonomy_min={autonomy} looks like the 6Wh-class regression"
        print(f"✓ Step 4 PASS: autonomy_min={autonomy} (coherent with 222 Wh, not a 6 Wh collapse)")

        # ── Step 5 ───────────────────────────────────────────────────────
        status = _say(orch, "estado", llm)
        text = render_startup_context(status.get("startup_context") or {})
        assert "[lipo_6s_10000mah]" in text, f"step5 FAIL: estado missing resolved battery line: {text[:500]!r}"
        print("✓ Step 5 PASS: estado shows battery [lipo_6s_10000mah] resolved")

        # ── Step 6: G27 — battery-chemistry-aware adapter, no live bind ────
        adapter = SemanticIntentAdapter()
        result6 = adapter.adapt({
            "action": "iterate",
            "parameters": {
                "variable": "battery_capacity_wh",
                "operacion": "aumentar",
                "valor": "6S 10000mAh",
                "confidence": 0.9,
            },
            "raw_user_input": "aumentar bateria a LiPo 6S 10000mAh",
        })
        assert result6 is not None and result6.value is not None
        wh_value = float(result6.value)
        assert wh_value != 6.0, f"step6 FAIL: G27 regression — got {wh_value} Wh from '6S 10000mAh'"
        assert wh_value == 222.0, f"step6 FAIL: expected ~222 Wh, got {wh_value}"
        print(f"✓ Step 6 PASS: 'LiPo 6S 10000mAh' -> {wh_value} Wh (never 6.0)")

        print("\n=== SUMMARY: 6/6 PASS ===")
        return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    try:
        raise SystemExit(main())
    except AssertionError as e:
        print(f"\n✗ FAIL: {e}", file=sys.stderr)
        raise SystemExit(1)
