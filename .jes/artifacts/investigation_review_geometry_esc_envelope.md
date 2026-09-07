# Investigation Review — ESC Declared Envelope (Geometry axis)

**Date:** 2026-09-07  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_geometry_esc_envelope.md](investigation_contract_geometry_esc_envelope.md)  
**Report:** [investigation_report_geometry_esc_envelope.md](investigation_report_geometry_esc_envelope.md)  
**Parents:** Battery B1 @ **2316** · Motor B1 @ **2323**

## Verdict

**PASS WITH NOTES**

Governing question answered. Variant ambiguity on the Hobbywing page is resolved honestly via existing `part_number: "30901001"` → **50.0 × 21.6 × 12.0 mm**. Default lean **B1 — ESC box L×W×H (Battery vocabulary), representar only** is Buy-ready.

Engineer ★ still required before IC / code.

---

## Checklist

| Criterion | Result |
|---|---|
| A–G present | **Pass** |
| As-is + bind path | **Pass** — SKU-first like Battery |
| Field bag + seed with evidence | **Pass** — `part_number` disambiguation |
| Honesty / ladder + reachability caveat | **Pass** |
| One default lean | **Pass** — **B1** |
| No `src/` this investigation | **Pass** (per investigator) |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| `EscSpec` no geometry; 1 catalog row | **Confirmed** |
| `part_number` 30901001 = International Version B | **Confirmed** — www.hobbywing.com table |
| Size for B: 50.0×21.6×12.0 mm; weight 15g | **Confirmed** |
| Version A: 42.0×21.6×12.0 mm / 18.5g (not this seed) | **Confirmed** |
| `bind_esc_from_catalog(sku, *, library=…)` Battery-shaped | **Confirmed** |
| No `bind_esc` / ESC pick in `orchestrator.py` | **Confirmed** |
| Docstring “no CLI/UX yet” still true for Continuity wizards | **Confirmed** |
| Seed `mass_g=26` vs page 15g for 30901001 | **Confirmed discrepancy** — N2 |

---

## Agreement with report core

1. **Reuse Battery `length_mm`/`width_mm`/`height_mm`** — correct; page is “Size (mm)” box.
2. **Disambiguate by `part_number`, not guess** — load-bearing and sound.
3. **Do not fix mass / dead `a.` URL in Geometry IC** — correct scope.
4. **Do not bundle FC/stack 30.5** — correct.
5. **Reachability caveat** — Geometry B1 is still worth buying; UX wizard is a separate Buy.

---

## Notes (must land in IC if Engineer ★ B1)

### N1 — Seed values (locked)

| SKU | L / W / H mm | Rule |
|---|---|---|
| `hobbywing_xrotor_40a_6s` | **50.0 / 21.6 / 12.0** | part `30901001` · verbatim `50.0×21.6×12.0` |

`source_note` must cite International Version B / 30901001 and that A (42×…) was **not** chosen.

### N2 — Pre-existing `mass_g` mismatch (flag only)

Page: **15g** for 30901001. Seed: **26g**. Do **not** “fix” mass in this IC. Optional later hygiene Buy.

### N3 — `source_url` TLS / mirror (flag only)

Cited `a.hobbywing.com` fails TLS; `www.hobbywing.com/...` works. IC may leave URL as-is or optionally normalize to `www.` in the same seed edit — **optional**, not required for dims.

### N4 — Reachability (honesty, not a blocker)

No Continuity ESC catalog-pick wizard. After B1:

- Unit tests + `bind_esc_from_catalog` work.
- Board shows dims **if** a project’s ESC component is catalog-bound (Engineer can smoke via writer/script, same class as Battery rebind smoke).
- Freeform `"ESC 40A"` cards (current live project) **will not** gain dims until rebind to the SKU.

Building the wizard is **out of Geometry B1**.

### N5 — Do not conflate `height_mm` with “stack height”

IC done-criteria / non-goals must forbid stack/fit copy.

---

## Buy recorded (awaiting Engineer ★)

| Option | Cursor stance |
|---|---|
| B0 | Unnecessary |
| **B1 ESC box** | **Recommended** |
| B2 +FC/stack | Later, separate |
| B3 glyph | Not now |
| Defer | Rejected |

**Suggested IC title:** *ESC declared envelope (box, reusing Battery vocabulary) — representar only.*

---

## What Engineer decides next

1. ★ **Buy B1** → Cursor writes IC → Claude implements  
2. Defer until ESC pick UX exists — Cursor does **not** recommend (pattern still valuable)  
3. Re-scope  

No code until ★.
