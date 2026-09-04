# Engineer Ratification — DSE apply honesto

**Date:** 2026-09-03  
**Authority:** Engineer (“Empecemos por DSE apply honesto”)  
**IC:** [implementation_contract_dse_apply_honest.md](implementation_contract_dse_apply_honest.md)

## Cut chosen

Params-only DSE **apply** honesty: keep catalog motor nameplate W; bind unique matching battery SKU (or disclose parametric / refuse if ambiguous). **Not** explore re-rank. **Not** Impl C C3. **Not** G24-B.

## ★

| ★ | Decision |
|---|---|
| **★1** | Do not write `motor_power_w` below (or different from) the bound catalog motor’s nameplate `max_watts`. Strip the W lever on apply; keep the SKU. |
| **★2** | If applied `battery_capacity_wh` matches **exactly one** library `energy_wh`, bind that SKU via existing `bind_battery_from_catalog` + `set_battery_component` (catalog mass/cells/`catalog_ref`). Walk: 148 Wh → `lipo_4s_10000mah`. |
| **★3** | Zero matches → parametric Wh + G5 clear + CLI says not a pack. Two or more → refuse apply (no silent pick). |
| **★4** | Apply-path only. Do not change `EXPLORATION_GRIDS`, `_score_candidate`, or Impl C motor catalog generation. Explore `#1` may still be the mixed row; post-apply L0 using nameplate W is the honest number. |
| **★5** | Frozen: Tier 3, Option B, G24-B, C3 battery DSE, Conversation Engine, Block PARCIAL, inventing W, catalog JSON, Engineer `workspace/`. |

Claude implements the IC. JES reviews after the report. This chat does not edit `src/`.
