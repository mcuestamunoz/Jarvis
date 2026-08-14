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
| F-1 | 🔴 | **Bug — prioritario** | `reducir payload` → Goal Plan de **aumentar** carga útil |
| F-2 | 🟡 | Known gap | `aumentar diámetro de las hélices` no llega a `propeller_diameter_in` / iterate limpio |
| F-3 | 🟡 | Expected (pre-UX) | `configurar hélices` → `propeller_rpm`, no pick SKU de hélice |
| F-4 | 🟢 | **Demostrado** | Motor catalog pick → identidad + masa → cálculo |
| F-5 | 🟡 | **Pendiente de verificación** | Divergencia numérica post-DSE → limpieza de `catalog_ref` |
| F-6 | 🟢 | **Demostrado** | Gap de catálogo honesto cuando no hay motor adecuado |

**Next queue (Engineer):**

```text
checkpoint-catalog-impl-b
        ↓
F-1 hardening (contrato pequeño)
        ↓
UX catálogo batería/hélice
        ↓
Impl C — DSE por SKUs
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

Small Implementation Contract: **F-1 hardening** with regression tests for both directions and Goal Plan smoke tests.

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

- **Do not** fix by stuffing synonyms into `match_plan_lever` (H4). That would reintroduce global keyword routing and weaken the "only preseed levers from active plan" property.
- Requires a separate authority decision for semantic intent → variable (outside H4 scope).

### Next step

Defer until after F-1. Design semantic resolution layer or explicit propeller configure entry point — not part of Impl C by default.

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

1. **F-1** → next Implementation Contract (before catalog UX or Impl C).
2. **F-5** → 🟡 until thrust-divergence CLI probe or state inspection.
3. **F-2** → no H4 synonym hack; design semantic authority separately.
4. **F-3** → catalog pick UX for battery/propeller is its own stage, not Impl C.
5. **No catalog code changes** until F-1 contract is approved and delivered.
