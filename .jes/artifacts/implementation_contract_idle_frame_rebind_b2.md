# Implementation Contract — IDLE frame rebind (B2)

**Project:** Jarvis  
**Date:** 2026-09-04  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** IMPLEMENTED · REVIEWED **PASS WITH NOTES** · CLOSED (suite **2250**)  
**Review:** [implementation_review_idle_frame_rebind_b2.md](implementation_review_idle_frame_rebind_b2.md)  
**Report:** [implementation_report_idle_frame_rebind_b2.md](implementation_report_idle_frame_rebind_b2.md)  
**Parents:**
- [investigation_contract_idle_component_reacquisition.md](investigation_contract_idle_component_reacquisition.md)
- [investigation_report_idle_component_reacquisition.md](investigation_report_idle_component_reacquisition.md)
- [investigation_review_idle_component_reacquisition.md](investigation_review_idle_component_reacquisition.md) — **PASS WITH NOTES**
- [engineer_ratification_idle_component_reacquisition.md](engineer_ratification_idle_component_reacquisition.md)

**Type:** Acquisition / Continuity UX — reopen **existing** frame catalog offer after architecture 4/4 and after bind.  
**Not** MEASURE. **Not** Structure PASS change. **Not** B3 (motors/props/battery). **Not** name→SKU bind. **Not** arms↔motors coherence.

**Baseline:** Structure block CLOSED @ suite **2229** · Catalog Foundation IC-3 frame offer/apply already shipped

**Buy (locked):** **B2 frame-first** named-mention rebind bridge.

---

## 0. You

- Reuse `_offer_component_frame_catalog` / `_apply_component_frame_catalog_pick` (IC-3) — **no** parallel binder or list builder.
- Prefer a **sibling IDLE dispatch** for the locked phrase set (review N2). Do **not** generalize `_try_start_acquisition_from_mention` / `_continue_block_acquisition` to “any satisfied component.”
- Do **not** extend the bridge to motors / propellers / battery (B3 out).
- Do **not** implement display-name → SKU resolution (review N1 out of slice).
- Do **not** add arms↔motors / configuration↔motor_count Continuity warnings.
- Do **not** change `_structure_evidence` / `_derive_*` / Structure PASS / ASSEMBLY_READY eligibility.
- Do **not** bump version.
- Full suite green. Zero weakened tests.

---

## 1. Intent

```text
IDLE, architecture 4/4, frame already catalog-bound (or freeform):
  User: "cambiar frame" | "definir frame" | "ayúdame a elegir frame"
        ↓
  DEFINE_MISSING + pending_missing_params=["frame"] + MISSING_COMPONENT_DEFINITION
        ↓
  _offer_component_frame_catalog  (existing numbered list)
        ↓
  pick N → _apply_component_frame_catalog_pick
        ↓
  root replaced from SKU; frame_* children cleared then upserted from new SKU
        ↓
  (no auto calcular/simular — same as other component picks)
```

Bare `"ayúdame a elegir"` (no frame token) **unchanged** — motor→propeller→battery triage, including T1 underspec first.

---

## 2. Locked Engineer decisions (★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **B2** frame-first |
| 2 | Phrases | `cambiar frame`, `definir frame`, `ayúdame a elegir frame` (+ accent/ASCII variants; synonyms below) |
| 3 | Children on re-pick | **Clear all** `parent_key=="frame"` children (or the four locked keys), **then** upsert from `frame_part_specs_from_catalog(new_sku)` |
| 4 | Coherence arms↔motors | **Debt** — no Continuity note in this IC |
| 5 | Name→SKU | **Out** — free-text / list+pick only |

---

## 3. Locked behavior

### 3.1 Phrase detector (new small helper)

Add a narrow predicate (prefer `frame_catalog_assist.py` next to existing helpers), e.g. `is_frame_rebind_phrase(user_input) -> bool`:

**True** when normalized text matches **either**:

1. **Help-choose + frame noun:** contains help-choose soft tokens (`ayudame` + `elegir|escoger`) **and** a frame noun token (`frame` | `chasis`).  
   - Examples: `ayúdame a elegir frame`, `ayudame a escoger el chasis`.
2. **Change/define verb + frame noun:** contains (`cambiar`|`cambia`|`definir`|`define`|`modificar`|`modifica`) **and** (`frame`|`chasis`), without requiring other component nouns to win.  
   - Examples: `cambiar frame`, `definir frame`, `modificar el chasis`.

**False** for:

- Bare `ayúdame a elegir` / `ayúdame a escoger` (no frame/chasis token) — must fall through to existing FN-005 chain.
- `cambiar batería` / `definir motores` / `optimizar estructura` / `cambiar material` — must **not** match.
- Do **not** treat bare `estructura` as frame rebind (iterate owns `estructura`).

Keep the matcher word-boundary safe (no `frame` inside unrelated tokens).

### 3.2 IDLE dispatch (orchestrator)

**Before** FN-005 bare help-choose **or** immediately after it but **before** iterate / FN-014 fallthrough — order must guarantee:

```text
IF IDLE and is_frame_rebind_phrase(user_input):
    open frame rebind offer
    return
ELIF IDLE and is_help_choose_phrase(user_input):
    existing motor → propeller → battery chain
    ...
```

Recommended: check **frame rebind first**, then bare help-choose. That way `"ayúdame a elegir frame"` never opens motors.

Opening rebind:

1. Require an active project (`_safe_active_project()`); else existing “no project” error path.
2. Set session:
   - `mode = DEFINE_MISSING_PARAMETERS`
   - `pending_missing_reason = MISSING_COMPONENT_DEFINITION`
   - `pending_missing_params = ["frame"]`
   - `pending_define_missing = False` (same shape as motor underspec / battery IDLE assist)
3. Call `_offer_component_frame_catalog(session, ["frame"])` — **even if** frame already has `catalog_ref` (this is the whole point: bypass `_wants_catalog_help`).

Do **not** call `_continue_block_acquisition` / do **not** require `_next_pending_block` non-None.

### 3.3 Offer path exception for rebind

Today frame help-choose inside `_handle_component_description` is gated on `_wants_catalog_help`. The **IDLE rebind entry** must call `_offer_component_frame_catalog` **directly** (as in §3.2), so that gate is irrelevant for this entry.

If the user is already in DEFINE_MISSING with `expected_keys` containing `frame` and says help-choose, existing IC-3 behavior may still use `_wants_catalog_help`. **Minimum for this IC:** IDLE locked phrases work when bound. Optional polish (same PR if tiny): when `expected_keys` includes `frame` and `is_frame_rebind_phrase` / help-choose, allow offer even if `catalog_ref` set — only if it does not disturb other families. Prefer the IDLE direct offer if dual-path risks scope creep.

### 3.4 Apply path — children clear (G-N4 catalog half)

In `_apply_component_frame_catalog_pick`, **after** loading project state and **before or after** root `set_frame_material`, but **before** upserting new parts:

1. **Remove** every component in `design_properties.components` where `parent_key == "frame"` (Fase 1: the four `frame_*` keys). Prefer a small writer helper e.g. `clear_frame_part_children(project_state) -> project_state` in `component_writers.py` — single legal mutation point.
2. Then upsert from `frame_part_specs_from_catalog(sku)` as today.
3. TBS / SKU with empty part dict → root only, **zero** leftover `└` children.

Root replace semantics of `set_frame_material` stay as today.

No auto `calcular` / `simular`.

### 3.5 Unchanged

- Free-text frame overwrite (global intercept) — still legal; still may orphan if user never re-picks catalog (pre-existing G-N4 free-text half — **not** required to clear on free-text in this IC).
- Bare help-choose triage order.
- Iterate for non-frame phrases.
- Structure PASS / BOM N1 `└` rendering / G-N1 free-text root+parts.

---

## 4. Tests (mandatory)

New file preferred: `tests/test_idle_frame_rebind_b2.py` (or extend `test_frame_catalog_bind_ux.py` if cleaner — either OK).

All from **clean IDLE** after architecture complete + frame catalog-bound (Armattan). Reconstruct like the investigation fixture; do not rely on Engineer workspace.

| # | Case |
|---|---|
| T1 | IDLE `"cambiar frame"` → opens numbered frame catalog (`frame_suggestions` non-empty); mode DEFINE_MISSING; params `["frame"]` |
| T2 | IDLE `"definir frame"` → same |
| T3 | IDLE `"ayúdame a elegir frame"` → **frame** list, **not** motor list |
| T4 | Pick Armattan index after TBS-bound (or freeform) project → `catalog_ref.sku == armattan_rooster_5in` + four `frame_*` children |
| T5 | Bound Armattan → rebind pick TBS → **no** `frame_arm`/`plate`/`cage`/`standoff` keys remain |
| T6 | IDLE bare `"ayúdame a elegir"` with underspec motor still opens **motor** assist (N4 regression) — not frame |
| T7 | IDLE `"cambiar batería"` / `"cambiar motores"` still do **not** open frame catalog (B3 not smuggled) |
| T8 | Full suite green |

Optional but valuable: `"ayudame a elegir el chasis"` matches detector.

---

## 5. Files (expected touch set)

| File | Change |
|---|---|
| `src/jarvis/core/frame_catalog_assist.py` | `is_frame_rebind_phrase` (+ export) |
| `src/jarvis/core/orchestrator.py` | IDLE frame-rebind dispatch; apply-path clear-then-upsert |
| `src/jarvis/core/component_writers.py` | `clear_frame_part_children` (or equivalent) |
| `tests/test_idle_frame_rebind_b2.py` (or extend existing) | T1–T7 |

Do not edit Continuity copy for arms↔motors. Do not widen FN-014 generally.

---

## 6. Explicit non-goals

- B3 multi-family rebind  
- Display-name / `"frame Armattan Quads Rooster 5\""` → SKU  
- Soft coherence Continuity  
- Clearing orphans on **free-text** root rewrite (debt remains unless trivial and tested — default **out**)  
- Structure PASS / MEASURE / Conversation Engine  
- Version bump  

---

## 7. Done criteria

- Behavior §1–§3 held  
- T1–T7 + full suite green  
- Implementation report at `.jes/artifacts/implementation_report_idle_frame_rebind_b2.md`  
- No forbidden scope  

---

## 8. After implement

Cursor writes implementation review. Engineer CLI smoke optional: ASSEMBLY READY project → `cambiar frame` → list → pick Armattan → `estado` shows `[sku]` + `└` / or TBS with no orphans.
