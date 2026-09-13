# Implementation Review (mid-flight) — Catalog sourced-only purge + battery rebind P0

**Date:** 2026-09-13  
**Reviewer:** Cursor (Engineer Interface) — **independent mid-flight check** (Claude still implementing; **no** implementation report yet)  
**Against:** [IC](implementation_contract_catalog_sourced_only_purge_battery_rebind_b1.md)  
**Not reviewing:** [craft montage Path F](implementation_contract_geometry_craft_montage_path_f_b1.md) — **zero code** for that IC (correct: Claude is on purge).

**Verdict:** **INCOMPLETE — do not PASS.** Core data + Bat-list/sku/help look directionally right; **suite not green** (~**52 failed** / 2730 passed). Not ready for Engineer smoke or review-of-record.

---

## What Claude got right (so far)

| Gate | Status |
|---|---|
| ★1 purge bat/mot/prop to KEEP inventory | **Pass** — 5 / 3 / 6; frames/esc/kit still sourced |
| Every remaining product row has `source_url` | **Pass** (live inventory check) |
| Bat-list `limit=None` (no truncate-10) | **Pass** — `battery_catalog_assist.py` |
| Bat-help on battery-only redefine | **Pass** — orchestrator G18-style escape |
| Bat-sku via `detect_battery_sku_token` → bind | **Present** in orchestrator path |
| Continuity W-candidates | **OK** — dynamic via `build_nameplate_watts_motor_suggestions` (not hardcoded DROP list) |
| Docstring tip `r2305` → `r2205` | **Pass** (closure/reasoning) |
| Materials untouched | **Pass** (out of scope) |

---

## Blockers (must finish before report / review PASS)

### B1 — Suite still red (~52 failures)

Sample classes still keyed to **DROP** SKUs:

- `test_cli_catalog_assist_watts_recovery` (`sunnysky_r2305_2500`, `emax_rs2205_2300`)
- `test_g24_viable_selection` (`brotherhobby_avenger_2500`)
- `test_energy_params`, `test_g9a_*`, `test_g21_g22_*`
- `test_geometry_motor_height_cited_b1` (DROP motors)
- `test_geometry_propeller_envelope_b0_b1` / `cited_seeds_b2` (`gemfan_5030`, `tmotor_*`, “18 rows”)
- `test_geometry_sourced_dims_b1` (generic `lipo_3s_2200mah` byte-stable)
- `test_geometry_sourced_battery_tattu_*` (other lipo_4s rows)
- `test_geometry_sourced_motor_xing_e_*` (hobbywing motor sibling — DROP)
- `test_iterate_session` / `test_orchestrator` / `test_project_closure_v1`
- ESC rebind tests failing (may be collateral / session — check)

IC §4.2: **redirect**, do not weaken. 39 min in and still ~52 red = unfinished redirect pass, not “almost done.”

### B2 — No implementation report

IC requires `.jes/artifacts/implementation_report_catalog_sourced_only_purge_battery_rebind_b1.md` — **absent**.

### B3 — Sourced-only gate test missing

IC §3.4 recommended unit asserting every product-family seed has `source_url` — **not found** as a dedicated regression (foundation tests partially adjusted; no hard gate).

### B4 — Bat-sku / rebind smoke tests thin

Existing `test_battery_catalog_bind_ux.py` covers help-choose in acquisition; **no clear new test** that IDLE `cambiar bateria` + free-text `tattu_…` binds (Field Note B2). Should be added before claiming Bat-sku closed.

---

## Notes (non-blocking / hygiene)

| ID | Note |
|---|---|
| N1 | Working tree also contains estimated-plate / MY5 / PRIORIDAD edits from earlier sessions — do not attribute all `orchestrator.py` churn to this Buy alone. |
| N2 | Stale comments still mention DROP SKUs (`lipo_6s_10000mah` in `detect_battery_sku_token` docstring) — optional cleanup. |
| N3 | Path F craft-montage IC is **READY FOR ★** but **must wait** until this purge suite is green — do not parallel-merge red catalog. |

---

## Ask Claude (before claiming done)

1. Finish **all** DROP→KEEP redirects until `pytest` full suite green.  
2. Add sourced-only gate test (§3.4).  
3. Add Bat-sku + Bat-help rebind tests (Tattu free-text + `ayúdame a elegir` after `cambiar bateria`).  
4. Write implementation report (redirects table + suite count + live DROP refs in `workspace/` if any).  
5. **Stop** if tempted to re-seed DROP rows “for tests.”

---

## Engineer action

- Treat current Claude run as **still in progress**.  
- Do **not** smoke purge as closed yet.  
- Path F ★ stays queued behind green purge.
