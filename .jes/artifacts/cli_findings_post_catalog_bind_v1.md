# CLI Findings — Post Catalog Bind v1 → F-1 / G5 / G3 / SYS-MAP-004

**Date:** 2026-08-15 (updated after G3 CLI PASS + G10 register)  
**Checkpoints:** `checkpoint-catalog-impl-b` · `checkpoint-f1-reducir-payload` · `checkpoint-g5-dse-component-sync` · **`checkpoint-g3`**  
**Evidence:** Engineer CLI (G3 probe + Continuity/materials) · SYS-MAP-004 audit  

> Living register of CLI findings. Distinguishes bugs, known limits, expected behavior, and deferred work. **Do not confuse a finding with a regression** after later checkpoints.

---

## Summary

| ID | Severity | Status | One-line |
|---|---|---|---|
| F-1 | 🔴→🟢 | **Fixed** | `reducir payload` → Plan Reducir + DSE ↓ |
| G5 | 🔴→🟢 | **Fixed** (+ CLI PASS) | Dual-truth DSE→iterate cerrado |
| **G3** | 🟡→🟢 | **Fixed + CLI PASS** | Active-goal continuity explore; override + consumed handoff |
| **G8** | 🟡 | **Registered — no implement** | DEFINE_MISSING UX-C swallows engineering/explore intent (map overclaim C-040) |
| **G9** | 🟡 | **Registered — no implement** | Continuity catalog-gap blind to declared thrust / `catalog_ref` |
| **G10** | 🟡 | **Registered — no implement** | Material catalog ↔ frame acquisition misalignment |
| **G6** | 🟡 | **Registered — no implement** | Mass breakdown must be deterministic / auditable (not LLM-invented) |
| **G7** | 🟡 | **Registered — no implement** | Iterate wizard: `operation=None` / mid-flow intent break |
| F-2 | 🟡 | Known gap | Diámetro hélices → iterate |
| F-3 | 🟡 | Expected | `configurar hélices` → RPM only |
| F-4 | 🟢 | Demostrado | Motor catalog pick + masa |
| F-5 | 🟡 | Pendiente verificación | Divergencia `catalog_ref` post-DSE |
| F-6 | 🟢→🟡 | Demostrado + **G9 elevates stale-gap** | Gap catálogo honesto; honesty vs bound SKU = G9 |

**Next queue (Engineer 2026-08-15):**

```text
✅ G3 CLI PASS → checkpoint-g3
        ↓
📝 G10 registered (materials / frame) — study before Impl C
        ↓
G10 design/contract  ⟷  R3 DEFINE_MISSING preempt (Engineer chooses order)
        ↓
R4 FN G8 (only after R3) · G9 aparte
        ↓
G1/G2 + H5 · UX catálogo · Impl C
```

**Explicitly out of scope for near-term implementation:** G6 · G7 · G8 (until R3) · G9 · G10 · Impl C · material ES/EN (3A) · H5/C-081 · BOM/Continuity SKU labeling. Do **not** port `_should_preempt_iterate_wizard` verbatim into DEFINE_MISSING.

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

## G5 🟢 — DSE params-only → iterate revierte empuje (675 N → 80 N)

**Severity:** was 🔴 · **Status:** **Fixed** (Option A)  
**Category:** State dual-truth — `current_parameters` vs `ComponentSpec`  

### Fix

`component_sync.sync_motors_component_from_params` wired after `invalidate_diverged_catalog_refs` in `_handle_apply_exploration`. Component stays current; `resolve_propulsion_parameters` no longer clobbers DSE elevations.  
Review: [implementation_review_g5_dse_component_sync.md](implementation_review_g5_dse_component_sync.md)

### Observed (historical)

```text
DSE estabilidad apply (iter_010): 10×67.5 → 675 N
iterate safety_factor (iter_011): 4×20 → 80 N   ← cerrado
```

---

## G3 🟡 — Explore explícito vs handoff activo

**Severity:** was 🟡 · **Status:** **Fixed** (PASS WITH NOTES)  
**Category:** Continuity / handoff (H1 partial)  
**Design:** [design_g3_active_goal_continuity.md](design_g3_active_goal_continuity.md) — ★1–★4 locked  
**Review:** [implementation_review_g3_active_goal_continuity.md](implementation_review_g3_active_goal_continuity.md)

### Observed

```text
Plan reducir_payload + "explora opciones"     → minimizar carga útil ✅
Plan reducir_payload + "optimiza payload"   → maximizar carga útil ❌
```

H1 solo bind en bare `"explora opciones"`. Explore explícito re-deriva goal del texto.

### Design direction (not implemented)

```text
explicit new goal  >  active goal  >  inferred/default goal
```

`"optimiza payload"` (undirected) should inherit active `reducir_payload`;  
`"ahora aumenta el payload"` must override. See design ★1–★4.

### Next step

~~IC → Claude~~ → **DONE**. Optional live CLI probe, then checkpoint when Engineer asks.

---

## G6 🟡 — Mass breakdown must be deterministic / auditable

**Severity:** 🟡 registered — **do not implement yet**  
**Category:** Explainability / Continuity — derived magnitudes  
**Depends on catalog:** Partially (Bind made mass contributions real; explanation layer did not catch up)

### Observed (CLI 2026-08-14, post-G5)

```text
masa_total = 5.783 kg

Actual (state):
  payload_kg           2.000
  structure_override   0.450
  battery_mass_kg      3.333   ← 500 Wh × 150 Wh/kg heuristic (unbound)
  motor_mass_kg        (absent → 0; catalog_ref cleared after DSE thrust diverge)

User: "De donde vienen los 5,783kg de masa_total"
LLM analyze: invents "peso adicional no especificado ~3.783 kg"  ❌
```

Physics was **correct**. Conversational audit trail was **not**.

### Principle (Engineer)

> **Toda magnitud derivada importante debe poder explicarse a partir de contribuciones deterministas del estado.**  
> El LLM interpreta; **no** es autoridad sobre hechos físicos.

### Why not now

- Not a handoff bug (≠ G3).  
- Not a Bind/calc bug.  
- Belongs near Continuity / G1–H5 explainability — separate contract later.  
- Recording prevents mistaking this for a mass regression after catalog.

### Next step

Document only. Candidate future: deterministic mass-breakdown block in Continuity / analyze context (0 LLM).

---

## G7 🟡 — Iterate wizard: `operation=None` / mid-flow intent break

**Severity:** 🟡 registered — **do not implement yet**  
**Category:** Iterate UX / wizard state machine  
**Depends on catalog:** No

### Observed (CLI 2026-08-14)

```text
"quiero reducir la carga útil a 0 kg"  → iterate starts
"no cambiar tamaño"                    → aborts / reinterprets as objective "tamano"
"-2kg"                                 → strategy="-2kg", operation=None, value=None
confirm                                → "Error: La iteración no tiene operación definida"
                                       → sticky loop (sí/s/confirmo all fail)
```

### Why separate

```text
G3 ≠ operation=None   (goal continuity / explore)
G5 ≠ operation=None   (component sync)
G7 = wizard state machine / slot completion
```

Do **not** fold into G3 scope.

### Next step

Document only. Future micro-contract: infer `reducir` from `-2kg` delta; do not reach confirm with `operation=None`; mid-flow restriction phrases should not replace the active iterate objective.

---

## G8 🟡 — DEFINE_MISSING swallows engineering / explore intent

**Severity:** 🟡 registered — **do not implement yet** (needs R3 design first)  
**Category:** Routing / session mode — mid-wizard authority  
**Depends on catalog:** No  
**Source:** SYS-MAP-004 audit + Cursor review PASS WITH NOTES (2026-08-14/15)

### Observed (CLI + audit probes P3/P6)

```text
DEFINE_MISSING open on battery (MISSING_COMPONENT_DEFINITION)
User > reducir payload
        ↓
IntentResolver → "iterate"
goal_planner   → reducir_payload   ✅ (F-1 OK)
        ↓
UX-C intercept (_handle_component_description) — unconditional
        ↓
"Vamos a definir la batería…"
        ✋ C-040 / Goal Plan never reached

Same swallow for: "explora opciones", "optimiza payload"
```

### Root cause (confirmed)

Checkpoint 10 (`DEFINE_MISSING_PARAMETERS`) returns before checkpoint 18 (C-040).  
`ITERATE_INTERACTIVE` has C-052 preempt; **DEFINE_MISSING has no analogue**.  
Map presented C-040 as if globally reachable → **B map overclaim** (code gate already comments "Runs only in IDLE").

### Why not implement now

- Do **not** port `_should_preempt_iterate_wizard` verbatim — DEFINE_MISSING carries `collected_params`.
- Sequence: **R3 design** (preempt policy) → **R4 FN** only after Engineer lock.
- Workaround for G3 CLI: `cancelar` → IDLE → then engineering/explore phrases.

### Separate from

```text
G3 ≠ G8   (explore continuity once IDLE; G8 blocks reaching it mid-wizard)
G9 ≠ G8   (catalog_ref honesty in Continuity)
FN-021 ≠ G8  (FN-021 = post-completion clear; G8 = mid-wizard turn)
```

### Next step

Document only until R3. Map caveat: R1 (C-040 / ACQUISITION_MAP).

---

## G9 🟡 — Continuity catalog-gap blind to bound `catalog_ref`

**Severity:** 🟡 registered — **do not implement yet**  
**Category:** Continuity / catalog honesty  
**Depends on catalog:** Yes (Bind + gap matcher)  
**Source:** SYS-MAP-004 §4.5 / probe P7 — elevates F-6 "Stale-gap UX" from suspected → confirmed-with-repro

### Observed

```text
motors.catalog_ref = sunnysky_r2305_2500   (bound, untouched)
physical requirements grow past that SKU's coverage
        ↓
build_startup_context recomputes catalog_matches from thrust/KV/prop
        ↓
never reads catalog_ref
        ↓
"no tengo un motor en el catálogo que cubra ese espacio"
```

### Root cause

`orchestrator.build_startup_context` catalog-gap block (~`:2747-2794`) — no `catalog_ref` read.  
Not Continuity authority violation (still 0 LLM); content honesty gap.

### Why separate from G8 / C-081

- Different symbols and call path than DEFINE_MISSING UX-C.
- Not C-081 (margin unread in PASS) — do not force-fit.
- Data-contract question: bound-but-underspec'd SKU → gap, warning, or silence?

### Next step

Document only. Future contract after R3/R4 or alongside Continuity/H5 work — Engineer decides.

**CLI addendum (2026-08-15, post-G3 apply):** after DSE set `per_motor_max_thrust_n=12` / `motor_count=6` (`empuje_disponible=72`, `requerido≈25.8`, PASS), Continuity still said *“Declara empuje ≥ 4.3 N… no tengo un motor en el catálogo”*. Physics was fine; the 4.3 N is the *requirement* recomputed for catalog matching (KV+prop filters → 0 hits), not missing declared thrust. Confirms G9 content-honesty gap.

---

## G10 🟡 — Material catalog / frame acquisition misalignment

**Severity:** 🟡 registered — **do not implement yet**  
**Category:** Catalog / Acquisition — non-motor physical entities  
**Depends on catalog:** Yes (`library/materiales/_datos.json`)  
**Source:** Engineer CLI 2026-08-15 (`plastico`/`PVC`/`PPC` rejected; only `fibra de carbono 450g` accepted)

### Observed

```text
definir material / frame wizard open
User > plastico 390g     → re-prompt ejemplo
User > PVC 390g          → re-prompt
User > PPC 390g          → re-prompt
User > fibra de carbono 450g → OK
```

Ask *“qué materiales tenemos en el catálogo?”* → LLM analyze invents/partial answer (no deterministic list path).

### Evidence (three layers)

1. **Library has 8 materials:** aluminio, fibra de carbono, titanio, acero, kevlar, magnesio, plástico, pvc (`library/materiales/_datos.json`).
2. **Frame rule keywords** (`aerial.py`) only: `frame, chasis, estructura, armazon, carbon, carbono, aluminio` — no `plastico`/`pvc` → `infer_component` → `generic_component` → scoped wizard rejects.
3. **`MATERIAL_MAP`** incomplete vs library (`plastico` present; **`pvc` absent**). No FN-019-style `infer_component_for_key(..., "frame")` force when wizard expects frame (unlike bare propeller size).
4. **No deterministic “list materials” intent** — catalog query falls to LLM.

### Why study before Impl C

G10 shows how Jarvis treats **physical catalog entities that are not motors**. Aligning materials acquisition/list/authority informs Catalog v1 architecture for batteries/props/BOM — do **not** bury under Impl C SKU DSE.

### Separate from

```text
G9 ≠ G10   (motor Continuity honesty vs frame/materials acquisition)
G8 ≠ G10   (routing mid-wizard vs material vocabulary)
Design 3A  related alias noise — G10 is the broader misalignment
```

### Next step

Document only. Candidate: G10 design/contract (align keywords + MATERIAL_MAP ↔ library; optional force-frame; deterministic list) — Engineer before or interleaved with R3; **before Impl C**.

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

- Stale-gap UX: message may not reflect a motor **already bound** earlier in the session — **confirmed as G9** (SYS-MAP-004): `build_startup_context` never reads `catalog_ref` when recomputing catalog gap.
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

1. ~~**F-1**~~ → **DONE** (`checkpoint-f1-reducir-payload`).
2. ~~**G5** investigation + fix + CLI~~ → **DONE** (`checkpoint-g5-dse-component-sync`).
3. **G6** / **G7** → registered only; **no implement** until separate contracts.
4. ~~**G3**~~ → **DONE** (PASS WITH NOTES + **CLI PASS** 2026-08-15) → `checkpoint-g3`.
5. **G8** / **G9** → registered (SYS-MAP-004); **no implement**. G8 needs R3 design before any FN. G9 separate.
6. **G10** → registered (materials/frame); **no implement** — study/design before Impl C.
7. **F-5** → 🟡 until thrust-divergence CLI probe or state inspection.
8. **G1/G2/H5** → design after G3 checkpoint; Impl C **after** objective layer + G10 study.
9. **No catalog Impl C** until G3 checkpoint (+ G10/G1 design) decided.
10. **Do not** port iterate preempt into DEFINE_MISSING without R3.

---

## Queue (updated 2026-08-15)

```text
✅ G3 CLI PASS → checkpoint-g3
        ↓
📝 G10 registered (materials / frame) — no implement
        ↓
G10 design/contract  ⟷  R3 preempt design (Engineer order)
        ↓
R4 FN G8 (if approved) · G9 aparte
        ↓
G1/G2 + H5 design
        ↓
(G6/G7 if prioritized)
        ↓
UX catálogo → Impl C → BOM
```
