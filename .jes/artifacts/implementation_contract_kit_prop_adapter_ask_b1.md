# Implementation Contract — Prop adapter ask B1 (after hélices; gated kit hole)

**Project:** Jarvis  
**Date:** 2026-09-09  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** IMPLEMENTED — REVIEWED PASS WITH NOTES @ **2523** — Engineer smoke  
**Parents:**
- Engineer ★ **`B1`** (2026-09-09) — “escribe ic” after investigation review
- [investigation_review_kit_prop_adapter_ask_b0.md](investigation_review_kit_prop_adapter_ask_b0.md) **PASS WITH NOTES**
- [investigation_report_kit_prop_adapter_ask_b0.md](investigation_report_kit_prop_adapter_ask_b0.md)
- [engineer_lock_assembly_kit_template.md](engineer_lock_assembly_kit_template.md)
- Kit B1-min **CLOSED** — `power_connector` / `signal_harness` unchanged in timing (do **not** fix N2 connector nag)
- Rooster Included plates B2 **CLOSED** — **out**

**Type:** One hardcoded splice in the propulsion composite wizard + a **presence-gated** kit key.  
**Not** a Conversation Engine. **Not** a generic condition engine. **Not** hub/shaft inference. **Not** XT60 catalog.

**Baseline:** package **`0.3.8`** · suite **2514**

**Output:** `.jes/artifacts/implementation_report_kit_prop_adapter_ask_b1.md`

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Shape | **B1** — Brief in the propulsion wizard **immediately after hélices save**, before ESC |
| 2 | Key | **`prop_adapter`** only |
| 3 | Need | **Never computed.** Do not read `shaft_diameter_mm` / `shaft_bore_mm` / `hub_diameter_mm` to decide whether to ask |
| 4 | Gate | Hole + ask exist iff domain is `dron`/`uav` **and** `motors` **and** `propellers` are declared with completeness ≠ `"low"`. Missing either → **do not ask, no slot** |
| 5 | PASS | **Do not** append `prop_adapter` to `BLOCK_TO_COMPONENTS["propulsion"]` (or any block). Hover / autonomy / `_block_progress_status` **byte-identical** |
| 6 | Persistence | **“va directa”** (or any non-empty description) → declarative `ComponentSpec`, no `catalog_ref`, no geometry. **“no lo sé” / skip** → **no spec written**, Board/BOM hole stays, wizard **advances to ESC** |
| 7 | Relabel | Reuse kit B1-min relabel. Composite remaining keys (`esc`) may trail — see §3.4 |
| 8 | Out | XT60/harness SKUs · VTX/RX · `"cabe"` · 3D · version bump · N2 connector reorder |

**Product sentence:**

```text
Tras guardar las hélices, Jarvis pregunta: ¿cómo montas la hélice?
Va directa / con adaptador (describe) / no lo sé (hueco pendiente).
No compara buje Ø con eje. Hover y PASS de propulsión no cambian.
```

**Not:**

```text
if hub ≈ shaft skip · KIT_TO += prop_adapter from create
· meter la key en BLOCK_TO propulsion · Conversation Engine
· SKU de adaptador · arreglar power_connector mid-architecture
```

---

## 1. You (Claude)

- Implement the registry gate + the **named** wizard splice. One helper for “is `prop_adapter` due?”; one helper to prepend it onto a still-missing list. Do not invent a generic “insert after N” engine.
- **STOP** if you put `prop_adapter` on `BLOCK_TO_COMPONENTS`. Forbidden (widens propulsion PASS).
- **STOP** if you gate on millimetres (shaft / bore / hub). Forbidden (dishonest on current catalog; live 5 min motor has **no** shaft figure).
- **STOP** if create / architecture-A lists `prop_adapter` before hélices exist (`kit_component_keys` today gates on **block declared**, not component presence — that is the bug to close).
- **STOP** if “no lo sé” writes a fake SKU or **blocks** the ESC turn.
- Do not seed catalog JSON. Do not bump version. `ui/` empty.
- Full pytest green. Report every **existing** assertion you change (kit B1-min T1/T2/T3/T7 **will** grow the third hole on a 7-key dron — that is intended).
- Write the report when done.

---

## 2. Intent

```text
motors saved + propellers saved + domain dron|uav
        ↓
kit_component_keys includes prop_adapter   → Board slot + BOM missing
        ↓
propulsion still_missing prepends prop_adapter before esc
        ↓
Brief → user declares | skip
        ↓
ESC Brief (BLOCK_TO still_missing). PASS still 3 keys.
```

---

## 3. Locked behavior

### 3.1 Registry (`system_architecture_catalog.py`)

Still schema-free. **Do not** mutate `BLOCK_TO_COMPONENTS` lists (`git diff` must show no new strings inside those lists).

```text
KIT_TO_COMPONENTS["dron"] = ["power_connector", "signal_harness", "prop_adapter"]
KIT_TO_COMPONENTS["uav"]  = same
KIT_HOME_BLOCK["prop_adapter"] = "propulsion"

KIT_REQUIRES_COMPONENTS: dict[str, tuple[str, ...]] = {
    "prop_adapter": ("motors", "propellers"),
}
```

`power_connector` / `signal_harness` stay **ungated** (no `KIT_REQUIRES_COMPONENTS` row).

Extend `kit_component_keys`:

```text
kit_component_keys(vehicle_type, system_blocks, components=None) -> list[str]
```

For each key in `KIT_TO_COMPONENTS[domain]` whose `KIT_HOME_BLOCK` is in `system_blocks`:

- If the key is **not** in `KIT_REQUIRES_COMPONENTS` → include (today’s rule).
- If it **is**: include **only** when `components` is provided **and** every required key exists with `completeness != "low"`.  
  `components is None` or a required spec missing/low → **exclude** (fail closed — never nag at create).

`bom_and_board_expected_keys(system_blocks, vehicle_type, components=None)` forwards `components` into `kit_component_keys`.

Call sites that **have** project components **must** pass them:

| Caller | Pass `components` |
|---|---|
| `project_closure.build_component_bom` | yes (already has them) |
| `spatial_board._expected_keys_by_column` / `project_spatial_nodes` | yes |
| `orchestrator._try_start_kit_component_from_mention` | yes |

Public helper (name may vary; behavior locked):

```text
prop_adapter_is_due(vehicle_type, system_blocks, components) -> bool
```

True iff `prop_adapter` would be returned by `kit_component_keys(...)` **and** the adapter spec is absent or `completeness == "low"`.

Prepend helper (hardcoded key, not a framework):

```text
splice_prop_adapter_ask(still_missing, *, vehicle_type, system_blocks, components) -> list[str]
```

If `prop_adapter_is_due(...)` and `"prop_adapter"` not already in `still_missing`: return `["prop_adapter"] + still_missing`. Else return `still_missing` unchanged. Do **not** take a `block_key` generic insert table.

### 3.2 Board / BOM

Same slot payload as kit B1-min (`kind: "slot"`, `estado: no declarado`, no SKU, no `geometry`). Home column = index of `propulsion` in `system_blocks`.

A dron with **empty** components: slots = seven architecture keys + connector + harness. **No** `prop_adapter`.

A dron with motors+propellers present (even if `esc` still missing): `prop_adapter` slot **appears**.

`robot` / no `vehicle_type`: zero adapter.

### 3.3 Wizard splice (the B1 moment)

`_set_pending_next_block` composite Phase A for **any** block must keep `missing_component_keys` sourced from `BLOCK_TO_COMPONENTS` only, then **`splice_prop_adapter_ask`** the result before writing `pending_missing_params`. Same for `_fresh_pending_keys_for_block` when it returns component keys.

`_handle_component_description` — **every** path that computes `still_missing` and then calls `_component_prompt_for_first_missing` or closes the wizard: run `splice_prop_adapter_ask` on that list (using the **updated** components after the save). When the spliced list is non-empty, **rewrite** session `pending_missing_params` (and `pending_param_definitions` if that is what the next turn reads as `expected_keys`) to the spliced list so the following turn’s `expected_keys[0]` is `prop_adapter`.

Fresh open with nothing declared: splice is a no-op (`motors`/`propellers` absent) → Brief still motors. After hélices save: splice puts adapter ahead of `esc`. Mixed D7 phrase that saves motors **and** hélices in one turn: same — next Brief is adapter, not ESC.

Do **not** add `prop_adapter` to the **initial** `BLOCK_TO` expected set. Splice only.

### 3.4 Relabel + skip (persistence)

Kit B1-min relabel today:

```text
len(expected_keys) == 1 and expected_keys[0] in KIT_HOME_BLOCK
```

**Widen** to: `expected_keys` non-empty **and** `expected_keys[0] in KIT_HOME_BLOCK` (so `["prop_adapter", "esc"]` still relabels). Keep the rest: generic → that key, promote low → medium, no `catalog_ref`, no `_geometry_from_spec`. Empty input does not save.

**Skip / unknown** (only when `expected_keys[0] == "prop_adapter"`): if the whole normalized input is one of Bug 77 skip phrases (`no sé`, `no se`, `no lo sé`, `no lo se`, `skip`, `omitir`, `omite`, `después`, `despues`, `más tarde`, `mas tarde`, `no tengo`, `no dispongo`) **or** the Brief’s own “no lo sé”:

- **Do not** write `prop_adapter`.
- Drop it from this turn’s `still_missing` **prompt** (advance to `esc`).
- Leave it in Board/BOM expected (gate still true).
- Rewrite `pending_missing_params` to the remaining BLOCK_TO holes (typically `["esc"]`).

“va directa” / “con collet” / “tuerca campana …” = normal relabel save (identity of mount method). Completeness medium. **No** millimetre properties invented.

No catalog help-choose for this key. Do not add `prop_adapter` to `OUT_OF_SCOPE_EXPLICIT_SAVE_KEYS`.

### 3.5 DEFINE / aliases / Brief

`COMPONENT_TERM_ALIASES` (whole-word only):

```text
prop_adapter → prop_adapter
adaptador    → prop_adapter
adapter      → prop_adapter
```

Do **not** alias bare `hélice` / `buje` / `eje`.

`COMPONENT_PROMPTS["prop_adapter"]` (Spanish, pending OK):

```text
¿Cómo montas la hélice? Va directa al eje, o con adaptador/collet/tuerca campana. Si no lo sabes, dilo — el hueco queda pendiente.
```

IDLE `_try_start_kit_component_from_mention`: already `_next_pending_block is None`. After 4/4, `definir adaptador` opens **single-key** `[prop_adapter]` only when the gate is due. Mid-architecture: kit IDLE must **not** steal the propulsion wizard (already true). Do not change connector/harness aliases or Briefs.

### 3.6 Continuity

No new rank. When `prop_adapter` is in BOM `missing` it already qualifies via `KIT_HOME_BLOCK` for the B3 sentence — list it among kit keys actually missing. **Do not** reorder so adapter beats `esc` in Continuity; architecture keys still precede kit keys in `bom_and_board_expected_keys`. The **wizard** is what asks between hélices and ESC. Do **not** change when `power_connector` nags (review N2 — later tidy).

### 3.7 PASS / ERF / hover

No edits to `_block_progress_status` component lists. Twin: propulsion `complete` on motors+propellers+esc **with** adapter absent equals the clone without the kit key. Architecture fraction still counts 4 blocks, 7 keys.

### 3.8 Existing tests you will have to update

Kit B1-min fixtures that set `vehicle_type=dron` **and** already have motors+propellers (the 7-root `_dron_state`):

- Board slot set grows `prop_adapter`
- BOM `missing` becomes `["power_connector", "signal_harness", "prop_adapter"]` (order locked)
- Continuity B3 lists the third key when it is missing
- T7 after stub connector: remaining slots include harness **and** adapter

Tests **without** `vehicle_type`, or `robot`, or **without** both motor and prop specs, must **not** grow an adapter hole.

Report the list. Do not delete tests.

---

## 4. Tests (new file)

`tests/test_kit_prop_adapter_ask_b1.py`:

| ID | Behavior |
|---|---|
| T0 | `vehicle_type=dron`, 4 blocks, **empty** components → Board slots = seven + connector + harness; **no** `prop_adapter`. `BLOCK_TO_COMPONENTS["propulsion"]` still `["motors", "propellers", "esc"]` |
| T1 | motors present, **no** propellers → **no** adapter slot / not in BOM `missing` |
| T2 | motors + propellers present, esc absent, adapter absent → Board has `prop_adapter` in the **propulsion** column; BOM `missing` contains `esc` **and** `prop_adapter` |
| T3 | Orchestrator: propulsion composite open; save hélices (motors already present) → returned message contains the adapter Brief (or `¿Cómo montas la hélice?`) and **not** the ESC prompt as the next question; `pending_missing_params[0] == "prop_adapter"` |
| T4 | From T3, `"va directa"` → `components["prop_adapter"]` exists, no `catalog_ref`, completeness ≠ `"low"`; follow-up is the ESC Brief |
| T5 | From T3, `"no lo sé"` → **no** `prop_adapter` spec; follow-up is ESC; BOM still lists `prop_adapter` in `missing` |
| T6 | `vehicle_type=robot` + motors + propellers → **zero** adapter |
| T7 | Twin: `_block_progress_status("propulsion")` with 3 BLOCK_TO keys present, adapter absent, `vehicle_type=dron` **equals** the no-`vehicle_type` clone (`complete`) |
| T8 | `kit_component_keys("dron", blocks)` **without** `components` → no `prop_adapter` (fail closed) |

Use existing kit-test helpers (`_RefuseLLM`, create_project merge) where they exist. Do not hit the network. Do not write `workspace/`.

---

## 5. Files (expected)

| Path | Change |
|---|---|
| `src/jarvis/core/system_architecture_catalog.py` | `prop_adapter` on `KIT_TO` / `KIT_HOME_BLOCK`; `KIT_REQUIRES_COMPONENTS`; gate + splice helpers. **`BLOCK_TO_COMPONENTS` values unchanged** |
| `src/jarvis/core/project_closure.py` | pass `components` into `bom_and_board_expected_keys` |
| `src/jarvis/workspace/spatial_board.py` | pass `components` into kit lookup |
| `src/jarvis/core/acquisition_target.py` | aliases + prompt |
| `src/jarvis/core/orchestrator.py` | splice on still_missing / pending rewrite; relabel `expected_keys[0]`; skip phrases for adapter; pass components into `kit_component_keys` |
| `src/jarvis/core/project_continuity.py` | **empty** unless B3 list already misses `KIT_HOME_BLOCK` members (it should not) |
| `tests/test_kit_prop_adapter_ask_b1.py` | T0–T8 |
| `tests/test_assembly_kit_template_b1.py` | assertions named in §3.8 |
| `library/` `ui/` | **empty** |
| `.jes/artifacts/implementation_report_kit_prop_adapter_ask_b1.md` | write |

---

## 6. Engineer smoke (after Cursor review)

Live **dron** create (or the 5 min project): after hélices, the next question is how you mount the propeller, **before** ESC.

- “va directa” → slot gone; ESC Brief next.
- “no lo sé” → dashed slot remains; ESC still next; architecture fraction unchanged.
- Hover / vatios **unchanged**.
- `estado` does not invent millimetres for the adapter.

Record `engineer_smoke_kit_prop_adapter_ask_b1.md`.

---

## 7. Done when

- [ ] T0–T8 green; full pytest green  
- [ ] `git diff` shows **no** new strings inside `BLOCK_TO_COMPONENTS` lists  
- [ ] No catalog seed, no version bump, no geometry, no shaft/hub comparison  
- [ ] Report lists existing-test updates  
- [ ] Report written  

---

## Explicitly not this IC

Hub-vs-shaft inference · XT60 / harness library rows · VTX/RX/camera kit keys · Conversation Engine · generic condition engine · N2 `power_connector` mid-architecture reorder · plate L×W · `"cabe"` · cylinder · version bump
