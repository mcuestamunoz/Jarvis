# Implementation Contract — Fit relations checklist B1 (`B1-fit-relations-checklist`)

**Project:** Jarvis  
**Date:** 2026-09-13  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer smoke

**Status:** READY FOR ★  
**Parents:**
- [Silhouette semantics lock](engineer_lock_silhouette_checklist_semantics.md) — next jump = **concrete relations**, not more “parece”  
- Fit attestation B1 **CLOSED** — [IC](implementation_contract_geometry_fit_attestation_b1.md) · writer `set_component_declared_fit_attestation` · gate = `screen_posed_envelope == overlap`  
- Screening CLOSED — `pose_envelope_screening.py` (never rename overlap → VERIFIED)  
- Silhouette S1 CLOSED — pattern peer for suggest-only IDLE checklist  
- [Fit attest all note](engineer_note_fit_attest_all_components.md) — disks = **later** Buy  

**Type:** Deterministic **suggest-only** IDLE checklist of **named assembly relations** (child → origin/target): what’s missing to screen, what’s `overlap` and ready to attest, what’s already attested — **reusing** existing screening + attestation writers. Optional thin Part A: scope silhouette footer copy.  
**Not** visual recognition. **Not** new fit math / margin / faces / CAD. **Not** renaming screening → VERIFIED. **Not** `ASSEMBLY_READY` flip. **Not** disk/motor station attestation (separate Buy). **Not** inventing dims or poses. **Not** version bump. **Not** `workspace/` mutation.

**Output:** `.jes/artifacts/implementation_report_geometry_fit_relations_checklist_b1.md`

**Checkpoint:** package **`0.4.1`** · suite ≥**2858** · UI ≥**103**

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fit-relations-checklist`** — Path **R1** checklist IDLE (this cycle). Disk-station attest = **out** |
| 2 | Claim | Copy may say relations are **listos para declarar verificado** / **bloqueados** / **ya declarados** — never “FIT VERIFIED automático” / “cabe” / “ensamblado real” |
| 3 | UX triggers | Normalize accents: **`relaciones`**, **`fit`**, **`qué falta verificar`**, **`verificaciones de encaje`** (document exact family in report). Must **not** steal `parece un dron` / `silueta` / `montajes estándar` / `layout pack` |
| 4 | Behavior | Pure module + orchestrator IDLE bridge → checklist. **Never** calls attest/pose/mount writers. Confirm = user types existing Continuity / Board attest phrases (or Situar / declare dims) |
| 5 | Relation set (fixed order) | Only these **when both ends exist** in `components` (skip absent keys — never invent). Prefer Continuity nouns in suggests: |
| | | `flight_controller` → `frame_plate*` (pose origin / mount target = boxed plate) |
| | | `esc` → same plate family |
| | | `battery` → same plate family |
| | | `sensors` → same plate family |
| | | `motors` → `frame_arm` (**mount** topology only this Buy — screening may be `n/a` if disk; say so honestly) |
| | | `propellers` → `motors` (**mount** only; disk → screening `n/a`) |
| 6 | Plate pick | Reuse silhouette / Path F plate origin honesty: exactly one boxed `frame_plate*` → that plate; 2+ → AMBIGUOUS row (no guess); zero → plate relations blocked with suggest `declara frame_plate estimada…` / measured declare |
| 7 | Per-relation status (deterministic) | Evaluate in order; first applicable wins: |
| | | `missing_child` / skip if child absent |
| | | `missing_origin` — target/plate/arm/motors missing |
| | | `no_box_child` / `no_box_origin` — suggest existing envelope phrases (Spanish nouns; exact keys OK if mount parse accepts) |
| | | `estimated_dims` — if screening would return estimated (reuse `_is_estimated_temporary_box` / screening) → **blocked** for attest; suggest measure/replace plate or child |
| | | `no_pose` — child lacks `declared_box_pose` (box–box pairs only) → suggest `apilar en placa` / `layout pack` / Situar — **do not invent z** |
| | | `no_mount` — optional warn row if `mounted_on` missing (does not block screening if pose exists; still list suggest `montajes estándar`) |
| | | `screen:no_overlap` / `screen:incomplete` / etc. — reuse `screen_posed_envelope` + `format_screening` honesty; suggest Situar |
| | | `screen:overlap` — **ready** → suggest existing attest phrase e.g. `declaro verificado el <noun>` (must match live IDLE grammar) |
| | | `attested` — valid fingerprint seal present → ✓ done |
| | | `n/a_disk` — motors/props (or any non-box) → honest “sin screening de caja hoy; montaje sí / attest disco = Buy aparte” |
| 8 | Verdict (checklist-scoped only) | e.g. `relaciones: N listas para declarar · M bloqueadas · K n/a` — **never** imply project Requirements/ASSEMBLY READY OK |
| 9 | Part A (thin, same cycle) | Silhouette footer when B*/B: replace bare “Nada crítico pendiente…” with **“Silueta: sin bloqueos críticos dentro de este checklist…”** (keep estimated reminder). No new triggers |
| 10 | Forbidden | New geometry formulas · auto-attest · weaken overlap gate · visual recognition · Conversation Engine |
| 11 | Version | **No** bump |

**Product sentence:**

```text
Pregunto “qué falta verificar” y Jarvis lista relaciones concretas
(FC↔placa, ESC↔placa, …): qué falta para screening, qué ya solapa y
puedo declarar verificado, y qué es n/a (disco). No inventa sellos.
```

### 0.1 Smoke target

```text
project: 10-min-autonomía (preferred) or autonomía-de-5min
expect: several stack relations overlap-ready or attested after Situar;
        motors/props rows n/a_disk for screening; mounts may show ok
code_star: checklist_idle + silhouette_footer_copy
```

---

## 1. You (Claude) — after ★

### Part A — Silhouette footer (thin)

In `format_silhouette_checklist`, when verdict is `silueta_estimada` / `silueta`, scope the closing line as checklist-local (lock copy above). Regression: still no “ASSEMBLY READY” / medido CAD.

### Part B — Fit relations module (e.g. `fit_relations_assist.py`)

```text
assess_fit_relations(components) -> FitRelationsAssessment
format_fit_relations_checklist(assessment) -> str
is_fit_relations_assist_trigger(user_input) -> bool
```

- Reuse `screen_posed_envelope`, existing attest field read, plate-origin helpers from craft/silhouette (no duplicate arithmetic).  
- Orchestrator IDLE bridge near silhouette (same suggest-only family).  
- Suggest strings = **existing** user-facing phrases only (attest / montajes / apilar / declara estimada / Situar hint in prose OK without new command).

Do **not** bump version. Do **not** mutate `workspace/`.

---

## 2. Tests

| ID | Behavior |
|---|---|
| A1 | Silhouette B* footer contains “este checklist” (or locked equivalent); no project-global “sin problemas” |
| R1 | No plate box → plate relations blocked / racimo-like honesty; no false “listo para verificar” |
| R2 | FC posed+boxed on estimated plate → `estimated_dims` blocked (not ready to attest) |
| R3 | FC posed+boxed on declared plate + screening overlap → status ready + suggest attest phrase that matches real parser/IDLE if one exists |
| R4 | Valid attestation present → `attested` |
| R5 | Motors/props → `n/a_disk` for screening; mount absence can still show as warn |
| R6 | Triggers resolve; `silueta` / `montajes estándar` / `parece un dron` do not steal |
| R7 | IDLE list-alone never mutates ProjectState / never calls attest writer |
| T | Full pytest green; package `0.4.1` |

---

## 3. Smoke (Engineer) — `10-min-autonomía`

1. `parece un dron` → B* with **scoped** footer.  
2. `relaciones` / `qué falta verificar` → list; stack rows honest; motors/props `n/a` for box screening.  
3. If a row is “listo”: run existing attest phrase or Board button → seal; re-trigger → attested.  
4. Confirm Requirements/autonomy banner still independent (silhouette/fit checklist ≠ project green).

---

## 4. Out of scope

Disk-station attest Buy · margin/compose/faces · ASSEMBLY_READY · plate L×W invent · frame-parts progressive Ask · visual recognition · HD-005

---

## 5. Done when

- [ ] Engineer ★  
- [ ] Part A + Part B + tests + report  
- [ ] Engineer smoke ACCEPT  

---

## 6. Handoff

```text
Engineer → ★ this IC
Claude   → implement + report
  implementation_report_geometry_fit_relations_checklist_b1.md
Cursor   → review
Engineer → smoke §3
```

### Paste for Claude (after ★)

```text
Implementá B1-fit-relations-checklist per
.jes/artifacts/implementation_contract_geometry_fit_relations_checklist_b1.md
— Part A: silhouette footer scoped to “este checklist”.
— Part B: IDLE relaciones / qué falta verificar — suggest-only; reuse
  screen_posed_envelope + existing attest; disk rows n/a; no auto-attest;
  no version bump; no workspace/ mutation.
Report → implementation_report_geometry_fit_relations_checklist_b1.md
```
