# Field Note — Smoke bugs after MY5 rebind + estimated plate (5min)

**Date:** 2026-09-13  
**Project:** `autonomía-de-5min`  
**Authority:** Engineer smoke transcript  
**Status:** OPEN — triage (no code this note)

---

## Observed (Engineer)

1. `cambiar frame` → `3` (HGLRC MY5) saves identity; Continuity next-step still hammers “motor sin W / no inventes motor_power_w”.  
2. `declara frame_plate estimada 120 x 55 mm` — **OK** (disclosure + ESTIMATED_TEMPORARY).  
3. `estado`: ASSEMBLY READY + Structure PASS* + **BLOQUE PROPULSIÓN/ENERGÍA: NO CERRADO** (copy tension).  
4. `cambiar bateria` list **omits** `tattu_2300mah_4s_75c_xt60`; typing the SKU / `ayúdame a elegir` loops the define-battery Brief.  
5. `cambiar sensor` → iterate/material wizard (wrong product path).

---

## Root causes (Cursor check)

| # | Bug | Cause |
|---|---|---|
| **B1** | Tattu missing from rebind list | `build_battery_catalog_suggestions(..., limit=10)` takes `list_batteries()[:10]`. Library now has **>10** rows; Tattu is **outside the cap** (seed grew with #4f). Bat-2 comment assumed “10 = full catalog” — **stale**. |
| **B2** | SKU typed after list → define loop | After rebind opens DEFINE_MISSING battery, free-text SKU is not bound as catalog pick; falls into acquisition Brief. `ayúdame a elegir` in that sub-mode does not re-offer the numbered list (or offers then still broken). Separate from B1 but worse when SKU not on list. |
| **B3** | `cambiar sensor` → iterate | `resolve_idle_catalog_rebind` has **no** `sensors` / `sensor` family — returns `None` → Continuity/iterate path. |
| **B4** | Frame pick leaves stale wb/body (prior session) | Rebind bind can leave prior projected dims until `actualiza frame desde catálogo`. (Engineer may or may not have hit this this walk.) |
| **B5** | ASSEMBLY READY vs bloque no cerrado | Pre-existing honesty stack (Energy PASS / Requirements vs propulsion-energy block closure) — **not introduced** by plate/MY5; noisy after layout actions. |
| **B6** | Post-frame Continuity spam (W/autonomy) | Layout/geometry saves still surface propulsion Continuity tip — product routing noise, not wrong physics. |

---

## Ranked Buys (Engineer ★)

| Priority | ★ | Fix |
|---|---|---|
| **P0** | **`B1-catalog-sourced-only-purge-battery-rebind`** | **IC READY FOR ★** — [implementation_contract_catalog_sourced_only_purge_battery_rebind_b1.md](implementation_contract_catalog_sourced_only_purge_battery_rebind_b1.md). Delete product seeds without `source_url` (7 bat / 20 mot / 13 prop) + fix battery list cap + SKU/`ayúdame` rebind bind. Engineer: no anonymous LiPo lists. |
| **P1** | **`B1-sensors-catalog-rebind`** | Add `sensors` to IDLE rebind (+ control-identity list) — mirror FC/GPS assist |
| **P1** | **`B1-frame-rebind-fresh-project`** | After frame pick, always refresh projected wb/body/parts (or clear stale) so `actualiza…` not required |
| **P2** | Continuity tip after geometry-only save | Suppress or demote W/autonomy tip when last action was frame/plate/pose |
| **P2** | ASSEMBLY READY vs bloque copy | Separate Field Note / small honesty Buy — do not mix into P0 |

### P0 purge snapshot (gate = `source_url`)

- **KEEP batteries (5):** gens_ace, tattu, CNHL 4S1500, Spektrum 4S5000, GNB 6S6000  
- **DROP batteries (7):** all anonymous `lipo_*` without URL (incl. `lipo_6s_10000mah`, `lipo_12s_16000mah`, …)  
- **KEEP motors (3) / props (6);** frames/esc/kit already clean. Materials out of scope.

---

## Workaround (today)

```text
cambiar frame → 3 → actualiza frame desde catálogo   # if wb still 208
declara frame_plate estimada 120 x 55 mm             # OK as smoked

# battery: until P0
# use a listed number, or cancel and a path that binds Tattu SKU if one exists
# (SKU free-text after "cambiar bateria" is currently broken)

# sensors: use control Continuity / "definir sensores" / identity assist — not "cambiar sensor"
```

---

## Out of this note

Estimated-temporary plate — **working**. MY5 catalog seed — **present**. HD-005 autonomy — unchanged.
