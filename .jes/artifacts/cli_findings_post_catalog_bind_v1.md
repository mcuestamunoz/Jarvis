# CLI Findings — Post Catalog Bind v1 (Impl B)

**Date:** 2026-08-14  
**Checkpoint:** `checkpoint-catalog-impl-b` (after this artifact)  
**Evidence:** Engineer CLI session, project `levantar-4kg-con-atonomia-de-70min` (`1f7e6e8d1a70`)  
**Review base:** [`.jes/artifacts/implementation_review_catalog_bind_v1.md`](implementation_review_catalog_bind_v1.md) — **PASS**

> Snapshot of real-user behavior **immediately after Impl B**. Purpose: distinguish bugs, known limits, expected behavior, and deliberately deferred work before the next contracts (F-1 hardening, catalog UX, Impl C).

---

## Summary

| ID | Severity | Status | One-line |
|---|---|---|---|
| F-1 | 🔴→🟢 | **Fixed** | `reducir payload` → Plan Reducir + DSE ↓ |
| **G5** | 🔴 | **Investigar** | DSE 675 N → iterate 80 N; dual-truth params vs ComponentSpec |
| G3 | 🟡 | Known gap | `optimiza payload` vs handoff `reducir_payload` |
| F-2 | 🟡 | Known gap | Diámetro hélices → iterate |
| F-3 | 🟡 | Expected | `configurar hélices` → RPM only |
| F-4 | 🟢 | Demostrado | Motor catalog pick + masa |
| F-5 | 🟡 | Pendiente verificación | Divergencia `catalog_ref` post-DSE |
| F-6 | 🟢 | Demostrado | Gap catálogo honesto |

**Next queue (Engineer 2026-08-14):**

```text
checkpoint-f1-reducir-payload ✅
        ↓
G5 investigation
        ↓
G3 handoff explore
        ↓
G1/G2 + H5 design
        ↓
UX catálogo → Impl C → BOM
```

**Explicitly out of scope here:** Impl C, material ES/EN (3A), H5/C-081, BOM/Continuity SKU labeling.

---

## F-1 🔴 — `reducir payload` invierte el objetivo

**Severity:** 🔴 prioritario  
**Category:** Bug — intent/goal interpretation  
**Depends on catalog:** No

### Observed

```text
User > reducir payload

Jarvis > Plan estratégico — Aumentar carga útil:
  1. Aumentar empuje disponible …
```

### Expected

```text
reducir payload / reducir carga útil
        ↓
objetivo: reducir payload (goal plan coherente)

aumentar payload / aumentar carga útil
        ↓
objetivo: aumentar payload
```

### Impact

Direct semantic inversion of user intent. Dangerous because the system proposes levers and DSE paths for the **opposite** engineering direction. Independent of Catalog v1.

### Notes

- Must not break existing Goal Plans for `aumentar empuje`, `maximizar autonomía`, `mejorar estabilidad`, etc.
- Fix belongs in goal/intent resolution — **not** in H4 `match_plan_lever` or catalog bind.

### Next step

~~F-1 hardening contract~~ → **DONE** (`checkpoint-f1-reducir-payload`). Next: **G5 investigation**.

---

## G5 🔴 — DSE params-only → iterate revierte empuje (675 N → 80 N)

**Severity:** 🔴 investigar (bloquea H5/G1)  
**Category:** State dual-truth — `current_parameters` vs `ComponentSpec`  
**Depends on catalog:** Partially (`catalog_ref` cleared on thrust diverge; revert is separate)

### Observed (CLI 2026-08-14, proyecto `1f7e6e8d1a70`)

```text
DSE estabilidad apply (iter_010):
  motor_count=10, per_motor_max_thrust_n=67.5 → empuje_disponible=675 N

iterate safety_factor=1.4 (iter_011):
  motor_count=4,  per_motor_max_thrust_n=20.0 → empuje_disponible=80 N
```

Sin explicación en UI. `components.motors` sigue en 4×20 N; `catalog_ref=null`.

### Hypothesis

Params-only DSE escribe `current_parameters`; `ComponentSpec` queda stale. Iterate recalcula y **pisa** params con verdad del componente.

### Impact

Secuencias DSE → iterate no son confiables; invalida confianza en exploración antes de objetivo compuesto (H5).

### Next step

Investigation contract: [`.jes/artifacts/investigation_contract_g5_dse_iterate_dual_truth.md`](investigation_contract_g5_dse_iterate_dual_truth.md)

---

## G3 🟡 — Explore explícito vs handoff activo

**Severity:** 🟡 known gap  
**Category:** Continuity / handoff (H1 partial)

### Observed

```text
Plan reducir_payload + "explora opciones"     → minimizar carga útil ✅
Plan reducir_payload + "optimiza payload"   → maximizar carga útil ❌
```

H1 solo bind en bare `"explora opciones"`. Explore explícito re-deriva goal del texto.

### Next step

Micro-contrato post-G5: prefer `handoff.goal_key` when active for explore verbs + payload dimension.

---

## F-2 🟡 — Diámetro de hélices no llega a iterate

**Severity:** 🟡 known gap  
**Category:** Routing / semantic resolution (not H4 regression)  
**Depends on catalog:** No

### Observed

```text
User > aumentar diámetro de las hélices
→ confirmación OK
→ wizard: ¿Qué quieres modificar?
→ user: componentes → optimizar estructura  (conversación mezclada)
→ user: hélices
→ Error: No reconozco 'hélices' como variable modificable
```

### Expected (future)

User phrase maps to `propeller_diameter_in` (or a dedicated propeller configure flow) without breaking the iterate wizard.

### Impact

Iterate UX friction when user follows Goal Plan lever wording (`propeller_diameter_in / propeller_rpm`) with natural language.

### Notes

- **Do not** fix by stuffing synonyms into `match_plan_lever` (H4).
- Requires a separate authority decision for semantic intent → variable (outside H4 scope).

### Next step

Defer until post-G5. Design semantic resolution layer or explicit propeller configure entry point.

---

## F-3 🟡 — `configurar hélices` modifica RPM, no hélice física

**Severity:** 🟡 expected (pre catalog UX)  
**Category:** Known limitation — between Impl B and catalog pick UX  
**Depends on catalog:** Partially (propeller catalog exists in library; no pick UX)

### Observed

```text
User > configurar hélices
→ ¿Cuál es el RPM del motor?
→ propeller_rpm=8000

Propeller description remains: "10x4,5" (free text)
No catalog_ref on propellers
```

### Expected (future)

Catalog-assisted propeller pick → `bind_propeller_from_catalog` → SKU identity (mass/thrust compatibility deferred per design).

### Impact

User cannot select a physical propeller SKU through CLI today. `propeller_rpm` change does not upgrade the propeller from description to bound component.

### Notes

- **Not an Impl B bug.** Helpers exist (`bind_propeller_from_catalog`); no UX entry point wired.
- Intermediate stage planned: **UX catálogo batería/hélice** before Impl C.

### Next step

Catalog pick UX for battery + propeller (Engineer queue item after F-1).

---

## F-4 🟢 — Motor catalog pick → identidad + masa → cálculo

**Severity:** 🟢 demonstrated  
**Category:** Impl B success path  
**Depends on catalog:** Yes (Bind)

### Observed

```text
DEFINE_MISSING motor pick → 2 → t-motor_antigravity_mn4006_380
Motor elegido: t-motor_antigravity_mn4006_380 (~500W, 20.0N). Sistema recalculado.
masa_total=7.04 kg, empuje_disponible=80.0 N
Continuity: Cambio: motor → t-motor_antigravity_mn4006_380 (~500W)
```

### Validates

- Shared `bind_motor_from_catalog` on DEFINE_MISSING path
- SKU identity persisted (Continuity thread shows SKU name)
- Mass enters physics (total mass reflects bound motor)
- Calculation recalc after pick

### Notes

Full state inspection (`catalog_ref` in `state.json`) not shown in CLI transcript; covered by automated tests (`test_catalog_bind_v1.py`). BOM/Continuity formal SKU labeling still deferred (accepted).

---

## F-5 🟡 — Divergencia post-DSE → limpieza de `catalog_ref`

**Severity:** 🟡 **pendiente de verificación**  
**Category:** Bind invalidation rule — needs targeted probe  
**Depends on catalog:** Yes (Bind)

### Observed (session)

```text
Motor bound: t-motor_antigravity_mn4006_380 (500W, 20N)
DSE apply (maximizar autonomía):
  motor_power_w: 500 → 375
  battery_capacity_wh: 111 → 222

Later Continuity:
  "no tengo un motor en el catálogo que cubra ese espacio"
```

### Why not marked 🟢

Invalidation compares **`thrust_n` vs `per_motor_max_thrust_n`**, not `motor_power_w`. The DSE apply above changed power and battery Wh; thrust may still match the SKU (20 N). The Continuity message is likely the **gap matcher** (requirement vs library), not proof that `catalog_ref` was cleared.

### Required verification

```text
1) Pick catalog motor (catalog_ref set)
2) Force divergence on compared field:
   - DSE/iterate that changes per_motor_max_thrust_n away from SKU thrust_n, OR
   - inspect state.json before/after
3) Confirm catalog_ref is None and motor_mass_kg reverts (unbound fallback)
```

### Notes

- Rule implemented and unit-tested (`test_dse_apply_diverging_thrust_clears_motor_catalog_ref`).
- CLI session did **not** demonstrate the thrust-divergence path end-to-end.

### Next step

Optional mini CLI probe (8 lines) before or after F-1; not blocking checkpoint.

---

## F-6 🟢 — Gap de catálogo honesto

**Severity:** 🟢 demonstrated  
**Category:** Expected architecture behavior  
**Depends on catalog:** Yes (library + gap matcher)

### Observed

```text
Catálogo: Necesitas empuje ≥ 19.3 N/motor, ~380KV, hélice ~10";
          no tengo un motor en el catálogo que cubra ese espacio
```

(after DSE pushed design toward higher per-motor thrust requirement)

### Validates

- Jarvis does **not** invent a motor when the library cannot satisfy stated requirements
- Gap is declared explicitly to the user

### Notes

- Stale-gap UX: message may not reflect a motor **already bound** earlier in the session (Continuity gap matcher vs bound `catalog_ref` — related to deferred BOM/Continuity SKU labeling).
- Epistemology warning in same Continuity block is valuable and should be preserved:

  > `Modelo energético simplificado: autonomía ≈ (Wh / W) × 60 — sin curva de descarga ni C-rating.`

---

## Additional CLI noise (not F-1…F-6)

Recorded for context; **do not** treat as Impl B regressions:

| Observation | Tracking |
|---|---|
| `plastico` / material frame rejected; `aluminio 450g` worked | Material ES/EN alias bug (Design 3A) — separate micro-fix |
| `definir bateria` → one turn back to propeller prompt | Acquisition routing noise — investigate separately if recurring |
| `estadoi` typo → analyze/LLM path | User input typo — no action |
| `simulation=PASS` + `RESTRICCIÓN INCUMPLIDA` (autonomía) | Known dual-status — vigilance item for future requirement model, not Impl B |

---

## Relationship to Impl B contract

| Contract gate | CLI evidence |
|---|---|
| SKU identity on pick | F-4 🟢 |
| Mass causality (SKU-bound) | F-4 🟢 |
| Diverge clears `catalog_ref` | F-5 🟡 (tests yes; CLI thrust path not shown) |
| Unbound unchanged | No regression observed |
| No Impl C / no battery-prop UX | F-3 🟡 confirms gap is expected |

---

## Engineer decisions locked in this artifact

1. ~~**F-1** → next Implementation Contract~~ → **DONE** (`checkpoint-f1-reducir-payload`).
2. **G5** → investigation contract **before** H5/G1 design.
3. **F-5** → 🟡 until thrust-divergence CLI probe or state inspection.
4. **G3** → post-G5 handoff explore bind extension.
5. **G1/G2/H5** → design only; Impl C **after** objective layer.
6. **No catalog Impl C** until G5 closed (+ fix if needed).

---

## Queue (updated 2026-08-14)

```text
checkpoint-f1-reducir-payload ✅
        ↓
G5 investigation (+ fix contract)
        ↓
G3 handoff explore
        ↓
G1/G2 + H5 design
        ↓
UX catálogo → Impl C → BOM
```
