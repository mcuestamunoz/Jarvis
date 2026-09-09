# Implementation Review — Prop adapter ask B1

**Date:** 2026-09-09  
**Reviewer:** Cursor (JES)  
**Contract:** [implementation_contract_kit_prop_adapter_ask_b1.md](implementation_contract_kit_prop_adapter_ask_b1.md)  
**Report:** [implementation_report_kit_prop_adapter_ask_b1.md](implementation_report_kit_prop_adapter_ask_b1.md)

## Verdict

**PASS WITH NOTES**

Gated `prop_adapter` is visible (Board + BOM) only after motors **and** hélices exist. Sequential propulsion fill asks the mount Brief **before** ESC. Skip does not invent a spec. `BLOCK_TO_COMPONENTS["propulsion"]` is still `["motors", "propellers", "esc"]`. Suite **2523** re-ran here (9 new). Closable after Engineer smoke §6.

The §3.3 splice on `_set_pending_next_block` / `_fresh_pending_keys_for_block` was **correctly not shipped**. Literal IC would reopen Phase A for a kit hole and steal `"definir esc"`. Locked going forward: splice only on a **just-saved** `still_missing` that is **non-empty**. Empty-list guard stays.

---

## Checklist

| Criterion | Result |
|---|---|
| `KIT_TO` + `KIT_HOME_BLOCK["prop_adapter"]=propulsion` + `KIT_REQUIRES_COMPONENTS` | **Pass** |
| `kit_component_keys(..., components=None)` fail closed (T8) | **Pass** |
| BOM / Board / IDLE pass `components` | **Pass** |
| `BLOCK_TO_COMPONENTS` values unchanged | **Pass** — dict body still three propulsion keys; no `prop_adapter` string inside any list |
| Empty dron → no adapter slot (T0) | **Pass** |
| Motors only → no adapter (T1) | **Pass** |
| Motors+props, esc absent → slot in propulsion column; BOM has both (T2) | **Pass** |
| Hélices save → adapter Brief, not ESC (T3) | **Pass** |
| `"va directa"` saves, no `catalog_ref`, then ESC (T4) | **Pass** |
| `"no lo sé"` writes nothing, ESC next, hole in BOM (T5) | **Pass** |
| Robot → zero adapter (T6) | **Pass** |
| Twin `_block_progress_status` (T7) | **Pass** |
| Relabel `expected_keys[0] in KIT_HOME_BLOCK` (not `len==1`) | **Pass** |
| No hub/shaft/bore read in gate | **Pass** — `_kit_requirements_met` is completeness only |
| No version bump / no catalog adapter family / `ui/` this Buy | **Pass** — no `prop_adapter` in `ui/` or `library/` |
| `OUT_OF_SCOPE_EXPLICIT_SAVE_KEYS` untouched | **Pass** |
| Continuity: no new rank; B3 lists kit keys via `KIT_HOME_BLOCK` | **Pass** — `project_continuity.py` unmodified this Buy |
| Suite **2523** | **Pass** — Cursor re-ran full pytest |
| Existing tests grown, not deleted | **Pass** — kit T1/T2/T3/T7 + three ASSEMBLY READY stubs + battery helper skip turn |

---

## Independent checks

| Claim | Cursor |
|---|---|
| Splice helper prepends only; not a generic insert table | **Confirmed** `splice_prop_adapter_ask` |
| Orchestrator wrapper `"esc" in expected_keys` | **Confirmed** — `esc` is unique to propulsion `BLOCK_TO` today (N3) |
| All six `still_missing` sites wrapped | **Confirmed** — 4 catalog-pick + frame-parts + main save |
| `_set_pending_next_block` / `_fresh_pending_keys_for_block` **no** splice | **Confirmed** (deviation, N1) |
| Empty `still_missing` → no splice | **Confirmed** |
| Skip runs before catalog help-choose | **Confirmed** |
| FN-ESC fixture: motors+props present, `"definir esc"` still ESC prompt | **Confirmed** — `test_definir_esc_opens_esc_prompt` green; this is why §3.3 was not followed |
| Battery helper extra `"no lo sé"` | **Confirmed** — catalog pick of hélices now legitimately splices |
| `_block_progress_status` in `engineering_readiness.py` | **No `prop_adapter`** |

---

## Notes

### N1 — §3.3 splice site (justified; lock this)

Claude is right. Splicing into `_set_pending_next_block` after an **empty** BLOCK_TO missing list would keep propulsion in Phase A for `prop_adapter` alone and block the numeric-params wizard. Splicing into `_fresh_pending_keys_for_block` would turn `"definir esc"` (motors+hélices already declared) into the adapter Brief — `test_fn_esc_acquisition.py` exists for that path.

The empty-list guard is necessary **and** insufficient by itself for FN-ESC (`still_missing == ["esc"]` is non-empty). Confining the splice to post-save follow-up is the product that matches “after hélices, before ESC” **in the sequential wizard** without stealing an explicit ESC mention.

**Smoke implication:** walk motors → hélices → Brief. Do **not** expect `"definir esc"` (with hélices already saved) to ask the adapter first. The dashed slot / BOM hole still appear; after 4/4 Continuity can nag. Do not “fix” this by putting the splice back on those two functions.

### N2 — Skip matcher is exact `.lower()`, not `_normalize`

T5 covers `"no lo sé"`. `"no lo sé."` or Bug 77 `"no sé aún"` would fall through to relabel and **save** a description. Optional later; not a reopen. Smoke: use the Brief’s own phrase.

### N3 — `"esc" in expected_keys` as propulsion detector

Works while no other block lists `esc`. One-off, not a condition engine. If energy ever gained `esc`, this wrapper would splice into the wrong wizard. Acceptable for this Buy.

### N4 — ASSEMBLY READY fixtures stub three kit keys

Same pattern as kit B1-min. Live demo with `prop_adapter` undeclared must **not** be ASSEMBLY READY. Hover numbers stay a twin of the clone without the hole.

### N5 — Mixed D7 (motors+hélices one phrase) untested

IC §3.3 named it; T3 is sequential. Catalog-pick path is covered by the battery helper. Optional extra test; not blocking smoke.

---

## Phase

Implementation **REVIEWED PASS WITH NOTES**. Engineer smoke: [implementation_contract_kit_prop_adapter_ask_b1.md](implementation_contract_kit_prop_adapter_ask_b1.md) §6. Record `engineer_smoke_kit_prop_adapter_ask_b1.md`. Package `0.3.8` · suite **2523**.
