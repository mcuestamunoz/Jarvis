# Investigation Report — Kit SKUs D (XT60 / harness into existing holes)

**IC:** [investigation_contract_kit_connector_harness_skus_d.md](investigation_contract_kit_connector_harness_skus_d.md)
**Investigator:** Claude Code
**Date:** 2026-09-09
**Checkpoint:** package `0.3.8` · suite 2523

**Do not implement — this is a read-only report. No `src/`/`library/` edit made.**

---

## Executive summary

The two kit holes (`power_connector`, `signal_harness`) exist and already accept free text without `catalog_ref` — confirmed live on the demo project (`autonomía-de-10min`): `power_connector` is literally `{"name": "XT60", ..., "catalog_ref": None}`, `signal_harness` is `{"name": "cable JST-SH 6 pines", ..., "catalog_ref": None}`. `CatalogRef.family` is a closed `Literal` with exactly 5 members (`motor`/`battery`/`propeller`/`esc`/`frame`) — no connector family exists, and widening it is a real, name-worthy contract change, not a JSON-only seed. A live web check (not a scrape — two individual, cited product pages) confirms at least one honestly seedable row per key exists today: Pololu's own XT60 product page (item #2175: 60A, yellow, 1×2 pin, no mass, no dimensions) and The Pi Hut's JST-SH 6-pin cable (SKU CAB1009: 1.0mm pitch, 26AWG, 100mm/300mm length options, no mass) — both real, both silent on mass/L×W×H, so both would seed with **zero** geometry-relevant fields, `_geometry_from_spec` staying `None` by construction (no L×W×H triple, no diameter). `bind_esc_from_catalog` is confirmed as a genuine "bind exists, no live UX" precedent (no `_offer_component_esc_catalog` anywhere) — the smallest possible shape for a family with identity but no wizard. **Recommendation: B2** — one small, **unified** `kit_hardware`-shaped family (not two full families) seeded with exactly the two cited rows above, bind-only (ESC-shaped, no help-choose), free text staying the only live way to close these holes today. B1 (adding a single-key help-choose/numbered-pick) is a reasonable, smaller-than-feared next step (one shared offer function, not two clones) but is **not** this investigation's default — the "template first, then catalog" order is satisfied by B2 alone.

---

## A. What exists vs. the hole

| Family/key | Catalog bind (`bind_*_from_catalog`) | Live catalog-pick UX (`_offer_component_*`/help-choose) | Kit-key free-text UX (relabel, no `catalog_ref`) |
|---|---|---|---|
| `motor` | Yes | Yes (`_offer_component_motor_catalog`, numbered pick) | N/A (not a kit key) |
| `battery` | Yes | Yes (`_offer_component_battery_catalog`) | N/A |
| `propeller` | Yes | Yes (`_offer_component_propeller_catalog`) | N/A |
| `frame` | Yes | Yes (`_offer_component_frame_catalog`) | N/A |
| `esc` | Yes (`bind_esc_from_catalog`) | **No** — confirmed by grep, no `_offer_component_esc_catalog` exists anywhere; its own docstring says so explicitly ("No CLI/UX entry point calls this yet") | N/A |
| `power_connector` | **No** — no family, no loader, no bind function | **No** | **Yes** — free text ("XT60") relabels to a declarative `ComponentSpec`, `catalog_ref` always `None` |
| `signal_harness` | **No** | **No** | **Yes** — same shape, confirmed live ("cable JST-SH 6 pines") |

**The asymmetry named in §1 is real and precisely inverted between the two existing patterns**: kit keys have UX (a working Brief + relabel + skip path) **without** any catalog identity underneath; `esc` has catalog identity **without** any UX to reach it live. Neither gap is an accident — kit B1-min was deliberately UX-first (per the Engineer's own locked order), and ESC's bind was deliberately identity-first with UX explicitly deferred.

---

## B. Candidate Buys

| ID | Shape | Assessment |
|---|---|---|
| **B-naive** | Scrape a connector aisle / invent a 3D box / infer XT60-vs-XT30 from the bound battery / seed `prop_adapter` SKUs in the same Buy / add a `BLOCK_TO_COMPONENTS`/`KIT_TO_COMPONENTS` entry | **Refused.** Section A's own evidence shows even the *best-documented* connector standard (XT60) has no reliably-citable mass/dimensions on the pages actually checked — a 3D box would have to be invented. Battery-vs-connector compatibility is a "later, user-confirmed" honesty clause (locked stance #4), never a silent refusal engine. `prop_adapter` catalog and any `BLOCK_TO`/`KIT_TO` edit are explicitly out of this investigation's two keys. |
| **B0** | Park — free text only, no `library/` rows | Safest, zero schema risk, but does not answer the Engineer's own question ("should Jarvis also offer curated rows the way motors/batteries/frames do") — leaves the BOM saying only the word "XT60," never which XT60. |
| **B2** | Seed **one** row per key + **one small, unified** loader/dataclass/bind function + a **minimal, named** `CatalogRef.family` widening. **No** help-choose (ESC-shaped). Free text unchanged. | **Default recommendation** — see reasoning below. |
| **B1** | B2 **plus** a single-key `"ayúdame a elegir"`/numbered-pick UX, reusing `_wants_catalog_help`, wired into the *existing* kit single-key wizard (never folded into the composite energy/propulsion wizard) | A real, reasonable next step — but not this Buy's default (see below). |

### Why B2, and why *one* small family, not two

Locked stance #5 requires "a new folder + dataclass + loader + `bind_*_from_catalog`, **or** an explicit refuse of a sixth family" for connector/harness identity. The IC explicitly invites comparing that against "one `kit_connectors` folder with a `kit_key` field," and asks me to argue rather than default to a generic parts dump. I looked at what a real seed row for each key would actually contain (per the cited pages below): `power_connector` → `current_a=60`, `color="yellow"`, `pin_config="1x2"`, `part_number="2175"` — no mass, no geometry. `signal_harness` → `pitch_mm=1.0`, `wire_gauge_awg=26`, a cable-length figure, `part_number="CAB1009"` — no mass, no geometry. These are **structurally identical, thin identity+electrical bags** — neither needs the kind of rich, family-specific shape `MotorSpec`/`FrameSpec` have (operating points, plate lists, standoff heights, design-space fields). Building **two** full families for two single-row, near-identical shapes would duplicate the entire `_load_X`/`_X_from_raw`/`get_X`/`list_X`/`has_X` boilerplate (confirmed by reading `ComponentLibrary`'s existing five families — each is 40–60+ lines) for content that fits in under ten fields combined. A **single** new family — one dataclass (e.g. `KitHardwareSpec`, fields: `kit_key: Literal["power_connector", "signal_harness"]` plus the few electrical/identity fields above), one `library/kit_hardware/_datos.json`, one loader, one `bind_kit_hardware_from_catalog(sku)` that reads the row's own `kit_key` to decide which component key it targets — still maps **1:1** to the two existing holes (never a generic "any part" dump; the dataclass has no room for anything beyond what these two specific keys need), and is the objectively smaller hook. This is the "argue, don't invent a generic parts dump" case the IC asked for: the unification is justified by the *actual thinness and structural similarity* of the two rows, not by a desire for a general catalog-everything mechanism.

`CatalogRef.family` widening, minimal and named: add exactly one new literal, `"kit_hardware"` (not two), since the row's own `kit_key` field (not `family`) is what distinguishes `power_connector` from `signal_harness` — `family="kit_hardware"` + `sku="pololu_xt60_pair"` (or similar) is sufficient identity, exactly mirroring how `family="motor"` doesn't need a second literal per motor shape. This is a one-line, explicitly-named `Literal` change for the future IC to call out, never silently smuggled into a "no schema change" framing.

### Why not B1 as the default

B1's own cost is smaller than the IC's own worst-case framing ("a fifth `_offer_component_*` clone") — a single shared `_offer_kit_hardware_catalog(key)` function (mirroring the same one-family unification argument above) would do for both keys, not two clones. But it is still **new live UX surface** (a help-choose branch, a numbered-pick handler) that this investigation's own governing question ("what is the *smallest* Catalog v1 extension...") doesn't require to answer "can Jarvis bind a named SKU into the hole" — B2 alone already answers that (a project can be bound via `bind_kit_hardware_from_catalog` in a script/test, exactly as ESC already is). Per the Engineer's own locked order ("template first, then catalog bind into named holes" — binding, not necessarily a full picker UX, is the named next step), B2 is the correct-sized answer; B1 is a legitimate, cheap follow-up once B2's identity model exists, not a requirement of this Buy.

---

## Live citations (re-fetched 2026-09-09, not a scrape — two individual product pages)

**`power_connector` candidate**: Pololu, "XT60 Connector Male-Female Pair" (`https://www.pololu.com/product/2175/specs`) — states: current rating "60 A", color "yellow", pin configuration "1x2", pin type "straight", Pololu item number "2175". **Does not state** voltage rating, wire gauge, material, weight/mass, or dimensions — those stay absent, never guessed.

**`signal_harness` candidate**: The Pi Hut, "JST-SH Cable - 6 Pin (pack of 4)" (`https://thepihut.com/products/jst-sh-cable-6-pin-pack-of-4`) — states: pin count "6", pin spacing "1.0mm", cable length options "100mm or 300mm", wire gauge "26AWG", SKU "CAB1009", "female JST SH connectors on both ends". **Does not state** weight/mass. Cable *length* is a real, cited number but is explicitly **not** treated as an L×W×H box input here (a 1-D length is not a 3-axis footprint) — no geometry proposed.

A third page (`handsontec.com`'s XT60 spec PDF) was also checked but returned unreadable/corrupted content on fetch — not used as evidence, named here only for transparency that it was attempted and discarded, not silently skipped.

---

## C. Hook map (exact types/functions — no patches)

- **`CatalogRef`** (`src/jarvis/schemas/action_schema.py:130`): `family: Literal["motor", "battery", "propeller", "esc", "frame"]`. B2 would name adding exactly one member, `"kit_hardware"` — the IC that does this must say so explicitly (locked stance #6); this report does not pretend a connector fits `"esc"`/`"frame"`.
- **`ComponentLibrary`** (`src/jarvis/knowledge/library.py`): five existing `self._motors`/`self._batteries`/`self._propellers`/`self._escs`/`self._frames` caches, each with its own `_load_X`/`_X_from_raw`/`get_X`/`list_X`/`has_X`. B2 would add **one** more (`self._kit_hardware`), not two.
- **`catalog_bind.py`**: `bind_esc_from_catalog` (line 243) is the exact bind-only precedent — no CLI/UX caller, projects `current_a`/optional `mass_g`/optional `length_mm`/`width_mm`/`height_mm` (when a row states them; ESC rows can produce a box — connectors, per the live citations above, would not, since neither candidate row states any dimension). A future `bind_kit_hardware_from_catalog(sku)` would mirror this shape, projecting only `current_a`/`pitch_mm`/`wire_gauge_awg`/etc. — never inventing a `length_mm`/`width_mm`/`height_mm` the source page never stated.
- **Kit DEFINE** (`src/jarvis/core/orchestrator.py`): `_try_start_kit_component_from_mention`, `resolve_kit_mention` (`acquisition_target.py`), the kit relabel block in `_handle_component_description` (`expected_keys[0] in KIT_HOME_BLOCK`) — none of these read `catalog_ref` today; they operate purely on free text. B2 requires **zero** changes here — a `catalog_ref`-bound spec would simply also be a valid, non-`"low"` `ComponentSpec`, which every existing check already accepts.
- **`_wants_catalog_help`** (`orchestrator.py:119`): `_is_stub_or_absent(spec) or spec.catalog_ref is None` — already TRUE for a freeform `"XT60"` kit spec today (no `catalog_ref`), but **nothing currently calls it for `power_connector`/`signal_harness`** (confirmed by grep — no `power_connector_wants_help`/`signal_harness_wants_help` variable exists, unlike the `motors_want_help`/`propellers_want_help` pair in `_handle_component_description`). B1 would be the one to add such a check; B2 must **not** add it (no help-choose branch is the whole point of "ESC-shaped").
- **Who must NOT gain a help-choose branch if the default is B2**: `_handle_component_description` (no new `kit_hardware_want_help`-style gate), `_try_start_kit_component_from_mention` (stays a pure mention-resolution bridge, no catalog suggestions attached), `param_definition_session.py`'s `ParamDefinitionSession.start` (no `ASSISTED_*_PARAMS`-style branch for these keys).
- **`_geometry_from_spec`** (`src/jarvis/workspace/spatial_board.py`): untouched under B2 by construction — it only ever reads `length_mm`/`width_mm`/`height_mm`/`diameter_mm`/`diameter_in` from `spec.properties`; neither cited candidate row would ever populate any of those keys, so a bound `power_connector`/`signal_harness` stays geometry-`None`, exactly like every kit-key spec today.

---

## D. Twin / non-goals

- **PASS/hover/autonomy untouched**: B2 adds no `BLOCK_TO_COMPONENTS`/`KIT_TO_COMPONENTS` entry and no new architecture key — `power_connector`/`signal_harness` remain exactly as gated as they are today (kit B1-min's own `KIT_HOME_BLOCK`), unaffected by whether their spec carries a `catalog_ref`.
- **Kit timing (including N2) unchanged**: this investigation does not touch `project_continuity.py`'s rank-4 B3 sentence or when `power_connector` first appears in `missing` — N2 stays a named, separate, later tidy, exactly as locked.
- **Prop adapter ask B1 unchanged**: no `prop_adapter` catalog row, no change to its own free-text-only "va directa" identity path — confirmed no file touched.
- **No geometry projection in the default Buy**: both cited candidate rows lack mass and dimensions; a future `bind_kit_hardware_from_catalog` would only ever project fields the source page actually states, and neither candidate states anything `_geometry_from_spec` reads.
- **No version bump proposed**; no `library/`/`src/` edit made this cycle (confirmed via `git status --short`, empty for both).

---

## Explicitly not this investigation

Implementing the bind function or any help-choose UX · seeding `library/kit_hardware/_datos.json` (no file created) · widening `CatalogRef.family` in code (named as a *future* IC's job, not done here) · any `KIT_TO_COMPONENTS`/`BLOCK_TO_COMPONENTS` edit · an adapter catalog for `prop_adapter` · VTX/RX · reordering Continuity's N2 `power_connector` nag · `"cabe"` · a GetFPV crawl · a version bump.
