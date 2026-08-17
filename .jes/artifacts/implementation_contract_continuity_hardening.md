# Implementation Contract — Continuity Hardening

**Project:** Jarvis  
**Date:** 2026-08-15  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)  

**Status:** READY FOR ENGINEER → send to Claude  

**Type:** Product behavior — Acquisition Target Authority (phased) restoring session continuity on BOM walk.

**Closes / advances:** G14 🔴 · G15 · G12 · G8 · G11 — [`.jes/artifacts/cli_findings_post_catalog_bind_v1.md`](cli_findings_post_catalog_bind_v1.md)

**Design authority (CLOSED ★1–★7):** [`.jes/artifacts/design_continuity_hardening.md`](design_continuity_hardening.md)  
**Investigation:** [`.jes/artifacts/investigation_continuity_hardening.md`](investigation_continuity_hardening.md)  
**Review of investigation/design:** [`.jes/artifacts/implementation_review_continuity_hardening_investigation.md`](implementation_review_continuity_hardening_investigation.md)

**Checkpoint base:** tag **`checkpoint-g3`**  
**Working tree:** G10 materials code may be present — **do not modify** `domains/materials.py` / frame keywords / mutation SoT / list-materials to “help” Continuity.

**Workflow:** Claude implements **all four slices** (or Slice 1 first if blocked — prefer all in one cut if tests stay green) + tests + report → Engineer → **Cursor review** → **CLI BOM walk** → commit/tag only if Engineer asks. **Do not commit or push unless asked.**

---

## 0. Why this cut

```text
No Acquisition Target Authority
  → force-*/intercept/preempt check "K ∈ local candidate set"
  → not "K = gap currently narrated to the user"
```

Smoking gun: motors wizard + `1x 2306 2400KV 50W` → “Hélices registradas” (G14).  
Plus sticky DEFINE_MISSING (G12/G8), iterate self-preempt (G11), catalog help contradictions (G15).

G10 PVC / checkpoint-g10 remain **deferred** until Continuity CLI walk works.

```text
★ CLOSED
        │
        ▼
Continuity Hardening IMPLEMENTATION  ← you are here
        │
        ▼
Cursor review → CLI BOM walk
        │
        ▼
resume G10 PVC / checkpoint-g10 · G13 …
```

---

## 1. Locked decisions (do not re-open)

| ★ | Requirement |
|---|---|
| ★1 | One contract · **4 slices** · order 1→4 |
| ★2 | G12/G8: **refuse (b)** — one honest line; keep wizard; only `cancelar` clears for retarget |
| ★3 | G11: **reorder owns-input before strong-intent** + **extend** owns-input to strategy-selection (`variable` set, `operation` still `None`) |
| ★4 | G14: **no force-propellers while `motors` still pending** unless phrase is clearly propeller-shaped; first-declared wins if multiple forces apply |
| ★5 | Deterministic list-motors escape in `ParamDefinitionSession.answer` |
| ★6 | Filtered (or explicitly labeled) max in `format_no_thrust_candidate_message` |
| ★7 | **No** under-requirement thrust validation gate |

---

## 2. Out of scope (hard)

| Forbidden |
|---|
| Retarget (a) clear-and-reopen path for `definir <X>` mid-wizard |
| Thrust under-req gate (★7) |
| G9 Continuity `catalog_ref` honesty |
| G10 materials / keywords / mutation / list-materials edits |
| G13 opaque `PVC 400g` iterate parse |
| Catalog Impl C / Conversation Engine / dual-dispatch rewrite |
| Editing System Map files (propose text in report only; optional doc PR later) |
| Weakening tests to pass |
| Commit / push unless Engineer asks |

---

## 3. Slice requirements

Prefer a small shared helper (e.g. extend `core/acquisition_target.py` or add `core/acquisition_target_authority.py`) **only if** it keeps call sites thin. Do **not** invent a Conversation Engine. Slice 1 may stay local in `orchestrator.py` if a helper is premature — but Slices 2+ should share refuse logic.

### Slice 1 — G14 composite force gate (★4)

**Files:** primarily `src/jarvis/core/orchestrator.py` (`_handle_component_description` force-propellers / force-frame blocks). Optional: tiny helper for “may force key K?”.

**Rules:**

1. When `expected_keys` is a **singleton** `{K}`, existing FN-019 / G10 force-K behavior remains (bare `10x4.5` still forces propellers; frame force still works).
2. When `expected_keys` is **composite** and includes both `motors` and `propellers`:
   - **Do not** call `infer_component_for_key(..., "propellers")` / accept forced propellers while `motors` is still in `expected_keys`, **unless** the phrase is **clearly propeller-shaped**.
3. **Clearly propeller-shaped** (deterministic, no LLM) — implement narrowly, e.g. one of:
   - matches real propeller size heuristic (plausible diameter inches, not model-number-as-pitch), **or**
   - contains propeller keywords (`hélice`/`helices`/`prop`/… already in domain), **or**
   - other equivalent documented predicate in the report.
4. Motor-shaped phrases like `"1x 2306 2400KV 50W"` / `"4x 2306 2400KV"` must **never** write propellers / return `"Hélices registradas."` while motors pending.
5. Prefer binding / prompting for **motors** (first-declared in propulsion block) when the phrase is motor-shaped or ambiguous.
6. Do **not** loosen `extract_propeller_properties` globally in a way that breaks FN-019 bare sizes — prefer gating the **force** call site.

### Slice 2 — G12/G8 refuse policy (★2)

**Files:** `orchestrator.py`; optional small helper module.

**Rules:**

1. While DEFINE_MISSING / component wizard is open for target `Y`, if user input clearly names a **different** valid acquisition target `X` (`definir frame`, `definir sensors`, engineering phrases that today fall into UX-C silence — at minimum declare-block mentions + the G8 engineering/explore phrases that currently get swallowed into the same brief fallback):
   - **Do not** silently re-show `Y`'s brief as if nothing was understood.
   - Respond with **one honest refuse line** naming `Y` and instructing `cancelar` before switching to `X` (Spanish, consistent tone with existing CLI).
   - **Keep** session / `collected_params` / mode unchanged (no clear, no reopen).
2. Same policy shared for G12-shaped declare retargets and G8-shaped engineering/explore absorbs that currently land on `_handle_component_description`'s `elif expected_keys:` silent brief — one code path, not two divergent copy blocks if avoidable.
3. `cancelar` remains the only session-clearing recovery (existing C-034 path).
4. Do **not** port `_should_preempt_iterate_wizard` verbatim into DEFINE_MISSING.

### Slice 3 — G15 list-motors + messaging (★5, ★6)

**Files:** `param_definition_session.py`, `motor_catalog_assist.py`.

**★5 list-motors:**

- Narrow patterns inside `ParamDefinitionSession.answer` (not only IDLE `intent_resolver`), e.g. `que motores` / `qué motores` / `motores disponibles` / `catálogo de motores` / `catalogo de motores` (finalize without stealing numeric thrust answers).
- Return deterministic catalog listing via existing assist formatters / `list_motors` (or suggestions builder output) — **0 LLM**.
- Does not clear the wizard; user can continue with a value after reading the list.

**★6 messaging:**

- `format_no_thrust_candidate_message` must not present unfiltered catalog max as if it were the filtered search max.
- Preferred: compute max from the **same filtered candidate universe** used by `build_motor_catalog_suggestions` / `find_motors_for_requirements` for that turn (pass filters or precomputed max into the formatter).
- Alternative allowed: keep unfiltered max **only if** the string explicitly labels it as unfiltered / full-catalog.

### Slice 4 — G11 iterate preempt (★3)

**Files:** `orchestrator.py` (`_should_preempt_iterate_wizard`, `_iterate_owns_component_input`).

**Rules:**

1. Consult an extended “wizard owns this input” predicate **before** the strong-intent ∈ `_ITERATE_PREEMPT_INTENTS` short-circuit.
2. Extend ownership to cover at least:
   - existing: `DEFINE` + `step == 2` (and motor_suggestions as today)
   - **new:** strategy-selection when `iteration_draft.variable` is set and `operation` is still `None` (G11-B bare material / component-shaped answers)
3. Natural answers like `"cambiar a pvc"`, `"cambiar material"`, `"pvc"` at those owned steps must **not** clear the wizard.
4. Genuine new strong actions that are **not** owned answers (e.g. `simula`, `explora opciones`, `calcula` when not answering a slot) must still preempt.
5. Do **not** remove `"iterate"` from `_ITERATE_PREEMPT_INTENTS` as the primary fix (★3 rejects (c)).
6. Do **not** weaken G10 frame material keywords.

---

## 4. Acceptance tests (required)

Create `tests/test_continuity_hardening.py` (or split by slice if clearer). Minimum:

| ID | Slice | Assert |
|---|---|---|
| T1 | 1 | Composite `expected_keys=["motors","propellers"]` + `"1x 2306 2400KV 50W"` → **not** propellers / not `"Hélices registradas"`; motors path or honest motors re-prompt |
| T2 | 1 | Same composite + bare `"10x4.5"` → still FN-019 propellers OK |
| T3 | 1 | Singleton `expected_keys=["propellers"]` + `"10x4.5"` still forces propellers |
| T4 | 2 | Battery/component wizard open + `"definir frame"` → refuse message mentions cancelar / active target; session mode + expected target unchanged |
| T5 | 2 | Same open wizard + `"reducir payload"` (or equivalent G8 phrase) → refuse, not silent battery brief-only absorb without acknowledgment |
| T6 | 3 | Mid numeric thrust wizard + `"que motores tenemos en el catalogo"` → deterministic list, 0 LLM, wizard still open |
| T7 | 3 | `format_no_thrust_candidate_message` with filtered empty set does not claim an unfiltered max that contradicts (or labels unfiltered explicitly) |
| T8 | 4 | Iterate step with `variable=material`, strategy step (`operation=None`) + `"pvc"` → no preempt |
| T9 | 4 | Same + `"cambiar a pvc"` → no preempt; wizard continues |
| T10 | 4 | Iterate open + `"simula"` (or clear strong non-answer) → still preempts |

Also run: FN-011…021, FN-019, `test_propulsion_composite_wizard_flow.py`, iterate session tests, `test_g10_materials_frame.py` — **no regressions**.

---

## 5. Deliverables

| Artifact | Path |
|---|---|
| Implementation report | `.jes/artifacts/implementation_report_continuity_hardening.md` |
| Tests | `tests/test_continuity_hardening.py` (+ helpers if needed) |
| Code | per slices above |

Report must include: files touched; per-slice behavior; test commands + results; residual risks; proposed System Map caveat text (not applied).

---

## 6. CLI acceptance (after Cursor PASS)

```text
# Slice 1
propulsion open (motors+propellers)
1x 2306 2400KV 50W  → motors (or honest motors re-prompt), NEVER "Hélices registradas"

# Slice 2
battery wizard open
definir frame  → refuse + cancelar hint; still on battery until cancelar

# Slice 3
thrust wizard, no filtered candidates
ayúdame a elegir  → coherent max vs filters
que motores tenemos  → deterministic list

# Slice 4
iterate material strategy/step-2
cambiar a pvc / pvc  → stays in wizard

# Overall
new project → propulsion → battery → frame without needing cancelar except intentional retarget
```

---

## 7. Review criteria (Cursor)

| Gate | Fail if |
|---|---|
| G14 | Motor-shaped phrase still writes hélices under composite expected_keys |
| FN-019 | Bare propeller size broken |
| G12/G8 | Silent brief re-show without refuse; or retarget/clear implemented |
| G11 | `cambiar a pvc` / bare `pvc` still preempts owned steps |
| G10 | materials modules changed without need |
| ★7 | Thrust gate added |
| Tests | T1–T10 missing or suite regressions |

**PASS / PASS WITH NOTES / FAIL.**

---

## 8. Prompt block for Claude (copy-paste)

```text
Read and execute:
.jes/artifacts/implementation_contract_continuity_hardening.md

Design CLOSED ★1–★7:
.jes/artifacts/design_continuity_hardening.md

Investigation:
.jes/artifacts/investigation_continuity_hardening.md

Implement all 4 slices (G14 → G12/G8 refuse → G15 → G11).
Do NOT modify G10 materials modules.
Do NOT implement retarget (a) or thrust under-req gate.
Add tests/test_continuity_hardening.py (T1–T10).
Write .jes/artifacts/implementation_report_continuity_hardening.md
Do not commit/push unless asked.
```

---

## 9. Stop conditions

Stop and ask Engineer if Slice 1 cannot prevent G14 without either (a) a Conversation Engine, or (b) regressing FN-019 bare propeller sizes, or (c) editing G10 materials vocabulary.
