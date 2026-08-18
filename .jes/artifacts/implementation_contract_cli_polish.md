# Implementation Contract — CLI Polish Bundle (S1–S7)

**Project:** Jarvis  
**Date:** 2026-08-18  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)  

**Status:** READY FOR ENGINEER → send to Claude  

**Type:** Product behavior — Continuity CTA honesty + catalog list-motors parity + cross-domain routing + force-motors + FN-013 session freshness.

**Closes / advances:** G9-B 🔴 · G16-A/B · G17 🔴 · G18 🔴 · G19 🔴 · G12/FN-013 — [`.jes/artifacts/cli_findings_post_catalog_bind_v1.md`](cli_findings_post_catalog_bind_v1.md)

**Audit authority:** [`.jes/artifacts/investigation_cli_polish_audit.md`](investigation_cli_polish_audit.md)  
**Work plan:** [`.jes/artifacts/work_plan_cli_polish_audit.md`](work_plan_cli_polish_audit.md)  
**Prior Continuity locks (do not reopen):** [`.jes/artifacts/design_continuity_hardening.md`](design_continuity_hardening.md) ★1–★7  
**Prior G10 locks (do not reopen):** [`.jes/artifacts/design_g10_materials_frame.md`](design_g10_materials_frame.md) ★1–★8  

**Checkpoint base:** commit **`39b85b2`** (audit report) on top of **`1b4769f`** (Continuity + G10). Prior tag: `checkpoint-g3`.  
**Target tag (Engineer, after CLI PASS):** `checkpoint-continuity-polish`

**Workflow:** Claude implements **all S1–S7 in one cut** (tests stay green) + tests + report → Engineer → **Cursor review** → **CLI re-walk** → commit/tag only if Engineer asks. **Do not commit or push unless asked.**

S8 (G13) is **verification-gated**: add the CLI/unit probe; **no code fix** unless the probe reproduces the original failure. If it does not reproduce, close G13 as “fixed by G10 ★2” with the regression test only.

---

## 0. Why this cut

```text
Physics PASS (margen 9.1, 180 N vs 19.8 N)
  + Continuity CTA "Declara empuje ≥ 3.3 N"
  + ¿qué motores…? → LLM
  + definir motores on dron → robot torque wizard
```

Root class (audit): local ranking / missing force-* / missing list-* / missing domain gate / stale session field — same shape Continuity Hardening already fixed once. No new subsystem.

```text
audit CLOSED
        │
        ▼
CLI Polish IMPLEMENTATION  ← you are here (this contract)
        │
        ▼
Cursor review → CLI re-walk
        │
        ▼
checkpoint-continuity-polish
```

---

## 1. Locked Engineer decisions (§4.7 audit)

| # | Decision | Lock |
|---|---|---|
| 1 | G9-B suppression threshold | **Per-motor:** `per_motor_max_thrust_n >= thrust_per_motor_needed_n` **and** `sim_status == "pass"`. Do **not** switch to total `empuje_disponible` vs `empuje_requerido` in this cut. |
| 2 | G18 fix location | **Orchestrator-side gate (a)**. Do **not** add `vehicle_type` to `IntentResolver` signature. |
| 3 | G19 reasoning executability | **Relabel only** the two motor-related suggestion labels so they name working phrases. **No** general “any suggestion is re-enterable” mechanism. |
| 4 | G13 | **S8 gated.** CLI/unit probe first. Code fix only if reproduced. |
| 5 | Checkpoint name | `checkpoint-continuity-polish` (Engineer tags after CLI PASS). |
| 6 | Packaging | **One IC** covering S1–S7. S8 verification-gated in this same contract. |

---

## 2. Out of scope (hard)

| Forbidden |
|---|
| G9-A (`catalog_ref` read in catalog-gap computation) |
| Changing `orchestrator.build_startup_context` catalog-gap **computation** (S1 ranks the already-computed gap; does not rewrite `find_motors_for_requirements` inputs) |
| Retarget (a) clear-and-reopen (Continuity ★2) |
| Thrust under-requirement validation gate (Continuity ★7) |
| G10 materials / keywords / mutation SoT / `domains/materials.py` |
| DSE axis for motors / new exploration grid |
| Conversation Engine / Decision Engine / dual-dispatch rewrite |
| IntentResolver signature change (`vehicle_type`) |
| Library JSON edits (`library/motores`, `library/materiales`) |
| Impl C / System Map file edits (propose caveat text in report only) |
| Weakening tests to pass |
| Commit / push unless Engineer asks |

---

## 3. Slice requirements

Implement in any order except **S7 after S1 and S2** (S7 CTA text names the S1 PASS branch and the S2 `list_motors` phrase). Prefer one cut if tests stay green.

Reuse existing helpers. Do **not** invent a new authority module unless a tiny local helper is clearly thinner than duplicating three call sites.

### S1 — G9-B catalog-gap ranking (PASS + declared thrust covers floor)

**Files:** `src/jarvis/core/project_continuity.py`. Caller `orchestrator.py` already passes `project_state`; **no new parameter** unless a unit-test seam is required.

**Rules:**

1. Before `elif motor_catalog_gap:` wins `next_useful_step`, evaluate:
   - `sim_status == "pass"` (already derived in this function), **and**
   - declared `per_motor_max_thrust_n` from `project_state.current_parameters` is present and `>= physical_requirements["thrust_per_motor_needed_n"]`.
2. If both hold: **demote**, do not suppress. Keep `motor_catalog_gap` in `evidence` (existing lines ~112–113). Do **not** let it win `next_useful_step`. Fall through to the existing PASS branch.
3. If `sim_status != "pass"` **or** declared thrust is absent **or** declared thrust `<` floor: catalog-gap branch **still wins** (regression guard — under-declared PASS must remain actionable).
4. Do **not** read `catalog_ref` (G9-A).
5. Do **not** change how `catalog_gap` is computed in `build_startup_context`.

**CTA copy on demotion:** S1 may leave the existing PASS copy unchanged; S7 extends it. S1 acceptance is: `next_useful_step` must **not** contain `"Declara empuje"` when the guard holds.

### S2 — G16-A/B + G19 list-motors global (G10 ★8 parity)

**Files:** `intent_resolver.py`, `orchestrator.py`, `motor_catalog_assist.py`, `param_definition_session.py`.

**G16-A — global `list_motors`:**

1. Add `LIST_MOTORS_PATTERNS` (narrow, same family as `LIST_MATERIALS_PATTERNS` / `is_list_motors_phrase`): `que motores`, `motores disponibles|tenemos|hay`, `catalogo de motores`, `lista(r) de motores`. Must still match after `_normalize_text` (strips `?` and diacritics).
2. Add `"list_motors"` to `IntentType`. Check it in `_resolve_strong_action_intent` **before** ANALYZE / question fallback — same position as `LIST_MATERIALS_PATTERNS`.
3. Add `_handle_list_motors()` mirroring `_handle_list_materials()`:
   - **0 LLM**
   - If an active project exists, filter with existing `build_motor_catalog_suggestions` / `derive_kv_prop_filters` / `find_motors_for_requirements`.
   - If no project or no filters: unfiltered `default_library.list_motors()` dump.
4. Soft-interrupt `intent == "list_motors"` in **every** place `list_materials` is already intercepted:
   - `DEFINE_MISSING_PARAMETERS` branch
   - iterate-interim branch (if `list_materials` is there)
   - IDLE dispatch
5. Wizard stays open when listed from DEFINE_MISSING (same as materials / Continuity ★5).

**G16-B — CTA dedupe:**

1. Single owner of “Elige un número…”. Keep it in `question` only.
2. `format_motor_catalog_suggestions` `message` must **not** append that CTA when used alongside a separate `question` (`_offer_catalog_help`).
3. Grep other callers (`iterate_interactive_session.py`, etc.). Do not introduce the same duplication there; do not silently strip a CTA from a caller that has no `question`.

### S3 — G18 aerial vs terrestrial `definir motores`

**Files:** `orchestrator.py` only (pre-dispatch). **Do not** change `IntentResolver` signature.

**Rules:**

1. When the resolved action is `define_missing_parameters` with `reason == "missing_transmission_parameters"` **and** the active project’s vehicle domain is **aerial** (`dron` / `uav` via existing `VEHICLE_TYPE_ALIASES` / the same `_domain_kind` used in `interactive_session.py`):
   - **Do not** start the terrestrial wizard (`per_actuator_torque_nm`, `wheel_radius_m`, `gear_ratio`).
2. Redirect to the **aerial motors** path:
   - If propulsion/motors acquisition is still the pending architecture gap: existing `_continue_block_acquisition` / `missing_propulsion_parameters` (`motor_count`, `per_motor_max_thrust_n`).
   - If architecture is already complete: open motors **component** DEFINE_MISSING / the same iterate-on-component path `definir propulsion` already uses — **never** terrestrial transmission.
3. Phrases like `definir torque` / `definir rueda` / `definir transmisión` on aerial: still must **not** open a silent terrestrial session as if this were a rover. Prefer an honest refuse (“este proyecto es aéreo…”) **or** the aerial motors redirect if the phrase is motors-shaped. Do not invent a terrestrial project.
4. Terrestrial projects (`robot` / `coche` / `rover`): `definir motores` **must still** open `missing_transmission_parameters`. Regression-guarded.

### S4 — G17 force-motors

**Files:** `orchestrator.py` (`_handle_component_description`).

**Rules:**

1. When `"motors" in expected_keys` and inferred specs are all `generic_component`, call `infer_component_for_key(user_input, "motors", registry=aerial_registry)`. If completeness `!= "low"`, bind **motors**.
2. Run **before** (or win over) force-propellers. Continuity ★4 gate stays: do **not** force propellers on motor-shaped text while motors is pending.
3. Phrases `"1x 2306 2400KV 50W"` and `"4x 2306 2400KV 50W"` in composite `["motors","propellers"]` → `"Motores registrados"` (or equivalent motors write), **not** a motors re-prompt, **not** `"Hélices registradas"`.
4. Singleton `expected_keys=["motors"]` + same phrases also force-binds.
5. Do **not** loosen `_looks_clearly_propeller_shaped`. Bare `"10x4.5"` still FN-019 / G14.

### S5 — G12 / FN-013 stale pending vs fresh block

**Files:** `orchestrator.py` (`_try_reprompt_active_block_declaration`).

**Rules:**

1. After proving `block_key == _next_pending_block(...)[0]`, do **not** blindly use `session.pending_param_definitions[0]` for the brief body.
2. If `pending[0]` is set and **not** in `BLOCK_TO_COMPONENTS[block_key]`, ignore stale pending. Re-derive the pending keys for `block_key` the same way `_set_pending_next_block` / `start_define_missing_params` would for a fresh open of that block. Build the brief from that fresh list.
3. If pending **is** in the named block’s components: keep FN-013 “don’t restart, don’t wipe `collected_params`”.
4. Do **not** implement retarget (a). This is same-target freshness, not cross-block jump.
5. Result: `definir bateria` after propulsion-complete (including via DSE/`component_sync`) → label **and** body are energy/battery-shaped.

### S7 — G19 Continuity CTA bridge + reasoning labels

**Depends on:** S1, S2.

**Files:** `project_continuity.py`, `reasoning_layer.py`.

**Rules:**

1. When `motor_catalog_gap` **wins** `next_useful_step` (genuine / not demoted by S1), append discoverability (Spanish, existing phrases):
   - `'qué motores tenemos'` (or `'que motores tenemos'`) **and**
   - `'explora opciones'`
2. When S1 **demotes** the gap (PASS + declared covers floor), extend the PASS `next_why` (and optionally `next_step`) per audit §4.5 — honest BOM note, **not** an imperative `"Declara empuje ≥ X"`:
   ```text
   next_step: Diseño en PASS (margen {margin:.1f}×) — puedes iterar, explorar
              alternativas, o vincular una pieza real del catálogo.
   next_why:  No hay gaps físicos bloqueantes. Nota de catálogo: {motor_catalog_gap}
              — di 'qué motores tenemos' para ver el catálogo, o 'explora opciones'
              para que Jarvis pruebe configuraciones que sí tengan SKU.
   ```
   Wording may be tightened for CLI length but **must** name both phrases and must **not** use the physics floor as a “declare thrust” command.
3. In `reasoning_layer.py`, the two motor-related `_build_declarative_next_steps` labels:
   - `"Definir empuje por motor real"`
   - `"Modelar unidad de potencia"`
   Relabel so the **visible text is a phrase the resolver already handles** after S2 (e.g. mention `qué motores tenemos` / `explora opciones` / `definir propulsion`). Do **not** add a new intent, numbered picker, or generic suggestion-execution engine.

### S8 — G13 verification (no code unless reproduced)

**Files:** `tests/` only unless probe fails.

**Rules:**

1. Add a unit (and/or documented CLI) probe: iterate material slot + `"PVC 400g"` → extracts `"pvc"` and computes impact (not opaque slug `pvc 400g`).
2. If **PASS:** close G13 as fixed by G10 ★2; no `iterate_interactive_session.py` change.
3. If **FAIL:** stop and ask Engineer before coding. Allowed fix if approved: `_estimate_material_impact` KeyError branch re-runs `_extract_material_from_text` once. No shared parse-helper redesign in this cut.

---

## 4. Acceptance tests (required)

Create `tests/test_cli_polish.py` (slice comments OK). Minimum:

| ID | Slice | Assert |
|---|---|---|
| T1 | S1 | `build_project_continuity` + sim PASS + `per_motor_max_thrust_n=30` + `thrust_per_motor_needed_n=3.3` + non-empty `motor_catalog_gap` → `next_useful_step` does **not** contain `"Declara empuje"`; gap still in evidence |
| T2 | S1 | Same but `per_motor_max_thrust_n=2.0` (under floor) → catalog-gap **still wins** `next_useful_step` |
| T3 | S2 | `resolve_intent("que motores tenemos en el catalogo?") == "list_motors"`; same with `¿qué motores hay?` |
| T4 | S2 | IDLE `handle_user_text` + `_FakeLLM` that raises → list-motors phrase (with and without `?`) returns deterministic list; LLM never called |
| T5 | S2 | DEFINE_MISSING thrust wizard + `"que motores tenemos en el catalogo?"` → list, wizard still open |
| T6 | S2 | `_offer_catalog_help` `message` does not contain `"Elige un número"`; `question` does |
| T7 | S3 | Aerial `dron` project + `"definir motores"` → **not** `missing_transmission_parameters` / no torque-N·m prompt |
| T8 | S3 | Terrestrial `robot`/`rover` + `"definir motores"` → still `missing_transmission_parameters` |
| T9 | S4 | Composite `["motors","propellers"]` + `"1x 2306 2400KV 50W"` / `"4x 2306 2400KV 50W"` → writes `motors` |
| T10 | S4 | Same composite + `"10x4.5"` → still propellers (G14/FN-019) |
| T11 | S5 | Session `pending_param_definitions=["motors"]` while `_next_pending_block` is energy; `"definir bateria"` → battery-shaped body, not motors |
| T12 | S7 | Genuine (non-demoted) `motor_catalog_gap` → next_step/why mentions motores list phrase **and** `explora opciones` |
| T13 | S7 | Demoted PASS case → no `"Declara empuje"`; mentions list-motors and `explora opciones` |
| T14 | S8 | `"PVC 400g"` in iterate material extract/impact → `"pvc"` + numeric impact (or Engineer-stop if this fails in live code) |

Also run, **no regressions:**

```text
python -m pytest tests/test_cli_polish.py tests/test_continuity_hardening.py tests/test_g10_materials_frame.py tests/test_project_continuity.py tests/test_fn019_bare_propeller_size.py -q
python -m pytest -q
```

Full suite must stay green (baseline 1753 at `1b4769f`; expect +T1–T14).

---

## 5. Deliverables

| Artifact | Path |
|---|---|
| Implementation report | `.jes/artifacts/implementation_report_cli_polish.md` |
| Tests | `tests/test_cli_polish.py` |
| Code | per slices above |

Report must include: files touched; per-slice behavior; test commands + results; S8 probe result (fixed-by-G10 vs still-open); residual risks; proposed System Map caveat text (not applied).

---

## 6. CLI acceptance (after Cursor PASS)

| # | Probe | Expected |
|---|---|---|
| 1 | `¿que motores tenemos en el catalogo?` at IDLE | Deterministic list, 0 LLM |
| 1b | Same mid thrust wizard, with `?` | Same list; wizard stays open |
| 2 | Post-DSE apply, PASS, margin > 2, declared thrust ≥ floor | Status next-step is PASS-framed; **no** `"Declara empuje ≥ {floor}"` |
| 2b | PASS but declared thrust **under** floor | Catalog gap **still** wins next-step |
| 3 | `definir motores` on `dron` | Aerial motors/propulsion path — **never** `"par de torsión"` |
| 3b | `definir motores` on `robot` | Terrestrial transmission wizard unchanged |
| 4 | `4x 2306 2400KV 50W` in motors+propellers wizard | `"Motores registrados"` |
| 4b | `10x4.5` same wizard | Hélices / propellers (G14) |
| 5 | `definir bateria` after propulsion complete (incl. DSE path) | Energy label **and** battery body |
| 6 | Actionable catalog_gap | CTA names `explora opciones` and list-motors |
| 7 | `plastico 550g` frame acquisition | Unchanged G10 PASS |
| 8 | Iterate material `"PVC 400g"` | Extract+impact OK **or** stop for Engineer if reproduced |

Overall: fresh dron BOM walk **without** mandatory `cancelar` except intentional retarget.

---

## 7. Review criteria (Cursor)

| Gate | Fail if |
|---|---|
| G9-B | PASS + declared ≥ floor still shows `"Declara empuje"` as next_step |
| G9-B over-suppress | Under-floor declared thrust loses catalog-gap next_step |
| G16-A | Trailing `?` or IDLE still hits analyze/LLM for list-motors |
| G16-B | Duplicate `"Elige un número"` in message+question |
| G17 | `"4x 2306 2400KV 50W"` still re-prompts without `motores` |
| G14 | Motor-shaped phrase writes hélices; or `"10x4.5"` no longer propellers |
| G18 | Aerial `definir motores` opens torque/rueda wizard |
| G18 terrestrial | Robot `definir motores` no longer transmission |
| G12 | Battery header + motors body after stale pending |
| G19 | Actionable gap CTA omits list-motors / `explora opciones` |
| G10 | `domains/materials.py` / force-frame / mutation SoT changed |
| ★2 / ★7 | Retarget (a) or thrust gate added |
| G9-A | `catalog_ref` read invented in this cut |
| Tests | T1–T14 missing or suite regressions |

**PASS / PASS WITH NOTES / FAIL.**

---

## 8. Prompt block for Claude (copy-paste)

```text
Read and execute:
.jes/artifacts/implementation_contract_cli_polish.md

Audit (authority, do not re-litigate locks):
.jes/artifacts/investigation_cli_polish_audit.md

Implement S1–S7 in one cut. S8 = probe only; no G13 code unless probe fails — then STOP and ask.

Do NOT: G9-A catalog_ref, IntentResolver vehicle_type signature, G10 materials,
retarget (a), thrust gate, Decision/Conversation Engine, library JSON, commit/push.

Add tests/test_cli_polish.py (T1–T14).
Write .jes/artifacts/implementation_report_cli_polish.md
Run pytest full suite; report counts.
```

---

## 9. Stop conditions

Stop and ask Engineer if:

1. S1 cannot demote the gap without changing catalog-gap **computation** or reading `catalog_ref`.
2. S3 cannot avoid terrestrial wizard on aerial without changing `IntentResolver` signature **and** the orchestrator gate has no viable redirect (existing `missing_propulsion_parameters` / `_continue_block_acquisition` / iterate-on-component).
3. S4 force-motors reintroduces G14 (hélices write) and cannot be ordered without loosening `_looks_clearly_propeller_shaped`.
4. S8 `"PVC 400g"` iterate probe **fails** (do not silently patch).
5. Any slice appears to need a new architectural subsystem.
