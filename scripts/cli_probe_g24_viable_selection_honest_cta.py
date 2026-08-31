#!/usr/bin/env python3
"""CLI probe — G24C Viable Selection + Honest CTA (contract §3 G24C-5).

Steps:
  1. Bound motor + thrust declared -> "optimiza para aumentar payload".
  2. >=1 catalog-native row in the real (unmodified) exploration.viable —
     investigation §5.1 found 0 on baseline v0.3.1.
  3. Explore message includes the honest CTA pointing at that index.
  4. "aplica la N" (real index from step 2) preserves catalog_ref.
  5. "aplica la mejor" on a fresh exploration still applies #1 (G24-A
     regression, byte-identical to before this IC).
  6. cli_probe_g24_apply_by_index.py still 6/6 (subprocess).
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
        print(f"Jarvis > {msg[:600]}")
    print(f"  [action={result.get('action')} status={result.get('status')}]")
    return result


_BOUND_SKU = "brotherhobby_avenger_2500"


def main() -> int:
    from jarvis.core.catalog_bind import bind_motor_from_catalog
    from jarvis.core.component_writers import set_motor_component
    from jarvis.core.design_explorer import _is_catalog_native_motor_candidate
    from jarvis.core.orchestrator import JarvisOrchestrator
    from jarvis.knowledge.library import default_library

    llm = _RefuseLLM()
    with tempfile.TemporaryDirectory(prefix="jarvis-probe-g24c-") as tmp:
        orch = JarvisOrchestrator(workspace_root=Path(tmp))
        orch.handle({
            "action": "create_project",
            "parameters": {
                "vehicle_type": "dron",
                "objective": "probe g24c viable selection",
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
        result1 = _say(orch, "optimiza para aumentar payload", llm)
        assert result1["status"] == "ok"
        print("✓ Step 1 PASS: explore ran")

        # ── Step 2 ───────────────────────────────────────────────────────
        exploration = orch.state_manager.get_runtime_session().last_exploration_result
        assert exploration is not None
        catalog_indices = [
            i for i, c in enumerate(exploration.viable, start=1)
            if _is_catalog_native_motor_candidate(c)
        ]
        assert catalog_indices, (
            f"step2 FAIL: 0 catalog-native candidates in real .viable ({len(exploration.viable)} total) "
            "-- G24C regression"
        )
        catalog_idx = catalog_indices[0]
        print(f"✓ Step 2 PASS: catalog-native candidate at real index {catalog_idx} "
              f"(baseline v0.3.1 had 0)")

        # ── Step 3 ───────────────────────────────────────────────────────
        message = result1["message"]
        assert f"aplica la {catalog_idx}" in message, f"step3 FAIL: no honest CTA in message: {message!r}"
        print(f"✓ Step 3 PASS: explore message CTA points to index {catalog_idx}")

        # ── Step 4 ───────────────────────────────────────────────────────
        picked_sku = exploration.viable[catalog_idx - 1].components_delta["motors"].catalog_ref.sku
        result4 = _say(orch, f"aplica la {catalog_idx}", llm)
        assert result4["status"] == "ok"
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
        print("✓ Step 5 PASS: 'aplica la mejor' still applies #1 (G24-A regression)")

        # ── Step 6 ───────────────────────────────────────────────────────
        result = subprocess.run(
            [sys.executable, "scripts/cli_probe_g24_apply_by_index.py"],
            capture_output=True, text=True, cwd=str(Path(__file__).resolve().parents[1]),
        )
        assert "6/6 PASS" in result.stdout, (
            f"step6 FAIL: cli_probe_g24_apply_by_index.py did not report 6/6:\n"
            f"{result.stdout[-1000:]}\n{result.stderr[-500:]}"
        )
        print("✓ Step 6 PASS: cli_probe_g24_apply_by_index.py still 6/6")

        print("\n=== SUMMARY: 6/6 PASS ===")
        return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    try:
        raise SystemExit(main())
    except AssertionError as e:
        print(f"\n✗ FAIL: {e}", file=sys.stderr)
        raise SystemExit(1)
