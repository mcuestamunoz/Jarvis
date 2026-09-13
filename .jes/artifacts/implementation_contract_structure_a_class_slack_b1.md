# Implementation Contract — Structure A LEVEL A class slack (5.x-on-5)

**Project:** Jarvis  
**Date:** 2026-09-11  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Cursor / Claude — after Engineer ★ on this text  
**Reviewer:** Cursor against this IC · Engineer smoke on `autonomía-de-5min` / `autonomía-15min`

**Status:** READY FOR ★ — predicate-only · no geometry · no “cabe”  
**Parents:**
- Structure A / [implementation_contract_structure_foundations.md](implementation_contract_structure_foundations.md) — LEVEL A class screening locked as **convention**, not geometric fit  
- Smoke stack #4*: Gemfan Hurricane MCK **51466-3** (`diameter_in=5.189`) + GEPRC GEP-Racer (`size_class_inch=5`) — bind works; Structure stays INCOMPLETE forever under today’s strict `D ≤ class`  
- [implementation_contract_geometry_sourced_prop_gemfan_51466_b1.md](implementation_contract_geometry_sourced_prop_gemfan_51466_b1.md) · [implementation_contract_geometry_sourced_frame_gep_racer_b1.md](implementation_contract_geometry_sourced_frame_gep_racer_b1.md)

**Type:** One-line predicate change in `frame_class_compatibility_state` (+ tests + Continuity/CTA honesty if copy names the inequality).  
**Not** CAD · not clearance · not plate L×W · not weakening `GAP-FRAME-SIZE-MISSING` · not version bump · not changing Gemfan/GEP catalog numbers.

---

## 0. Why (Engineer smoke evidence)

| Fact | Value |
|---|---|
| Prop catalog | `gemfan_hurricane_mck_51466_3_v2` → **D = 5.189 in** (sourced) |
| Frame catalog | `geprc_gep_racer_5in` → **class = 5 in** (page Propeller: 5 inches) |
| Today’s predicate | `class_compatible` iff `D <= size_class_inch` |
| Result | **5.189 > 5** → `class_incompatible` → `GAP-FRAME-PROP-SIZE` → Structure / arch block never closes |
| Bind | Already OK — project shows `geprc_gep_racer_5in` + parts; wizard re-asks because class gap keeps `frame` in `still_missing` |

**Product sentence:**

```text
En FPV, "frame 5\"" es clase comercial (props ~5–5.1"), no un tope
geométrico D≤5.000. LEVEL A sigue siendo convención de clase — con
holgura explícita — nunca "la hélice cabe".
```

---

## 0.1 Engineer Buy (locked options — pick one ★)

| Option | Predicate | Covers Gemfan 5.189 on class 5? | Notes |
|---|---|---|---|
| **A (DEFAULT propose)** | `D <= size_class_inch + SLACK` with **`SLACK = 0.25` in** | **Yes** (5.189 ≤ 5.25) | Covers common 5.1 / 5.25 props on 5" freestyle frames; still fails a true 6" prop on 5" class (6 > 5.25) |
| **B** | `ceil(D) <= size_class` (or `floor(D+ε)` band) | **Yes** for 5.189→6? **Dangerous** — ceil(5.189)=6 would require class ≥6, which **fails** this stack. Reject unless redefined carefully | Do **not** pick B as written |
| **C** | Nominal class match: treat prop as class `round(D)` or manufacturer size class if seeded | Needs prop `size_class_inch` field or round rules | Larger schema; out unless Engineer insists |
| **D HOLD** | Keep strict `D <= class` | **No** | Smoke must use 7" frame or smaller prop — abandons #4* stack |

**Locked recommendation for ★:** **Option A · SLACK = 0.25 in**, named constant, disclosed in docstring + Continuity/gap evidence fact.

Engineer may ★ A with a different slack (e.g. **0.20** still covers 5.189; **0.10** does **not**). Report the ratified number.

---

## 1. You (implementer)

- Wait for ★ (Option A + final `SLACK`, or D HOLD / other).  
- If ★ A: change **only** the compare in `frame_class_compatibility_state` (and docstring).  
- Keep return tokens identical: `not_required` / `missing` / `class_compatible` / `class_incompatible`.  
- Keep gap types / severity / blocks unchanged.  
- Update Continuity / `frame_next_missing_question` copy **only if** it hard-codes “D supera clase” without acknowledging class slack — still **never** “cabe” / VERIFIED / misfit geométrico.  
- Tests: Gemfan-shaped 5.189 + class 5 → compatible; 6.0 + class 5 → still incompatible; 5.0 + class 5 → compatible; missing class unchanged.  
- Full suite green. Report.  
- **STOP** if asked to invent plate clearance, arm boxes, or to delete LEVEL A.

---

## 2. Intent

```text
prop D (exact sourced inches)
frame size_class_inch (commercial class)
        ↓
LEVEL A: D <= class + SLACK   (Option A)
        ↓
GAP-FRAME-PROP-SIZE only when clearly wrong class
        ↓
#4* stack GEP-Racer 5" + Gemfan 51466 can close Structure class gate
```

Honesty preserved: still **class convention**, not geometric interference.

---

## 3. Locked behavior (Option A)

### 3.1 Predicate — `project_closure.frame_class_compatibility_state`

Replace:

```text
class_compatible  iff  D <= size_class_inch
class_incompatible iff  D >  size_class_inch
```

With:

```text
SLACK_IN = <Engineer-ratified float, default propose 0.25>
class_compatible  iff  D <= size_class_inch + SLACK_IN
class_incompatible iff  D >  size_class_inch + SLACK_IN
```

- Single named constant (module-level), not a magic inline number at call sites.  
- Docstring must state: slack is **FPV class convention** (e.g. 5.1" props on 5" frames), **not** a clearance budget, **not** proof the prop fits the arm.  
- `frame_size_blocks_structure_complete` / ERF `_frame_class_gaps` / Continuity `_frame_class_gap_live` keep calling the **same** predicate — no duplicated inequality.

### 3.2 Evidence / copy

| Surface | Change |
|---|---|
| Gap evidence fact | May include `slack_in=0.25` alongside `diameter_in` / `size_class_inch` |
| Continuity CTA | Keep LEVEL A / “no establecida” / “no demuestra interferencia”; may say class screening uses commercial slack — **never** “cabe” |
| BOM tails | Unchanged strings; they already key off predicate state |

### 3.3 Out of scope

- Changing catalog `diameter_in` or `size_class_inch` seeds to “lie” the numbers  
- Prop `size_class_inch` schema  
- Geometry / CAD / standoff Ø / plate L×W  
- Softening `GAP-FRAME-SIZE-MISSING` (class still required when D known)  
- Version bump  

---

## 4. Tests (minimum)

| ID | Assert |
|---|---|
| T1 | `D=5.189`, class `5` → `class_compatible` (under ratified slack ≥ 0.189) |
| T2 | `D=6.0`, class `5` → `class_incompatible` (still clearly wrong class) |
| T3 | `D=5.0`, class `5` → `class_compatible` (unchanged happy path) |
| T4 | `D=5.189`, class missing → `missing` (unchanged) |
| T5 | Live-shaped: bind GEP-Racer + Gemfan 51466 on a mini project → **no** `GAP-FRAME-PROP-SIZE`; structure class gate not blocked by this pair |
| T6 | Regression: existing Structure A test that used `D=7` vs class `5` still incompatible |

Update any golden that assumed strict `5.189 > 5` if present (should not invent new gap types).

---

## 5. Files (expected)

| Path | Action |
|---|---|
| `src/jarvis/core/project_closure.py` | `SLACK` constant + predicate compare + docstring |
| `tests/test_structure_a.py` (and/or thin new file) | T1–T6 |
| Continuity / prompt helpers | **only if** copy asserts strict `D > class` without slack |
| docs / `.jes` state / report | sync after |
| catalog seeds · ui · version | **no** |

---

## 6. Smoke (Engineer)

On `autonomía-de-5min` (already has GEP-Racer + Gemfan 51466):

1. `estado` → **no** `GAP-FRAME-PROP-SIZE` for this pair.  
2. Structure / architecture can leave the class gate (other gaps may remain).  
3. Continuity must **not** claim geometric fit / “cabe”.

---

## 7. Handoff

```text
Engineer → ★ Option A + SLACK (propose 0.25), or D HOLD / other
Cursor/Claude → implement + report
Cursor → review
Engineer → smoke 5min/15min stack
```
