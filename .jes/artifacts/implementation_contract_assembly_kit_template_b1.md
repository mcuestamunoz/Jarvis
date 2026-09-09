# Implementation Contract — Assembly kit template B1-min (`power_connector` + `signal_harness`)

**Project:** Jarvis  
**Date:** 2026-09-09  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** IMPLEMENTED — REVIEWED PASS WITH NOTES @ **2507** — Engineer smoke  
**Parents:**
- Engineer ★ **`B1-min`** (2026-09-09) — [next steps](engineer_next_assembly_kit_template.md)
- [investigation_review_assembly_kit_template_b0.md](investigation_review_assembly_kit_template_b0.md) **PASS WITH NOTES**
- [engineer_lock_assembly_kit_template.md](engineer_lock_assembly_kit_template.md)
- Plate L×W **B0** — **out**. Fit / `"cabe"` / STEP / Conversation Engine / GetFPV scrape — **out**

**Type:** Visibility of two **pending kit holes** without widening architecture/PASS.  
**Not** a new block. **Not** append to `BLOCK_TO_COMPONENTS["propulsion"|"energy"]`. **Not** XT60 catalog. **Not** 3D.

**Baseline:** package **`0.3.8`** · suite **2497**

**Output:** `.jes/artifacts/implementation_report_assembly_kit_template_b1.md`

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Shape | **B1-min** + **B3** sentence (same IC) |
| 2 | Keys | **Only** `power_connector`, `signal_harness` |
| 3 | Registry | New `KIT_TO_COMPONENTS` keyed by **domain** (`dron` / `uav`). **Never** mutate `BLOCK_TO_COMPONENTS` lists |
| 4 | Domain gate | Kit applies iff `VEHICLE_TYPE_ALIASES[vehicle_type]` ∈ `{dron, uav}` **and** the key’s home block is in `system_blocks`. No `vehicle_type` → **zero** kit keys (existing tests stay) |
| 5 | PASS | `_block_progress_status` / ERF propulsion·energy·structure / hover / autonomy **byte-identical**. Architecture stays **4/4** on the seven energy keys |
| 6 | BOM / ASSEMBLY READY | Kit holes **are** BOM `missing`. A 7-key-complete dron is **no longer** BOM-complete. That is the product. Do not twin-preserve empty `missing` on those fixtures |
| 7 | DEFINE | After architecture **4/4**, IDLE declare-phrase opens a **single-key** wizard (G18 pattern). Do **not** fold kit keys into composite energy/propulsion Phase A |
| 8 | 3D / catalog / version | **No** solids, **no** SKU family, **no** bump |

**Product sentence:**

```text
Tras 4/4, el Board muestra dos slots: conector de potencia y harness de señal.
Continuity pide declararlos. No propone XT60. Hover y PASS de bloques no cambian.
Si el usuario no los conoce, el hueco sigue pendiente.
```

**Not:**

```text
añadir keys a propulsion · arquitectura 5/5 · adaptador de hélice · VTX/RX
· scrape Included · cilindro · L×W Rooster · Conversation Engine
```

---

## 1. You (Claude)

- Implement the registry + the **named** call sites below. One helper; do not copy-paste union logic.
- **STOP** if you “fix” PASS by putting kit keys on `BLOCK_TO_COMPONENTS`. That is B1-naive, forbidden.
- **STOP** if kit DEFINE opens the energy/propulsion **composite** wizard (battery/motors/esc). Single key only.
- Do not seed catalog JSON. Do not invent millimetres. `ui/` empty unless `kind: "slot"` is broken (it should not be).
- Full pytest green. Report every **existing** test assertion you changed (BOM `missing`, Continuity next-step) with the reason “kit holes now expected.”
- Write the report when done.

---

## 2. Intent

```text
vehicle_type → dron|uav
        ↓
KIT_TO_COMPONENTS[domain] = [power_connector, signal_harness]
        ↓
Board slots + BOM expected + Continuity missing     YES
architecture / composite PASS / hover               NO (BLOCK_TO only)
IDLE 4/4 “definir conector” → wizard [power_connector] only
```

---

## 3. Locked behavior

### 3.1 Registry (`system_architecture_catalog.py`)

This module stays **schema-free** (strings/lists/dicts).

```text
KIT_TO_COMPONENTS: dict[str, list[str]] = {
    "dron": ["power_connector", "signal_harness"],
    "uav":  ["power_connector", "signal_harness"],
}
KIT_HOME_BLOCK: dict[str, str] = {
    "power_connector": "energy",
    "signal_harness":  "control",
}
```

`robot` / `coche` / `rover`: **no** entries (empty lookup).

Public helpers (names may vary; behavior locked):

| Helper | Returns |
|---|---|
| `canonical_vehicle_domain(vehicle_type: str \| None) -> str \| None` | `VEHICLE_TYPE_ALIASES` after `_normalize`, else `None` |
| `kit_component_keys(vehicle_type, system_blocks) -> list[str]` | Keys in `KIT_TO_COMPONENTS[domain]` whose `KIT_HOME_BLOCK` is in `system_blocks`, **order preserved**. `[]` if domain unknown / `vehicle_type` empty |
| `bom_and_board_expected_keys(system_blocks, vehicle_type) -> list[str]` | `blocks_to_component_keys(blocks)` then append kit keys not already present |

**Do not** change `blocks_to_component_keys` — architecture/PASS keep using it (or keep using `BLOCK_TO_COMPONENTS` directly, as today).

### 3.2 Board (`spatial_board.py`)

`project_spatial_nodes` reads `current_parameters["vehicle_type"]`.

`_expected_keys_by_column(blocks, vehicle_type=None)`: existing first-match `BLOCK_TO` walk **unchanged**, then append each kit key to the **column of its home block** (index of `energy` / `control` in `blocks`). If that home block is not declared, skip the key.

Slot payload **unchanged**: `kind: "slot"`, `estado: no declarado`, no SKU, no `geometry`.

Existing projector tests **without** `vehicle_type` must stay **7** slots for a 4-block empty project (T0 regression). New tests set `vehicle_type="dron"`.

### 3.3 BOM (`project_closure.py` `build_component_bom`)

`expected_keys` = `bom_and_board_expected_keys(blocks, vehicle_type)` when `blocks` non-empty. `vehicle_type` from `current_parameters`.

Kit keys absent from `components` → `missing` (same loop as today). Declared kit roots classify like any extra/root spec. `parent_key` children still excluded.

### 3.4 PASS / ERF / hover (must not read kit keys)

No edits to `_block_progress_status` component lists (orchestrator **and** `engineering_readiness.py`). No new `system_blocks`. No `BLOCK_TYPE` row.

Twin (T5): fixture with 7 energy keys present, `vehicle_type=dron`, kit absent → architecture fraction still `4/4`; propulsion/energy/structure ERF (or `_block_progress_status`) **equal** to the same fixture with `vehicle_type` unset **or** to pre-computed expected `complete`. Hover/`resolve_operating_point` not invoked unless already in that fixture — if you add a calc twin, numbers must match a no-kit clone.

### 3.5 Continuity (B3)

No new rank. Rank 4 already uses BOM `missing[0]`.

When **any** kit key is in `missing`:

- `next_step` may stay `Define el componente pendiente: {key}.` (`key` will be `power_connector` if both missing, because kit keys append **after** the seven).
- `next_why` (or situation line — one place, not both duplicated essays) **must** include:

```text
La arquitectura 4/4 no es la lista de montaje. Falta declarar: power_connector, signal_harness.
```

List only the kit keys that are actually still `missing`. Do not claim XT60.

### 3.6 DEFINE / IDLE (G18-shaped, not FN-014)

FN-014 `_try_start_acquisition_from_mention` returns `None` when architecture is complete. **Do not** add kit keys to `_owning_block_for_component` via `BLOCK_TO_COMPONENTS` — that would make “definir conector” look like an **energy** mention and open the **composite** energy wizard (battery/motors). Forbidden.

**Do:**

1. `COMPONENT_TERM_ALIASES` (whole-word only):

```text
power_connector → power_connector
conector        → power_connector
xt60            → power_connector   # names the hole, does not seed a SKU
signal_harness  → signal_harness
harness         → signal_harness
```

Do **not** alias bare `cable` / `cableado`.

2. `COMPONENT_PROMPTS` for both keys (Brief: what it is, example, pending is OK). No catalog help-choose for these keys this IC.

3. IDLE, **only when** `_next_pending_block is None` (architecture complete or no pending block), declare-verb + alias resolves to a kit key for this project’s `kit_component_keys(...)`:

```text
start_define_missing_params([that_key], reason=MISSING_COMPONENT_DEFINITION)
```

Same as G18 `start_define_missing_params(["motors"], ...)`. Mid-architecture: kit DEFINE **does not steal** FN-014 (slots may already show; Continuity still asks architecture holes first because they precede kit in `expected_keys`).

4. `_handle_component_description` fallback already `set_control_component` + “registrado.” Keep it. Completeness low/declarative OK. **No** `catalog_ref`. **No** `_geometry_from_spec` keys.

Unknown → user never opens the wizard → slot remains. Success.

### 3.7 Existing tests you will have to update

Any test that sets `vehicle_type` to `dron`/`uav`/`drone`/… **and** asserts BOM `missing == []` (or Continuity “Diseño validado”) with only the seven keys present: change the assertion to include the two kit holes **or** declare stub kit specs in the fixture if the test is about something else (hover, frame class, …).

Tests **without** `vehicle_type` must not grow `missing`.

Report the list. Do not delete tests.

---

## 4. Tests (new file)

`tests/test_assembly_kit_template_b1.py`:

| ID | Behavior |
|---|---|
| T0 | 4 aerial blocks, **no** `vehicle_type`, empty components → Board slot ids = the **seven** keys only (regression vs current projector) |
| T1 | `vehicle_type=dron`, 7 roots present, kit absent → Board has slots `power_connector` and `signal_harness`; **no** extra architecture slots; `derive_architecture_progress` still complete 4/4 |
| T2 | Same state → BOM `missing` contains exactly those two (order: connector then harness). A clone with `vehicle_type` unset → those keys **not** in `missing` |
| T3 | Continuity on T2 dron state (physics not blocking): `next_step` names `power_connector`; `next_why` (or situation) contains the B3 sentence and both kit keys |
| T4 | Architecture 4/4, IDLE phrase with declare verb + `conector` → `pending_missing_params == ["power_connector"]` (or returned wizard targets that key). Must **not** be `["battery", "motors"]` |
| T5 | Twin: `_block_progress_status` for `propulsion`/`energy`/`structure`/`control` on T1 state **equals** the no-`vehicle_type` clone (all `complete` if 7 keys present) |
| T6 | `vehicle_type=robot`, actuation/energy/control/transmission blocks as in `SYSTEM_ARCHITECTURES["robot"]` → **zero** kit slots |
| T7 | T1 + stub `ComponentSpec` `power_connector` (low OK) → that slot **gone**; `signal_harness` slot remains; propulsion status still `complete` |

Use existing projector/BOM/Continuity/orchestrator test helpers where they exist. Do not hit the network. Do not write `workspace/`.

---

## 5. Files (expected)

| Path | Change |
|---|---|
| `src/jarvis/core/system_architecture_catalog.py` | `KIT_*` + helpers. **`BLOCK_TO_COMPONENTS` values unchanged** |
| `src/jarvis/workspace/spatial_board.py` | union + home-block columns; read `vehicle_type` |
| `src/jarvis/core/project_closure.py` | BOM expected via helper |
| `src/jarvis/core/acquisition_target.py` | aliases + prompts |
| `src/jarvis/core/orchestrator.py` | IDLE 4/4 kit single-key wizard only |
| `src/jarvis/core/project_continuity.py` | B3 clause when kit keys missing |
| `tests/test_assembly_kit_template_b1.py` | T0–T7 |
| existing tests | only the `vehicle_type=dron` BOM/Continuity fixtures named in the report |
| `ui/` | **empty** |
| `.jes/artifacts/implementation_report_assembly_kit_template_b1.md` | write |

`engineering_readiness._block_progress_status`: **empty diff** unless you prove a bug; kit must not appear there.

---

## 6. Engineer smoke (after Cursor review)

Live demo is a **dron** with the seven keys. After this Buy:

- Board: **two** new dashed slots (`power_connector`, `signal_harness`).
- Architecture fraction still **4/4**.
- Continuity names the kit hole + B3 sentence.
- Hover / vatios / autonomy numbers **unchanged**.
- Leave pending if you don’t know the parts — that is ACCEPT.

Record `engineer_smoke_assembly_kit_template_b1.md`.

---

## 7. Done when

- [ ] T0–T7 green; full pytest green  
- [ ] `git diff` shows **no** new strings inside `BLOCK_TO_COMPONENTS` lists  
- [ ] No catalog seed, no version bump, no geometry, no `prop_adapter`  
- [ ] Report lists existing-test updates  
- [ ] Report written  

---

## Explicitly not this IC

`prop_adapter` · VTX/RX/camera · Rooster HD/VTX plate seed (later B2) · plate L×W · STEP · `"cabe"` · in-product scrape · Conversation Engine · XT60 library row
