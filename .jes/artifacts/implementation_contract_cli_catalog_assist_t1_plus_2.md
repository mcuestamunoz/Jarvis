# Implementation Contract — CLI catalog-assist T1+2 (named G22 second pass)

**Project:** Jarvis  
**Date:** 2026-09-02  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Cursor (Engineer: “vamos con T1+2”)  
**Reviewer:** Cursor against this IC after the edit

**Status:** RATIFIED by Engineer proceed (2026-09-02). Implement this file only.

**Type:** Named G22 filter relax on the **underspec motor** offer. **Not** a second ranker. **Not** Tier 3. **Not** battery propose. **Not** the 15 min vs 5 min energy walk.

**Evidence:**
- [investigation_report_cli_catalog_assist_misfit_propose.md](investigation_report_cli_catalog_assist_misfit_propose.md) Gate C + §7
- [investigation_review_cli_catalog_assist_misfit_propose.md](investigation_review_cli_catalog_assist_misfit_propose.md) Note 2
- [implementation_contract_cli_catalog_assist_t1.md](implementation_contract_cli_catalog_assist_t1.md) (shipped)

**Checkpoint base:** live tree after T1 + feasibility autonomy-below. Do not revert those.

**Walk fixture (tmp tests only):** T1 combo — `sunnysky_r2305_2500` + `gf_5045x3` + `lipo_6s_10000mah`, `motor_count=2`, sim fail, `bound_sku_underspec`. Do **not** mutate Engineer `workspace/`.

**Honest scope vs last CLI:** `autonomia-15min` has thrust **covering**. T1+2 **does not fire** there. This IC is the deferred Block Closure misfit (thrust underspec), not energy propose.

---

## 0. You

- Edit only files listed in §5.
- Reuse `find_motors_for_requirements`. **No** new scoring. **No** silent KV-only fallback inside `build_motor_catalog_suggestions`.
- G22 stays: default `build_motor_catalog_suggestions` empty-when-strict-empty. `test_g22_strict_empty_when_prop_excludes_kv_matches` **unchanged intent**.
- Do not change `_derive_overall`, `ASSEMBLY_READY`, Block Closure, G24-B, catalog JSON, DSE mixed deltas.
- Do not invent SKUs, W, or minutes. Do not bind propeller in the same turn (investigation §7 option **a**, not **b**).
- Full suite green. Zero weakened G21/G22 tests.

---

## 1. Intent

When the bound motor is **thrust-underspec** and Jarvis offers the numbered list (`ayúdame a elegir` / Continuity), T1 (current thrust + inherited KV + prop inch) stays **first**.

A **named** second pass then lists additional motors from the **same** D8 search with **both** inherited filters dropped (`kv=None`, `prop_inch=None`, still `min_thrust_n` from `derive_physical_requirements`).

CLI must say the filters were relaxed. A candidate that fails `default_library.match_motor_propeller(candidate_sku, bound_prop_sku)` must carry the frankenstein line (prop may need re-bind). Picking still binds **motor only**.

Copy must **not** claim sim PASS, bloque CERRADO, or “5″ family” for a ±1″ tolerance match (`emax_eco_ii_2207_1700` vs `gf_5045x3`).

When the bound SKU **covers** thrust: no second pass (G21 intact). First-time unbound pick: G22 only.

---

## 2. Locked behavior

### 2.1 Exact relax (Gate C)

One second pass only:

```text
find_motors_for_requirements(min_thrust_n=<thrust_per_motor_needed_n>, kv=None, prop_inch=None)
```

Do **not** add a drop-KV-only pass or drop-prop-only pass (Gate C: drop-prop empty; drop-KV still short of PASS on the fixture). Deduplicate by `name` against the T1 list. Reindex `1..n` across T1 then extras.

Limits: T1 up to 5, extras up to 5 (total ≤ 10). Same D8 sort as today.

New helper in `motor_catalog_assist.py` (name free, e.g. `build_underspec_motor_offer`). Optional dict keys on suggestions: `relaxed: bool`, `prop_mismatch: bool`. Bound prop SKU from `design_properties.components.propellers.catalog_ref.sku`. If no bound prop, `prop_mismatch=False` for all.

`build_motor_catalog_suggestions` **byte-intent unchanged** (no relax flag that silent-defaults on).

### 2.2 Offer copy — `_offer_component_motor_catalog` when `bound_motor_sku_is_underspec`

If T1+extras non-empty, **do not** use the G22-empty `format_no_thrust_candidate_message` merely because T1 is empty.

Locked structure (Spanish verbatim headers):

```text
Candidatos del catálogo para este espacio de diseño:
  {T1 lines, existing _format_candidate_line detailed}

Filtros relajados (sin KV ni pulgadas de hélice del combo actual) — no es un combo motor+hélice+batería:
  {extra lines; if prop_mismatch append:}
   ⚠ la hélice vinculada puede no encajar; habría que redefinir propellers
```

If T1 empty, omit the first section (or print one line `Ninguno con KV/hélice actuales.`) then the relaxed section. If both empty: keep today’s honest empty (`format_no_thrust_candidate_message` with **strict** kv/prop filters).

Trailing CTA: same as today (`Elige un número…` / per_motor_max_thrust_n). Plus one line:

```text
Elegir no garantiza sim PASS.
```

Unbound / covering: existing `format_motor_catalog_suggestions` only — no relaxed header.

### 2.3 Pick

Existing `_apply_component_motor_catalog_pick`. If `prop_mismatch` is true, append:

```text
 Nota: la hélice vinculada puede no ser compatible; redefine propellers.
```

Do not clear propeller `catalog_ref`. Do not open the propeller picker this turn.

### 2.4 Continuity rank-2 (underspec)

Keep T1 underspec **first** (T1 names / empty-G22 sentence).

When extras exist, **replace** the T1-only “Candidatos: {names}” sentence with:

```text
El motor vinculado ya no cubre el empuje (≥ {N} N/motor). Candidatos (KV/hélice actuales): {t1_names}. Filtros relajados (sin KV ni pulgadas heredados): {relax_names}. Di 'ayúdame a elegir'. Elegir no garantiza sim PASS. Un candidato relajado puede exigir otra hélice.
```

`t1_names` / `relax_names` = up to 5 each. If T1 empty: `Candidatos (KV/hélice actuales): ninguno.` If extras empty: **keep the T1 locked string unchanged**.

Call the new helper from Continuity when `_underspec_live` (same as the offer). Do not feed relaxed SKUs into `resolve_motor_catalog_surface` / GAP (G22 honesty).

### 2.5 Out of this offer

DSE `build_motor_catalog_suggestions` call sites, iterate wizard, battery picker, `definir motor` when **covering**.

---

## 3. Tests (mandatory)

| File | What |
|---|---|
| `tests/test_g21_g22_catalog_bind_ux.py` | G22 empty-strict tests **unchanged**. G21 covering noop **unchanged**. |
| `tests/test_cli_catalog_assist_t1.py` | Underspec IDLE still opens a list. Covering still no motor picker. |
| `tests/test_cli_catalog_assist_t1_plus_2.py` **new** | Underspec fixture: message contains `Filtros relajados`; contains `sunnysky_r2205_2500` (T1); contains a thrust-only extra (e.g. `sunnysky_v4006_740`); that extra’s line contains the hélice warning; does **not** say `Diseño validado` / `CERRADO` as a claim of the pick. Covering bound SKU: **no** `Filtros relajados`. `build_motor_catalog_suggestions` on G22 empty fixture still `[]`. |
| `tests/test_project_continuity.py` | Underspec + extras: next_step contains `Filtros relajados` and `ayúdame a elegir`; T1 candidate still named. Underspec without extras (if you stub empty relax): T1 string still valid. |

Optional: `scripts/cli_probe_cli_catalog_assist_t1.py` print the new header. Not a substitute.

---

## 4. Non-goals

```text
Tier 3 joint motor+prop+battery
Battery bound_sku_underspec / filtering build_battery_catalog_suggestions
Silent G22 fallback / changing find_motors_for_requirements
G24-B / DSE mixed deltas / Conversation Engine
Option B ERF / _derive_overall / Block Closure rollup
autonomia-15min covering SKU → motor list
H5 / Catalog Foundation / library JSON expansion
```

---

## 5. Files

| File | Role |
|---|---|
| `src/jarvis/core/motor_catalog_assist.py` | Helper + format |
| `src/jarvis/core/orchestrator.py` | Underspec offer uses helper; pick note |
| `src/jarvis/core/project_continuity.py` | Rank-2 copy when extras |
| `tests/test_cli_catalog_assist_t1_plus_2.py` | New |
| `tests/test_project_continuity.py` | Continuity extras |
| `tests/test_cli_catalog_assist_t1.py` | Keep green (adjust only if copy collides) |
| `scripts/cli_probe_cli_catalog_assist_t1.py` | Optional |
| `docs/IMPLEMENTATION_TASKS.md` | Sync |
| `.jes/state/engineering_state.json` | Sync |

---

## 6. Acceptance

- Underspec help-choose: T1 then named relax; `v4006` (or any `match_motor_propeller` false vs `gf_5045x3`) has the hélice warning; pick does not unbind prop.
- G22 default search still empty on the 10″ / 2400 KV fixture.
- Covering SKU: no relax header, no motor re-offer.
- Continuity names both bands when extras exist; no PASS/CERRADO claim.
- Suite green.

---

## 7. After you finish

Write `implementation_report_cli_catalog_assist_t1_plus_2.md`.
