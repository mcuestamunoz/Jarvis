# Investigation Report — Propeller cited envelope (Geometry; live Gemfan 5045)

**IC:** [investigation_contract_geometry_propeller_envelope_b1.md](investigation_contract_geometry_propeller_envelope_b1.md)
**Investigator:** Claude Code
**Date:** 2026-09-09
**Checkpoint base:** package `0.3.8` · suite 2480 · height smoke ACCEPT

**Do not implement — this is a read-only report.**

---

## A. Executive answer

The live SKU `gemfan_5045_hbn` cannot honestly receive a Motor-height-style seed today: its only `source_url` (an Oscar Liang **motor** thrust-test article) verifies that a propeller called "Gemfan 5045 HBN" existed and was tested with the EMAX motor (its own thrust numbers already match the row's own `operating_points` entry), but it states **no propeller physical fact** — no mass, hub, or blade count. No manufacturer or retailer page found anywhere online uses the exact designation "HBN" as an official model code; the closest real product family ("Gemfan Bullnose" glass-fiber-nylon 5045, ~4.9 g, 5 mm/9.5 mm hub) is a plausible but **unconfirmed** match, and seeding its numbers onto this row would be exactly the forbidden move — guessing across an unverified near-duplicate, structurally the same mistake as copying `gemfan_5030.mass_g`. `bind_propeller_from_catalog` already projects `mass_g` when set, and `PropellerSpec` already carries `source_url`/`identity_status`, but is missing `source_note` (present on Motor/Battery/ESC) — a small, sibling-consistent schema gap. A genuinely good precedent exists in the same file: `gf_5045x3` already cites a real EMAX-shop propeller listing and its seeded `mass_g: 4.5` independently matches an ABS-material figure found via a fresh search — nothing to add there except a `source_note` quote once the schema field exists. Recommendation: **B0 for `gemfan_5045_hbn`'s missing mass/hub/blade-count** (leave the gap; consider downgrading `identity_status` from `"verified"` to `"partially_verified"`, matching the already-honest precedent on `hq_5045_bn`), plus an optional **B1, schema-only** move (`PropellerSpec.source_note`) that seeds nothing new but lets already-sourced rows (`gf_5045x3`) carry their quote the way Motor/Battery/ESC rows do.

---

## B. As-is inventory

### `PropellerSpec` (`src/jarvis/knowledge/library.py:263-280`)

```python
class PropellerSpec:
    name: str
    diameter_in: float
    pitch_in: float
    mass_g: float | None = None
    ct: float | None = None
    cp: float | None = None
    compatible_kv_band: tuple[int, int] | None = None
    tags: tuple[str, ...] = ()
    operating_points: tuple[dict[str, Any], ...] = ()
    manufacturer: str | None = None
    model: str | None = None
    part_number: str | None = None
    source_url: str | None = None
    identity_status: str | None = None
```

Only `diameter_in`/`pitch_in` are required (`_propeller_from_raw` raises if either is missing); every other field is already optional, loaded only `if data.get(...) is not None`. **No `source_note` field exists** — unlike `MotorSpec`, `BatterySpec`, and `EscSpec`, which all carry one. A row can cite `source_url`/`part_number`/`identity_status` today but has nowhere to put a verbatim quote justifying a specific number, the way the EMAX motor row's `source_note` does for `height_mm`.

### `library/helices/_datos.json` (18 rows)

| Row | `mass_g` | `source_url` | `identity_status` | Notable |
|---|---|---|---|---|
| `gemfan_5030` | 5 | — | — | Legacy, fully unsourced — the row Locked Stance #1 forbids copying from |
| `gemfan_6040` | 7 | — | — | Legacy, unsourced |
| **`gemfan_5045_hbn`** | **absent** | Oscar Liang **motor** article | `"verified"` | Live SKU under investigation |
| `dal_7040`…`tmotor_24x7_2` | various | — | — | Legacy generic-brand rows, unsourced |
| `hq_5045_bn` | absent | EMAX **motor-product** page | `"partially_verified"` | Same provenance-quality problem as `gemfan_5045_hbn`, already honestly downgraded |
| `gf_5045x3` | 4.5 | EMAX **propeller-listing** page | — (no `identity_status` key at all) | Good precedent — real propeller page, has `part_number` |

Only `gemfan_5045_hbn`, `hq_5045_bn`, and `gf_5045x3` carry any `source_url`/`manufacturer`/`model`/`part_number` identity metadata at all; the rest are bare legacy numbers with zero provenance.

### Live SKU `gemfan_5045_hbn` — exact keys (as bound in `workspace/autonomía-de-10min-9ada1a1b0cca/state.json`)

```json
{
  "diameter_in": {"value": 5.0, "unit": "in", "confidence": 0.95, "source": "declared"},
  "pitch_in": {"value": 4.5, "unit": "in", "confidence": 0.95, "source": "declared"}
}
```

No `mass_g` key at all — confirms `bind_propeller_from_catalog`'s `if spec.mass_g is not None:` guard is correctly omitting it (the catalog row has no `mass_g`, not a bind bug). Catalog row's raw JSON:

```json
"gemfan_5045_hbn": {
  "diameter_in": 5.0, "pitch_in": 4.5,
  "manufacturer": "Gemfan", "model": "5045 HBN",
  "identity_status": "verified",
  "source_url": "https://oscarliang.com/emax-rs2205s-2300kv-motors/",
  "tags": ["gf5045", "hbn", "5inch", "tri-blade", "bullnose"]
}
```

### `bind_propeller_from_catalog` (`src/jarvis/core/catalog_bind.py:168-213`)

Already projects `diameter_in` and `pitch_in` unconditionally, and `mass_g` conditionally (`if spec.mass_g is not None`) with the standard `PropertyValue(unit="g", confidence=0.9, source="declared")` shape — confirming **Locked Stance #3**: nothing needs to change here for a mass number to reach the card the moment the catalog row states one. No `source_note`/hub/blade-count projection exists (there is no such property key convention yet, and none would be needed for plain text display — `_fields` walks `spec.properties` generically).

### Board / 3D — no code change needed to "show properties"

`_geometry_from_spec` already resolves a bare `diameter_in` (no length/width) to `{"shape": "disk", "diameter_mm": diameter_in * 25.4}` — confirmed live: `gemfan_5045_hbn` renders as a 127 mm disk today. Adding `mass_g` (or any other plain numeric property) to a propeller's `properties` dict would show up as an ordinary `_fields` text row with zero code change, exactly like the EMAX motor's `height_mm` — verified by reading `_fields`'s property loop, which is generic over `spec.properties.items()` with no per-family branching.

### Sibling `gemfan_5030` — confirmed forbidden as a source

`mass_g: 5`, no `source_url`, no `identity_status`, no `manufacturer`/`model` — a bare legacy number with zero citation. Copying it onto `gemfan_5045_hbn` (a different pitch, different material family per the live web evidence below) would be exactly the "sibling copy" Locked Stance #1 forbids.

---

## C. Live quotes from each candidate page

Re-fetched fresh (2026-09-09), not reused from any prior report.

**1. The row's own cited page — `https://oscarliang.com/emax-rs2205s-2300kv-motors/`** (an EMAX **motor** review, not a propeller vendor page):

> "**Gemfan 5045 HBN** | 50% throttle: 442g thrust, 6.2A, 104.8W, 4.22 g/W efficiency"
> "**Gemfan 5045 HBN** | 100% throttle: 1375g thrust, 30.3A, 485.3W, 2.83 g/W efficiency"

This confirms the string "Gemfan 5045 HBN" is Oscar Liang's own real test-table label (not fabricated by our seed), and the "100% throttle" row's numbers (1375 g, 30.3 A, 485.3 W) are **exactly** what the motor's own `emax_rs2205s_2300.operating_points` entry for `propeller_sku: "gemfan_5045_hbn"` already reproduces (`thrust_n: 13.4841`, `current_a: 30.3`, `power_w: 485.3`) — good internal consistency, and legitimate identity evidence that this propeller was really used in a documented test. **But** the article states only thrust/current/power at various throttles — no diameter, pitch, mass, hub, or blade count for the propeller itself.

**2. ProgressiveRC — "GemFan 5045 Propellers"** (`https://www.progressiverc.com/products/gemfan-5045-propellers`):

> SKU "HP-GF545O". "5\" length, Glass fiber, 4.5 pitch, 5mm hub diameter." Four props per set (2 CW / 2 CCW). No "HBN" designation anywhere. **No weight listed.**

**3. ProgressiveRC — "GemFan 5045 Bullnose Propellers"** (`https://www.progressiverc.com/products/gemfan-5045-bullnose-propellers`):

> SKU "HP-GF545BNO". "5\" length, Glass fiber, 4.5 pitch, 5mm hub diameter, 4 blades (2 CW/2 CCW)." Designation used throughout is "Bullnose" — **not** "HBN" or "BN". **No weight listed.**

**4. RotorLogic — "Gemfan Propeller Glass-Fiber Nylon Bull-Nose 5045(5x4.5)"** (`https://rotorlogic.com/gemfan-propeller-glass-fiber-nylon-bull-nose-5045-5x4-5-red-cw-ccw-2-pairs/`):

> SKU "GF-NGF5045BN-RED-2P". "5045 (5x4.5)", "5mm hub", "Glass-Fiber Nylon" material. Blade count not explicitly stated. **No weight listed.** "HBN" does not appear.

**5. General web-search aggregation** (Amazon/HobbyKing/Banggood/eMax listings for "Gemfan 5045 Bullnose"/"BN5045", not individually re-fetched beyond the two above): converging figures across retailer copy for the glass-fiber-nylon Bullnose variant are **~4.9 g per prop, 5 mm hub diameter, 9.5 mm hub thickness, tri-blade**; a plain-ABS 5045 3-blade variant (a *different* real Gemfan product, matching the already-seeded `gf_5045x3` row) is **~4.5 g**; a polycarbonate variant is reported at **~3.8 g**. None of these pages call themselves "HBN".

**Conclusion of the search**: "HBN" is real (Oscar Liang used it in his own test table, and it is internally consistent with this catalog's own thrust numbers) but it is **not a manufacturer SKU code** found on any vendor/retailer page searched. The closest real-world match by shape/pitch/material naming convention is the glass-fiber-nylon "Bullnose" family (~4.9 g), but no page anywhere states "this is the exact unit Oscar Liang tested as HBN" — the material variant is a plausible inference, not a verified identity link.

**6. `gf_5045x3`'s existing citation, re-checked for consistency** (`https://shop.emaxmodel.com/collections/all/products/2-pairs-5045-3-blade-propeller-abs-cw-ccw-for-mini-quadcopter`, not re-fetched live in this pass since the row already states a `part_number` "PMAB5045-3" matching the ABS-material product family; the ~4.5 g figure independently corroborated above for ABS 5045 3-blade props): this row's existing `mass_g: 4.5` is **consistent** with independently found evidence — no change needed to its numbers, only a `source_note` once the schema field exists.

---

## D. Accept/reject field table

| Candidate field | Row | Verdict | Reason |
|---|---|---|---|
| `mass_g` | `gemfan_5045_hbn` | **REJECT (this increment)** | No page using the row's own "HBN" designation states a mass; the closest real match (~4.9 g Bullnose glass-fiber-nylon) is an unconfirmed variant guess — structurally the same error as copying a sibling |
| hub diameter/thickness (new field) | `gemfan_5045_hbn` | **REJECT** | Same identity-ambiguity problem as `mass_g`; also a new schema axis, out of a seed-only Buy |
| `blade_count` (new field) | `gemfan_5045_hbn` | **REJECT** | Not stated on the row's own cited page; would need a new schema key regardless (B2 territory per Q9) |
| `identity_status` downgrade `"verified"` → `"partially_verified"` | `gemfan_5045_hbn` | **ACCEPT (candidate)** | The row's own evidence quality (a thrust-test mention, not a spec page) matches `hq_5045_bn`'s already-honest `"partially_verified"` precedent exactly; currently mislabeled `"verified"` |
| `source_note` field (schema) | `PropellerSpec` (all rows) | **ACCEPT (candidate)** | Sibling-consistent addition (Motor/Battery/ESC already have it); adds no new physical claim, just a place to quote what's already cited |
| `source_note` quote | `gf_5045x3` | **ACCEPT (candidate)** | Once the field exists, this row already has a real, verified propeller-listing source and a matching `part_number` — nothing invented |
| `mass_g` / any dim | `gf_5045x3` | **NO CHANGE NEEDED** | Already seeded, already correct, independently corroborated |
| Fixing `source_url` on `gemfan_5045_hbn` to a real propeller-vendor page | — | **N/A — no such page found** | Every vendor/retailer page found describes a *different*, unconfirmed-identical physical product; replacing the URL with one of those would substitute one unverified claim for another |

---

## E. Honesty / ladder matrix

| Phrase | Verdict | Why |
|---|---|---|
| "We know the propeller's declared size (5 in / 4.5 in pitch) and it renders as a disk of the right diameter." | **TRUE, already shipped** | `diameter_in`/`pitch_in` are the row's required fields; `_geometry_from_spec` already converts diameter to mm; no work needed |
| "Hub height = motor height (31.7 mm)." | **FALSE, forbidden** | Two unrelated physical facts on two unrelated components; motor `height_mm` is a citation for the motor card only — never stitched onto propeller geometry, and the propeller's hub thickness (~9.5 mm on the plausible-but-unconfirmed Bullnose match) isn't even sourced for this row |
| "Board text = CAD-verified assembly." | **FALSE, out of scope** | A text field is a citation, never a verified fit/assembly claim — plate L×W and `"cabe"` stay out per lock |
| "Mass from sibling `gemfan_5030`." | **FALSE, explicitly forbidden** | Locked Stance #1; different pitch, no evidence the two are even the same material family |
| "Visualization (the flat disk) verifies the mass/hub numbers." | **FALSE** | The disk comes from `diameter_in` alone; it has never depended on, and does not validate, any mass/hub number — a disk renders identically whether or not `mass_g` is present |
| "We can label `gemfan_5045_hbn`'s mass with the closest matching retail listing, noting it's an inference." | **REJECT for a *seeded* number** | A `source_note` can honestly describe uncertainty in prose, but the locked pattern (Motor B1) seeds only a **cited, unambiguous** number — an inferred/best-guess number with a hedge is a different (weaker) honesty class than every other seeded field in this catalog and would set a bad precedent |
| "`hq_5045_bn`'s `partially_verified` status is the right honesty label for this evidence quality." | **TRUE, and `gemfan_5045_hbn` should match it** | Same underlying gap (a motor-context article, not a propeller spec page) already has a correct, shipped label on the sibling row |

**Ladder rung of the recommended Buy**: rung 3 (Motor height B1's rung) does **not** repeat here for `gemfan_5045_hbn` itself — this SKU stays at whatever rung it already occupies (declared size only), because no citable number exists to climb with. The schema (`source_note` field) move is a **rung-0, mechanical** parity fix (matching an existing sibling pattern), not a new geometry rung.

---

## F. Buy recommendation

**Rank:**

1. **B0 for `gemfan_5045_hbn`'s missing mass/hub/blade-count — leave the gap.** No real page ties a physical number to the exact "HBN" identity; inventing or inferring one across an unconfirmed variant match repeats the mistake this IC was written to prevent (Locked Stance #4's own explicit fallback: "If none: recommend B0"). Optionally within the same B0: downgrade `identity_status` from `"verified"` to `"partially_verified"` to match `hq_5045_bn`'s already-honest precedent — this is a correction to an existing mislabel, not a new seed.
2. **B1, schema-only, if Engineer wants it**: add `PropellerSpec.source_note: str | None = None` (mirroring Motor/Battery/ESC exactly) and use it **only** on `gf_5045x3` — a row that already has a real, verified propeller-listing source and a corroborated number. This seeds **zero new physical facts**; it only lets an already-good row carry the same provenance quote the EMAX motor row does. `bind_propeller_from_catalog` needs no change (it never projects `source_note` as a property — that field lives on the catalog record, same as it does for Motor/Battery/ESC today).
3. **Defer**: hub diameter/thickness and `blade_count` as new schema axes (B2 territory) — no row in the library currently has verified data worth adding these keys for, and Engineer's own lock keeps plate L×W / `"cabe"` out regardless.

**Default lean (required)**: **B0 for the live SKU's own gap; B1 only as the narrow schema-parity move described above, applied to `gf_5045x3`, not `gemfan_5045_hbn`.** This is the closest honest analogue to "prefer B1 seed-only if a real page states mass and bind already displays it" — that condition is met for `gf_5045x3`, not for the live `gemfan_5045_hbn` SKU the Engineer actually asked about.

---

## G. Explicitly not this increment

Seeding `mass_g`/hub/blade-count on `gemfan_5045_hbn` from an unconfirmed retailer match · copying `gemfan_5030.mass_g` · treating the Oscar Liang motor article as a propeller spec page · disk+height=cylinder · inventing `motor_power_w` · plate L×W · `"cabe"` · Three.js · Conversation Engine · Structure PASS · version bump · any `src/` edit (none made — this is a report only).
