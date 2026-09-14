# Implementation Contract — Estimated-temporary ESC height (Skystars KO50A II) B1

**Project:** Jarvis  
**Date:** 2026-09-14  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer smoke

**Status:** IMPLEMENTED · review **PASS WITH NOTES** — awaiting Engineer smoke ACCEPT  
**§0.1 bag (filled by Engineer after B0 pause):** `height_mm: 8` · `projects: 10-min-autonomía`  
**Parents:**
- Estimated-temporary plate B1 **CLOSED** — [IC](implementation_contract_geometry_estimated_temporary_plate_b1.md) — lock #2 / §4 debt: *“Estimated dims for non-plate families → Separate ★”* — **this Buy is that follow-on**, scoped to ESC (Skystars KO50A II)
- Library FC/sensors P0 **CLOSED** — [IC](implementation_contract_library_fc_sensors_b1.md) · review N1: FC bind exists, IDLE rebind not wired
- Live catalog seeds (already on disk, **not** invented here):
  - `library/esc/_datos.json` → `skystars_ko50a_ii_bls` — L×W **41×46**, mass **13.3 g**, **no** `height_mm`
  - `library/fc/_datos.json` → `skystars_f4_v4` — identity only, **no** L×W×H
- ESC visor rebind B1 **CLOSED** — `cambiar esc` already lists / binds this SKU (partial box today)
- Feature locks: craft montage honesty · no silent invent mm as `declared` / Class A catalog fact

**Type:** Honest **hybrid envelope** for Skystars ESC: **cited** L×W (+ mass) from catalog + **Engineer-supplied** `height_mm` with `source=estimated_temporary` on the **project** component — same gates / disclosure philosophy as provisional plate.  
**Not** quiet `height_mm` seed into `library/esc` as verified. **Not** inventing H from SpeedyBee 8 mm / mass / photo. **Not** plate-box. **Not** Path N. **Not** version bump. **Not** full evidence taxonomy.

**Output:** `.jes/artifacts/implementation_report_geometry_estimated_temporary_esc_skystars_b1.md`

**Checkpoint:** package **`0.4.1`** · suite ≥**2911** · UI ≥**105** (or current green at ★ time)

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-estimated-temporary-esc-skystars`** — complete Skystars KO50A II **Board box** without lying that H is cited |
| 2 | Evidence (locked prose) | Family/docs: **41 × 46 mm** and **13.3 g** appear on KO50 / standalone KO50A materials already mapped to catalog `length_mm`/`width_mm`/`mass_g`. **No reliable source found** for thickness/height of the **KO50A II** revision specifically; current pack sheet also **omits H**. Therefore H is **UNKNOWN as fact** → may only enter the **project** as `estimated_temporary` |
| 3 | Catalog SoT rule | `library/esc/_datos.json` **keeps** omitting `height_mm` for `skystars_ko50a_ii_bls`. **Forbidden:** add a numeric `height_mm` to that JSON row (even with a soft note). Update `source_note` only to point at this Buy / “H = project estimated_temporary, not catalog” |
| 4 | Hybrid property sources | After bind (or refresh): `length_mm`/`width_mm`/`mass_g` stay `source=declared` from catalog; **only** `height_mm` is written `source=estimated_temporary`, `confidence=0.3` (same as plate writer) |
| 5 | Schema | Reuse existing `PropertyValue.source` literal `estimated_temporary` — **no** new enum this Buy |
| 6 | Writer | New thin writer (name OK, e.g. `set_estimated_temporary_esc_height` / generalize plate writer carefully): may set **only** `height_mm` estimated on component key `esc` (or the live ESC key) when the component already has cited L+W (catalog-bound Skystars or any ESC with L+W and missing H). **Do not** weaken plate-only writer semantics; prefer additive helper over broadening plate allowlist blindly |
| 7 | Continuity / IDLE | Phrase family parallel to plate: Spanish triggers with `estimada` / `temporal` / `provisional` + `esc` + height mm (exact patterns in report). Optional one-shot after `cambiar esc` / catalog pick: if §0.1 filled and ★ Path D, apply estimated H in the same session — document path taken |
| 8 | §0.1 number | Engineer ★ supplies **`height_mm`** in the bag — **agent must not invent**. Empty → **B0 hold** |
| 9 | Gates (reuse) | Existing screening / fit-relations / `cabe` / fit-attestation SET already treat **any** of L/W/H with `estimated_temporary` as `estimated_dims` — **keep that**. Add regression: hybrid ESC (declared L/W + estimated H) → refuse `cabe` / refuse `declaro verificado` / fit checklist `estimated_dims` |
| 10 | Disclosure | Mandatory Spanish block on success, e.g. `ESC · H ESTIMADA TEMPORAL · L×W citada (41×46) · evidencia H: ninguna ficha KO50A II · sustituir al citar/medir H: SÍ` — Continuity message (+ Board badge if DTO already shows property source; no Three.js rewrite) |
| 11 | Replace path | Later cited/measured H → `source=declared` (catalog seed **or** declared write) **overwrites** estimated H; clear fit attestation per existing fingerprint-clear rules. Prefer: when a future catalog `height_mm` appears, `refresh_component_from_catalog` replaces estimated H with declared |
| 12 | FC in this Buy | **Out of primary bag** unless Engineer fills §0.2. Identity `skystars_f4_v4` stays no-box. Optional additive locks in §0.2 only |
| 13 | Forbidden | Invent H · seed catalog H · treat estimate as `declared` · claim `cabe` with provisional H · use SpeedyBee/`hobbywing` H as Skystars H · version bump · Conversation Engine |
| 14 | Live apply | ★ picks project(s) or tests-only. Recommend smoke on craft project that already uses / will use Skystars ESC |

**Product sentence:**

```text
El ESC Skystars KO50A II tiene L×W y masa citadas; la H no está en ficha.
Jarvis deja poner H como ESTIMADA TEMPORAL (como la placa), enseña el
sólido en Board, y se niega a validar “cabe”/VERIFIED con esa H.
Cuando haya cita o calibre, se sustituye.
```

### 0.1 Estimated H bag — **Engineer fills under ★**

```text
### esc skystars_ko50a_ii_bls height estimated_temporary
purpose: architecture_validation / Board solid / layout
evidence: none for KO50A II H (L×W 41×46 + 13.3g cited elsewhere — already in catalog)
replace_when_cited_or_measured: YES
height_mm: 8          # Engineer-chosen estimate (2026-09-14); NOT a KO50A II citation
projects: 10-min-autonomía
forbidden_copy:
  - do NOT copy SpeedyBee BLS 60A height 8.0 as this value without explicit Engineer override in this bag
  - do NOT invent from mass or photo pixel-scale
# Note: Engineer explicitly chose 8 after SpeedyBee 8.0 was shown as class reference only.
```

### 0.2 Optional FC bag (only if Engineer wants FC solid this ★)

```text
### flight_controller skystars_f4_v4 estimated_temporary box
purpose: architecture_validation
evidence: none (Rotorama pack page has no board L×W×H)
replace_when_cited_or_measured: YES
length_mm: ?   # all three required if this bag is taken
width_mm: ?
height_mm: ?
# If any ? left empty → skip FC envelope this Buy (identity-only remains OK)
# Catalog library/fc row must NOT gain these mm as verified
# Prefer project-only estimated_temporary on all three axes + disclosure
# Optional additive: wire IDLE FC rebind (library review N1) — only if ★ says yes here: [ ] yes / [ ] no
```

**Rejected without override:**

| Source | Why |
|---|---|
| Silent `height_mm` in `library/esc` for KO50A II | Contaminates Class A / “sé esto” |
| Copy SpeedyBee 8.0 / Hobbywing 12.0 as declared Skystars H | Wrong SKU evidence |
| Mark hybrid box fully `declared` | Lies about H |
| Auto-pick H from “typical 4in1” | Invent |

---

## 1. You (Claude)

1. Confirm catalog row still has L×W + mass, **no** `height_mm`; tighten `source_note` per lock #3.  
2. Additive writer + Continuity parse for estimated ESC H (locks #6–#7).  
3. Path: bind/rebind Skystars ESC → apply §0.1 H estimated → Board shows **box** (L×W×H).  
4. Gates: T-tests for hybrid estimated child (lock #9). Disclosure string (lock #10).  
5. If §0.2 fully filled + ★: estimated FC box writer (project-only) and/or FC IDLE rebind — **only** what ★ checks; else leave FC untouched.  
6. Tests T1–T8. No version bump. No invent mm.  
7. Report: exact phrases, gate strings, whether §0.2 taken.

**STOP if** forced to write `height_mm` into `library/esc/_datos.json`, or to skip gates, or to invent §0.1.

---

## 2. Tests

| ID | Behavior |
|---|---|
| T1 | Catalog `get_esc("skystars_ko50a_ii_bls")` → L=41, W=46, mass=13.3, `height_mm is None` |
| T2 | Bind ESC → L/W `declared`; no H yet → geometry **not** full box (same as today) |
| T3 | Apply estimated H from writer → H `source=estimated_temporary`; L/W still `declared`; geometry **box** |
| T4 | `cabe` / screening with that ESC as child → `estimated_dims` refuse (no overlap verdict) |
| T5 | Fit attestation SET involving that ESC → refuse / no write |
| T6 | Fit-relations checklist row → `estimated_dims` (not attested) |
| T7 | Success copy includes ESTIMADA/TEMPORAL + replace-when-cited signal |
| T8 | Full pytest green; package `0.4.1`; **no** `height_mm` key added under catalog JSON for this SKU |
| T9 | (Only if §0.2 taken) FC estimated box project-only; catalog FC row still dim-less |

---

## 3. Smoke (Engineer)

1. `cambiar esc` → pick `skystars_ko50a_ii_bls` (or rebind).  
2. Declare/apply estimated H with §0.1 mm → Board shows ESC **box**; disclosure visible.  
3. `cabe` / `relaciones` involving ESC → **refuse** / `estimated_dims` (not a false “cabe”).  
4. Confirm `library/esc/_datos.json` still has **no** `height_mm` for this SKU.  
5. (If §0.2) FC solid + same gate honesty; else FC remains identity-only (expected).

---

## 4. Out of scope (named debt)

| Item | Note |
|---|---|
| Catalog-verified KO50A II H when a primary cite appears | New tiny Buy / seed; then refresh replaces estimate |
| Full Skystars FC L×W×H cite | Data-gated; §0.2 only if Engineer estimates |
| Library N1 FC IDLE rebind alone | Only if ★ checks §0.2 rebind box |
| Estimated dims for battery / motors / props | Still separate ★ |
| Full evidence taxonomy enum | Still later |
| Plate-box / Path N | Unchanged holds |

---

## 5. Done when

- [ ] ★ + filled §0.1 `height_mm`  
- [ ] Writer + Continuity + gates + T1–T8 (+ T9 if §0.2) + report  
- [ ] Engineer smoke ACCEPT  
- [ ] Catalog JSON still omits Skystars ESC `height_mm`

---

## 6. Handoff

```text
Engineer → ★ + fill §0.1 height_mm (required)
           optional §0.2 FC estimate + optional FC rebind checkbox
Claude   → implement + report (no catalog H seed)
Cursor   → review
Engineer → smoke §3 · later replace H when cited/measured
```
