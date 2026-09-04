# Implementation Review — DSE apply honesto

**Date:** 2026-09-03  
**Reviewer:** JES / Cursor  
**IC:** [implementation_contract_dse_apply_honest.md](implementation_contract_dse_apply_honest.md)  
**★:** [engineer_ratification_dse_apply_honest.md](engineer_ratification_dse_apply_honest.md) — Engineer “Empecemos por DSE apply honesto”  
**Report:** [implementation_report_dse_apply_honest.md](implementation_report_dse_apply_honest.md)  
**Implementer:** Claude Code

## Verdict

**PASS WITH NOTES**

§2.1–§2.4 match the IC on the params-only apply path. Nameplate W is kept. Unique Wh binds the catalog pack. Zero matches stay parametric + G5. Two-or-more refuses before save. Explore scoring / Impl C `components_delta` / G5 motor thrust comparison / MOP-2 hook untouched. Reviewer re-ran adjacent tests (**123 passed**) and full suite (**2124 passed**). Notes are hygiene, not a re-implement.

---

## Contract checklist

| Criterion | Result |
|---|---|
| §2.1 nameplate `motor_power_w` when catalog motor has `max_watts` | **Pass** — `catalog_motor_nameplate_watts` + write into `canonical_params` |
| §2.1 unbound / emax (`max_watts is None`) leave `_apply_delta` W | **Pass** — helper returns `None`; unbound-motor test writes 165 W |
| §2.1 do not clear motor `catalog_ref`; do not touch `per_motor_max_thrust_n` | **Pass** — walk test keeps r2305; G5 still thrust-only |
| §2.2 unique Wh → `bind_battery_from_catalog` + `set_battery_component` | **Pass** — 148 → `lipo_4s_10000mah`, mass 0.98, name is the new SKU |
| §2.2 zero matches → parametric + G5 clear | **Pass** — 185 Wh, `catalog_ref is None`, parametric sentence |
| §2.2 two+ → `status=error`, `action=apply_exploration_result`, no disk write | **Pass** — locked message; params unchanged |
| §2.3 honesty **before** G5; G5 before `sync_motors_component_from_params` | **Pass** |
| §2.3 G5 motor comparison unchanged | **Pass** — no `motor_power_w` in `invalidate_diverged_catalog_refs` |
| §2.4 nameplate / bind / parametric sentences | **Pass** — appended, not replacing change lines |
| §2.4 parametric sentence only when Wh changed | **Pass** — `_battery_parametric_wh` set only inside `wh_changed` |
| Params-only only (`not best.components_delta`) | **Pass** |
| No `set_motor_component` from this block | **Pass** — `set_battery_component` only (existing MOP-2) |
| No `EXPLORATION_GRIDS` / `_score_candidate` / catalog JSON | **Pass** |
| §5 files | **Pass** — `catalog_bind.py` + `orchestrator.py` + tests; `component_writers.py` not edited |
| Mandatory tests | **Pass** — `tests/test_dse_apply_honest.py` 7/7 |
| Adjacent (IC §3) | **Pass** — design_explorer / Impl C / battery OP / DSE motor-OP dual-truth |
| Suite | **Pass** — reviewer **2124** |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| Mixed 2.0×Wh + 0.75×W: W stays 220, not 165 | **Confirmed** — `test_mixed_apply_keeps_nameplate_w_and_binds_battery_sku` |
| Battery `lipo_4s_10000mah`, Wh 148, mass 0.98, name not 5000mah | **Confirmed** |
| Motor `catalog_ref` still r2305 | **Confirmed** |
| Message: nameplate sentence + batería vinculada | **Confirmed** |
| 2.5× → 185 Wh parametric, `catalog_ref` None, W 220 | **Confirmed** |
| Wh-only 2.0× binds 10000mah, W 220 | **Confirmed** |
| Unbound motor: W becomes 165; battery still binds | **Confirmed** — documented fixture |
| 2+ matches refuse, params unchanged | **Confirmed** — monkeypatch on `find_battery_skus_for_energy_wh` |
| Helper 148/74/185 | **Confirmed** |
| Full suite | **2124 passed** (reviewer) |

Refuse path patches the list helper in `catalog_bind` and the orchestrator imports it **inside** the apply function — the monkeypatch reaches the call. Locked 2+ copy is present (`Hay más de un pack de catálogo con {Wh} Wh…`).

---

## Notes (non-blocking)

### Note 1 — `bind_battery_from_catalog` without `base=`

IC allowed `base=existing or None`. Claude uses `None` so a SKU switch does not keep `lipo_4s_5000mah` as `.name`. Matches the walk lock. Disclosed in the report. Do not add `base=` on this path.

### Note 2 — Battery keys merged, not full `current_parameters` replace

IC said refresh params from `set_battery_component` state. Implementation copies only `battery_capacity_wh` / `battery_mass_kg` / `battery_cell_count` so nameplate W and other `_apply_delta` keys survive. Correct. Do not replace the whole dict.

### Note 3 — Two-or-more only via monkeypatch

v1 battery `energy_wh` values are unique. Live duplicate is unreachable until catalog JSON adds one. Helper still returns `None` on 2+. Leave as-is.

### Note 4 — Nameplate sentence says “consumo inferior”

Grids only scale W down (0.75 / 0.65). If a future delta raised W, the same sentence would still say “inferior” while the value is forced back to nameplate. Not in this IC. Optional later copy tweak.

### Note 5 — No dedicated emax apply test

§2.1 “leave delta W when `max_watts is None`” is implied by the helper returning `None`. Unbound-motor test covers the other false branch. Not required to ship.

### Note 6 — `find_unique_battery_sku_for_energy_wh` unused in orchestrator

Orchestrator uses `find_battery_skus_for_energy_wh` + `len` so 0 vs 1 vs 2+ can refuse. Unique helper is tested and is the IC’s named API. Fine.

---

## Next

Code **closed**. Optional Engineer CLI on `autonomia-15min`: same mixed apply should keep 220 W and bind `lipo_4s_10000mah`. Explore `#1` preview may still show 165 W — expected; this IC did not re-rank.

**Not automatic:** Option B, Tier 3, C3, G24-B, CAD.

**Queue after this review:** Structure A (mass honesty + min prop/frame fit) — IC next, Engineer ★ before Claude.
