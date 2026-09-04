# Investigation Contract — Structure A (masa + encaje)

**Project:** Jarvis  
**Date:** 2026-09-03  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_structure_a.md`

**Status:** INVESTIGATION CLOSED — reviewed PASS WITH NOTES. IC awaits Engineer `ratifico`.

**Type:** Product-path investigation. Trace **seams** (masa write, completeness/4/4, gap registry) so the first IC can implement the **already-ratified-in-essence** Structure A model without invading propulsion. **Not** a re-study of what `diameter_in` does to thrust. **Not** CAD. **Not** an Implementation Contract. **Do not implement.**

**Checkpoint base:** tag **`v0.3.5`** / **`checkpoint-phase25-hover-energy`** · commit `fc46938`  
**Live tree:** DSE apply honesto is in product (review PASS WITH NOTES, suite **2124**). Do not revert it.

**You are Claude Code.** This file is your work order. Cursor does not investigate and does not implement this slice. You write the report. Cursor reviews it. The **product model is locked** (Engineer, in essence). Your ★-relevant output is **seams**: one vs two ICs (B vs A-then-fit), gap vs completeness wiring, and the ASSEMBLY_READY gate. A later Implementation Contract is the only authorization to edit `src/`.

**Do not implement. Do not bump `pyproject.toml`. Do not weaken tests. Do not invent density, SKUs, watts, or a CAD subsystem.**

---

## 0. Role split (do not invert)

```text
Cursor  → writes this contract (and later the IC)
Claude  → investigates, writes investigation_report_structure_a.md
Cursor  → investigation review
Engineer ★ → only if the report picks A (split) or trips the ASSEMBLY_READY gate
Cursor  → writes IC from locked model + report seams
Claude  → implements from the IC only
```

**★ ratification (investigation):** [engineer_ratification_structure_a.md](engineer_ratification_structure_a.md)

Draft IC (hypothesis only — **not** your work order, **not** to implement):  
[implementation_contract_structure_a.md](implementation_contract_structure_a.md)

Optional notes (Cursor, **not** a report):  
[engineer_notes_structure_a.md](engineer_notes_structure_a.md)  
Walk leak: [engineer_cli_walk_block_closure_product_scope.md](engineer_cli_walk_block_closure_product_scope.md) — `PVC 200g` did not change `structure_mass_override_kg` (stayed 0.65).

Treat **notes and draft-IC file paths / function names / gap IDs** as hypotheses. Verify or refute with `file:line`. **Do not refute** the locked product model in §1 (unidirectional `diameter_in`, class required when \(D\) known, **class compatibility** LEVEL A not geometric fit, no class→thrust). If a seam cannot implement that model without lying, recommend shape **A** (masa now, class-compat next) — do not change the screening rules.

---

## 1. Why this investigation exists

Engineer **ratified in essence** the product model (2026-09-03, after the `diameter_in` repo map). This investigation does **not** reopen that model. It exists because the **draft IC guessed seams** (`apply_material_definition`, two gap types, completeness wiring). Claude traces those seams so the real IC is precise.

### Locked product model (do not contradict)

```text
diameter_in
     ├─ PROPULSIÓN (already in product — do not change)
     │     OP/combo > pairing filter > D⁴ only if thrust missing
     │     gemfan_5045 does not produce newtons via D⁴ when OP/bound thrust exists
     └─ STRUCTURE (this slice — new question)
           frame.size_class_inch vs D → CLASS COMPATIBILITY (LEVEL A / CLASS-BASED)
           never "cabe físicamente" / never FIT VERIFIED
           D is physical prop diameter; class is an architectural label — screening only
```

Unidirectional: `size_class_inch` **never** enters thrust, power, RPM, \(C_T\), or autonomy. Pitch / blades / bullnose stay out (no invented \(C_T\)).

Class-compatibility rules (Engineer physics lock, 2026-09-03 — **not** geometric fit):

```text
D known + class absent  → GAP + Structure INCOMPLETE
                          (class compatibility unverifiable — not silent PASS)
D <= class              → CLASS COMPATIBILITY PASS — LEVEL A / CLASS-BASED
                          (no thrust change; physical clearance NOT demonstrated)
D > class               → CLASS COMPATIBILITY GAP — Structure INCOMPLETE
                          (class convention exceeded; physical impossibility NOT demonstrated)
D unknown / no propeller → do not evaluate class compatibility;
                          structure may close on mass+material
```

**Forbidden copy (internal and CLI):** `STRUCTURAL FIT: VERIFIED`, “la hélice cabe”, “misfit geométrico demostrado”.  
**Allowed:** CLASS COMPATIBILITY PASS/GAP; user-facing may say “compatible de clase (nivel A)” / “clase incompatible (nivel A)”.  
**Gap type name:** prefer `GAP-FRAME-PROP-SIZE` (size/class), not a type named MISFIT.  
**No** `+0.25 in` slack. **No** mm→inch class fabrication.

**Do not** spend the report re-deriving OP vs \(D^4\). Confirm with `file:line` that a first IC **cannot** call `calculate_thrust_from_propeller` from frame class, then move on.

**Open gate (report must name, not invent a ★):** Three surfaces that are **not** the same:

```text
architecture 4/4          (_block_progress_status structure)
ERF ASSEMBLY_READY        (_derive_overall: 9 subsystems PASS + zero HIGH)
Continuity "not ready"    (situation / next_step copy)
```

Engineer said class-incompatibility → structure incomplete / not assembly-ready **in the conservative-policy sense** (do not convert unknown geometry into PASS). ★5: first IC does **not** add HIGH / does **not** edit `_derive_overall`. Prove whether structure **incomplete** already makes 4/4 false and/or Continuity honest. If ERF can still say ASSEMBLY_READY while structure is incomplete or a MEDIUM fit gap exists, **say so with `file:line`**. That dual is allowed today elsewhere; do **not** “fix” it with HIGH unless incomplete-block is **insufficient to stop a lying 4/4**. If you believe HIGH is required, **stop** — that is a separate Engineer ★.

---

## 2. Field facts (inspect, do not mutate)

Do **not** edit Engineer `workspace/`. Reconstruct from tests + code if needed.

```text
Walk: iterate PVC 200g → material string registered; structure_mass_override_kg stayed 0.65
Acquisition: "carbono 450g" → set_frame_material (hypothesis: already correct)
Thrust: propeller diameter_in / catalog OP — not frame
PRODUCT_SCOPE v1: CAD/FEM out of scope
_frame_completeness today: mass_kg + material → high (hypothesis)
apply_material_definition: patches design_properties.structure.material only (hypothesis)
PVC: MATERIAL_ALIASES has pvc; library density may be missing (Bug 44 class)
```

---

## 3. What you must trace (file:line)

### 3.1 Masa — every write path

| Path | Find |
|---|---|
| Acquisition / component description | `"carbono 450g"` / `_apply_inferred_component_spec` frame → `set_frame_material` |
| Iterate `PVC 200g` / `pvc 200g` / `frame pvc 200g` | IntentResolver + iterate session + `MutationEngine` (`apply_material_definition` **and** `apply_material_mutation`) + `iterate_interactive_session` (PVC “no physics data”). Where grams are dropped. |
| Material-only `"pvc"` | Density mutation vs “registrado sin datos físicos”. Does anything invent mass? |
| Canonical vs leftover | `components["frame"]` vs `design_properties.structure.material` vs `structure_mass_override_kg`. Who reads calc (`calculation_engine.py`). |

Name the **one** writer that should own mass after a first IC (expected: `set_frame_material`). Name every caller that bypasses it.

### 3.2 Completeness / architecture 4/4 / ERF

How `_block_progress_status("structure")`, `_frame_completeness`, BOM incomplete, and ERF `_structure_evidence` decide “structure done”. These can disagree (completeness high vs override stale; 4/4 vs ERF PASS). What happens if size is required **only when** \(D\) is known.

**When is \(D\) known?** Trace all of: `current_parameters["propeller_diameter_in"]`, `components["propellers"].properties["diameter_in"]`, catalog SKU with `diameter_in` but param missing. The first IC must use **one** predicate; name it.

### 3.3 Prop diameter — invasion check only

Confirm `GAP-PROP-MOTOR-MISMATCH` is motor↔prop, not frame↔prop. Confirm `CalculationEngine` uses `per_motor_max_thrust_n` before the \(D^4\) path. **Do not** redesign propulsion. List the files a Structure A IC must **not** edit (`aerodynamics.py`, `resolve_operating_point`, G22 filters) unless a helper is purely read-only.

### 3.4 Class compatibility — gap cost + LEVEL A copy

If the first IC adds `GAP-FRAME-SIZE-MISSING` and/or `GAP-FRAME-PROP-SIZE`:

- Which files must change.
- MEDIUM vs structure-incomplete vs Continuity vs `_derive_overall` (Gate in §1).
- Copy is **CLASS COMPATIBILITY / LEVEL A**, never VERIFIED, never “cabe”.
- Whether structure-block-incomplete is enough without a new gap type.

### 3.5 Extractors

`extract_frame_properties` — mass, material, would size regex collide with grams? (`200g` vs `5"`). mm conversion: confirm **out of first IC** unless a parser already exists.

---

## 4. Mandatory first-IC shapes (pick exactly one)

The report **must** recommend **exactly one**:

| Shape | Meaning |
|---|---|
| **B — Masa + class compatibility (product default)** | Engineer physics: masa honesta **and** class required iff \(D\) known; missing/incompatible class → structure incomplete; thrust untouched; CLASS COMPATIBILITY LEVEL A copy. **Physically preferred — do not pick A to “simplify physics”.** |
| **A — Masa only, then class-compat IC** | **Only if** combining the two **code seams** is unclean. Class compatibility still the next IC with the same rules — not dropped. |
| **C — Size always required** | Only if B cannot be implemented without lying 4/4 before any prop. |
| **D — Stop** | First IC not justified. |

Product default is **B**. Do not pick A to “simplify” the physics — the physics is already decided. A is a **sequencing** escape hatch.

Do **not** recommend CAD, \(D^4\) from class, invented \(C_T\) from pitch/blades, copying class from the prop, HIGH/`_derive_overall` without the §1 gate, control catalog, or H5.

If B is recommended, specify:

- Exact live iterate utterance + functions to change (not “mutation_engine and/or iterate”).
- One vs two gap types, or completeness-only with no new gap.
- How `_frame_completeness` vs project-level helper avoids a dual 4/4.
- Where CLASS COMPATIBILITY / LEVEL A is printed (gap title / Continuity / estado — never “verificado”, never “cabe”).
- Class incompatibility marks structure **incomplete**, not “complete + warning only”.

---

## 5. Report sections (required)

1. Executive summary (B unless A/C/D with evidence; seams in one paragraph).
2. Masa path table (path → writer → calc reads → walk leak yes/no) with `file:line`.
3. Completeness / 4/4 / ERF dual analysis.
4. Invasion check: files Structure A must not write (`file:line`).
5. Gap-registry + incomplete vs ASSEMBLY_READY (Gate §1).
6. Draft IC: **keep / change / drop** vs Engineer physics (CLASS COMPATIBILITY not FIT; no “cabe”; no +0.25; `GAP-FRAME-PROP-SIZE` not a type named MISFIT).
7. Recommended first IC: files, tests, non-goals.
8. Frozen honored.

No `src/` diffs. No new tests (investigation only).

---

## 6. Frozen

```text
CAD / FEM / STL / piece design
Invent PVC or any density
size_class_inch → CalculationEngine thrust / power / RPM / Ct / autonomy
Invent Ct from pitch / blades / bullnose
Copy size_class from propeller diameter
Claim STRUCTURAL FIT: VERIFIED / “la hélice cabe” / geometric misfit demonstrated
+0.25 in class slack
mm → size_class_inch
HIGH gap / `_derive_overall` change (unless Gate §1: stop and ask)
Control / sensors / ESC catalog (H5)
Option B ERF / Block PARCIAL
DSE scoring / EXPLORATION_GRIDS
G24-B, Tier 3, Conversation Engine
Mutating Engineer workspace/
Implementing the draft IC
```

---

## 7. After you finish

Write `.jes/artifacts/investigation_report_structure_a.md`. Stop. Cursor reviews. Cursor writes the real IC from the locked model + your seams (B unless you justified A). Engineer ★ only if you picked A or tripped the ASSEMBLY_READY gate.
