# Implementation Contract — CLI Routing Residuals (G17 · G14 · G13)

**Project:** Jarvis  
**Date:** 2026-08-19  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)

**Status:** READY FOR ENGINEER → send to Claude after ratification

**Type:** UX/routing deuda — three bare-input residuals from CLI Polish.

**Checkpoint base:** tag **`checkpoint-erf2`** (`9af0cc9`) + docs commit `89cb03f`  
**Workflow:** Claude implements **Slices 1→3 in order** + tests + report → Engineer → Cursor review → CLI walk → checkpoint only if Engineer asks.

---

## 0. Why this cut

Three inputs work correctly inside the acquisition wizard (DEFINE_MISSING_PARAMETERS mode) but fail at **IDLE** — they fall through to the LLM `analyze` path instead of being routed deterministically:

| ID | Input example | Expected | Actual at IDLE |
|---|---|---|---|
| **G17** | `"4x 2306 1400kv"` | Motors acquisition / intercept | → LLM analyze |
| **G14** | `"10x4.5"` | Propellers acquisition / intercept | → LLM analyze |
| **G13** | `"PVC 400g"` via iterate | Material extracted correctly | No CLI-level integration test |

All three share the same root cause layer: `_interceptable_component_specs` (the IDLE global intercept) lacks the force-inference bypass that `_handle_component_description` (the wizard handler) already has.

**Hard rules:**

- No new architectural subsystems.
- No changes to `ComponentRule` keywords — the fix is in the **orchestrator intercept**, not in the inference registry.
- No LLM involvement in the fix path.
- Preserve all existing test assertions — zero weakened tests.
- The force logic must be **narrow**: only fire when the input matches a specific component shape (motor-shaped, propeller-shaped, material compound), not a broad catch-all.

---

## 1. Root cause analysis

### G17 — Bare motor phrase at IDLE

**Path:** `_handle_user_text_inner` → `_interceptable_component_specs("4x 2306 1400kv")` → `infer_components` → motors `ComponentRule` has keyword `"motor"` only → no match → returns `generic_component` → filtered out at line 365 → empty list → input falls through to `resolve_intent` → `"ambiguous"` → `_handle_analyze` (LLM).

**Wizard fix exists:** `_handle_component_description` lines 2120-2126 — when `"motors" in expected_keys` and all specs are `generic_component`, forces `infer_component_for_key(text, "motors")`. This code never runs at IDLE because the wizard isn't open.

### G14 — Bare propeller size at IDLE

**Path:** Same as G17 — `infer_components("10x4.5")` → propellers `ComponentRule` has keywords `("helice", "hélice", "propeller", "props")` → no match → `generic_component` → filtered → falls to LLM.

**Wizard fix exists:** `_handle_component_description` lines 2127-2137 — force-propellers with `_looks_clearly_propeller_shaped()` guard and `infer_component_for_key(text, "propellers")`.

### G13 — Iterate material compound slug CLI coverage

**Status:** T14 unit test passes (`test_t14_iterate_material_compound_pvc_400g_extracts_and_estimates`). The CLI and the unit test converge at the same `IterateInteractiveSession.answer()`. The audit could not reproduce the originally filed failure. What's missing is a **CLI-level integration test** to lock the full path: orchestrator → iterate session → material extraction → impact estimate.

---

## 2. Slices

### Slice 1 — G17: Bare motor intercept at IDLE

**Scope:** Add a force-motors bypass in `_interceptable_component_specs` (or a helper called from it) that mirrors the wizard-context logic.

**Logic:**

1. After `infer_components` returns only `generic_component` specs at IDLE:
2. If the project has a propulsion architecture block pending motors:
   - Try `infer_component_for_key(text, "motors")`.
   - Accept only if `completeness == "high"` (same guard as wizard path).
   - If accepted, return `[forced_spec]` — the global intercept fires and routes to `_handle_component_description`.
3. The guard `completeness == "high"` ensures only clearly motor-shaped input triggers this (e.g. `"4x 2306 1400kv"` with power/KV data, not `"cuatro motores"`).

**Files changed:**
- `src/jarvis/core/orchestrator.py` — `_interceptable_component_specs` (extend)

**Tests:**
- New test: `test_g17_bare_motor_idle_intercept` — IDLE + bare motor phrase → motors registered (not analyze).
- Regression: existing `test_t9*` wizard tests must remain green.

### Slice 2 — G14: Bare propeller intercept at IDLE

**Scope:** Add a force-propellers bypass in `_interceptable_component_specs` that mirrors the wizard-context logic.

**Logic:**

1. Same gate: `infer_components` returns only `generic_component` at IDLE.
2. If the project has a propulsion architecture block pending propellers:
   - Check `_looks_clearly_propeller_shaped(text)` (existing helper — realistic NxP band, no KV marker).
   - If true, try `infer_component_for_key(text, "propellers")`.
   - Accept if `completeness != "low"`.
3. Disambiguation: if both motors and propellers are pending, the motor check (Slice 1) runs first. Only if motors didn't match, try propellers. This mirrors the wizard-context order.

**Files changed:**
- `src/jarvis/core/orchestrator.py` — `_interceptable_component_specs` (extend, same function as Slice 1)

**Tests:**
- New test: `test_g14_bare_propeller_idle_intercept` — IDLE + `"10x4.5"` → propellers registered (not analyze).
- Regression: `test_t10*` composite guard must remain green.

### Slice 3 — G13: CLI-level integration test for iterate material

**Scope:** Add an integration test that exercises the full orchestrator → iterate session → material extraction → impact estimate path for `"PVC 400g"`.

**No `src/` changes.** This slice is test-only.

**Logic:**

1. Set up a project at IDLE with complete propulsion + `material="aluminio"` (or any initial material).
2. Send `"cambiar material"` or `"iterar material"` → opens iterate wizard.
3. Walk the wizard steps: confirm → `"material"` → `"cambiar material"` → `"PVC 400g"`.
4. Assert: `value == "pvc"`, impact estimate present, no LLM call.

**Files changed:**
- `tests/test_cli_routing_residuals.py` (new) — or append to an existing test file.

**Tests:**
- New test: `test_g13_iterate_material_compound_cli_path` — orchestrator-level material iterate with compound slug.

---

## 3. Scope boundaries

### In scope
- Force-inference bypass at IDLE for motors and propellers (G17, G14).
- CLI integration test for material iterate compound slug (G13).
- Regression coverage for existing wizard-context behavior.

### Out of scope (do not implement)
- Adding new keywords to `ComponentRule` in `aerial.py` — the fix is in the orchestrator intercept, not the domain registry.
- Changing `IntentResolver` patterns.
- Changing `infer_component` / `infer_components` core logic.
- Any `project_continuity.py` changes.
- Any `engineering_readiness.py` changes.
- Frame material intercept at IDLE (not in the G17/G14/G13 set — separate if needed).
- `G11 / G8 / G7` preempt policy (R3 — next in queue, separate IC).

---

## 4. Acceptance criteria

1. `"4x 2306 1400kv"` at IDLE → motors registered deterministically (no LLM).
2. `"10x4.5"` at IDLE → propellers registered deterministically (no LLM).
3. `"PVC 400g"` through iterate wizard via orchestrator → `value == "pvc"`, impact present.
4. All existing tests pass (1851+ baseline).
5. No new `_RefuseLLM` fixtures needed (existing ones reused).
6. Zero weakened assertions.

---

## 5. Decision log

| # | Decision | Rationale |
|---|---|---|
| ★1 | Fix in `_interceptable_component_specs`, not in `ComponentRule.keywords` | Keywords are the domain registry's vocabulary; the orchestrator intercept is the routing layer. Changing keywords risks false positives across all callers. |
| ★2 | Motor check before propeller check (same order as wizard) | Disambiguation: motor-shaped input (with KV) must not be captured by propellers force. |
| ★3 | `completeness == "high"` guard for motors, `completeness != "low"` for propellers | Same guards as the wizard path — proven by existing tests. |
| ★4 | G13 is test-only, no `src/` change | T14 already proved the session handles it; what's missing is the CLI-level lock. |
| ★5 | Require active project with pending architecture block for the component | Don't force-intercept if the user doesn't have a project or the component is already fully defined. |
