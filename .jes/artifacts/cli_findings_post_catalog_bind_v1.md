# CLI Findings — Post Catalog Bind v1 → F-1 / G5 / G3 / SYS-MAP-004 / G10–G15

**Date:** 2026-08-15 (updated — **2026-08-17** CLI polish bundle queued · commit `1b4769f`)  
**Checkpoints:** `checkpoint-catalog-impl-b` · `checkpoint-f1-reducir-payload` · `checkpoint-g5-dse-component-sync` · **`checkpoint-g3`** · post-g3 **`1b4769f`** (Continuity + G10, untagged)  
**Evidence:** Engineer CLI `continuity-bom` walk 2026-08-17 + prior G10–G13 sessions  

> Living register of CLI findings. Distinguishes bugs, known limits, expected behavior, and deferred work. **Do not confuse a finding with a regression** after later checkpoints.

---

## Summary

| ID | Severity | Status | One-line |
|---|---|---|---|
| F-1 | 🔴→🟢 | **Fixed** | `reducir payload` → Plan Reducir + DSE ↓ |
| G5 | 🔴→🟢 | **Fixed** (+ CLI PASS) | Dual-truth DSE→iterate cerrado |
| **G3** | 🟡→🟢 | **Fixed + CLI PASS** | Active-goal continuity explore; override + consumed handoff |
| **G14** | 🔴→🟢 | **Fixed (Continuity)** | Motors phrase no longer force-writes hélices in composite wizard |
| **G15** | 🟡→🟢 | **Fixed (Continuity; residuals → G16)** | Filtered max + list-motors mid-wizard (sin `?`) |
| **G16** | 🟡 | **Registered — polish** | (A) list-motors + `?` → analyze (wizard **and IDLE**); (B) CTA duplicada |
| **G17** | 🔴 | **Registered — force-motors gap** | Example `4x 2306…` re-prompts; needs keyword `motores` |
| **G18** | 🔴 | **Registered — cross-domain routing** | `definir motores` on **dron** opens terrestrial transmission wizard (torque/rueda) |
| **G19** | 🔴 | **Registered — CTA/discoverability** | Catalog-gap CTA no conecta con DSE/list-motors; exploración oculta |
| **G10** | 🟡→🟢 | **Fixed (CLI parcial)** | `plastico` + **`PVC 400g` acquisition PASS** (Continuity CLI 2026-08-17) |
| **G11** | 🟡 | **Registered — Continuity/R3** | Iterate preempt / acquisition collision (C-052) |
| **G12** | 🟡 | **Registered — Continuity/R3** | DEFINE_MISSING sticky retarget — hay que `cancelar` |
| **G13** | 🟡 | **Registered — later** | Iterate material `PVC 400g` opaque slug |
| **G8** | 🟡 | **Registered — Continuity/R3** | DEFINE_MISSING swallows engineering/explore |
| **G9** | 🟡 | **Registered — polish bundle** | Catalog-gap misleading post-PASS (G9-B); blind to `catalog_ref` (G9-A) |
| **G6** | 🟡 | **Registered — later** | Mass breakdown deterministic |
| **G7** | 🟡 | **Registered — Continuity** | Iterate `operation=None` / mid-flow break |
| F-2 | 🟡 | Known gap | Diámetro hélices → iterate |
| F-3 | 🟡 | Expected | `configurar hélices` → RPM only |
| F-4 | 🟢 | Demostrado | Motor catalog pick + masa |
| F-5 | 🟡 | Pendiente verificación | Divergencia `catalog_ref` post-DSE |
| F-6 | 🟢→🟡 | Demostrado + **G9 elevates stale-gap** | Gap catálogo honesto; honesty vs bound SKU = G9 |

**Next queue (Engineer 2026-08-17 — POLISH BUNDLE):**

```text
✅ checkpoint-g3
✅ Continuity Hardening impl + review + CLI walk (continuity-bom)
✅ G10 impl + PVC/plastico acquisition CLI PASS
✅ commit 1b4769f (Continuity + G10 + findings G16–G19)
        ↓
🔴 CLI Polish Audit (Claude) — IC: implementation_contract_cli_polish_audit.md
   Plan: work_plan_cli_polish_audit.md
        ↓
Design + Implementation Contract (from audit report)
        ↓
Polish impl (G9-B · G16 · G17 · G18 · G19 · G12-FN013 · …)
        ↓
CLI re-walk → checkpoint tag
        ↓
G11/G13/R3 remainder · Impl C
```

**Engineer lock:** Audit before impl. No `src/` until IC approved from audit report.

**Explicitly deferred:** G10 PVC CLI · G13 · G9 isolate · thrust gate (★7) · Impl C · H5/C-081.

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
G12 ≠ G8  (G12 = sticky acquisition retarget `definir <otro>`; G8 = engineering/explore swallow)
FN-021 ≠ G8  (FN-021 = post-completion clear; G8 = mid-wizard turn)
```

### Next step

Document only until R3. Map caveat: R1 (C-040 / ACQUISITION_MAP).  
**CLI addendum:** acquisition retarget sticky → **G12** (same DEFINE_MISSING layer; do not fold silently into G8 text).

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

### G9-B — Misleading catalog-gap CTA when physics PASS with declared thrust (2026-08-17)

**Severity:** 🔴 UX — **priority polish bundle**  
**Source:** `continuity-bom` after DSE apply (`per_motor_max_thrust_n=30`, `motor_count=6`)

```text
Cálculos: empuje_requerido=19.777 N, empuje_disponible=180.0 N, margen=9.101
Sim: PASS

Continuity:
  Siguiente paso: Declara empuje real por motor (≥ 3.3 N) …
  Por qué: Necesitas empuje ≥ 3.3 N/motor, ~2400KV, hélice ~10"; no tengo un motor…
```

**Root:**

- `thrust_per_motor_needed_n` = `required_thrust_n / motor_count` ≈ **3.3 N** (piso físico).
- `per_motor_max_thrust_n` = **30 N** (declarado vía DSE) — no leído por Continuity CTA.
- `find_motors_for_requirements(≥3.3, kv=2400, prop=10)` → 0 SKU (filtro KV+hélice, no falta empuje).
- `project_continuity.py` rank 3: `motor_catalog_gap` **gana** sobre “diseño validado PASS”.

**User impact:** mensaje suena a “te falta empuje” cuando el margen es ~9×. El gap real es **identidad BOM/catálogo** (combo 2400KV+10″ sin SKU), no viabilidad física.

**Expected:** si `per_motor_max_thrust_n ≥ thrust_per_motor_needed_n` y sim PASS → suprimir o degradar a aviso BOM no bloqueante; no pedir “declara empuje ≥ X” usando el piso físico.

**Fix sketch:** guard en `build_project_continuity` + reformular CTA; opcionalmente leer `catalog_ref` (G9-A).

---

## G10 🟢 — Material catalog / frame acquisition misalignment

**Severity:** was 🟡 · **Status:** **Fixed (CLI parcial)** — impl + tests + Cursor PASS WITH NOTES; ★8 CLI PASS; **`plastico 390g` frame CLI PASS**; PVC frame clean probe still pending; ★6 mutate CLI blocked by G11  
**Category:** Catalog / Acquisition — non-motor physical entities  
**Depends on catalog:** Yes (`library/materiales/_datos.json`)  
**Source:** Engineer CLI 2026-08-15; investigation + design CLOSED ★1–★8  
**Design:** [design_g10_materials_frame.md](design_g10_materials_frame.md) — ★1–★8 locked  
**Implementation:** [implementation_report_g10_materials_frame.md](implementation_report_g10_materials_frame.md)  
**Review:** [implementation_review_g10_materials_frame.md](implementation_review_g10_materials_frame.md) — PASS WITH NOTES  

### Status detail (2026-08-15)

| Gate | Result |
|---|---|
| Implementation ★1–★8 | ✅ |
| Unit/acceptance tests (T1–T8) | ✅ |
| Cursor review | ✅ PASS WITH NOTES |
| CLI ★8 list-materials | ✅ PASS |
| CLI ★1–★4 frame `plastico 390g` | ✅ PASS — `Frame registrado: plástico 0.39kg` (proyecto `volar`; wizard frame real tras `cancelar` por **G12**) |
| CLI ★1–★4 frame `PVC 400g` | 🟡 **pending** — clean **acquisition** wizard. Post-arquitectura `definir frame` abre **iterate**, no DEFINE_MISSING frame |
| CLI ★6 material mutate density | 🟡 **CLI partial** — bare `PVC` → ρ OK; **`PVC 400g` as iterate value FAILS** (opaque slug) → see **G13** |

### Observed (original pre-fix)

```text
definir material / frame wizard open
User > plastico 390g     → re-prompt ejemplo
User > PVC 390g          → re-prompt
User > fibra de carbono 450g → OK
```

### CLI addendum (2026-08-15 — frame declare)

```text
# After cancelar (G12 sticky) + guiame → frame wizard open
User > plastico 390g
→ Frame registrado: plástico 0.39kg. ✓ Bloque completado: Estructura (frame).
```

PVC vía iterate (`definir frame` post-arquitectura → wizard iterate → `material` → …) **no** valida ★1–★4 acquisition.

| Iterate value | Result |
|---|---|
| `PVC` | ★6 OK — `ρ 1200→1380`, `+3.8%` |
| `PVC 400g` | fail lookup — treat as slug `pvc 400g`; lists `pvc` as available → **G13** |

### Closed in code

Shared `MATERIAL_ALIASES`, force-frame, keywords, mutation SoT, list-materials 0-LLM. Library JSON untouched.

### Engineer locks

- Do **not** fix G9 Continuity in isolation before catalog architecture (G10 → Impl C).  
- Do **not** weaken G10 keywords / force-frame to paper over **G11** / **G12**.

### Separate from

```text
G9 ≠ G10   ·  G8 ≠ G10   ·  G11 ≠ G10   ·  G12 ≠ G10
```

### Next step

Document only. PVC **acquisition** probe **deferred** until Continuity Hardening restores a clean path. See queue re-lock (G14/G15).

---

## G11 🟡 — Iterate wizard preemption / acquisition collision (C-052)

**Severity:** 🟡 registered — **do not implement yet** (R3-adjacent routing design; **not** a G10 patch)  
**Category:** Routing / session — ITERATE_INTERACTIVE preempt vs in-wizard answers  
**Depends on catalog:** Indirect — G10 ★4 keyword expansion made manifestation B reproducible  
**Source:** Engineer CLI 2026-08-15 while probing G10 material mutate  

### Root (one finding, two faces)

> **C-052 / `_should_preempt_iterate_wizard` does not adequately distinguish a new engineering intent from a valid answer to the currently open iterate wizard.**

### G11-A — Wizard’s own action phrases are swallowed

```text
Iterate step 2 prompt suggests: "cambiar material", "optimizar estructura", …
User > cambiar material
        ↓
IntentResolver → iterate ∈ _ITERATE_PREEMPT_INTENTS
        ↓
"He cerrado la iteración en curso…" → wizard restarts → loop
```

### G11-B — Material names collide with frame while iterate is open

```text
Iterate step 2
User > pvc
        ↓
G10 ★4: "pvc" is a frame keyword → infer_component → frame
        ↓
C-052 component-intercept preempt
        ↓
closes iterate → frame mass / analyze — material mutation never completes
```

### Why not fold into G7 only / why not fix inside G10

G7 = broader iterate slot fragility. G11 = new reproducible preempt-collision evidence from G10 (needed for R3 / iterate-preempt policy before Impl C).  
G11 sits **above** G10 — do not regress ★4 to hide B.

### Separate from

```text
G8 = DEFINE_MISSING vs engineering/explore
G12 = DEFINE_MISSING sticky acquisition retarget (related layer; different face)
G10 = materials identity (do not regress)
G7 = related; G11 is the preempt-collision slice
```

### Next step

Document only. After G10 checkpoint decision → feed R3 design (and/or narrow iterate-preempt design). No `src/` in G10 cut.

---

## G12 🟡 — DEFINE_MISSING sticky acquisition retarget (`definir <otro>` → mismo wizard)

**Severity:** 🟡 registered — **do not implement yet** (R3 DEFINE_MISSING preempt / retarget policy)  
**Category:** Routing / session — DEFINE_MISSING UX-C vs explicit `definir <component>`  
**Depends on catalog:** No  
**Source:** Engineer CLI 2026-08-15 (proyecto `volar`, while probing G10)

### Observed

While a DEFINE_MISSING wizard is open for gap A, asking to define gap B does **not** retarget. User must `cancelar` (then often `guiame`) to reach B.

```text
Battery wizard open
User > definir frame
        ↓
"Vamos a definir la batería…"   ← same wizard
```

Worse — Continuity already points to the next block, but the open session still serves the previous prompt body:

```text
Battery completed → Continuity: "Siguiente bloque: Estructura (frame)"
User > definir frame
Jarvis > Seguimos con Estructura (frame) — sin reiniciar lo ya capturado.
        ↓
        still prints battery guide + "Describe la batería…"
```

Same pattern later in the session:

```text
Frame completed → User > definir flight_controller
→ "Seguimos con Control…" then re-shows frame wizard

User > definir sensors   (gap = sensors)
→ still "Describe la controladora de vuelo…"
```

**Workaround proven:** `cancelar` → `guiame` → `definir frame` → frame wizard correct → `plastico 390g` OK (G10).

### CLI addendum (2026-08-15 — Continuity Hardening post-impl)

Slice 2 refuse (`_maybe_refuse_different_target`) did **not** catch this path. After propulsion “complete”, session still had `pending_param_definitions` on **motors** while `_next_pending_block` was already **energy**:

```text
User > definir bateria
→ "Seguimos con Energía (batería) — sin reiniciar lo ya capturado."
→ brief body = motors ("Hélices ya declarado(s); gap activo = motors")
```

**Root (refined):** `_try_reprompt_active_block_declaration` (FN-013, runs **before** `_handle_component_description` / Slice 2) uses:
- label from `_next_pending_block` == named block (`energy`), but
- `brief` from `session.pending_param_definitions[0]` (stale `motors`).

So Continuity Hardening ★2 closes silent UX-C absorb; **FN-013 stale-pending vs next-block mismatch remains G12**. Fix later: sync/clear pending to the named block’s keys before building the brief, or refuse if `pending[0]` ∉ named block’s components.

### Root (working hypothesis)

Same DEFINE_MISSING layer as **G8**: UX-C / open `MISSING_COMPONENT_DEFINITION` absorbs turns without a retarget/preempt policy when the user names a **different** acquisition target.  
G8 = engineering/explore swallowed.  
G12 = **acquisition→acquisition** sticky / incoherent “Seguimos con X” + body of Y.

### Why separate from G8

Reusable evidence for R3: not only “don’t swallow `reducir payload`”, but also “honor `definir <other_component>` or clear session honestly”.  
Do **not** patch inside G10.

### Separate from

```text
G8  = engineering/explore mid-DEFINE_MISSING
G11 = iterate preempt vs in-wizard answers
G10 = materials acquisition identity (validated once wizard is actually frame)
```

### Next step

Document only. Feed **R3** / Continuity Hardening with G8 + G12. No `src/` now.

---

## G13 🟡 — Iterate material value: compound `PVC 400g` not parsed (opaque slug)

**Severity:** 🟡 registered — **do not implement yet** (not a G10 acquisition regression; post-checkpoint micro-design or materials-parse shared helper)  
**Category:** Iterate / materials parse — slot grammar vs acquisition phrase grammar  
**Depends on catalog:** Yes (uses G10 aliases / density table)  
**Source:** Engineer CLI 2026-08-15 (proyecto `volar`)

### Observed (same session, contrast)

```text
Iterate material slot
User > PVC
→ Cambio plástico → pvc: ρ 1200.0→1380.0 kg/m³, peso total estimado +3.8%   ✅

User > PVC 400g
→ El material 'pvc 400g' ha sido registrado… pero no tengo datos físicos…
  Materiales con datos disponibles: … pvc …                 ❌
→ confirm apply → "No se recalcula impacto físico"
→ masa_total unchanged (2.25 kg)
```

### Root (working hypothesis)

Frame **acquisition** accepts `material + masa` (`plastico 390g` → G10 PASS).  
Iterate **material** slot treats the whole token as material id → lookup `pvc 400g` misses alias `pvc`.  
Does not strip trailing mass / does not split into material + optional mass update.

### Why not fold into G10 / why not patch G10 now

G10 ★1–★4 = DEFINE_MISSING frame acquisition — already PASS for `plastico`.  
G13 = iterate slot grammar after architecture complete. Fixing by weakening G10 keywords would be wrong.  
May later share parse helper with acquisition — **design decision after checkpoint-g10**, not in G10 cut.

### Separate from

```text
G10 ★6 tests / bare-PVC CLI = density path works
G11 = preempt / routing collision
G7  = operation=None / wizard break
G13 = compound phrase in material slot only
```

### Next step

Document only. **Deferred** with G10 PVC micro-probes until Continuity Hardening. Do not block Continuity cut on G13.

---

## G14 🔴 — Propulsion acquisition: motors prompt saves as hélices

**Severity:** 🔴 continuity-blocking — **Continuity Hardening cut** (design before impl)  
**Category:** Acquisition / component inference — wrong key bind  
**Depends on catalog:** No  
**Source:** Engineer CLI 2026-08-15 — proyecto nuevo `prueba`

### Observed

```text
User > definir propulsion
Jarvis > Vamos a definir los motores.
        Describe los motores. Ej: '4x 2306 2400KV 50W'

User > 1x 2306 2400KV 50W
Jarvis > Acción ejecutada: component_description_saved
        Hélices registradas. Describe los motores. Ej: '4x 2306 2400KV 50W'
```

User followed the motors example almost verbatim; system acknowledged **hélices** and re-asked motors. Continuity of propulsion block broken.

### Root (working hypothesis)

Likely `infer_components` / force-propellers path (FN-019-style) winning over active gap `motors` — size/KV tokens or incomplete propellers gap steals the turn. Related to G10 force-frame pattern applied to propellers without respecting open motors wizard authority.

### Why Continuity cut (not G10)

G10 materials identity is fine. This is acquisition **target authority** mid-propulsion — same family as G12 sticky, blocks any clean BOM walk including later frame/PVC probes.

### Acceptance (future contract sketch)

```text
Motors wizard open + phrase matching motors example
  → motors registered (not propellers)
  → prompt advances correctly (hélices or next param)
```

### Next step

Include in **Continuity Hardening** investigation/design. No drive-by `src/` fix without contract.

---

## G15 🟢 — Motor catalog help incoherent + mid-wizard list rejected

**Severity:** was 🟡 · **Status:** **Fixed (Continuity Hardening Slice 3)** — residuals tracked as **G16**  
**Category:** DEFINE_MISSING / catalog UX mid-wizard  
**Depends on catalog:** Yes  
**Source:** Engineer CLI 2026-08-15 — proyecto `prueba` (pre-fix); Continuity CLI 2026-08-15 (post-fix)

### Closed in Continuity

- ★6: filtered max in `format_no_thrust_candidate_message` (same KV/prop universe as search).  
- ★5: `is_list_motors_phrase` inside `ParamDefinitionSession._answer_assisted_motor` — works for e.g. `que motores tenemos en el catalogo` **without** trailing `?`.

### Residual → G16

See **G16** (analyze soft-interrupt missing; CTA duplication in catalog-help response).

---

## G16 🟡 — Continuity residual: list-motors analyze bypass + catalog CTA duplication

**Severity:** 🟡 polish — **do not block Continuity CLI BOM walk**; fix in small follow-up after walk / with map caveats  
**Category:** Routing / catalog UX — list-motors parity vs G10 ★8  
**Depends on catalog:** No (routing/UX)  
**Source:** Engineer Continuity CLI 2026-08-15 + **2026-08-17 addendum** (`continuity-bom`, post 4/4)

### G16-A — Trailing `?` (or other analyze-shaped phrasing) bypasses ★5

```text
# Mid-wizard (thrust DEFINE_MISSING)
User > que motores tenemos en el catalogo?   → intent=analyze → LLM   ❌
User > que motores tenemos en el catalogo    → list-motors deterministic ✅

# Post-architecture IDLE (2026-08-17 — NEW)
User > ¿que motores tenemos en el catalogo?
→ analyze → LLM describes declared motors, NOT catalog list   ❌
→ "No se proporciona información específica sobre un catálogo de motores…"
```

**Root (two layers):**

1. **Orchestrator soft-interrupt missing (wizard):** DEFINE_MISSING soft-interrupts `list_materials` (G10 ★8) but **not** `is_list_motors_phrase` before analyze→LLM (`orchestrator.py` ~774–803). List-motors only runs inside `param_definition_session.answer` — never reached if intent is `analyze`.

2. **No global `list_motors` intent (IDLE):** G10 added `LIST_MATERIALS_PATTERNS` → `list_materials` → `_handle_list_materials()` in `intent_resolver.py` + orchestrator. **Motors have no equivalent** — `is_list_motors_phrase` exists but is only wired in `ParamDefinitionSession._answer_assisted_motor`. At IDLE, even without `?`, there is no orchestrator handler; with `?`, `_looks_like_question` → `analyze`.

**Probe (code):** `IntentResolver.resolve_intent("…catalogo?") == "analyze"` while `is_list_motors_phrase` is still True. No `LIST_MOTORS_PATTERNS` in `_resolve_strong_action_intent`.

**Fix sketch:** (1) mirror G10 ★8 soft-interrupt for `is_list_motors_phrase` in orchestrator; (2) add global `list_motors` intent + `_handle_list_motors()` for IDLE/post-architecture (filtered by project requirements when available).

### G16-B — “Elige un número…” printed twice

```text
User > que motores tenemos en el catalogo
Jarvis > Candidatos del catálogo …
         Elige un número, indica empuje en N … o di 'no' para omitir.
Siguiente paso:
         Elige un número, indica empuje en N … o di 'no' para omitir.
```

**Root:** `format_motor_catalog_suggestions(..., param=per_motor_max_thrust_n)` appends the CTA line into **`message`** (`motor_catalog_assist.py` ~284–287), and `_offer_catalog_help` sets **`question`** to nearly the same string (`param_definition_session.py` ~338–341). CLI prints `message` then `Siguiente paso: question` → duplicate.

**Fix sketch:** keep CTA only in `question` (strip trailing choose-line from `format_motor_catalog_suggestions` when used for thrust) **or** leave message as list-only and question as the single CTA — one source of truth.

### Separate from

```text
G15 core (filtered max + list-motors happy path) = closed
G10 ★8 list-materials = already has orchestrator soft-interrupt (pattern to copy for G16-A)
```

### Next step

Document only during Continuity BOM walk. Micro-contract after walk PASS (or fold into Continuity polish PR). Workaround CLI: omit `?`; ignore duplicated line.

---

## G17 🔴 — Motors wizard: example phrases don't bind without keyword `motores` (no force-motors)

**Severity:** 🔴 continuity / acquisition — **same class as pre-G10 frame** (prompt example does not work as typed)  
**Category:** Acquisition — missing FN-019-style force for `motors` when scoped wizard expects motors  
**Depends on catalog:** No  
**Source:** Engineer Continuity CLI 2026-08-15 (`continuity bom`) after Continuity Hardening Slice 1

### Observed

```text
Motors wizard open (expected_keys=["motors","propellers"])
Prompt example: '4x 2306 2400KV 50W'

User > 1x 2306 2400KV 50W   → re-prompt motors brief (no write)   ❌
User > 4x 2306 2400KV 50W   → same re-prompt                      ❌  (code-confirmed)
User > motores 4x 2306 2400KV 50W → Motores registrados…          ✅
```

G14 correctly stopped `1x 2306…` from writing **hélices**. It did **not** make the phrase bind as **motors**.

### Root (code-confirmed)

1. Motors `ComponentRule` keywords = only `("motor",)` — bare `Nx 2306 2400KV 50W` → `infer_components` → `generic_component`.  
2. Force-propellers is gated (★4) so G14 no longer steals the turn.  
3. **There is force-frame (G10 ★3) and force-propellers (FN-019), but no `force-motors`** when `"motors" in expected_keys` and specs are generic.  
4. `infer_component_for_key(..., "motors")` would return **high** completeness for both `1x` and `4x` phrases — the extractor works; the orchestrator never calls it.  
5. Prompt `COMPONENT_PROMPTS["motors"]` advertises an example **without** the word `motores` → same UX trap as pre-G10 frame examples.

### Relation to Continuity / G14

```text
G14 = don't write wrong key (hélices)     ✅ closed
G17 = do write correct key (motors)       ❌ missing force-motors
```

Not a regression of G14 — G14 exposed the gap by removing the false-positive path. Fix belongs in Acquisition (mirror FN-019 for motors), **not** by weakening the G14 propeller gate.

### Workaround (CLI now)

```text
motores 4x 2306 2400KV 50W
```
(or any phrase containing `motor`/`motores` + specs)

### Fix sketch (later contract)

When `"motors" in expected_keys` and all specs are `generic_component`, call `infer_component_for_key(..., "motors")` if completeness ≠ low — same shape as force-propellers / force-frame. Composite tiebreak already prefers not forcing propellers on motor-shaped text; force-motors should run (or run first) for the active motors gap.

### Next step

Register only. Include in Continuity polish / small FN after BOM walk (with G16). Do not patch mid-walk.

---

## G18 🔴 — `definir motores` on aerial project opens terrestrial transmission wizard

**Severity:** 🔴 cross-domain routing — **E1 overreach**  
**Category:** Intent / DEFINE_PARAMS — vehicle_type ignored  
**Depends on catalog:** No  
**Source:** Engineer Continuity CLI 2026-08-17 (`continuity bom`, architecture 4/4 complete)

### Observed

```text
Project: dron (vehicle_type=dron), architecture 4/4, motors component already declared

User > definir motores
→ "¿Cuál es el par de torsión por actuador en N*m?"
User > 1.4
→ "¿Cuál es el radio de rueda en metros?"
```

Session snapshot confirms: `param_definition_reason=missing_transmission_parameters`, `pending=["wheel_radius_m","gear_ratio"]`, `collected={"per_actuator_torque_nm":1.4}`.

### Root (code-confirmed)

`intent_resolver.py` E1 added terrestrial `DEFINE_PARAMS_PATTERNS`:

```text
definir … motor(es)  →  define_params  →  missing_transmission_parameters
```

**No check** of active `vehicle_type` / domain. On a **dron**, `definir motores` should route to aerial acquisition (`definir propulsion` / component wizard), **not** ground transmission params.

Contrast:

| Phrase | Intent (IDLE) | On dron should be |
|---|---|---|
| `definir motores` | `define_params` → **transmission** | propulsion / motors component |
| `definir propulsion` | `iterate` | acquisition reprompt or refuse |

### Workaround

On drone projects, **never** use `definir motores` post-architecture. Use:

```text
cancelar                    ← if stuck in wheel wizard
definir propulsion          ← or describe component directly
motores 4x 2306 2400KV 50W  ← if motors wizard open
```

### Separate from

```text
G17 = force-motors inside composite wizard (acquisition)
G18 = intent routes aerial user into ground param wizard
G12 = FN-013 stale pending (different path)
```

### Next step

Register only. Fix: gate E1 terrestrial `define_params` on `vehicle_type != dron/aerial` OR map `definir motores` to aerial block alias when project is aerial.

---

## G19 🔴 — Catalog-gap CTA: poor discoverability + no list/explore bridge

**Severity:** 🔴 product gap — **CTA incoherente con capacidades existentes**  
**Category:** Continuity + catalog + reasoning — discoverability  
**Depends on catalog:** Yes (`library/motores`, `find_motors_for_requirements`)  
**Source:** Engineer Continuity CLI 2026-08-17 (`continuity-bom`, post 4/4, sim PASS)

### Observed (phase 1 — dead-end aparente)

Continuity repeatedly says:

```text
Siguiente paso: Declara empuje real por motor (≥ 4.8 N) o elige una pieza fuera de catálogo
Por qué: Necesitas empuje ≥ 4.8 N/motor, ~2400KV, hélice ~10"; no tengo un motor en el catálogo que cubra ese espacio.
```

User tries to **explore options**:

```text
User > ¿que motores tenemos en el catalogo?
→ analyze/LLM: describes declared motors, denies catalog info          ❌ (G16-A)

User > modelar unidad de potencia
→ analyze/LLM: "No puedo estimar ese impacto con precisión…"           ❌
```

### Observed (phase 2 — path oculto existe, 2026-08-17 addendum)

```text
User > declarar empuje        → engineering_intent → Plan estabilidad
User > explora opciones       → DSE 5 configs (mejor: 30N × 6 motores)  ✅
User > aplica la mejor        → per_motor_max_thrust_n 20→30, motors 4→6 ✅
→ sim PASS margen 9.1 — pero Continuity sigue pidiendo "declara empuje ≥ 3.3 N" (G9-B)
```

**Refined diagnosis:** exploración **existe** vía `declarar empuje` → `explora opciones` → `aplica la mejor`, pero:
- Continuity **no lo anuncia** cuando hay catalog_gap
- list-motors **no funciona** en IDLE / con `?`
- reasoning suggestions no son **ejecutables**

### Root (code-confirmed)

| Layer | Behavior | Gap |
|---|---|---|
| `project_continuity.py` rank 3 | `motor_catalog_gap` → CTA = "declare thrust or off-catalog" | No "explore catalog" / "see closest matches" branch |
| `intent_resolver.py` | `LIST_MATERIALS_PATTERNS` → `list_materials` at IDLE | **No `LIST_MOTORS_PATTERNS`** |
| `motor_catalog_assist.py` | `is_list_motors_phrase`, `offer_catalog_help`, filtered search | Only reachable mid-wizard or without `?` in wizard |
| `reasoning_layer.py` | Suggests "Modelar unidad de potencia" (`action="iterate"`) | Suggestion text shown in analyze response; **not executable** from user phrase → analyze dead-end |
| DSE `EXPLORE_PATTERNS` | `explorar opciones`, `optimiza para payload` | No motor/thrust-specific exploration bridge from catalog_gap state |

### Expected (Engineer requirement)

When Continuity reports a **catalog gap on thrust/motor requirements**, the user should be able to:

1. **List catalog motors** (deterministic, 0 LLM) — globally, with `?`, at IDLE
2. **See filtered/closest matches** vs declared KV/hélice/requisito (even when 0 exact hits — show max compatible, like G15 ★6 mid-wizard)
3. **Enter exploration** — e.g. `explorar motores`, `ayúdame a elegir motor`, or Continuity CTA that opens assisted selection / DSE thrust axis

### Workarounds (CLI now)

```text
# Only inside thrust DEFINE_MISSING wizard (if you can open it):
que motores tenemos en el catalogo    ← sin ?
ayúdame a elegir
<número>                              ← pick from list

# Declare thrust directly (bypasses catalog):
20                                    ← N per motor (if wizard open)
definir propulsion → si → motores …   ← re-declare component

# DSE (generic, not motor-specific):
explorar opciones / optimiza para payload

# Avoid:
definir motores                         ← G18 terrestrial wizard
¿que motores…?                          ← G16-A analyze
modelar unidad de potencia              ← analyze dead-end
```

### Relation to other findings

```text
G16-A = list-motors routing (symptom — user can't list catalog)
G9    = gap honesty vs bound catalog_ref (content — gap may be stale/noisy)
G19   = product gap — Continuity tells user what's wrong but offers no exploration path
G15   = filtered max works mid-wizard; G19 is the IDLE/post-architecture mirror missing
```

### Fix sketch (later IC — polish bundle or catalog parity)

1. **G10 ★8 parity for motors:** `LIST_MOTORS_PATTERNS` → `list_motors` → `_handle_list_motors()` (filter by `physical_requirements` + declared KV/prop when live project exists).
2. **Continuity CTA branch:** when `motor_catalog_gap` and `catalog_matches == []`, offer "Di 'que motores tenemos' para ver el catálogo" or auto-suggest closest `find_motors_for_requirements` partial matches.
3. **Reasoning → action wiring:** map "Modelar unidad de potencia" / "Definir empuje por motor real" to `define_params` thrust wizard or `list_motors`, not analyze.
4. **Optional:** DSE axis for motor/thrust when gap active (larger scope — defer unless Engineer wants).

### Next step

Register only. Include in polish bundle with G16/G17/G18. **Do not patch mid-walk.**

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
| `plastico` / material frame rejected; `aluminio 450g` worked | → **G10** (impl done; frame CLI probe pending) · collision mid-iterate → **G11-B** |
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
2. ~~**G5**~~ → **DONE** (`checkpoint-g5-dse-component-sync`).
3. **G6** / **G7** → registered; Continuity may touch G7-related.
4. ~~**G3**~~ → **DONE** + CLI PASS → `checkpoint-g3`.
5. **RELOCK:** Continuity Hardening **before** G10 PVC / `checkpoint-g10`.
6. **G10** → impl done; `plastico` PASS; PVC **deferred**; **do not** patch materials for routing.
7. **G14 / G15 / G12 / G8 / G11** → Continuity Hardening bundle (design → contract → impl).
8. **G13** → deferred with PVC micro-probes.
9. **G9** → documented; **do not implement in isolation**.
10. **No `src/`** until Continuity Hardening contract approved. No Impl C until continuity + G10 checkpoint path restored.

---

## Queue (updated 2026-08-15 — Engineer RELOCK)

```text
✅ checkpoint-g3
✅ G10 impl + ★8 + plastico CLI
⏸ checkpoint-g10 / PVC — DEFERRED
        ↓
🔴 Continuity Hardening (G14 · G15 · G12 · G8 · G11)   ← AHORA
        ↓
restore BOM walk
        ↓
G10 PVC / checkpoint-g10 · G13
        ↓
R3 remainder · G9 · G1/H5 · UX · Impl C
```
