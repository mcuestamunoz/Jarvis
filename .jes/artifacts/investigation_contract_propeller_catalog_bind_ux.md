# Investigation Contract — Propeller Catalog Bind UX (P2-1 unlock)

**Project:** Jarvis  
**Date:** 2026-08-21  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output:** `.jes/artifacts/investigation_report_propeller_catalog_bind_ux.md`

**Status:** READY FOR CLAUDE

**Type:** Audit + design — bring **live propeller catalog pick + bind** to CLI (same class of work as G21 for motors), so Phase 2 P2-1 can reach `exact_operating_point` without test-only `bind_propeller_from_catalog`.

**Checkpoint base:** tag **`checkpoint-phase2-p2-1`** · commit `e82b8a1`

**Design / product authority (read-only):**
- [`.jes/artifacts/implementation_contract_g21_g22_catalog_bind_ux.md`](implementation_contract_g21_g22_catalog_bind_ux.md) — motor help-choose pattern
- [`.jes/artifacts/implementation_contract_phase2_lookup_operating_point.md`](implementation_contract_phase2_lookup_operating_point.md) — exact OP needs `propellers.catalog_ref`
- [`docs/PHYSICAL_COMPONENT_CATALOG_V1.md`](../../docs/PHYSICAL_COMPONENT_CATALOG_V1.md) — propeller family / `catalog_ref`

**Prerequisites (CLOSED):**
- Impl B `bind_propeller_from_catalog` (test-callable today)
- G21/G22 motor catalog UX
- Phase 2 P2-1 lookup OP (`checkpoint-phase2-p2-1`)

**Explicitly out of scope for this investigation:**
- G24 / G26 / G27  
- ESC catalog / H5  
- Changing OP resolver / ★6 dataset / `v1_max_thrust` policy  
- Conversation Engine / Step D  
- Full Continuity formula rewrite  
- Battery catalog pick UX (still deferred C3)

**Workflow:** Investigate → report → Engineer ★ → Cursor IC → Claude implements. **No production fix in this contract.**

---

## 0. Context

### 0.1 Problem

P2-1 CLI walk proved:

```text
emax_rs2205s_2300 bound
  → Propulsión (evidencia): fallback_operating_point · 10.042 N
```

Exact path (`hq_5045_bn` → 9.7086 N) works in the **probe** via `bind_propeller_from_catalog`, but **there is no live CLI propeller catalog picker**. Freeform `hélices 5x4.5` does not set `catalog_ref` → resolver correctly stays on fallback.

### 0.2 Target (to-be — validate feasibility)

```text
definir propulsion / propellers gap
  → ayúdame a elegir   (or equivalent)
  → numbered propeller SKUs (filtered by bound motor when possible)
  → pick N
  → bind_propeller_from_catalog → set_propeller_component
  → re-resolve motor OP (set_motor_component or equivalent)
  → estado: exact_operating_point · … · 9.7086 N
```

### 0.3 Known assets (do not reinvent)

| Asset | Status |
|---|---|
| `bind_propeller_from_catalog` | Exists, test-callable |
| `set_propeller_component` | Exists (bridges diameter/pitch) |
| `ComponentLibrary` propellers + `hq_5045_bn` / `gf_5045x3` | Seeded in P2-1 |
| `match_motor_propeller` / `compatible_prop_inch` | ERF-2 electrical facts |
| G21 motor help-choose wiring | Pattern to reuse, not copy-paste blindly |

---

## 1. What Claude must investigate

### 1.1 As-is propeller acquisition path (mandatory)

Trace how propellers are acquired today after motor bind.

| Step | File / symbol | Questions |
|---|---|---|
| Component wizard | `_handle_component_description` | When `expected_keys` includes `propellers`, what phrases work? |
| Help-choose | `is_help_choose_phrase` / FN-005 | Motors only? Propellers ignored? |
| Freeform | `10x4.5` / `hélices 5x4.5` | Does any path set `catalog_ref`? |
| Bind | `bind_propeller_from_catalog` | Call sites today (tests only?) |
| Writer | `set_propeller_component` | After bind, does motor OP re-resolve? Who must call `set_motor_component` again? |
| Continuity | acquisition brief for propellers | Copy mention `ayúdame a elegir`? |

**Deliverable:** sequence diagram motor-done → propeller declare → state.

### 1.2 Suggestion authority for propellers (mandatory)

Propose how to build a **numbered propeller list** (deterministic, no LLM SKU invention):

Options to evaluate:

| Option | Approach |
|---|---|
| **A** | Filter `list_propellers()` by bound motor `compatible_prop_inch` / `compatible_prop_ids` / `match_motor_propeller` |
| **B** | Always show full propeller catalog (limit N) |
| **C** | Prefer P2-1 seeded props (`hq_5045_bn`, `gf_5045x3`) when motor is `emax_rs2205s_2300` / `sunnysky_r2205_2500`, else A |

Recommend one. **Must reuse library predicates** — no second catalog reader.

**Question:** New `build_propeller_catalog_suggestions(project_state)` next to `motor_catalog_assist`, or extend existing module? Prefer small dedicated helper if motor module is motor-specific.

### 1.3 Session / sub-mode wiring (mandatory)

Where does pick-by-number live?

- Reuse `session.motor_suggestions`-style field vs new `propeller_suggestions`?
- `MISSING_COMPONENT_DEFINITION` with `propellers` in `expected_keys`?
- IDLE `ayúdame a elegir` when propellers unbound / incomplete?
- Conflict with motor help-choose when both incomplete?

### 1.4 Re-resolve OP after propeller bind (mandatory)

P2-1 bridge reads propeller `catalog_ref` inside `set_motor_component`. After propeller bind:

1. Does `set_propeller_component` alone trigger motor OP refresh?  
2. If not, IC must require an explicit re-call of `set_motor_component` (or shared refresh helper) — **investigate which is minimal and correct**.  
3. Confirm `propulsion_resolution` JSON string remains hashable (P2-1 constraint).

### 1.5 Voltage context for exact OP

Exact EMAX rows need ~16 V. After propeller bind without battery:

- Does fallback still win until battery cells declared?  
- What CLI order should Continuity recommend (prop first vs battery first)?  
- Investigation must state honest expected `estado` sequences for the Engineer walk.

### 1.6 Design options (2–3) for v1 IC

| Option | Scope |
|---|---|
| **A** | Propeller help-choose only inside propulsion component wizard (mirror G21 motors) |
| **B** | A + IDLE re-bind when propellers freeform / unbound |
| **C** | A + Continuity CTA only (no numbered pick) — likely insufficient |

Recommend A or A+B. Reject C unless proven.

### 1.7 Test + CLI probe sketch

Minimum future probes:

```text
1) Bind emax_rs2205s_2300 → estado fallback 10.042 N
2) ayúdame a elegir (propellers) → list includes hq_5045_bn
3) pick → catalog_ref set → (with ~16 V context) exact 9.7086 N
4) Freeform hélices 5x4.5 → still no false exact (no catalog_ref)
5) Regression: motor G21 help-choose still works
```

### 1.8 Slice outline for future IC

Bullets only (Prop-1…Prop-N).

---

## 2. Scope boundaries

### In scope

- Full audit §1.1–1.8  
- Recommendation for suggestion authority + session wiring  
- Explicit OP re-resolve plan after bind  
- ★ decisions for Engineer  

### Out of scope

- Any `src/` changes  
- New OP seed rows  
- Battery/ESC catalog pick  
- G24–G27 fixes  
- Changing `resolve_operating_point` match rules (except documenting call-order needs)

---

## 3. Output format

`.jes/artifacts/investigation_report_propeller_catalog_bind_ux.md`

Required sections:

1. Executive summary  
2. As-is propeller acquisition audit  
3. Suggestion authority options + recommendation  
4. Session / help-choose wiring plan  
5. OP re-resolve after bind (mandatory answer)  
6. Voltage / walk sequencing notes  
7. Design options (2–3) + trade-offs  
8. Test + CLI probe sketch  
9. Recommended approach  
10. ★ Decisions for Engineer  
11. Suggested IC outline (slices)

---

## 4. Hard constraints for future IC

- **LLM never invents propeller SKUs** — numbered list from library only.  
- **Reuse `bind_propeller_from_catalog`** — no parallel binder.  
- **ProjectState remains SoT**; no second propeller list authority.  
- **Do not break G21 motor help-choose.**  
- **Hashable `current_parameters` values** (P2-1 lesson).  
- **Zero weakened tests.**

---

## 5. Acceptance (Cursor review)

**PASS** if report answers §1, includes ≥2 options, solves OP re-resolve, and delivers ★ + slices.  
**FAIL** if invents Conversation Engine, duplicates catalog search, or changes OP physics rules.

---

## 6. Queue after investigation

```text
Investigation PASS
  ↓
Engineer ★
  ↓
Cursor: implementation_contract_propeller_catalog_bind_ux.md
  ↓
Claude implements → review → CLI walk (fallback→exact) → checkpoint
```

---

**End of contract.**
