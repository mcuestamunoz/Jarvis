# Implementation Review — Assembly kit template B1-min

**Date:** 2026-09-09  
**Reviewer:** Cursor (JES)  
**Contract:** [implementation_contract_assembly_kit_template_b1.md](implementation_contract_assembly_kit_template_b1.md)  
**Report:** [implementation_report_assembly_kit_template_b1.md](implementation_report_assembly_kit_template_b1.md)

## Verdict

**PASS WITH NOTES**

Two kit holes are visible (Board + BOM + Continuity) for `dron`/`uav` without widening architecture/PASS. `BLOCK_TO_COMPONENTS` lists **byte-identical** to HEAD. Suite **2507** re-ran here (10 new). Closable after Engineer smoke §6.

The relabel step (§3.6.4 IC overclaim) is a **justified deviation**, not a reopen: without it the wizard could not save a kit description. Pattern matches existing force-blocks; T4c covers the save.

---

## Checklist

| Criterion | Result |
|---|---|
| `KIT_TO_COMPONENTS` / `KIT_HOME_BLOCK` as locked | **Pass** |
| `BLOCK_TO_COMPONENTS` values unchanged | **Pass** — Cursor extracted both dicts vs HEAD; identical |
| No `vehicle_type` → zero kit keys (T0) | **Pass** |
| Dron + 7 keys → two slots; architecture 4/4 (T1) | **Pass** |
| BOM missing exactly those two, order preserved (T2) | **Pass** |
| Continuity B3 sentence + both keys (T3) | **Pass** |
| IDLE `declara el conector` → `["power_connector"]` not energy composite (T4) | **Pass** |
| Twin `_block_progress_status` (T5) | **Pass** |
| Robot → zero kit slots (T6) | **Pass** — domain gate, even though robot declares `energy`+`control` |
| Stub connector removes its slot (T7) | **Pass** |
| `engineering_readiness.py` empty this Buy | **Pass** — `git diff --stat` empty |
| No version bump / no catalog family / no `prop_adapter` | **Pass** |
| Suite **2507** | **Pass** — Cursor re-ran full pytest |

---

## Independent checks

| Claim | Cursor |
|---|---|
| Helpers `canonical_vehicle_domain` / `kit_component_keys` / `bom_and_board_expected_keys` | **Confirmed** |
| Board appends kit keys to home-block columns | **Confirmed** `_expected_keys_by_column` |
| BOM uses shared helper + `vehicle_type` | **Confirmed** |
| Kit IDLE only if `_next_pending_block is None` | **Confirmed** |
| `resolve_kit_mention` uses same aliases, caller-supplied `kit_keys` | **Confirmed** — does not put kit keys in `_owning_block_for_component` |
| Relabel only when `len(expected_keys)==1` and key in `KIT_HOME_BLOCK` and completeness ≠ low | **Confirmed** |
| Aliases: no `cable` / `cableado` | **Confirmed** |
| `ui/` / `_geometry_from_spec` this cycle | **Not this Buy** (prior geometry diffs remain uncommitted) |

---

## Notes

### N1 — Relabel (IC §3.6.4 was wrong; 1-token Brief example hotfix)

Claude is correct: kit keys have no `ComponentRule`. Relabel-before-filter is required.

**Smoke 2026-09-09:** Brief example `'XT60'` is one token → generic completeness `low` → relabel skipped → same Brief forever. Hotfix: non-empty kit description relabels and promotes `low` → `medium` so the wizard closes. Regression: `test_t4d_brief_example_xt60_single_token_saves_and_closes_wizard`. Escape still cancels without saving.

### N2 — Continuity first clause still says “arquitectura”

Rank 4 still sets `next_why` to “{key} aparece en la arquitectura…” and **then** appends B3. Slightly sloppy for a kit key, but B3 is present and T3 locks it. Optional later tidy; not a reopen.

### N3 — ASSEMBLY READY fixtures stub the kit

Six existing tests declare high/empty kit specs so they stay “assembly ready.” Live demo with holes undeclared should **not** be ASSEMBLY READY. Smoke: confirm 4/4 + two slots + Continuity kit ask; hover numbers unchanged. Leaving slots pending is ACCEPT.

### N4 — T4c

Saves `power_connector` without `catalog_ref`. Does not assert completeness band; the relabel path requires non-`low`. Enough for this Buy.

---

## Phase

Implementation **CLOSED**. Engineer smoke [engineer_smoke_assembly_kit_template_b1.md](engineer_smoke_assembly_kit_template_b1.md) **ACCEPT**. Package `0.3.8` · suite **2507** / T4d **2508**.
