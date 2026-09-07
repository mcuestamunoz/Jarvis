# Investigation Review — Geometry Assembly Pose B1+ (numeric pose / reference frame)

**Date:** 2026-09-07  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_geometry_assembly_pose_b1plus.md](investigation_contract_geometry_assembly_pose_b1plus.md)  
**Report:** [investigation_report_geometry_assembly_pose_b1plus.md](investigation_report_geometry_assembly_pose_b1plus.md)  
**Parents:** Assembly `mounted_on` CLOSED · Continuity CLOSED · Board edges B2 CLOSED @ **2385** · prior B1+ rejection

## Verdict

**PASS WITH NOTES**

Governing questions A–E answered with tree evidence. Default lean **B0 — Defer** is correct. Report **reaffirms** (does not supersede) the assembly-espacial rejection of numeric pose: `mounted_on` + edges solved addressability, not reference-frame convention. No READY implementation IC should be written from this report.

Engineer ★ still required to **lock Defer** (or override with an explicit risk Buy).

---

## Checklist

| Criterion | Result |
|---|---|
| Executive recommendation | **Pass** — B0 Defer |
| Evidence table (schema / catalog / Board / Continuity) | **Pass** |
| Answers A–E | **Pass** |
| Reaffirm vs supersede prior B1+ rejection | **Pass** — reaffirm |
| Reversal criteria named | **Pass** — three concrete conditions |
| Contingency field sketch (not recommended) | **Pass** — scalar + prose only |
| No `src/` / `tests/` this cycle | **Pass** (investigator + `git status`) |
| Fit / layout-as-SoT / invented mounts out | **Pass** |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| `ComponentSpec` has `parent_key` + `mounted_on` only (no pose fields) | **Confirmed** (`action_schema.py`) |
| Continuity assist is relation-only | **Confirmed** (no pose/offset parse surface) |
| Board edges use card pixel rects, not mm pose | **Confirmed** (`mountEdgeGeometry.ts`) |
| Catalog seeds lack mount/hole/offset/CG keys | **Consistent** with report’s field-key union + prior FC hole-pattern note |
| Pose stub still DO NOT IMPLEMENT | **Confirmed** |

---

## Agreement with report core

1. **Addressability ≠ reference frame** — correct and load-bearing.  
2. **Plate labels name plates; they do not define a geometric center** — correct.  
3. **B1 / B1+ numeric bags presuppose an axis convention that does not exist** — correct.  
4. **Defer with named reversal criteria** beats permanent Reject — agree.  
5. **Contingency scalar+prose is not a Buy recommendation** — agree; must not become a silent IC.

---

## Notes

### N1 — Engineer ★ Defer

Locking B0 means: pose stub stays queued/blocked; **no** schema/Continuity/Board pose work; assembly queue item **2/3** closes as **Deferred** (not Implemented).

### N2 — Do not open fit by default

Fit/compare (queue 3/3) remains separately gated. Deferring pose does **not** auto-★ fit — fit needs its own investigation when Engineer chooses.

### N3 — Stack bolt patterns (reversal #1)

If Engineer later ★ a **narrow** “FC/ESC stack hole-pattern KNOW” investigation, keep it **orthogonal** to relative-assembly pose (report §E) — do not conflate 30.5×30.5mm self-geometry with airframe mount pose.

---

## Recommended Engineer moves

| Choice | Effect |
|---|---|
| ★ **Defer (recommended)** | Close pose 2/3 as deferred; idle or ★ fit investigation separately |
| ★ Override (scalar+prose or axis convention) | Requires explicit risk acceptance + new READY IC — do not use the stub as-is |
| ★ Skip to fit | Allowed only as separate Buy; write fit investigation contract first |

---

## Phase

Investigation **reviewable**. Await Engineer ★ on **B0 Defer** (default). No implementation.
