# Implementation Contract — Propeller Catalog Bind UX

**Project:** Jarvis  
**Date:** 2026-08-21  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)

**Status:** READY FOR CLAUDE

**Type:** Live propeller catalog pick + bind (G21-class UX) so Phase 2 P2-1 can reach `exact_operating_point` from CLI without test-only `bind_propeller_from_catalog`.

**Investigation:** [`.jes/artifacts/investigation_report_propeller_catalog_bind_ux.md`](investigation_report_propeller_catalog_bind_ux.md) — **CLOSED**  
**Investigation review:** [`.jes/artifacts/investigation_review_propeller_catalog_bind_ux.md`](investigation_review_propeller_catalog_bind_ux.md) — **PASS WITH NOTES**  
**Checkpoint base:** tag **`checkpoint-phase2-p2-1`** · commit `e82b8a1`

**Workflow:** Claude implements **Prop-1 → Prop-7 in order** + report → Cursor review → CLI walk (fallback → exact) → commit/tag if Engineer asks.

---

## 0. Engineer ratification (locked)

| ★ | Decision |
|---|---|
| **★1** | Suggestion authority = `match_motor_propeller` filter. **No** P2-1 SKU hardcode (Option C dropped). |
| **★2** | New module `propeller_catalog_assist.py` — import shared `is_help_choose_phrase` / `match_suggestion_by_input` from `motor_catalog_assist.py` (no duplication). |
| **★3** | Add `propeller_suggestions: list[dict]` on `InteractiveSessionState` (additive). |
| **★4** | **Must fix** motors help-choose starvation: gate **both** motor and propeller help-choose on live “wants catalog help” predicates — not bare `"motors" in expected_keys`. |
| **★5** | After propeller catalog bind → `set_propeller_component` then **explicit re-call** `set_motor_component` when motors already has `catalog_ref`. No new refresh helper. |
| **★6** | Scope **A+B**: composite wizard help-choose + IDLE re-bind for freeform/unbound propellers. |
| **★7** | Engineer CLI walk to exact OP does **not** require battery step for ★6 dataset. |

**Additional locks:**

- Reuse **`bind_propeller_from_catalog` + `set_propeller_component`** — no parallel binder.
- Do **not** change `resolve_operating_point` match rules / ★6 seeds / `v1_max_thrust`.
- Do **not** touch G24 / G26 / G27 / ESC / battery catalog pick / version bump.
- Do **not** break G21 motor help-choose / IDLE motor re-bind.
- `propulsion_resolution` stays a **JSON string** (hashable) via existing `set_motor_component`.
- Zero weakened tests.

**Architecture constraint:** Minimum change that unlocks CLI exact OP. Prefer mirroring G21 call shapes (`_offer_component_*` / `_apply_component_*`).

---

## 1. Problem / intent

Today: after binding `emax_rs2205s_2300`, CLI shows `fallback_operating_point · 10.042 N`. Freeform hélices never set `catalog_ref`. Exact path only via probe.

**Target:**

```text
ayúdame a elegir  (propellers pending, motors catalog-bound)
  → numbered list via match_motor_propeller
  → pick N → bind_propeller_from_catalog → set_propeller_component
  → set_motor_component(re-bound motors spec)   # OP re-resolve
  → estado: exact_operating_point · manufacturer_test · 9.7086 N
```

---

## 2. Locked predicates (★4 — non-negotiable)

Reuse the same incompleteness notion already used after motor pick (`still_missing`):

```text
_is_stub_or_absent(spec) :=
    spec is None OR (completeness or "low") == "low"
```

**Wants catalog help** (for help-choose / pick dispatch):

```text
_wants_catalog_help(spec) :=
    _is_stub_or_absent(spec)
    OR (spec is not None AND catalog_ref is None)
```

Rationale: stub/absent needs definition; freeform high-completeness without `catalog_ref` is the G21 upgrade-to-SKU case (motors today, propellers under ★6 B).

**Dispatch order in `_handle_component_description` (replace bare membership gate):**

```text
if "motors" in expected_keys and _wants_catalog_help(motors) and is_help_choose_phrase(...):
    → motor catalog offer
elif "motors" in expected_keys and session.motor_suggestions and pick matches:
    → motor catalog apply   # only while motors still wants help OR suggestions live
elif "propellers" in expected_keys and _wants_catalog_help(propellers) and is_help_choose_phrase(...):
    → propeller catalog offer
elif "propellers" in expected_keys and session.propeller_suggestions and pick matches:
    → propeller catalog apply
```

**When both motors and propellers want help:** motors wins (existing Continuity motors-first precedent).

**When motors catalog-bound (`catalog_ref` set) and propellers wants help:** propeller branch reachable — this is the starvation fix.

Clear the other family's suggestions when offering a new list (e.g. offering propellers clears `motor_suggestions` and vice versa) to avoid cross-pick ambiguity.

---

## 3. Slice Prop-1 — Schema

`InteractiveSessionState` (`action_schema.py`):

```python
propeller_suggestions: list[dict] = Field(default_factory=list)
```

Additive only. Persist/clear via the same runtime session patterns as `motor_suggestions`.

**Acceptance:** model loads; existing sessions without the field default to `[]`.

---

## 4. Slice Prop-2 — `propeller_catalog_assist.py`

New module next to `motor_catalog_assist.py`.

### 4.1 Types

`PropellerSuggestion` TypedDict (minimum keys): `idx`, `name` (sku), plus optional display fields (`diameter_in`, `pitch_in`, `mass_g`) for formatting.

### 4.2 `build_propeller_catalog_suggestions(project_state, *, limit=5) -> list[PropellerSuggestion]`

1. If bound motor has `catalog_ref.family == "motor"`:  
   candidates = propellers where `default_library.match_motor_propeller(motor_sku, prop_sku)` is true.  
   Sort deterministic (e.g. by name); apply `limit`.
2. If **no** catalog-bound motor:  
   return **`[]`** and let the offer path show an honest message — **do not** dump the full propeller catalog (G22 honesty; Cursor review note).  
   Message shape (example): *"Primero elige un motor del catálogo; luego podré listar hélices compatibles."*
3. Never invent SKUs; never special-case `emax_rs2205s_2300`.

### 4.3 `format_propeller_catalog_suggestions(suggestions) -> str`

Numbered list mirroring motor formatter tone.

### 4.4 Imports only

`is_help_choose_phrase`, `match_suggestion_by_input` from `motor_catalog_assist` — **do not copy** their implementations.

**Acceptance:** with `emax_rs2205s_2300` bound, suggestions include `hq_5045_bn` and `gf_5045x3` (order not byte-locked). With no motor bound, empty list.

---

## 5. Slice Prop-3 — Component wizard wiring

### 5.1 Priority-gated help-choose (★4)

In `_handle_component_description`, replace the unconditional:

```python
if "motors" in expected_keys:
```

with the §2 predicates. Add the propeller `elif` branch symmetrically.

### 5.2 `_offer_component_propeller_catalog(session, expected_keys)`

Mirror `_offer_component_motor_catalog`: build suggestions, set `propeller_suggestions`, clear `motor_suggestions`, return interactive prompt with numbered list (or honest empty message).

### 5.3 `_apply_component_propeller_catalog_pick(suggestion, expected_keys)`

1. `bind_propeller_from_catalog(suggestion["name"])`  
2. `set_propeller_component(ps, spec)`  
3. **★5:** if `components["motors"].catalog_ref` is set, re-load motors spec + `power_w` and call `set_motor_component` again (same pattern as P2-1 probe).  
4. Clear `propeller_suggestions`.  
5. Advance wizard via `still_missing` (same completeness rule as motor pick).  
6. Return `component_description_saved` + follow-up prompt.

**Acceptance:** composite wizard, motors already bound → `ayúdame a elegir` → propeller list (not motor list). Pick → `catalog_ref` on propellers + `propulsion_resolution` JSON parses to `exact_operating_point` for ★6 pair (no battery required).

---

## 6. Slice Prop-4 — covered inside Prop-3 step 3

No separate file — ensure tests assert the re-call side effects (`per_motor_max_thrust_n` / evidence type).

---

## 7. Slice Prop-5 — IDLE re-bind (★6 B)

Extend FN-005 IDLE dispatch after `_try_start_assisted_motor_help` returns `None` because motor already has `catalog_ref` (or otherwise motors do not want help):

Add `_try_start_assisted_propeller_help()`:

- Active project required.  
- Propellers `_wants_catalog_help` true.  
- Motors **not** `_wants_catalog_help` for stub — recommend require motors present and **not stub** (prefer catalog-bound motor so suggestions non-empty; if motor freeform without catalog_ref, motor IDLE path should have won first).  
- Open COMPONENT sub-mode with `pending_missing_params` including `propellers` (singleton `["propellers"]` is fine) and offer propeller catalog.

When propellers already has `catalog_ref`, return `None` (no picker noise).

**Acceptance:** freeform propeller, catalog-bound motor, IDLE `ayúdame a elegir` → propeller picker, not bare `estado`.

---

## 8. Slice Prop-6 — Acquisition brief

`acquisition_brief.py`: extend the catalog bullet to `key in ("motors", "propellers")` and update the comment that currently says propellers have no bind path.

**Acceptance:** propeller Brief mentions `ayúdame a elegir`.

---

## 9. Slice Prop-7 — Tests + CLI probe

### 9.1 New tests (`tests/test_propeller_catalog_bind_ux.py`)

1. Wizard help-choose after motors bound → propeller list (not motors).  
2. Pick → `catalog_ref` + exact OP re-resolve (★6 pair).  
3. IDLE freeform unbound propeller → picker.  
4. IDLE no-op when propeller `catalog_ref` set.  
5. Both incomplete → motors list wins.  
6. Freeform hélices never yields `exact_operating_point`.  
7. No motor bound → empty suggestions / honest message (no full dump).  
8. Regression: `tests/test_g21_catalog_bind_ux.py` + `tests/test_phase2_lookup_operating_point.py` green unchanged.

### 9.2 Probe `scripts/cli_probe_propeller_catalog_bind_ux.py`

Real wizard turns only (no `bind_propeller_from_catalog` state patch):

```text
1. Bind emax_rs2205s_2300 via ayúdame a elegir → N
2. estado → fallback · 10.042 N
3. ayúdame a elegir → list includes hq_5045_bn
4. pick → catalog_ref
5. estado → exact_operating_point · 9.7086 N
6. Spot-check G21 motor help-choose still works on fresh project
```

---

## 10. Forbidden

- Hardcoded P2-1 propeller lists per motor SKU  
- Growing `motor_catalog_assist.py` with propeller domain logic (beyond importing shared helpers)  
- New `refresh_propulsion_resolution` helper  
- Changing OP resolver / DSE scoring / Continuity ranking formulas  
- Battery/ESC catalog UX  
- G24–G27 / version bump  
- Dumping full propeller catalog when no motor is bound  

---

## 11. Implementation report (required)

`.jes/artifacts/implementation_report_propeller_catalog_bind_ux.md`:

1. Files changed  
2. Behavior changed / unchanged  
3. ★1–★7 compliance (especially ★4 predicate + ★5 re-call)  
4. Tests + commands + results  
5. CLI probe result  
6. Remaining risks  

---

## 12. Exit criterion

Complete when Prop-1…Prop-7 green, Cursor review PASS (or PASS WITH NOTES), and Engineer CLI can demonstrate **fallback → exact** without probe patches.

### Engineer definitive acceptance (locked — review must verify)

**CLI (product path only — no state patch, no manual `bind_propeller_from_catalog`):**

```text
emax_rs2205s_2300
        ↓
fallback_operating_point · 10.042 N
        ↓
ayúdame a elegir
        ↓
hq_5045_bn
        ↓
catalog_ref
        ↓
exact_operating_point · 9.7086 N
```

**Prop-5 IDLE matrix (must stay green — watch for regressions that steal normal IDLE):**

| Motor | Hélice | `ayúdame a elegir` |
|---|---|---|
| stub | stub | **motor** |
| catalog | stub | **hélice** |
| catalog | freeform | **hélice** |
| catalog | catalog | **nada** (fall through) |
| freeform | stub | **motor** |
| none | none | **motor / existing flow** |

Prop-5 must not become an IDLE cascade that hijacks unrelated turns. Cursor review must explicitly check this matrix against tests + dispatch order.

---

## 13. Queue after implementation

```text
Claude implements
  ↓
Cursor review
  ↓
Engineer CLI walk (new or continuing project)
  ↓
checkpoint (e.g. checkpoint-propeller-catalog-bind)
  ↓
Then consider: G27 / G26 / G24 / version bump — Engineer call
```

---

**End of contract.**
