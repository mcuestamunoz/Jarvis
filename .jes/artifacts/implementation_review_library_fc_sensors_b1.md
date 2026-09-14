# Implementation Review — Relocate FC + GPS envelopes into `library/` B1

**Date:** 2026-09-14  
**Reviewer:** Cursor (Engineer Interface) — independent of implementer session  
**Against:** [IC](implementation_contract_library_fc_sensors_b1.md) · [report](implementation_report_library_fc_sensors_b1.md)

**Verdict:** **PASS WITH NOTES**

---

## Checklist

| Gate | Result |
|---|---|
| `library/fc` + `library/sensors` exist; dims match citations | **Pass** — SpeedyBee 41.6×39.4×7.8 · Pixhawk 44×84×12 · Holybro 50×50×14.4 |
| No `FLIGHT_CONTROLLER_DIMENSIONS` / `GPS_DIMENSIONS` in `aerial.py` | **Pass** — hasattr + full `src/` grep clean |
| ComponentLibrary-only JSON read | **Pass** — `FcSpec`/`SensorSpec` + get/list/has |
| Extractors resolve dims via library | **Pass** — L4/L5; bare `m10` still no dims |
| Assist lists from `list_fcs` / `list_sensors` | **Pass** — L6; no aerial dimension imports |
| Bind + `CatalogRef.family` per lock #7 | **Pass** — families `"flight_controller"` / `"sensors"` (documented) |
| No invented mm / no antenna fold-in | **Pass** — notes preserve φ50 / 25×25×4 honesty |
| Live 10-min envelopes unchanged | **Pass** — FC box 41.6×39.4×7.8 · sensors box 50×50×14.4 |
| Version / workspace | **Pass** — `0.4.1`; no workspace mutation |

---

## Independent checks (Cursor)

1. `pytest tests/test_library_fc_sensors_b1.py` → **19 passed**.  
2. `default_library.get_fc` / `get_sensor` dims match IC bags.  
3. `aerial` has **no** DIMENSIONS attributes; no DIMENSIONS strings under `src/`.  
4. Live `10-min-autonomía` read-only: FC/sensors geometries **box** with cited L×W×H (unchanged).  
5. Identity assist returns Pixhawk + SpeedyBee + Holybro M10 from library.  
6. Binds project `catalog_ref` correctly; **not** registered in `component_writers` APPLY map (see N1).

---

## Notes

| ID | Severity | Note |
|---|---|---|
| **N1** | Accepted | Bind helpers exist but are **not** wired to a new IDLE rebind trigger / writers table. Matches minimal P0 surface + lock #8 (pick still free-text extractor). Future ★ if Engineer wants ESC-class `cambiar controladora <sku>`. |
| **N2** | Soft | `source_urls` → singular `source_url` + second URL in `source_note` — content preserved; shape aligned with other families. OK. |
| **N3** | Info | Holybro M10 remains a **box** 50×50×14.4 (φ50 bound square). Board may *look* roundish from some angles; geometry DTO is still box — correct, not a cylinder invent. |
| **N4** | Soft | Live projects may still lack `catalog_ref` on FC/sensors until re-declare/rebind — envelopes identical via free-text path; Path D not taken (IC default). |

---

## Verdict

**PASS WITH NOTES** — ready for Engineer smoke §3.

**Smoke script (`10-min-autonomía`):**  
1. Confirm `library/fc/_datos.json` + `library/sensors/_datos.json` on disk.  
2. Cards/Board: FC **41.6×39.4×7.8** · sensors **50×50×14.4**.  
3. Optional: `ayúdame a elegir` controladora/GPS lists sourced identities.  
4. No dimension SoT left in `aerial.py` (already verified in review).

---

## Engineer smoke ACCEPT (2026-09-14)

Engineer **ACCEPT** — library files on disk; live FC/GPS envelopes unchanged. **Buy CLOSED.**

---

## Related: Disk axial Visor smoke

Engineer **ACCEPT** 2026-09-14 (Board screenshot: motors/props show axial cylinder depth). Buy **`B1-disk-axial-visor` CLOSED**.
