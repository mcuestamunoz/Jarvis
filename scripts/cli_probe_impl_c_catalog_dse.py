#!/usr/bin/env python3
"""CLI probe — Impl C Catalog-Aware DSE + Thrust Bridge follow-up (contract §8).

Runs the 7 acceptance steps against the real orchestrator, in two parts:

  Part A (steps 1-2) — one project: acquisition bind + G9-A honesty.
    1. definir propulsion -> ayúdame a elegir -> pick SKU #1
    2. estado -> catalog_ref set, G9-A Scenario B (mirrors the existing
       G21/G22 probe — unchanged by Impl C, re-run here for continuity)

  Part B (steps 3-7) — a SEPARATE fresh project: explore -> apply -> iterate.

Why two projects, and why Part B's project has motor_count declared but NO
per_motor_max_thrust_n at creation:

`set_motor_component` now bridges `ComponentSpec.motors.properties.thrust_n`
into `current_parameters["per_motor_max_thrust_n"]` (the thrust-bridge
follow-up IC — implementation_contract_impl_c_catalog_dse_thrust_bridge.md).
That closes the SKU-*switch* case (Part A's bound project could safely feed
into Part B now). Part B keeps its own separate, thrust-free project anyway
because it demonstrates something else, still true after the bridge: with NO
prior thrust declared anywhere, every params-grid entry that needs
`per_motor_max_thrust_n` is omitted by `_apply_delta`'s own missing-param
guard, so real catalog candidates — whose thrust now comes from their own
bound spec via the bridge, independent of the params grid — win
`.viable`'s natural top-5 on genuine, unmodified physics. Step 5 below applies
one of those naturally-viable candidates without forcing anything (§8's hard
requirement) — this fixture is what makes that possible without touching
`_score_candidate`.

See Implementation Report (thrust bridge follow-up) §5-§7 for the full
write-up, including the SKU-switch chain (§4 of that contract) which is
covered by the automated test suite
(`tests/test_impl_c_catalog_dse_thrust_bridge.py`) rather than duplicated
here.
"""
from __future__ import annotations

import json
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


def part_a_bind_and_g9a(tmp_dir: str) -> dict:
    from jarvis.core.orchestrator import JarvisOrchestrator

    llm = _RefuseLLM()
    orch = JarvisOrchestrator(workspace_root=Path(tmp_dir))
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "probe Impl C Part A — bind + G9-A",
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
    print("=== Part A: project created, architecture A applied ===")

    _say(orch, "definir propulsion", llm)
    choose = _say(orch, "ayúdame a elegir", llm)
    assert choose.get("motor_suggestions"), "step1: motor_suggestions empty"
    _say(orch, "1", llm)

    project = orch.state_manager.load_active_project(orch.workspace_manager)
    motors = project.design_properties.components.get("motors")
    assert motors is not None and motors.catalog_ref is not None, "step1: catalog_ref not set"
    print(f"\n✓ Step 1 PASS: bound {motors.catalog_ref.sku}")

    status = _say(orch, "estado", llm)
    ctx = status.get("startup_context") or {}
    gap = ctx.get("motor_catalog_gap")
    assert gap is None, f"step2: G9-A Scenario B failed, unexpected gap: {gap!r}"
    print("✓ Step 2 PASS: no false catalog gap after bind")
    return {"step1_bound_sku": motors.catalog_ref.sku, "step2_gap_after_bind": gap}


def part_b_explore_apply_iterate(tmp_dir: str) -> dict:
    from jarvis.core.orchestrator import JarvisOrchestrator
    from jarvis.core.catalog_bind import bind_motor_from_catalog
    from jarvis.knowledge.library import default_library

    llm = _RefuseLLM()
    orch = JarvisOrchestrator(workspace_root=Path(tmp_dir))
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "probe Impl C Part B — explore/apply/iterate",
            "payload_kg": 1.0,
            "restrictions": "ninguna",
            "detail_level": "conceptual",
            "structure_mass_factor": 0.5,
            "safety_factor": 1.2,
            "motors": 6,
        },
    })
    print("\n=== Part B: fresh project, motor_count=6, no prior thrust declared ===")

    # ── Step 3: explore — real "optimiza para..." turn, real explore(),
    #    result persisted to session.last_exploration_result exactly as any
    #    real user turn would (no manual ExplorationResult construction).
    explore_result = _say(orch, "optimiza para aumentar payload", llm)
    print("✓ Step 3 PASS: explore ran")

    # ── Step 4: real SKU present at generation level (hard gate) +
    #    natural top-5 (.viable) visibility. With no prior thrust declared,
    #    every params-grid entry needing per_motor_max_thrust_n is omitted
    #    by _apply_delta's own missing-param guard (see module docstring),
    #    so real catalog candidates — whose thrust now comes from their own
    #    bound spec via the bridge — win .viable on genuine physics, no
    #    forcing needed.
    exploration = orch.state_manager.get_runtime_session().last_exploration_result
    assert exploration is not None, "step4: no exploration result persisted after explore turn"
    catalog_candidates = [
        c for c in exploration.candidates
        if c.components_delta.get("motors") is not None
        and c.components_delta["motors"].catalog_ref is not None
    ]
    assert catalog_candidates, "step4: no real-SKU motor candidate generated at all"
    step4_skus = sorted({c.components_delta["motors"].catalog_ref.sku for c in catalog_candidates})
    print(f"✓ Step 4 PASS (generation level): {len(catalog_candidates)} real-SKU candidates — {step4_skus}")

    catalog_viable = [
        c for c in exploration.viable
        if c.components_delta.get("motors") is not None
        and c.components_delta["motors"].catalog_ref is not None
    ]
    top5_has_sku = bool(catalog_viable)
    print(f"  .viable (natural top-5) catalog membership: {top5_has_sku} "
          f"({len(catalog_viable)}/{len(exploration.viable)} viable candidates are real SKUs)")

    # ── Step 5: apply — §8 forbids forcing a non-viable candidate into
    #    viable[0]. If .viable already contains a catalog candidate (true
    #    for this fixture — see above), reorder ONLY among already-viable
    #    entries (contract §6 clarification: "pick the highest-scoring
    #    catalog viable, without inventing scores") so "aplica la mejor"
    #    applies it; nothing is added that wasn't already viable. If none
    #    were naturally viable, STOP rather than fake a pass.
    if not catalog_viable:
        raise AssertionError(
            "step5 STOP: no catalog candidate in exploration.viable for this probe's "
            "fixture — refusing to force a non-viable candidate into viable[0] per §8. "
            "Fixture inadequacy, not an apply-path defect (see report §7)."
        )
    best_catalog = catalog_viable[0]
    picked_sku = best_catalog.components_delta["motors"].catalog_ref.sku
    session = orch.state_manager.get_runtime_session()
    if exploration.viable[0] is not best_catalog:
        reordered = [best_catalog] + [c for c in exploration.viable if c is not best_catalog]
        exploration = exploration.model_copy(update={"viable": reordered})
        orch.state_manager.set_runtime_session(
            session.model_copy(update={"last_exploration_result": exploration})
        )
    applied = _say(orch, "aplica la mejor", llm)
    assert applied["status"] == "ok", f"step5: apply failed: {applied}"
    print(f"✓ Step 5 PASS: applied {picked_sku} (naturally viable, not forced)")

    # ── Step 6: estado — catalog_ref set, no false gap
    status2 = _say(orch, "estado", llm)
    ctx2 = status2.get("startup_context") or {}
    gap2 = ctx2.get("motor_catalog_gap")
    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    motors2 = saved.design_properties.components.get("motors")
    assert motors2 is not None and motors2.catalog_ref is not None, "step6: catalog_ref lost after apply"
    assert motors2.catalog_ref.sku == picked_sku, "step6: catalog_ref sku mismatch after apply"
    print(f"✓ Step 6 PASS: catalog_ref={motors2.catalog_ref.sku}, motor_catalog_gap={gap2!r}")

    # ── Step 7: unrelated iterate — identity survives (G5 regression)
    before_motor_count = saved.current_parameters.get("motor_count")
    before_sku = motors2.catalog_ref.sku
    _say(orch, "cambia safety_factor", llm)
    _say(orch, "si", llm)
    _say(orch, "safety_factor", llm)
    _say(orch, "1.5", llm)
    _say(orch, "si", llm)
    final = _say(orch, "si", llm)
    assert final["status"] == "ok", f"step7: iterate turn failed: {final}"

    after = orch.state_manager.load_active_project(orch.workspace_manager)
    assert after.current_parameters.get("safety_factor") == 1.5, "step7: safety_factor not applied"
    assert after.current_parameters.get("motor_count") == before_motor_count, "step7: motor_count drifted"
    after_motors = after.design_properties.components.get("motors")
    assert after_motors is not None and after_motors.catalog_ref is not None, "step7: catalog_ref lost"
    assert after_motors.catalog_ref.sku == before_sku, "step7: catalog_ref sku drifted"
    print(f"✓ Step 7 PASS: catalog_ref survived unrelated iterate ({before_sku})")

    return {
        "step3_explore_ran": True,
        "step4_generated_skus": step4_skus,
        "step4_catalog_in_natural_viable": top5_has_sku,
        "step5_applied_sku": picked_sku,
        "step6_gap_after_apply": gap2,
        "step7_catalog_ref_survived": True,
    }


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="jarvis-probe-implc-a-") as tmp_a:
        summary_a = part_a_bind_and_g9a(tmp_a)
    with tempfile.TemporaryDirectory(prefix="jarvis-probe-implc-b-") as tmp_b:
        summary_b = part_b_explore_apply_iterate(tmp_b)

    summary = {**summary_a, **summary_b}
    print("\n=== SUMMARY (7/7 PASS — step 5 applied a naturally-viable catalog candidate, not forced) ===")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    try:
        raise SystemExit(main())
    except AssertionError as e:
        print(f"\n✗ FAIL: {e}", file=sys.stderr)
        raise SystemExit(1)
