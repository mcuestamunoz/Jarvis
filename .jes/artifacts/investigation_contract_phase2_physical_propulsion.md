# Investigation Contract — Phase 2 Physical Propulsion Engine

**Project:** Jarvis  
**Date:** 2026-08-21  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output:** `.jes/artifacts/investigation_report_phase2_physical_propulsion.md`

**Status:** READY FOR CLAUDE

**Type:** Architecture investigation — define what **“real physics”** means for Phase 2 as a **data + calculation contract**, not an implementation plan for a full engine.

**Checkpoint base:** tag **`checkpoint-impl-d`** · commit `24fa7ba`

**Design authority (read-only):**
- [`docs/PHYSICAL_PROPULSION_ENGINE_PHASE2.md`](../../docs/PHYSICAL_PROPULSION_ENGINE_PHASE2.md) — vision (operating point, provenance, evolution path)
- [`docs/PHYSICAL_COMPONENT_CATALOG_V1.md`](../../docs/PHYSICAL_COMPONENT_CATALOG_V1.md) — Catalog V1 complete (Impl A–D)
- [`docs/ENGINEERING_READINESS_VISION.md`](../../docs/ENGINEERING_READINESS_VISION.md) — readiness / subsystem interaction

**Prerequisites (CLOSED):**
- Catalog V1 **Impl A–D** (`checkpoint-impl-d`)
- ERF-1/2, G9-A, Impl C catalog-aware DSE + thrust bridge

**Engineer decision (2026-08-21) — locked framing:**

```text
Impl D
  ↓
Investigation Phase 2   ← THIS CONTRACT (no production code)
  ↓
Does G26/G27 block Phase 2 data contract?
  ├── YES → fix those first, then IC Phase 2
  └── NO  → IC Phase 2 (implementation later)
```

**Do NOT implement Phase 2 in this investigation.**  
**Do NOT default to fixing G24 / Create-handoff / `req_lines` here.**

**Workflow:** Investigate → report → Engineer ratifies ★ → (optional debt ICs if ★ says so) → Cursor writes Implementation Contract for first Phase 2 slice → Claude implements. **No production fix in this contract.**

---

## 0. Context

### 0.1 Why investigate now (not implement)

After Impl D, the product path is:

```text
intent → ProjectState → architecture → components → catalog_ref → BOM
      → calculation → simulation → Engineering Readiness
```

CLI proved: bound motor SKU + qty + BOM PASS + sim PASS.  
**NOT ASSEMBLY READY** with Requirements INCOMPLETE is expected debt (G26), not an Impl D failure.

The current physics model still treats thrust largely as a **motor-attached fixed number** (`per_motor_max_thrust_n` / catalog `thrust_n`), optionally with a crude propeller-RPM path. Vision Phase 2 requires:

```text
catalog_ref(s) → operating point → thrust / power / current / efficiency
              → ProjectState → readiness
```

Jumping straight into code without a contract risks rebuilding integration twice (especially around DSE apply / battery energy / readiness).

### 0.2 What this investigation must deliver

A **precise as-is → to-be contract** for the first Phase 2 cut, plus an explicit verdict on whether **G26/G27 are technical prerequisites** for that cut (not merely product polish).

### 0.3 Explicit non-goals

- Implementing operating-point calculation  
- Expanding the full catalog / manufacturer test DB  
- Fixing G24 (DSE apply `#1`) unless investigation proves Phase 2 **cannot** be designed without it  
- Conversation Engine / Step D / H5 ESC catalog as full product  
- Version bump  

---

## 1. What Claude must investigate

### 1.1 As-is propulsion physics audit (mandatory)

Trace how thrust / power / autonomy are produced today.

| Step | File / symbol | Questions |
|---|---|---|
| Calc entry | `calculation_engine.py` | Order: declared thrust vs torque vs propeller path? |
| Params | `per_motor_max_thrust_n`, `motor_count`, `battery_capacity_wh` | Who writes them? Bind / DSE / iterate / wizard? |
| Catalog | `MotorSpec.thrust_n`, `bind_motor_from_catalog` | Is catalog thrust treated as context-free truth? |
| Propeller | `calculate_thrust_from_propeller`, diameter/RPM heuristics | Is this “Model 1” estimate or unused in catalog-bind path? |
| Sim | simulation / safety margin | What inputs does PASS/FAIL actually use? |
| Autonomy | Wh / W model | How battery capacity enters; honesty notes |
| Electrical | `electrical_compatibility.py` | What is already validated vs deferred to Phase 2? |

**Deliverable:** annotated call graph + table: “where does thrust come from for a catalog-bound motor today?”

### 1.2 Catalog data inventory vs vision (mandatory)

For motors, propellers, batteries, ESC in `ComponentLibrary` / JSON seeds:

| Family | Fields present today | Fields vision Phase 2 needs | Gap |
|---|---|---|---|
| Motor | … | kv, voltage_range, max_current, R, performance_tests[] | |
| Propeller | … | diameter, pitch, blades, mass | |
| Battery | … | cells, V_nom, capacity, C-rating, mass | |
| ESC | … | continuous_current, voltage_range | |

**Question:** Can Phase 2 v1 run on **lookup tables of manufacturer operating points** without new motor intrinsic models? Preferred if feasible (vision §12: small validation set first).

### 1.3 Operating point — data contract (mandatory)

Propose a **minimal Operating Point schema** (fields only — no code) aligned with vision §6, that:

- references `catalog_ref` identities (motor required; propeller/battery/ESC as available);
- carries provenance `source_type`: `manufacturer_test | calculated | estimated | assumed`;
- produces at least: thrust_n, electrical_power_w (or enough to derive sim inputs);
- states where it would live: ProjectState? derived calc artifact? library only?

**Hard rule to validate:** Motor SKU alone must **not** be presented as universal thrust once Phase 2 path is active (or honesty gate must label provenance).

### 1.4 Integration with ProjectState / calc / sim / ERF

Answer:

1. Does Phase 2 v1 **replace** `per_motor_max_thrust_n` or **populate** it from an operating point with provenance?  
2. What happens when propeller has no `catalog_ref` (today: freeform `5x4.5`)? Honest fallback?  
3. Interaction with G5 invalidate / Impl C thrust bridge — does operating-point thrust still clear `catalog_ref` on diverge?  
4. Continuity / ERF: new gaps? Or reuse propulsion/catalog gaps?  
5. BOM (Impl D): unchanged projection — confirm no need to reopen Impl D.

### 1.5 G26 / G27 dependency verdict (mandatory — Engineer ranking #2)

This is a **first-class deliverable**, not a footnote.

| Finding | What breaks | Does Phase 2 **data/calc contract** require it fixed first? |
|---|---|---|
| **G27** `6S` → `6 Wh` | Silent wrong `battery_capacity_wh`; autonomy cliff | **Must answer YES/NO with evidence** — vision Phase 2 uses battery voltage/capacity for operating point |
| **G26** restrictions ≠ `parsed_constraints` | Requirements INCOMPLETE; ASSEMBLY READY blocked | **Must answer YES/NO** — is Requirements completeness required for first physics slice, or parallel debt? |

**Recommendation rule:**  
- If Phase 2 v1 **reads** `battery_capacity_wh` / cell voltage from user-declared battery to choose operating points → G27 is likely a **hard prerequisite** before implementation.  
- If Phase 2 v1 v1 only uses **library-bound battery SKU** + manufacturer tables and ignores freeform Wh parse → G27 may be parallel (still urgent product debt).  
- G26: usually **does not** block operating-point math; it blocks ASSEMBLY READY UX — say so explicitly if true.

### 1.6 G24 (DSE apply) — default defer

State whether Phase 2 investigation **depends** on G24. Engineer default: **no**. Only elevate if catalog-aware DSE cannot coexist with operating-point apply without apply-path redesign. Prefer “Phase 2 calc first; G24 later” unless proven otherwise.

### 1.7 Scope options for first Implementation Contract (mandatory — 2–3)

Propose Phase 2 **v1 slices**, e.g.:

| Option | Scope | Pros | Cons |
|---|---|---|---|
| **A — Lookup OP** | Small set of motor+prop(+V) manufacturer points → write thrust into calc with provenance | Minimal; matches vision §12 | Limited coverage |
| **B — Bind-combo** | Require motor+propeller catalog_refs; resolve OP; fail honestly if missing | Strong identity story | Needs propeller bind UX |
| **C — Full electro-mech** | Current, ESC limits, efficiency in one cut | Closest to vision | Too large for v1 |

Recommend one for first IC; defer others.

### 1.8 What stays Model 1

List calculation/sim behaviors that **remain unchanged** in Phase 2 v1 (safety margin formula, structure mass, etc.).

### 1.9 Test / probe inventory

- Existing tests that pin `thrust_n` as motor property  
- Which become **contracts** vs which must be rewritten when OP lands  
- Sketch of a future CLI probe: bind motor (+ prop?) → OP-derived thrust with provenance visible  

### 1.10 Slice recommendation for future IC

Ordered bullets only (P2-1, P2-2, …) — not a full IC.

---

## 2. Scope boundaries

### In scope

- Full audit §1.1–1.10  
- Operating-point schema proposal  
- Explicit **G26/G27 prerequisite verdict** with rationale  
- 2–3 Phase 2 v1 options + ★ for Engineer  
- Clear non-goals list  

### Out of scope (do not implement)

- Any `src/` production changes  
- New tests (investigation only)  
- Fixing G24–G27 (unless ★ later opens a **separate** debt IC)  
- Full catalog expansion  
- Conversation Engine / Step D  

---

## 3. Output format

Single artifact: `.jes/artifacts/investigation_report_phase2_physical_propulsion.md`

Required sections:

1. Executive summary (≤20 lines)  
2. As-is propulsion physics audit  
3. Catalog data inventory vs vision  
4. Operating-point schema proposal  
5. ProjectState / calc / sim / ERF / BOM integration answers  
6. **G26/G27 dependency verdict** (table + recommendation)  
7. G24 deferral confirmation (or elevation with proof)  
8. Design options (2–3) + trade-offs  
9. What stays Model 1  
10. Test inventory + probe sketch  
11. Recommended approach  
12. ★ Decisions for Engineer (numbered)  
13. Suggested Implementation Contract outline (slices only)  
14. Explicit: “implement Phase 2? not yet — gates remaining”

---

## 4. Hard constraints for any future Phase 2 IC

- **ProjectState remains source of truth**; OP results are projections or typed params with provenance — LLM never invents thrust.  
- **Never present estimate as manufacturer_test.**  
- **Prefer extending calc/library** over a parallel “Physics Engine” subsystem unless investigation proves necessity.  
- **Do not reopen Impl D BOM schema** without cause.  
- **G5 / catalog_ref honesty** remains: diverge still clears identity.  
- **Zero weakened tests** without explicit contract note.  

---

## 5. Acceptance (Cursor investigation review)

**PASS** if report answers §1, includes ≥2 options, delivers a clear G26/G27 prerequisite verdict, and actionable ★ + slices.  
**FAIL** if jumps to implementation, invents Conversation Engine, or treats G24 as must-fix without proof.

---

## 6. Queue after investigation

```text
Investigation PASS
        ↓
Engineer ratifies ★ (incl. G26/G27 gate)
        ↓
[optional] debt IC for G27/G26 if ★ requires
        ↓
Cursor: implementation_contract_phase2_… (first slice only)
        ↓
Claude implements → review → CLI → checkpoint
        ↓
Version bump only after Phase 2 slice or significant bug lote (Engineer call)
```

---

**End of contract.**
