# Implementation Review — CLI Polish Bundle (S1–S7 + S8 gated)

**Date:** 2026-08-18  
**Reviewer:** Cursor (Implementation Review)  
**Contract:** [implementation_contract_cli_polish.md](implementation_contract_cli_polish.md)  
**Report:** [implementation_report_cli_polish.md](implementation_report_cli_polish.md)  
**Audit:** [investigation_cli_polish_audit.md](investigation_cli_polish_audit.md)

**Verdict: PASS WITH NOTES**

---

## Scope check

| Gate | Result |
|---|---|
| S1–S7 present | ✅ |
| S8 probe only, no G13 code unless reproduced | ✅ did not reproduce; T14 locks G10 ★2 |
| G9-A / `catalog_ref` | ✅ not touched |
| Catalog-gap *computation* in `build_startup_context` | ✅ unchanged |
| IntentResolver signature / `vehicle_type` | ✅ unchanged; S3 is orchestrator gate |
| G10 materials / force-frame / mutation SoT | ✅ not touched |
| Retarget (a) / thrust gate (★7) | ✅ not present |
| Library JSON | ✅ not touched |
| Tests T1–T14 | ✅ `tests/test_cli_polish.py` (15 tests; T9b extra) |
| Targeted re-run | ✅ `test_cli_polish` + continuity + G10 + project_continuity + FN-019 → **63 passed** |

Implementer claims full suite 1768; spot suite green under this review. Pre-existing assertion updates (T6 status shape, G16-B message CTA, S7 labels) match intentional contract behavior — not weakened gates.

---

## Spot-checks (code ↔ contract)

| Slice | Evidence | Status |
|---|---|---|
| S1 G9-B | `_catalog_gap_covered_by_declared_thrust`: PASS **and** `per_motor_max_thrust_n >= floor`; gap stays in evidence; under-floor still wins (T1/T2) | ✅ |
| S2 G16-A | `LIST_MOTORS_PATTERNS` + `"list_motors"` before ANALYZE; soft-interrupt ITERATE / DEFINE_MISSING / IDLE; `_handle_list_motors` 0-LLM | ✅ live: `…catalogo?` → `list_motors` |
| S2 G16-B | `include_cta=False` in `_offer_catalog_help`; default True elsewhere | ✅ T6 |
| S3 G18 | Aerial + `missing_transmission_parameters` → `_redirect_aerial_motors_request`; terrestrial T8 unchanged | ✅ with N2 |
| S4 G17 | Force-motors **before** force-propellers; `completeness == "high"` (see Notes) | ✅ accepted deviation |
| S5 FN-013 | `_fresh_pending_keys_for_block` vs stale head; brief rebuilt (T11) | ✅ display; see N1 |
| S7 G19 | Genuine gap `next_why` names both phrases; demoted PASS copy; labels `"Qué motores…"`, `"Explora opciones de motor"` | ✅ live: those strings resolve `list_motors` / `explore_design_space` |
| S8 G13 | T14: `"PVC 400g"` → `value=="pvc"` + impact; no iterate code | ✅ |

Live extractor check (S4 justification):

```text
"4x 2306 2400KV 50W" → motors completeness=high
"10x4.5"             → motors completeness=medium (motor_count false-match)
                       propellers completeness=high
```

`!= "low"` would have stolen `"10x4.5"` into motors and failed T10 / G14. `== "high"` is the correct reading of stop condition #3.

---

## Notes (review + CLI — closed 2026-08-18)

### N1 — S5 refreshes the brief, not the session field

`_try_reprompt_active_block_declaration` rebuilds `pending` / `question` for the **response** when the stale head is not in `fresh_pending`, but does **not** write `fresh_pending` back onto `session.pending_param_definitions`.

The smoking-gun display bug (header Energía + body motors) is fixed for that turn (T11). The **next** answer still uses `session.pending_param_definitions` as `expected_keys` in `_handle_component_description`. A user who types `LiPo 6S…` after the corrected battery brief could still hit the motors wizard.

This is not retarget (a). Syncing session to `fresh_pending` for the stale-head case is the same FN-021 hygiene the audit described. Optional follow-up; not a FAIL for this cut if CLI re-walk still uses `cancelar` only as intentional retarget.

### N2 — S3 can fall through to terrestrial if redirect is `None`

```text
redirect = self._redirect_aerial_motors_request(...)
if redirect is not None:
    return redirect
# still:
start_define_missing_params(missing_transmission_parameters)
```

`_redirect` returns `_continue_block_acquisition()` when propulsion is the pending block; that helper can return `None` if `_set_pending_next_block` no-ops (e.g. param-phase `missing` empty). On aerial that must **never** open torque/rueda. T7 covers the common create-project path (not system_defined → motors component wizard). Residual: add `return refuse` / motors fallback when aerial and redirect is None — do not fall through.

Also: any terrestrial DEFINE_PARAMS phrase (`definir rueda`, `definir torque`) on aerial currently redirects to **motors**, not an honest “este proyecto es aéreo”. Contract allowed that as alternative to refuse. Acceptable; slightly broad.

### N3 — S4 `== "high"` vs contract `!= "low"`

Accepted. Report residual #1 is accurate. Do **not** revert to `!= "low"`. Prefer documenting this in the contract addendum rather than “fixing” it back.

### N4 — S3 complete-architecture branch opens `["motors"]` only

Matches report residual #2 and the user’s phrase `definir motores`. Not a FAIL. Engineer may later want the full propulsion pair.

### N5 — S7 `action="iterate"` vs labels

Labels are re-entrant (verified). Structured `action` field is still `"iterate"` — pre-existing shape; CLI prints labels. No general suggestion engine (locked). Fine.

### N6 — Demoted CTA vs `suggested_action` rank

If `suggested_action` is set on PASS with empty BOM gaps, that branch still wins **before** the new demoted-gap PASS copy. S1 already prevents `"Declara empuje"` (catalog-gap rank gated). Catalog note remains in `evidence`. T13 uses `suggested_action=None`. Live post-DSE may show an optimize suggestion instead of the long §4.5 copy — still must not show `"Declara empuje"`.

---

## Review criteria (contract §7)

| Gate | Result |
|---|---|
| G9-B PASS + declared ≥ floor shows `"Declara empuje"` | ✅ does not (T1/T13) |
| G9-B over-suppress under-floor | ✅ still wins (T2) |
| G16-A `?` / IDLE → LLM | ✅ `list_motors` |
| G16-B duplicate CTA | ✅ T6 |
| G17 bare `4x 2306…` | ✅ T9/T9b |
| G14 `"10x4.5"` still hélices | ✅ T10 |
| G18 aerial torque wizard | ✅ T7 |
| G18 terrestrial | ✅ T8 |
| G12 header/body | ✅ T11 (display) |
| G19 CTA phrases | ✅ T12/T13 |
| G10 materials | ✅ untouched |
| ★2 / ★7 | ✅ |
| G9-A | ✅ not invented |
| Tests | ✅ T1–T14 present |

---

## CLI re-walk — CLOSED (2026-08-18)

Engineer walk on proyecto `prueba-9f1031895508`. **Verdict: PASS WITH NOTES** (same as code review).

| # | Probe | Result |
|---|---|---|
| 1 | `¿que motores tenemos en el catalogo?` | ✅ `list_motors`, 0 LLM |
| 2 | Post-DSE apply PASS + margin > 2 | ✅ no "Declara empuje ≥ floor" (G9-B) |
| 3 | `definir motores` on dron | ✅ aerial motors wizard (G18) |
| 4 | `4x 2306 2400KV 50W` in motors wizard | ⚠️ partial — needs `motores` prefix at some paths (G17 residual) |
| 5 | `definir bateria` after propulsion | ✅ battery brief (S5/G12) |
| 6 | catalog_gap / DSE discoverability | ✅ `explora opciones` / list-motors CTA (G19) |
| 7 | `PVC 400g` frame acquisition | ✅ G10 |
| 8 | iterate `PVC 400g` | ⚠️ opaque slug (G13 CLI path; unit T14 closed) |

**New findings registered:** G20 (energy 3/4 label after catalog motor re-pick), G20-B (`si` to energy hint → motor_power_w wizard).

**Checkpoint:** `15aa503` · **`checkpoint-continuity-polish`**

Optional follow-ups: N1 session sync, N2 aerial redirect `None` fallthrough, G20 micro-fix copy.
