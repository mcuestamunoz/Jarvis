# Investigation Review — Prop adapter ask (after hélices)

**Date:** 2026-09-09  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_kit_prop_adapter_ask_b0.md](investigation_contract_kit_prop_adapter_ask_b0.md)  
**Report:** [investigation_report_kit_prop_adapter_ask_b0.md](investigation_report_kit_prop_adapter_ask_b0.md)  
**Parents:** [engineer_lock_assembly_kit_template.md](engineer_lock_assembly_kit_template.md) · kit B1-min CLOSED

## Verdict

**PASS WITH NOTES** · recommended Buy **B1** (wizard insert after hélices; `KIT_TO` **gated** on motor+prop present; **no** hub/shaft inference)

B-naive is correctly refused. B2 (Continuity/BOM only) cannot ask between hélices and ESC: `still_missing` of the propulsion wizard is `BLOCK_TO` only, and kit keys are **appended** on BOM so they never become `missing[0]` while `esc` (and the rest) are still holes. Only a **hardcoded** insert into that wizard list hits the Engineer moment. Not a Conversation Engine. Not a generic condition engine (N3 holds).

No IC until Engineer ★ **B1** (or explicit B0 / B2).

---

## Checklist

| Criterion | Result |
|---|---|
| Census shaft / bore / hub; hub ≠ bore | **Pass** — Cursor re-counted JSON: motors **22**, shaft **1** (`emax_rs2205s_2300` 3 mm); props **18**, bore **1** (`apc_10x6_ep`); hub **3**. Zero same-build pair |
| B-naive refused | **Pass** |
| One default lean | **Pass** — **B1** |
| Hook map: files + `still_missing` | **Pass** — `_handle_component_description` / `_set_pending_next_block` composite |
| `KIT_TO` must not list adapter at create | **Pass** — `kit_component_keys` gates on **block declared**, not component presence |
| No `src/` / library | **Pass** — report only |
| XT60 SKUs out | **Pass** |
| PASS / `BLOCK_TO` untouched in the proposal | **Pass** |

---

## Independent checks

| Claim | Cursor |
|---|---|
| `bom_and_board_expected_keys` = architecture keys, then kit append | **Confirmed** |
| Continuity rank 4 = `missing[0]` + B3 if any kit key in `missing` | **Confirmed** |
| Composite wizard `expected_keys` = `BLOCK_TO["propulsion"]` only | **Confirmed** |
| Kit IDLE `_try_start_kit_component_from_mention` requires `_next_pending_block is None` | **Confirmed** — cannot steal the hélices→ESC wizard turn |
| Relabel path is `KIT_HOME_BLOCK` membership | **Confirmed** — adapter needs an equivalent membership **without** making `kit_component_keys` fire at architecture A |

---

## Notes

### N1 — Live 5 min SKU ≠ `emax_rs2205s_2300`

Walk bound **`emax_rs2205_2300`**, which has **no** `shaft_diameter_mm`. Shaft 3 mm is on **`emax_rs2205s_2300`**. Report’s “live-bound pair has shaft 3.0 vs hub 5.0” mixes SKUs. Honesty is **stronger** on the real walk: there is **no** shaft figure at all. Do not treat hub 5 mm as a hole. Does not change B-naive refuse.

### N2 — Continuity “power_connector” mid-walk

Engineer paste: after **only** the motor, footer still asked `power_connector` while the wizard said hélices+ESC (0/4). Claude reconstructed “all 7 keys exist, params missing.” That reconstruction is **plausible** for rank 4 (`missing` = only kit keys) but was **not** shown against the gitignored 5 min `state.json`. The **product** finding still holds: Continuity kit rank is the wrong surface for “right after hélices.” B1 does not fix the connector nag; do not silently expand this IC to reorder `power_connector`. Separate later tidy.

### N3 — B1 persistence

Inserting `prop_adapter` into `still_missing` for **one** turn is not enough. “No lo sé” must leave a **gated** BOM/Board hole; “va directa” must save a declarative spec (reuse kit relabel). IC must name: gated `kit_component_keys` predicate (motor+prop present), wizard insert, Brief, skip/pending, **no** `BLOCK_TO` append. Tests: before hélices → no slot; after hélices save → Brief before ESC; `robot` → zero; PASS twin.

---

## Buys (after review)

| ID | Engineer ★ |
|---|---|
| **B1** | **Default** — wizard after hélices + gated kit key |
| **B2** | Weaker: slot/BOM only, ESC still next in wizard |
| **B0** | Park |
| **B-naive** | **Forbidden** |

---

## Phase

Investigation **REVIEWED PASS WITH NOTES**. Engineer ★ **B1** (2026-09-09). IC: [implementation_contract_kit_prop_adapter_ask_b1.md](implementation_contract_kit_prop_adapter_ask_b1.md). Package `0.3.8` · suite **2514**.
