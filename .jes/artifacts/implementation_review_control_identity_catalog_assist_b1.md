# Implementation Review — Control identity assist (FC/GPS #4b smoke fix)

**Project:** Jarvis  
**Date:** 2026-09-12  
**Reviewer:** Cursor (Engineer Interface)  
**Against:** live smoke failure on `autonomía-15min` (SpeedyBee declare loop + missing `ayúdame a elegir` list) · #4b identity/dim tables  
**Verdict:** **PASS WITH NOTES** — free-text + numbered identity list work; two review fixes landed in-cycle

---

## Checklist

| Gate | Result |
|---|---|
| Free-text `SpeedyBee F405 V4` binds in control wizard | **Pass** — force-bind + `speedybee`/`f405` keywords |
| Bare `f405` still no dims (T2 honesty) | **Pass** |
| `ayúdame a elegir` lists FC dim-table rows (Pixhawk 4, SpeedyBee) | **Pass** |
| Pick `2` → SpeedyBee + dims 41.6×39.4×7.8 | **Pass** |
| Then sensors list Holybro M10 → pick binds 50×50×14.4 | **Pass** |
| No new `library/fc` / `catalog_ref` family | **Pass** — dim-table identity only |
| Apply reuses `infer_component_for_key` + `set_control_component` | **Pass** |
| Head-key gating (FC then sensors) | **Pass** |
| Brief advertises help-choose for FC/sensors | **Pass** |
| Tests `test_control_identity_catalog_assist_b1` + #4b geometry | **Pass** (5+5 after review fix) |

---

## Notes (fixed in review)

| ID | Note |
|---|---|
| **N1** | Suggestions lacked `name`; `match_suggestion_by_input` only keys off `name` → label pick failed. **Fixed:** set `name` = declare label; regression test added. |
| **N2** | Motor/prop/battery/frame/kit/ESC offers did not clear `flight_controller_suggestions` / `sensor_suggestions`. **Fixed:** peer-clear on those offers. |
| **N3** | List is **sourced dim-table identities only** (not every string in `FLIGHT_CONTROLLER_MAP`). Honest vs #4b; Betaflight-without-box stays free-text. |

---

## Smoke (Engineer) — `autonomía-15min`

1. Restart CLI.  
2. `definir controladora` → `ayúdame a elegir` → `2` (SpeedyBee).  
3. `ayúdame a elegir` → `1` (Holybro M10).  
4. Or free-text `SpeedyBee F405 V4` / `Holybro M10`.

---

## Verdict

**PASS WITH NOTES** — ready for Engineer smoke on 15min control block.
