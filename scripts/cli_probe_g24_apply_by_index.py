#!/usr/bin/env python3
"""CLI probe — G24-A DSE Apply By Index (contract §3 G24-5).

Steps:
  1. Create project + bind a real catalog motor (thrust already declared —
     the G24 precondition).
  2. "optimiza para aumentar payload" -> real exploration persisted.
  3. G24-TF: place a real, already-generated catalog candidate at viable
     index 5 (1-based), abstract candidate stays at #1 — no scorer touched.
  4. "aplica la 5" -> catalog_ref preserved, matches the applied SKU.
  5. Fresh explore on the same project -> "aplica la mejor" -> applies #1;
     if abstract/params-only, catalog_ref clears (G5, unchanged — expected
     regression, not a bug in this IC).
  6. "aplica la 99" -> error, no crash, no state mutation.

Real handle_user_text turns throughout (no LLM) — same discipline as the
Closure/Battery/P2-1 probes.
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


_BOUND_SKU = "brotherhobby_avenger_2500"


def main() -> int:
    from jarvis.core.catalog_bind import bind_motor_from_catalog
    from jarvis.core.component_writers import set_motor_component
    from jarvis.core.orchestrator import JarvisOrchestrator
    from jarvis.knowledge.library import default_library

    llm = _RefuseLLM()
    with tempfile.TemporaryDirectory(prefix="jarvis-probe-g24-") as tmp:
        orch = JarvisOrchestrator(workspace_root=Path(tmp))
        orch.handle({
            "action": "create_project",
            "parameters": {
                "vehicle_type": "dron",
                "objective": "probe g24 apply by index",
                "payload_kg": 1.0,
                "restrictions": "no",
                "detail_level": "conceptual",
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
        ps = ps.model_copy(update={
            "current_parameters": {
                **ps.current_parameters,
                "motor_count": 6, "propeller_diameter_in": 5.0,
                "per_motor_max_thrust_n": bound_motor.thrust_n,
            },
        })
        orch.workspace_manager.save_state(ps)
        print(f"=== Setup: motor bound to {_BOUND_SKU}, thrust declared ===")

        # ── Step 1 ───────────────────────────────────────────────────────
        ps = orch.state_manager.load_active_project(orch.workspace_manager)
        assert ps.design_properties.components["motors"].catalog_ref is not None
        print(f"✓ Step 1 PASS: catalog_ref={ps.design_properties.components['motors'].catalog_ref}")

        # ── Step 2 ───────────────────────────────────────────────────────
        exploration = orch.design_explorer.explore(ps, "aumentar_payload")
        assert exploration.viable, "step2 FAIL: no viable candidates"
        print(f"✓ Step 2 PASS: exploration has {len(exploration.viable)} viable candidates")

        # ── Step 3: G24-TF ───────────────────────────────────────────────
        catalog_candidates = [
            c for c in exploration.candidates
            if c.components_delta.get("motors") is not None
            and c.components_delta["motors"].catalog_ref is not None
        ]
        assert catalog_candidates, "step3 FAIL: no catalog candidate generated"
        picked = catalog_candidates[0]
        picked_sku = picked.components_delta["motors"].catalog_ref.sku
        abstract_viable = [
            c for c in exploration.viable
            if not (c.components_delta.get("motors") is not None and c.components_delta["motors"].catalog_ref is not None)
        ]
        assert abstract_viable, "step3 FAIL: no abstract candidate to keep at #1"
        new_viable = [abstract_viable[0]] + [c for c in exploration.viable if c is not abstract_viable[0]][:3] + [picked]
        catalog_index = len(new_viable)
        assert catalog_index > 1, "step3 FAIL: catalog candidate landed at #1, test doesn't prove selection"
        exploration_patched = exploration.model_copy(update={"viable": new_viable})
        session = orch.state_manager.get_runtime_session()
        orch.state_manager.set_runtime_session(
            session.model_copy(update={"last_exploration_result": exploration_patched})
        )
        print(f"✓ Step 3 PASS: catalog candidate ({picked_sku}) placed at index {catalog_index}, "
              f"viable[0] is abstract, no scorer called")

        # ── Step 4 ───────────────────────────────────────────────────────
        result4 = _say(orch, f"aplica la {catalog_index}", llm)
        assert result4["status"] == "ok", f"step4 FAIL: {result4}"
        assert result4["applied_index"] == catalog_index
        saved = orch.state_manager.load_active_project(orch.workspace_manager)
        motors = saved.design_properties.components["motors"]
        assert motors.catalog_ref is not None and motors.catalog_ref.sku == picked_sku, (
            f"step4 FAIL: catalog_ref={motors.catalog_ref}"
        )
        print(f"✓ Step 4 PASS: catalog_ref preserved, sku={motors.catalog_ref.sku}")

        # ── Step 5 ───────────────────────────────────────────────────────
        result5a = _say(orch, "optimiza para aumentar payload", llm)
        assert result5a["status"] == "ok"
        result5b = _say(orch, "aplica la mejor", llm)
        assert result5b["status"] == "ok"
        assert result5b["applied_index"] == 1
        saved5 = orch.state_manager.load_active_project(orch.workspace_manager)
        motors5 = saved5.design_properties.components["motors"]
        note = "catalog_ref cleared (G5, expected/unchanged)" if motors5.catalog_ref is None else "catalog_ref survived (candidate #1 happened to be catalog-native)"
        print(f"✓ Step 5 PASS: 'aplica la mejor' applied #1 — {note}")

        # ── Step 6 ───────────────────────────────────────────────────────
        before6 = orch.state_manager.load_active_project(orch.workspace_manager)
        result6 = _say(orch, "aplica la 99", llm)
        assert result6["status"] == "error", f"step6 FAIL: {result6}"
        after6 = orch.state_manager.load_active_project(orch.workspace_manager)
        assert after6.current_parameters == before6.current_parameters, "step6 FAIL: state mutated"
        print("✓ Step 6 PASS: out-of-range index rejected, no state mutation")

        print("\n=== SUMMARY: 6/6 PASS ===")
        return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    try:
        raise SystemExit(main())
    except AssertionError as e:
        print(f"\n✗ FAIL: {e}", file=sys.stderr)
        raise SystemExit(1)
