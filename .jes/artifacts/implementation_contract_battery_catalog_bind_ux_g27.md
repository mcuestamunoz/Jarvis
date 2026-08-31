# Implementation Contract — Battery Catalog UX + G27 Hardening (IC 2 / Project Closure arc)

**Project:** Jarvis  
**Date:** 2026-08-30  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)

**Status:** READY FOR CLAUDE

**Type:** Live battery catalog pick + bind in CLI (propeller-class UX), plus **G27** hardening so free-text `"LiPo 6S 10000mAh"` never silently becomes `6 Wh`. Closes the energy traceability gap on top of the already-proven bind→calc chain.

**Investigation:** [`.jes/artifacts/investigation_report_project_closure_assembly_ready.md`](investigation_report_project_closure_assembly_ready.md) — §4–§5, §11 IC 2 outline  
**Prior IC:** [`.jes/artifacts/implementation_contract_requirements_closure.md`](implementation_contract_requirements_closure.md) — **CLOSED** (`checkpoint-requirements-closure`)  
**Checkpoint base:** tag **`checkpoint-requirements-closure`** · commit `e986a58`  
**Product base:** **`v0.3.0`** (unchanged until Engineer decides bump)

**Arc position:** IC **2 of 3**. IC 3 = Closure policy + propeller `sku_resolved`. **G24 out of scope.**

**Workflow:** Claude implements **Bat-0 trace (report §1) → Bat-1…Bat-8** + implementation report → Cursor review → CLI probe → optional Engineer energy walk → commit/tag if Engineer asks.

---

## 0. Engineer ratification (locked)

| ★ | Decision |
|---|---|
| **★1 (arc)** | Checkpoint IC 1 before IC 2 — **`checkpoint-requirements-closure`** is base. |
| **★4 (investigation)** | Battery pick UX mirrors propeller-bind shape (`_offer/_apply`, numbered list, `bind_*_from_catalog`). |
| **★5 (investigation)** | G27 fix **narrow** to battery chemistry/cell-count/mAh free-text — do **not** change `_parse_value`'s generic behavior for unrelated iterate variables. |
| **★7 (investigation)** | Battery family: `freeform_ok` today; catalog bind is **evidence-strong**, not required for ASSEMBLY READY in IC 2. |

**IC 2 gate (Engineer, locked):**

> Catalog-bound battery via live CLI pick → `battery_capacity_wh` / `battery_mass_kg` / `battery_cell_count` from SKU → **`calcular`** yields coherent `autonomía_min` (real Wh, not 6 Wh). G27 scenario **never** silently sets `6 Wh` for `"6S 10000mAh"`.

**Philosophy locks (inherit from closure arc):**

- **Do not invent SKUs** — lists from `ComponentLibrary` only.
- **Reuse `bind_battery_from_catalog` + `set_battery_component`** — no parallel binder.
- **Catalog bind bypasses G27** — pick path must not go through `_parse_value` first-digit regex.
- **Do not weaken tests** — disclose any assertion change explicitly.

---

## 1. Problem / intent

### 1.1 As-is (investigation-confirmed)

| Layer | Status |
|---|---|
| `bind_battery_from_catalog` + `set_battery_component` | **Complete** — test-callable only; **zero** production call sites outside `catalog_bind.py` |
| Calc / autonomy / discharge | **Complete** once bound — `calculation_engine`, `electrical_compatibility`, `_energy_evidence` |
| CLI pick UX | **Missing** — user declares `"LiPo 6S 5000mAh"` freeform or bare Wh via param wizard |
| G27 | **Open** — `semantic_intent_adapter._parse_value` grabs first digit (`6` from `6S`) → `battery_capacity_wh=6.0` |

**Seed reference:** `lipo_6s_10000mah` → `energy_wh: 222.0`, `cells: 6`, `capacity_mah: 10000` (`library/baterias/_datos.json`).

### 1.2 Target (to-be)

```text
energy block / battery gap
  → ayúdame a elegir
  → numbered battery SKUs (from library, Bat-2 authority)
  → pick N
  → bind_battery_from_catalog(sku) → set_battery_component
  → calcular
  → autonomía_min reflects real Wh (e.g. 222 Wh for lipo_6s_10000mah)
  → estado: ✓ battery: lipo_6s_10000mah [lipo_6s_10000mah] · energy evidence
```

**G27 parallel target:**

```text
free-text "aumentar bateria a LiPo 6S 10000mAh" (unbound or post-bind)
  → resolve to ~222 Wh OR refuse/clarify
  → NEVER battery_capacity_wh=6.0 from "6S"
  → if catalog-bound, catalog_ref must not be silently destroyed by a rejected parse
```

### 1.3 Implementation order (mandatory — Engineer discipline)

Claude **must** document the as-is trace in the implementation report **§1 (Bat-0)** before coding UX:

1. **Trace** existing bind → writer → calc → autonomy → readiness (investigation §5 call graph — verify, don't assume).
2. **UX** — session field, assist module, orchestrator offer/apply, brief copy.
3. **G27** — battery-specific parse/refuse path.
4. **Prove** — tests + CLI probe + autonomy coherence after `calcular`.

---

## 2. Locked predicates (mirror propeller IC — adapt for battery)

Reuse module-level helpers from propeller/motor pattern in `orchestrator.py`:

```text
_wants_catalog_help(spec) :=
    stub/absent OR (spec exists AND catalog_ref is None)
```

**Dispatch (energy / composite wizard):**

- Gate battery help-choose on `"battery" in expected_keys AND _wants_catalog_help(battery_spec)`.
- When `battery_suggestions` already on session, numbered pick applies.
- **Do not** starve battery branch with bare `"battery" in expected_keys` if energy block keeps static expected_keys (same ★4 lesson as propellers).

**IDLE fallback (optional but recommended — mirror Prop-5):**

- After motor/propeller IDLE assists return `None`, try `_try_start_assisted_battery_help` when energy/battery wants catalog help.
- Guard: do not open battery picker when battery already catalog-bound.

---

## 3. Suggestion authority (Bat-2 — locked)

**★1 for batteries:** suggestions from **`ComponentLibrary` only** — no SKU hardcode in orchestrator.

Recommended authority (investigation-aligned):

| Option | Approach | Verdict |
|---|---|---|
| **A** | `list_batteries()` capped at N (10 entries — honest full v1 catalog) | **Acceptable default** |
| **B** | `find_batteries(min_energy_wh=…)` when `parsed_constraints.autonomy_min` + known power enables a defensible floor | Optional enhancement |
| **C** | Hardcode `lipo_6s_10000mah` in orchestrator | **Rejected** |

Implement **`battery_catalog_assist.py`** (new module):

- `BatterySuggestion` TypedDict: `idx`, `name`, `energy_wh`, `cells`, `capacity_mah`, `mass_g`, `chemistry`
- `build_battery_catalog_suggestions(project_state, *, library, limit=5)` — uses `list_batteries()` or `find_batteries` with **documented** optional filter; never invent rows
- `format_battery_catalog_suggestions(suggestions)` — numbered list + CTA
- Import `is_help_choose_phrase` / `match_suggestion_by_input` from `motor_catalog_assist` (same ★2 as propellers)

**Empty list policy:** if filter yields zero, honest message — not a silent fallback to freeform Wh=6.

---

## 4. Session / schema (Bat-1)

- Add `battery_suggestions: list[dict] = Field(default_factory=list)` on `InteractiveSessionState` (additive, runtime-only — same tier as `motor_suggestions` / `propeller_suggestions`).
- Document in `state_manager.py` comment — not persisted.

---

## 5. Orchestrator wiring (Bat-3 / Bat-4)

Mirror propeller methods:

| Method | Behavior |
|---|---|
| `_offer_component_battery_catalog` | Build suggestions, set `battery_suggestions`, clear `motor_suggestions`/`propeller_suggestions`, return `component_description_prompt` |
| `_apply_component_battery_catalog_pick` | `bind_battery_from_catalog(sku)` → `set_battery_component` → save → clear suggestions → advance wizard / `_set_pending_next_block` |
| `_try_start_assisted_battery_help` | IDLE help-choose when battery wants catalog help |

**Apply path (locked):**

```python
spec = bind_battery_from_catalog(suggestion["name"])
updated_state = set_battery_component(
    project_state, spec, spec.properties["battery_capacity_wh"].value
)
```

**No new refresh helper.** Do **not** re-call motor/propeller writers unless investigation trace proves a gap (unlikely — battery voltage for OP already flows through `set_battery_component` / existing P2-1 bridge).

**Priority in composite energy wizard:** if both battery and motors incomplete, **document chosen precedence** in report (recommend: battery after propulsion block complete — energy block order from architecture; if both in same `expected_keys`, battery-only if motors not in list).

---

## 6. Acquisition brief (Bat-5)

Update `acquisition_brief.py`:

- Extend catalog bullet gate from `("motors", "propellers")` to include **`"battery"`**.
- Copy: `'ayúdame a elegir' para ver candidatos numerados del catálogo` for battery gap.

---

## 7. G27 hardening (Bat-6 — same checkpoint)

**Root cause (locked):** `semantic_intent_adapter._parse_value` first-number regex on LLM `valor` when variable is `battery_capacity_wh`.

**Scope (★5 — locked):**

- Add battery-specific resolution **before** or **instead of** bare `_parse_value` when the target param is `battery_capacity_wh` (or when user text matches battery chemistry patterns).
- Acceptable outcomes for `"LiPo 6S 10000mAh"`:
  1. **Deterministic Wh** from mAh × nominal voltage / standard LiPo formula **or** library SKU match (`lipo_6s_10000mah`), **or**
  2. **Refuse/clarify** — never silent wrong Wh.
- **Never** `6.0` Wh from cell count alone.
- **Post-bind:** rejected/clarified parse must not clear `catalog_ref` or overwrite bound Wh without explicit user confirm (align with `invalidate_diverged_catalog_refs` spirit).

**Do not** change `_parse_value` for non-battery variables.

**Preferred implementation locus (investigate, pick smallest):**

- Dedicated helper e.g. `parse_battery_capacity_wh_from_text(text) -> float | None` in a small module or `semantic_intent_adapter` battery branch
- Optional: match normalized text to catalog SKU name patterns (`6s` + `10000mah` → `lipo_6s_10000mah`) via library lookup — **no new JSON rows**

Regression anchor: [`.jes/artifacts/cli_finding_g27_battery_6s_parsed_as_6wh.md`](cli_finding_g27_battery_6s_parsed_as_6wh.md) — expected **~222 Wh** for 6S 10000mAh seed.

---

## 8. Tests (Bat-7 — new `tests/test_battery_catalog_bind_ux.py`)

Minimum **8 tests** (adjust names in report):

1. Component wizard help-choose → battery list (includes `lipo_6s_10000mah` or project-relevant SKU)
2. Pick → `catalog_ref` set, `battery_capacity_wh` = SKU `energy_wh`, real `battery_mass_kg`
3. After pick + recalc path → `autonomy_min` uses real Wh (not heuristic-only if mass changed)
4. IDLE help-choose when battery freeform unbound (if Bat-3 IDLE implemented)
5. IDLE noop when battery already catalog-bound
6. Propulsion/motor help-choose still wins when both incomplete (if applicable fixture)
7. **G27:** `"LiPo 6S 10000mAh"` → Wh ≈ 222 **or** refuse — **never** 6.0
8. **G27 post-bind:** bound SKU + bad free-text follow-up → `catalog_ref` preserved or explicit divergence handling — not silent 6 Wh

Plus targeted regressions: `test_catalog_bind_v1.py`, `test_phase2_lookup_operating_point.py` (battery bridge), `test_requirements_closure.py` unchanged.

---

## 9. CLI probe (Bat-8 — `scripts/cli_probe_battery_catalog_bind_ux.py`)

Target **6/6 PASS** — real `handle_user_text` turns, no state-patch bind shortcuts:

| Step | Action | Pass |
|---|---|---|
| 1 | Create/minimal project with propulsion bound, battery stub | baseline |
| 2 | Open battery wizard / energy gap → `ayúdame a elegir` | list includes `lipo_6s_10000mah` |
| 3 | Pick SKU | `catalog_ref`, `battery_capacity_wh=222` (or seed value) |
| 4 | `calcular` | `autonomía_min` coherent with 222 Wh / known motor power — **not** 6 Wh |
| 5 | `estado` | battery line shows `[sku]` resolved; energy subsystem evidence |
| 6 | G27 phrase on freeform project | ≠ 6 Wh; refuse or correct Wh |

Optional step 7 (document in report if implemented): post-bind G27 phrase does not corrupt bound SKU.

---

## 10. Files — expected touch set

| File | Change |
|---|---|
| `src/jarvis/schemas/action_schema.py` | Bat-1 `battery_suggestions` |
| `src/jarvis/core/state_manager.py` | comment |
| `src/jarvis/core/battery_catalog_assist.py` | **new** Bat-2 |
| `src/jarvis/core/orchestrator.py` | Bat-3/4 |
| `src/jarvis/core/acquisition_brief.py` | Bat-5 |
| `src/jarvis/llm/semantic_intent_adapter.py` and/or new small parser | Bat-6 G27 |
| `src/jarvis/core/param_definition_session.py` | Bat-6 **only if** ingest path needs choke point |
| `tests/test_battery_catalog_bind_ux.py` | Bat-7 |
| `scripts/cli_probe_battery_catalog_bind_ux.py` | Bat-8 |

**Must NOT change:**

- `resolve_operating_point`, P2-1 seeds, propeller/motor catalog assist behavior
- `_requirements_declared` / IC 1 semantics
- `project_closure._bom_sku_resolved` propeller line (IC 3)
- G24 DSE, ESC catalog, version bump
- `library/baterias/_datos.json` (unless investigation proves missing seed — unlikely)

---

## 11. Explicit non-goals

- IC 3 policy docs / propeller `sku_resolved` fix
- Requirements / G26 changes
- Auto-refresh sim after bind (user still `calcular` — same as propeller IC)
- Battery catalog expansion beyond existing 10 SKUs
- H5 ESC catalog
- Engineer manual CLI walk **required** — probe + tests are gate; manual walk optional for comfort (energy/autonomy feel)

---

## 12. Acceptance (Cursor review)

**PASS** if:

- Bat-0 trace documented in implementation report with file:line
- Live pick → bind → `set_battery_component` → real Wh/mass/cells on disk
- Probe **6/6**; new tests green; full suite green
- G27 scenario never produces `6.0` Wh for 6S 10000mAh class input
- Motor/propeller/propulsion IC 1 regressions intact
- No weakened tests without disclosure

**FAIL** if:

- Hardcoded SKU list in orchestrator
- Parallel `bind_battery_*` helper duplicates `catalog_bind.py`
- Generic `_parse_value` changed globally for G27
- Fake PASS via invented battery rows or silent 6 Wh

---

## 13. Queue after IC 2

```text
IC 2 PASS + probe 6/6
  ↓
Engineer optional checkpoint (checkpoint-battery-catalog-bind-ux)
  ↓
Cursor: IC 3 Closure policy + propeller sku_resolved
```

---

**End of contract.**
