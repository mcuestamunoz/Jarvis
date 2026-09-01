#!/usr/bin/env python3
"""CLI probe — Propeller Catalog Bind UX (IC §9.2).

Real wizard turns only — no bind_propeller_from_catalog state patch (unlike
scripts/cli_probe_phase2_lookup_op.py's step 3, which this probe replaces
with a genuine "ayúdame a elegir" turn).

Steps:
  1. Bind emax_rs2205s_2300 via "ayúdame a elegir" -> N (real wizard, G21).
  2. estado -> fallback_operating_point · 10.042 N.
  3. "ayúdame a elegir" (propellers pending) -> list includes hq_5045_bn.
  4. Pick by number -> catalog_ref set.
  5. estado -> fallback_operating_point · 10.042 N (still no battery step —
     Motor OP Voltage Coherence IC MOP-1: an unknown voltage no longer
     auto-matches an exact row, so this stays honest fallback until a real
     battery is bound, unlike the pre-MOP-1 ★7 "exact without voltage"
     behavior this step used to assert).
  6. Spot-check: G21 motor help-choose still works on a fresh project.
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
    from jarvis.core.orchestrator import JarvisOrchestrator

    llm = _RefuseLLM()
    with tempfile.TemporaryDirectory(prefix="jarvis-probe-propbind-") as tmp:
        orch = JarvisOrchestrator(workspace_root=Path(tmp))
        orch.handle({
            "action": "create_project",
            "parameters": {
                "vehicle_type": "dron",
                "objective": "probe propeller catalog bind UX",
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
        motor_suggestions = choose.get("motor_suggestions") or []
        assert motor_suggestions, "step1: motor_suggestions empty"
        idx = next((s["idx"] for s in motor_suggestions if s["name"] == "emax_rs2205s_2300"), None)
        assert idx is not None, "step1: emax_rs2205s_2300 not in wizard suggestions"
        pick = _say(orch, str(idx), llm)
        assert pick.get("status") == "ok"
        print(f"\n✓ Step 1 PASS: bound emax_rs2205s_2300 (wizard idx={idx})")

        # ── Step 2: estado -> fallback resolution ───────────────────────────
        status = _say(orch, "estado", llm)
        ctx = status.get("startup_context") or {}
        rendered = render_startup_context(ctx)
        assert "fallback_operating_point" in rendered, f"step2 FAIL:\n{rendered}"
        assert "10.042" in rendered
        print("✓ Step 2 PASS: estado shows fallback_operating_point / 10.042 N")

        # ── Step 3: real "ayúdame a elegir" for propellers ──────────────────
        prop_choose = _say(orch, "ayúdame a elegir", llm)
        prop_suggestions = prop_choose.get("propeller_suggestions") or []
        assert prop_suggestions, "step3: propeller_suggestions empty"
        prop_names = [s["name"] for s in prop_suggestions]
        assert "hq_5045_bn" in prop_names, f"step3: hq_5045_bn not listed: {prop_names}"
        print(f"✓ Step 3 PASS: propeller list includes hq_5045_bn: {prop_names}")

        # ── Step 4: pick by number ───────────────────────────────────────────
        prop_idx = next(s["idx"] for s in prop_suggestions if s["name"] == "hq_5045_bn")
        prop_pick = _say(orch, str(prop_idx), llm)
        assert prop_pick.get("status") == "ok"
        project = orch.state_manager.load_active_project(orch.workspace_manager)
        propellers = project.design_properties.components.get("propellers")
        assert propellers is not None and propellers.catalog_ref is not None
        assert propellers.catalog_ref.sku == "hq_5045_bn"
        print("✓ Step 4 PASS: propellers.catalog_ref = hq_5045_bn")

        # ── Step 5: estado -> still honest fallback, no battery bound ───────
        # Motor OP Voltage Coherence IC (MOP-1): voltage unknown -> no exact
        # match, even with a real propeller re-resolve firing (★5/★7 still
        # re-fires on propeller pick; it just can't produce "exact" without
        # a known voltage anymore).
        status2 = _say(orch, "estado", llm)
        ctx2 = status2.get("startup_context") or {}
        rendered2 = render_startup_context(ctx2)
        assert "fallback_operating_point" in rendered2, f"step5 FAIL:\n{rendered2}"
        assert "10.042" in rendered2, f"step5 FAIL: expected fallback thrust 10.042 N:\n{rendered2}"
        print("✓ Step 5 PASS: estado shows fallback_operating_point / 10.042 N (still no battery step)")

        # ── Step 6: G21 motor help-choose still works on a fresh project ───
        orch2 = JarvisOrchestrator(workspace_root=Path(tmp) / "second")
        orch2.handle({
            "action": "create_project",
            "parameters": {
                "vehicle_type": "dron", "objective": "spot-check G21", "payload_kg": 1.0,
                "restrictions": "ninguna", "detail_level": "conceptual",
                "structure_mass_factor": 0.5, "safety_factor": 1.2,
            },
        })
        ps2 = orch2.state_manager.load_active_project(orch2.workspace_manager)
        orch2.system_definition_session.start("dron", ps2)
        orch2.system_definition_session.answer("A")
        _say(orch2, "definir propulsion", llm)
        motor_choose2 = _say(orch2, "ayúdame a elegir", llm)
        assert motor_choose2.get("motor_suggestions"), "step6: G21 motor help-choose regressed"
        print("✓ Step 6 PASS: G21 motor help-choose still works on a fresh project")

        print("\n=== SUMMARY: 6/6 PASS ===")
        return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    try:
        raise SystemExit(main())
    except AssertionError as e:
        print(f"\n✗ FAIL: {e}", file=sys.stderr)
        raise SystemExit(1)
