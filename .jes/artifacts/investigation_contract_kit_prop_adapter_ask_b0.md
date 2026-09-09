# Investigation Contract — Prop adapter ask (after hélices; novice; no inferred need)

**Project:** Jarvis  
**Date:** 2026-09-09  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_kit_prop_adapter_ask_b0.md`

**Status:** INVESTIGATION REVIEWED — PASS WITH NOTES · Engineer ★ **B1** · IC [implementation_contract_kit_prop_adapter_ask_b1.md](implementation_contract_kit_prop_adapter_ask_b1.md)  
**Parents:**
- Engineer ★ “me gusta el lean” after the `autonomía-de-5min` create walk
- [engineer_lock_assembly_kit_template.md](engineer_lock_assembly_kit_template.md)
- [engineer_next_assembly_kit_template.md](engineer_next_assembly_kit_template.md) §3 B
- [investigation_review_assembly_kit_template_b0.md](investigation_review_assembly_kit_template_b0.md) **N3** — conditional pending is later; do not invent a condition engine in the first adapter Buy
- Kit B1-min **CLOSED** — `KIT_TO_COMPONENTS` = `power_connector`, `signal_harness` only
- Rooster Included plates B2 **CLOSED** — **out**
- XT60 / harness **catalog SKUs** — **out of this investigation** (later ★, Engineer lock)

**Type:** Routing + honesty investigation. **Not** an IC. **Do not implement. Do not change `KIT_TO` / `BLOCK_TO`. Do not seed adapters.**

**Checkpoint:** package **`0.3.8`** · suite **2514**

**You are Claude Code.** Write the report only.

---

## 0. Role split

```text
Engineer  → ask after hélices: “¿cómo montas la hélice?”; Jarvis must not
            pretend to know if an adapter is required
Cursor    → this contract; review; IC only after ★ on hook shape
Claude    → investigation_report_kit_prop_adapter_ask_b0.md
```

---

## 1. Why this exists

Locked lean (Engineer accepted):

```text
prop_adapter in the kit template only once motor AND propeller exist.
Brief: how do you mount the propeller?
  • goes on direct
  • with adapter / collet / bell nut  →  describe or leave pending
  • I don’t know  →  hole, no SKU invented
Zero hub-vs-shaft inference.
XT60 catalog rows = later ★, not this Buy.
```

Today Continuity already nags `power_connector` **during** architecture fill (seen on `autonomía-de-5min`). An always-on third kit key would make that worse. The Engineer wants the **adapter question at the propulsion moment** (right after hélices), not at 4/4.

Wrong next step:

```text
if hub_diameter ≈ shaft → skip · if hub ≠ shaft → invent adapter SKU
· comparar buje Ø 5 mm de gf_5045x3 con un eje no citado
· KIT_TO += prop_adapter from create (nags before any hélice)
· Conversation Engine · SKUs XT60 in the same IC
```

Right question:

> Where does the existing DEFINE / propulsion wizard / Continuity / `KIT_TO` machinery hook so a novice is asked **after hélices**, without inferring need from incomplete millimetres, and without widening propulsion PASS?

---

## 2. Locked stances

1. **Need is not computed.** Census (cite `_datos.json`): almost no `shaft_diameter_mm` on motors; `shaft_bore_mm` is rare; `hub_diameter_mm` **is not** the shaft hole. The live 5 min pair (EMAX + `gf_5045x3`) has **no** comparable pair. Report must not propose hub-vs-shaft as a gate.  
2. **Temporal gate only:** both `motors` and `propellers` exist as declared keys → the hole may appear. Missing either → **do not ask**.  
3. Unknown → pending. “Va directa” is a valid **declaration** (identity of mount method), not a catalog SKU.  
4. Reuse DEFINE / Continuity / Board slot / BOM `missing` — **no** Conversation Engine.  
5. **Do not** append `prop_adapter` to `BLOCK_TO_COMPONENTS["propulsion"]`. PASS / hover / autonomy **byte-identical**. Same split as kit B1-min (`KIT_TO` vs `BLOCK_TO`).  
6. XT60 / harness library rows, VTX/RX, `"cabe"`, 3D solids for adapters — **out**.  
7. Optional later: *if both* shaft and bore are cited, Continuity may **say** they match or differ. Still the user confirms. Not this investigation’s default Buy unless you prove it is a one-line honesty clause with both fields already on the specs.

---

## 3. Baseline to inventory (cite live tree)

| Surface | Check |
|---|---|
| `KIT_TO_COMPONENTS` / `KIT_HOME_BLOCK` / `kit_component_keys` | When keys appear; any `vehicle_type` / block gate already |
| Continuity rank 4 + B3 sentence | Why `power_connector` wins **before** 4/4 on a create walk |
| Propulsion composite wizard | Order motors → hélices → ESC. Where a post-hélice step could insert **without** a new engine |
| IDLE `definir X` / kit relabel (N1 B1-min) | Can `prop_adapter` reuse the single-key kit Brief? |
| `MotorSpec.shaft_diameter_mm` / `PropellerSpec.shaft_bore_mm` / `hub_diameter_mm` | Counts; EMAX; `gf_5045x3` — prove inference is dishonest |
| BOM `expected_keys` union | What happens if `prop_adapter` is expected from project create vs after two keys exist |

If `workspace/autonomía-de-5min*` readable, cite Continuity lines that asked the connector mid-architecture. If not, use the Engineer paste in chat (2026-09-09).

---

## 4. Report sections (required)

### A. Why Jarvis cannot know

One table: motor SKUs with `shaft_diameter_mm` vs propeller SKUs with `shaft_bore_mm` vs hub-only. Explicit: hub ≠ bore.

### B. Candidate Buys (ranked, **one default**)

Must include at least:

| ID | Shape |
|---|---|
| **B0** | Park. Keep two kit keys. Ask adapter later. |
| **B1** | Insert the Brief **in the propulsion wizard** immediately after hélices save (before ESC). `KIT_TO` key still exists but **gated** (no slot until motor+prop). |
| **B2** | No wizard insert. Only gated `KIT_TO` + Continuity/DEFINE (same as connector, but hole appears only after hélices). |
| **B-naive** | Infer adapter from hub/shaft numbers | **Refuse** — dishonest on current catalog |

Name **one default** matching the Engineer lean (ask after hélices). If B1 and B2 both work, pick the **smaller** hook that still hits that moment; say what B1 extra cost is (composite wizard vs IDLE).

### C. Hook map

Exact functions / flags: who would read “motor+prop present”; who must **not** list `prop_adapter` at create. Cite files. No patches.

### D. Twin / non-goals

PASS unchanged. Connector/harness behavior **unchanged** except they must not steal the turn **between hélices and ESC** if B1 is default. SKUs of kit **out**.

---

## 5. Done when

- [ ] Report written; one **default lean** (B1 or B2)  
- [ ] No `src/` / library edits  
- [ ] Explicit refuse of geometric inference  
- [ ] Explicit: XT60 SKUs not this Buy  

---

## Explicitly not this investigation

Implement `prop_adapter` · `KIT_TO` edit · catalog adapter family · Conversation Engine · `"cabe"` · plate L×W
