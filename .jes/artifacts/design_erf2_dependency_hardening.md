# Design — ERF-2 Dependency Hardening

**Status:** **CLOSED — Engineer ratified 2026-08-19**  
**Type:** Design only. Zero product `src/` changes. Not an Implementation Contract.  
**Date:** 2026-08-18  
**Ratification:** Engineer locks absorbed — see §1 and §13  
**Next:** [implementation_contract_erf2.md](implementation_contract_erf2.md)  
**Vision:** [`docs/ENGINEERING_READINESS_VISION.md`](../../docs/ENGINEERING_READINESS_VISION.md) §ERF-2  
**Investigation (CLOSED):** [investigation_erf2_dependency_hardening.md](investigation_erf2_dependency_hardening.md) — **PASS**  
**Investigation contract:** [implementation_contract_erf2_investigation.md](implementation_contract_erf2_investigation.md)  
**Builds on:** [design_erf1_readiness_foundation.md](design_erf1_readiness_foundation.md) · tag **`checkpoint-erf1`**

---

## 0. Where this lives

```text
checkpoint-erf1 ✅
        ↓
investigation_erf2_dependency_hardening.md     ✅ PASS
design_erf2_dependency_hardening.md            ✅ CLOSED (2026-08-19)
        ↓
implementation_contract_erf2.md                ← IC ready for Engineer
        ↓
checkpoint-erf2
```

ERF-2 **extends** ERF-1 — it does not replace it. All ERF-1 ★ locks remain in force unless explicitly extended here.

---

## 1. Locked ★ summary (authoritative)

| ★ | Lock |
|---|---|
| **★1 — Purpose boundary** | ERF-2 detects **known deterministic electrical incompatibilities** — not "Jarvis designs the electrical system." No full electrical solver. |
| **★2 — Compatibility authority** | New pure module `electrical_compatibility.py` owns compatibility **facts**; `engineering_readiness` **aggregates** facts → gaps + verdicts. Do not inline all rules in readiness. |
| **★3 — INCOMPATIBLE gate** | **`INCOMPATIBLE` only when topology + evidence are deterministically established.** Missing topology, missing limits, heuristic-only evidence → `UNVERIFIABLE` or `INCOMPLETE` — **never** upgraded to `INCOMPATIBLE`. |
| **★4 — Electrical topology (MVP)** | Conventional multirotor: **1 motor ↔ 1 ESC**. Compare `esc.current_a` vs **per-motor** draw — **not** `I_motor × motor_count` on one ESC rating. If topology not determinable → `UNVERIFIABLE`. |
| **★5 — ESC in architecture** | Add `esc` to `BLOCK_TO_COMPONENTS["propulsion"]` so BOM/arch surface `GAP-ESC-UNDEFINED` honestly. |
| **★6 — Gap orthogonality** | ERF-2 gaps are **orthogonal** to ERF-1. Example: `simulation.status == pass` + `GAP-ESC-UNDERSIZED` → `overall NOT_ASSEMBLY_READY`, `propulsion/electronics INCOMPATIBLE`. Sim answers physics; Readiness answers assembly closure. |
| **★7 — No H5 blocker** | ESC JSON catalog (H5) is **not required** for ERF-2 MVP. Declared props + motor/battery SKU fields suffice. Impl C / H5 = "what SKU to buy"; ERF-2 = "can it work." |
| **★8 — Subsystems v2** | **Nine lines:** ERF-1 eight + **`electronics`**. Do **not** add `integration` or `communications` without authority. |
| **★9 — Continuity defer** | ERF-2 MVP = **Readiness + CLI** only. Continuity electrical handoff = optional Slice 5 (mirror ERF-1 C-108 scoped pattern). **Do not** bundle ERF-1 Slice 4b. |
| **★10 — Prop↔motor gap** | `GAP-PROP-MOTOR-MISMATCH` is **Readiness integration (B)** — exposes existing `library.match_motor_propeller`; **no duplicate rule** in ERF-2. |
| **★11 — Voltage/KV defer** | No `GAP-MOTOR-ESC-VOLTAGE-MISMATCH` in ERF-2 MVP. KV×voltage estimates RPM; incompatibility requires explicit limit authority not present today. |

---

## 2. Problem statement (why ERF-2)

ERF-1 answers: **"¿Qué falta?"**  
ERF-2 begins: **"¿Qué dependencias e incompatibilidades existen?"**

Today Jarvis can sim PASS while:

- ESC is **inferrable but architecturally invisible**,
- declared ESC amp rating is **below per-motor demand**,
- battery pack discharge limit is **exceeded** (when SKU evidence exists),
- motor↔propeller mismatch is **computable but not in Gap Registry**.

Without ERF-2, `"aplica la mejor"` and assembly-ready rollup cannot distinguish **missing** from **incompatible**.

---

## 3. Authority model (binding)

```text
                    ProjectState
                         │
          ┌──────────────┼──────────────┐
          ↓              ↓              ↓
   Architecture      Components      Catalog (motor/battery)
   BOM/closure       (esc, motors)   library.py
          │              │              │
          └──────────────┼──────────────┘
                         ↓
              electrical_compatibility.evaluate()
                         │
                         ↓  CompatibilityResult (facts only)
              engineering_readiness.build_engineering_readiness()
                         │
                         ↓  gaps + 9 subsystem lines + overall
              CLI render / (optional future Continuity)
```

| Module | Authority |
|---|---|
| `library.py` | Component specifications; `match_motor_propeller` |
| `electrical_compatibility.py` | **NEW** — deterministic compatibility facts |
| `engineering_readiness.py` | Gap aggregation + subsystem verdicts (extends ERF-1) |
| `simulator.py` | Physics feasibility — **unchanged** in ERF-2 MVP |
| `project_continuity.py` | Human next step — **out of ERF-2 MVP** |

**ERF-2 is authoritative over:** electrical compatibility **assertions** that meet ★3, and their projection into gaps/verdicts.

**ERF-2 is NOT authoritative over:** sim physics, catalog SKU truth, or user-facing copy.

---

## 4. Target CLI shape (after ERF-2)

```text
ENGINEERING READINESS

Requirements       PASS
Architecture       PASS
Structure          PASS
Propulsion         INCOMPATIBLE
Energy             PASS
Electronics        INCOMPATIBLE
Control            PASS
Catalog            PASS
BOM                INCOMPLETE

PROJECT STATUS: NOT ASSEMBLY READY

TOP GAPS

GAP-ESC-UNDERSIZED
  ESC current rating below per-motor demand
  HIGH — blocks: electronics, propulsion, energy
  depends_on: []
  next: revise_esc_rating

GAP-ESC-UNDEFINED
  ESC not defined
  HIGH — blocks: electronics, propulsion, bom
  ...
```

---

## 5. Electrical compatibility authority

### 5.1 Entry point (design intent)

```python
def evaluate_electrical_compatibility(project_state: Any) -> CompatibilityResult:
    """Pure. No I/O. No LLM. Returns facts — not gaps."""
```

`CompatibilityResult` carries enumerated check outcomes, e.g.:

- `esc_presence: defined | missing | unverifiable`
- `esc_vs_motor: compatible | undersized | unverifiable`
- `battery_discharge: within_limit | exceeded | unverifiable`
- `prop_motor: compatible | mismatch | unverifiable | not_applicable`

Readiness maps facts → gap types + `INCOMPATIBLE` / `INCOMPLETE` / `UNVERIFIABLE`.

### 5.2 Per-motor current draw (priority order)

1. SKU `MotorSpec.max_current_a` when motor `catalog_ref` bound  
2. Else `motor_power_w / V_nom` when both `motor_power_w` and `battery_cell_count` (→ `V_nom = cells × 3.7`) present  
3. Else **`unverifiable`** for ESC undersized check

### 5.3 Battery discharge (pack-level)

When battery SKU bound with `max_continuous_current_a` **or** derivable from `c_rating × capacity`:

- Compare against **total** draw estimate (`I_motor × motor_count` when per-motor draw known)
- Exceeded → fact `battery_discharge: exceeded` → `GAP-BATTERY-DISCHARGE-EXCEEDED`

Pack-level vs per-ESC comparison is **intentional** — different physical questions.

### 5.4 Topology

**MVP lock:** one declared `components["esc"]` represents the **per-channel ESC rating** replicated across motors (conventional quad). Jarvis does **not** infer series/parallel/custom wiring.

Future: explicit topology model — **out of ERF-2**.

---

## 6. Gap catalog (ERF-2 MVP — stable type IDs)

### 6.1 `GAP-ESC-UNDEFINED`

| Field | Value |
|---|---|
| **Trigger** | `esc` in expected keys (post ★5) and `classify_component("esc") == missing` while motors + battery are present enough for flight evaluation |
| **Severity** | HIGH |
| **Verdict impact** | `electronics: INCOMPLETE`, `bom: INCOMPLETE` — **not INCOMPATIBLE** |
| **blocks** | `electronics`, `propulsion`, `bom` |
| **depends_on** | `[]` |
| **recommended_next_step** | `{action: "define_component", params: {component_key: "esc"}}` |

If ESC missing **and** current evidence insufficient for undersized check → emit **UNDEFINED only**, not UNDERSIZED.

### 6.2 `GAP-ESC-UNDERSIZED`

| Field | Value |
|---|---|
| **Trigger** | `electrical_compatibility.esc_vs_motor == undersized` (★3, ★4) |
| **Severity** | HIGH |
| **Verdict impact** | `electronics: INCOMPATIBLE`, `propulsion: INCOMPATIBLE` |
| **blocks** | `electronics`, `propulsion`, `energy` |
| **depends_on** | `[]` — if ESC absent, UNDEFINED wins; do not co-emit |
| **recommended_next_step** | `{action: "revise_esc_rating", params: {}}` |

**Predicate (locked):** `esc.current_a < I_motor` (per-motor), not × motor_count.

### 6.3 `GAP-BATTERY-DISCHARGE-EXCEEDED`

| Field | Value |
|---|---|
| **Trigger** | `electrical_compatibility.battery_discharge == exceeded` |
| **Severity** | HIGH |
| **Verdict impact** | `energy: INCOMPATIBLE` |
| **blocks** | `energy`, `propulsion` |
| **depends_on** | `[]` |
| **recommended_next_step** | `{action: "revise_battery_or_load", params: {}}` |

### 6.4 `GAP-PROP-MOTOR-MISMATCH` (integration B)

| Field | Value |
|---|---|
| **Trigger** | `library.match_motor_propeller(...)` returns no viable match when both sides have sufficient evidence |
| **Severity** | HIGH |
| **Nature** | **Existing authority exposed through Readiness** — no second implementation of match logic |
| **Verdict impact** | `propulsion: INCOMPATIBLE`, `catalog: WARNING` or INCOMPATIBLE per evidence table in IC |
| **blocks** | `propulsion`, `catalog` |
| **depends_on** | `[]` |
| **recommended_next_step** | `{action: "revise_propeller_or_motor", params: {}}` |

### 6.5 Explicitly deferred gap types

- `GAP-MOTOR-ESC-VOLTAGE-MISMATCH` — **not in ERF-2**
- ESC/FC/integration/wiring/comms gaps — **ERF-3+**

---

## 7. Subsystem model (v2 — nine lines)

```text
requirements | architecture | structure | propulsion | energy | electronics | control | catalog | bom
```

| Subsystem | ERF-2 change |
|---|---|
| **electronics** | **NEW** — ESC presence + ESC amp compatibility facts |
| **propulsion** | May show `INCOMPATIBLE` from ESC/prop checks |
| **energy** | May show `INCOMPATIBLE` from battery discharge |
| **others** | ERF-1 rules unchanged |

**Forbidden:** `integration`, `communications`, `sensors` as readiness lines without new authority.

### 7.1 INCOMPATIBLE vs INCOMPLETE (examples)

| Case | Gap | Verdict |
|---|---|---|
| ESC not defined | `GAP-ESC-UNDEFINED` | `electronics: INCOMPLETE` |
| ESC 20A, motor needs 30A | `GAP-ESC-UNDERSIZED` | `electronics: INCOMPATIBLE` |
| No current evidence | none | `electronics: UNVERIFIABLE` |
| Sim PASS + ESC undersized | `GAP-ESC-UNDERSIZED` | sim validated; `overall: NOT_ASSEMBLY_READY` |

---

## 8. Architecture change — ESC orphan fix (★5)

**Required product change (ERF-2):**

```python
BLOCK_TO_COMPONENTS["propulsion"] = ["motors", "propellers", "esc"]  # esc added
```

Effects:

- `build_component_bom` may emit `esc` in missing/incomplete
- `GAP-ESC-UNDEFINED` fires deterministically
- Acquisition/Brief prompts — **optional slice**; not blocking MVP if gap + CLI suffice

---

## 9. depends_on matrix (ERF-2 MVP)

All **`[]`** unless future contract adds explicit edges.

**Mutual exclusion (implementation rule, not depends_on graph):**

- ESC missing → `GAP-ESC-UNDEFINED` only  
- ESC present + undersized evidence → `GAP-ESC-UNDERSIZED` only  

---

## 10. Implementation slices (binding order)

| Slice | Deliverable | Depends on |
|---|---|---|
| **1 — Compatibility authority** | `electrical_compatibility.py` + tests | — |
| **2 — ESC in architecture** | `BLOCK_TO_COMPONENTS` + BOM regression tests | — |
| **3 — Readiness extension** | New gaps, `electronics` line, `INCOMPATIBLE` emission | 1, 2 |
| **4 — CLI surface** | TOP GAPS + subsystem INCOMPATIBLE in render | 3 |
| **5 — Continuity handoff (optional)** | Scoped electrical top_gap branch | 3 — **defer from MVP** |

**Do not** implement Slice 5 or ERF-1 Slice 4b in the same cut unless Engineer explicitly expands scope.

---

## 11. Explicit non-goals

- Full electrical solver (transients, wiring, connectors)
- ESC JSON catalog H5 (parallel track OK, not blocking)
- KV/voltage → INCOMPATIBLE
- Geometric integration / cabling
- `"aplica la mejor"` optimizer
- Impl C procurement BOM
- LLM compatibility inference
- `integration` / `communications` subsystem lines
- ERF-1 Slice 4b bundled
- Changes to `FeasibilitySimulator` electrical surface (defer)

---

## 12. Acceptance probes (design-time)

1. **Sim PASS + ESC undersized:** `overall NOT_ASSEMBLY_READY`, `propulsion/electronics INCOMPATIBLE`, ERF-1 gaps still compose.
2. **ESC undefined:** `GAP-ESC-UNDEFINED`, `INCOMPLETE` not `INCOMPATIBLE`.
3. **Insufficient evidence:** no false `INCOMPATIBLE`.
4. **Battery C-rating exceeded:** `GAP-BATTERY-DISCHARGE-EXCEEDED` when SKU evidence supports it.
5. **Prop mismatch:** gap fires via `match_motor_propeller` — single implementation in library.
6. **ERF-1 regression:** all 40 ERF-1 tests green when compatibility returns all-compatible.
7. **Nine subsystems:** exactly 9 keys; no integration/comms lines.

---

## 13. Engineer decisions — absorbed (2026-08-18)

See investigation §13. All five blocking decisions **CLOSED**. This design doc operationalizes them as ★1–★11.

---

## 14. Next step

```text
ERF-2 INVESTIGATION     ✅ CLOSED
ERF-2 DESIGN            ← this file — await Engineer ratification
Implementation Contract   ← implementation_contract_erf2.md
Claude implementation     ←
checkpoint-erf2             ←
```

**Do not implement until Implementation Contract is approved.**

---

**End of design.**
