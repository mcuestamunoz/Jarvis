# Engineer Ratification — CLI catalog-assist watts recovery

**Date:** 2026-09-02  
**Authority:** Engineer (“bien ratifico” after the wiring explanation)  
**IC:** [implementation_contract_cli_catalog_assist_watts_recovery.md](implementation_contract_cli_catalog_assist_watts_recovery.md)

## ★

| ★ | Decision |
|---|---|
| **★1** | T1-shaped: same G22 + pick. Trigger = bound SKU lacks nameplate W + autonomy target + no minutes + **not** thrust-underspec. |
| **★2** | List **filters** to `max_watts is not None`. Do not re-offer the no-W SKU as a recovery pick. |
| **★3** | IDLE `ayúdame a elegir` opens that list. Continuity next_step names it. Do not invent `motor_power_w`. |
| **★4** | T1+2 / Tier 3 / Option B `ASSEMBLY_READY` **frozen**. G21 covering-with-W unchanged. G18 definir-motor list unchanged. |
| **★5** | Recovery ≠ 15 min fulfilled. L0 may return ~5 min and the unmet-autonomy path is allowed. |

Cursor implements. Review against the IC after the edit.
