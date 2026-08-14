# Implementation Contract — F-1 (Vehicle-Agnostic Payload Direction)

**Project:** Jarvis  
**Date:** 2026-08-14  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)  

**Status:** READY FOR ENGINEER → send to Claude  

**Type:** Product behavior — direction-aware payload goal resolution (vehicle-agnostic).  

**Closes:** F-1 🔴 — [`.jes/artifacts/cli_findings_post_catalog_bind_v1.md`](cli_findings_post_catalog_bind_v1.md)  

**Checkpoint base:** tag `checkpoint-catalog-impl-b` · commit `202a408`  

**Workflow:** Claude implements + tests + report → Engineer forwards → **Cursor review** → **CLI aggressive probe** → commit only if Engineer asks. **Do not commit or push.**

---

## Execute Implementation Contract F-1 — Vehicle-Agnostic Payload Direction

Read and follow the F-1 design/analysis already established in the project.  
The objective is to close the payload-direction bug at the goal-planning layer, **not** to redesign Jarvis, catalog logic, or vehicle-specific behavior.

---

### CONTEXT

**Current bug:**

```text
"reducir payload"
        ↓
detect_goal()
        ↓
aumentar_payload
```

**Root cause:** `_GOAL_KEYWORDS` contains the bare token `"payload"`, so detection is substring/keyword based and does not encode direction.

This is a systemic goal-resolution issue, but **F-1 must remain deliberately small**: fix payload direction and establish the correct pattern without generalizing every engineering dimension yet.

---

### CORE PRINCIPLE

Goals represent:

```text
engineering dimension + direction
```

For this contract:

```text
payload + increase → aumentar_payload
payload + decrease → reducir_payload
```

The resolution must be **vehicle-agnostic**.

**Do NOT add:**

```python
if vehicle_type == "dron":
    ...
```

The same input must resolve identically for: `dron`, `robot`, `ground`, other supported physical-system types.

---

### SCOPE

#### 1. `goal_planner.py` — direction-aware payload goal detection

**Required outcomes:**

| Input | Expected |
|---|---|
| `aumentar payload` | `aumentar_payload` |
| `aumentar carga útil` | `aumentar_payload` |
| `subir payload` | `aumentar_payload` |
| `subir carga útil` | `aumentar_payload` |
| `reducir payload` | `reducir_payload` |
| `reducir carga útil` | `reducir_payload` |
| `bajar payload` | `reducir_payload` |
| `bajar la carga útil` | `reducir_payload` |
| `transportar menos peso` | `reducir_payload` |

Positive existing intent must remain compatible, including existing phrases that currently resolve to `aumentar_payload`.

**Do NOT rely** on the bare token `"payload"` (or equivalent undirected payload terms) as sufficient evidence for `aumentar_payload`.

The implementation may use the existing normalization layer and existing keyword infrastructure, but direction must be represented explicitly enough that `"reducir payload"` can **never** resolve to `aumentar_payload`.

#### 2. Add new goal: `reducir_payload`

Add it to the existing goal strategy/registry structures using the **same architecture** as existing goals. The plan must remain vehicle-agnostic.

**Minimum strategy set:**

| # | Action | Lever |
|---|---|---|
| 1 | Reducir requisito de carga útil | `payload_kg` |
| 2 | Aligerar estructura si está sobredimensionada | `structure_mass_factor / material` |
| 3 | Reducir actuadores si el payload baja | `motors / motor_count` |

Use the existing strategy representation and prioritization mechanisms. **Do not invent a parallel planning architecture.**

Wording must describe engineering effects, not require drone-specific concepts.

**Engineer lock — `motor_count` is architecture-conditional, not universal:**

> Strategy 3 uses lever `motors / motor_count` because many architectures include actuators — but **`motor_count` is not a property of every vehicle**. Dron/UAV propulsion and robot/rover actuation may have it; other architectures may not.

- Keep strategy 3 in the catalog (Handoff/H4 may reference it when relevant).
- `_prioritize_strategies` must **deprioritize or omit** the motor/actuator strategy when `motor_count` is absent from the `sim_context` snapshot — do not invent `motor_count` on projects without actuators.
- Do not refactor unrelated goals beyond what F-1 tests require.

#### 3. Prioritization

Integrate `reducir_payload` with the existing `sim_context`-based prioritization mechanism where appropriate. If margin is low, prioritizing `payload_kg` reduction is appropriate.

**Do not redesign `_prioritize_strategies` globally.**

#### 4. DSE parity

Implement symmetric DSE support for `goal_key = reducir_payload`. The explorer must explore **lower** payload configurations — not accidentally use the `aumentar_payload` direction.

Use the existing DSE architecture/grid mechanism. Grid must contain values/factors **below** the current payload value. Preserve existing DSE behavior for all other goals.

**Do not redesign DSE or introduce catalog/SKU awareness.**

Also update orchestrator `_GOAL_EXPLORE_DOMAIN` if required: `"reducir_payload": "payload"`.

#### 5. Tests

Focused tests covering detection **independently of vehicle domain**:

| Input | Expected |
|---|---|
| `reducir payload` | `reducir_payload` |
| `reducir carga útil` | `reducir_payload` |
| `bajar la carga útil` | `reducir_payload` |
| `necesito transportar menos peso` | `reducir_payload` |
| `aumentar payload` | `aumentar_payload` |
| `aumentar carga útil` | `aumentar_payload` |
| `mejorar autonomia` | `mejorar_autonomia` |
| `aumentar empuje` | `mejorar_estabilidad` |
| `reducir payload a 2kg` | `None` / iterate path (numeric value) |

For payload detection tests, run the same intent against at least `vehicle_type ∈ {dron, robot, ground}` and prove `goal_key` is identical. Detection functions must be pure text-in/text-out; parametrization documents that no `vehicle_type` branch exists.

**DSE regression coverage:**

- `reducir_payload` → candidates with lower `payload_kg`; does not increase `payload_kg`
- `aumentar_payload` → still produces increasing payload candidates

#### 6. Regression coverage

Run:

- tests directly related to `goal_planner`
- tests related to DSE / goal planning / handoffs
- FN-022 regression tests
- H1–H4 handoff regressions
- full test suite

Existing behavior unchanged except:

```text
"reducir payload"  previously → aumentar_payload (wrong)
                   now        → reducir_payload
```

**Do not weaken existing assertions merely to make tests pass.**

---

### OUT OF SCOPE

Do **NOT** implement:

- F-1b direction handling for autonomy
- F-1b direction handling for thrust
- F-2 propeller semantic mapping
- catalog changes / Catalog Impl C
- Create → BOM
- H5 / C-081
- material ES/EN fix
- Conversation Engine
- general vehicle-specific copy system
- synonym/LLM semantic matching
- **global rewrite of `goal_planner`**
- changes to catalog bind
- changes to `ComponentSpec`

---

### IMPORTANT ARCHITECTURAL CONSTRAINT

Do **not** solve the problem by adding special cases such as:

```python
if "reducir" in text and "payload" in text:
    return "reducir_payload"
```

if this bypasses the existing goal-resolution architecture.

The implementation should establish a **small reusable direction + dimension resolution pattern**, but **only payload** needs to be migrated to that pattern in this contract.

Future dimensions (`autonomía`, `thrust`, `mass`, `safety margin`) — separate contracts.

---

### DSE CONSTRAINT

Do not make DSE catalog-aware. DSE remains continuous/numeric in F-1.

For `reducir_payload`, use existing numeric parameter `payload_kg` and existing DSE mutation/grid mechanisms.

---

### HANDOFF CONSTRAINT

If Goal Plan → HandoffContext → DSE already propagates `goal_key`, **preserve that mechanism**. Do not introduce a new handoff field unless absolutely required.

**Invariant:**

```text
"reducir payload"
        ↓
GoalPlan(goal_key="reducir_payload")
        ↓
HandoffContext
        ↓
"explora opciones"
        ↓
DSE(reducir_payload)
        ↓
lower payload candidates
```

**Do not silently fall back to `aumentar_payload`.**

---

### CLI VALIDATION

After tests pass, perform a small CLI probe using an existing mature dron project.

Verify at least:

```text
reducir payload   → Goal Plan — Reducir carga útil
                    → strategies appropriate to reduction
                    → "explora opciones" explores lower payload

aumentar payload  → Goal Plan — Aumentar carga útil
                    → existing behavior preserved
```

Optional CLI: one non-drone intent-level test (`robot` or `ground`). **Mandatory** at unit-test level.

---

### FILES / SCOPE

**Expected primary implementation areas:**

- `src/jarvis/core/goal_planner.py`
- `src/jarvis/core/design_explorer.py`
- `src/jarvis/core/orchestrator.py` — `_GOAL_EXPLORE_DOMAIN` only if needed
- `src/jarvis/core/intent_resolver.py` — EXPLORE_PATTERNS extension **only if** tests prove necessary
- focused tests

**Do not modify unrelated architecture files.**

---

### DOCUMENTATION

Update `.jes/artifacts/implementation_report_f1_reducir_payload.md` with:

- root cause
- direction-aware payload resolution
- new `reducir_payload` goal
- DSE symmetry
- vehicle-agnostic validation
- tests executed
- CLI result

Do not create a new broad design system unless the existing project protocol requires it.

---

### ACCEPTANCE CRITERIA

F-1 is complete only if **all** are true:

- [ ] `"reducir payload"` resolves to `reducir_payload`
- [ ] `"reducir carga útil"` resolves to `reducir_payload`
- [ ] positive payload phrases still resolve to `aumentar_payload`
- [ ] numeric payload requests remain on iterate/manual path
- [ ] detection is vehicle-agnostic
- [ ] `reducir_payload` has a valid Goal Plan
- [ ] `reducir_payload` has DSE support
- [ ] DSE reduction produces lower payload candidates
- [ ] `aumentar_payload` DSE remains correct
- [ ] H1–H4 behavior remains green
- [ ] FN-022 behavior remains green
- [ ] full suite passes
- [ ] no catalog/H5/BOM/material work introduced
- [ ] `motor_count` strategy is architecture-conditional (not presented as universal)
- [ ] implementation report updated

---

### DELIVERABLE

**Do not commit or push.**

Return a concise implementation report containing:

1. Files changed
2. Root cause
3. Direction-resolution implementation
4. `reducir_payload` strategy
5. DSE changes
6. Tests: focused · regressions · full suite
7. CLI probe result
8. Any findings or remaining risks

**Stop after implementation and verification.**

---

### Queue after F-1

```text
F-1 PASS + Cursor review + CLI aggressive probe
        ↓
UX catálogo batería/hélice
        ↓
Catalog Impl C
        ↓
F-1b / F-2 (separate contracts)
```
