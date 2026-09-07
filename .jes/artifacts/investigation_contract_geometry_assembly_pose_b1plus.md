# Investigation Contract — Geometry Assembly Pose B1+ (numeric pose / reference frame)

**Project:** Jarvis  
**Date:** 2026-09-07  
**Author:** JES / Cursor (Engineer Interface)  
**Formulation:** Engineer ★ — assembly queue **2/3** after Board edges B2 CLOSED + smoke ACCEPT  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_geometry_assembly_pose_b1plus.md`

**Status:** READY FOR INVESTIGATION — Engineer asked to redact (`redactalo`) after closing B2  
**Parents (mandatory):**
- [implementation_contract_geometry_assembly_pose_b1plus.md](implementation_contract_geometry_assembly_pose_b1plus.md) — **QUEUED stub** (DO NOT IMPLEMENT; this investigation unblocks a superseding READY IC)
- [investigation_report_geometry_assembly_espacial_b1.md](investigation_report_geometry_assembly_espacial_b1.md) — B1+ pose **rejected** then: no catalog mount source, no reference frame
- [investigation_review_geometry_assembly_espacial_b1.md](investigation_review_geometry_assembly_espacial_b1.md) — agree defer B1+
- Assembly relation CLOSED: `mounted_on` @ **2364** · Continuity declare @ **2380** · Board edges B2 @ **2385** + smoke ACCEPT
- [engineer_lock_geometry_spatial_representation_progression.md](engineer_lock_geometry_spatial_representation_progression.md)

**Type:** Investigation only — minimum **honest numeric pose** model (if any) on top of declared `mounted_on`.  
**Not** an Implementation Contract. **Do not implement.**

**Checkpoint base:** package **`0.3.8`** · suite **2385**

**Single objective (locked):**

> Determine whether Jarvis can store a **minimum declared pose** (position and/or orientation relative to a named reference) that is **honest without inventing catalog mount patterns**, and what Buy (if any) is safe after `mounted_on` + Board edges — **without** fit, CAD, or treating Board card `x`/`y` as physical pose.

**Product sentence this rung must enable (honest) — provisional until report:**

```text
Sé a qué se declara montado + (si procede) con qué pose declarada respecto a un origen nombrado
```

**Not:**

```text
Cabe · ensamblado verificado · el drag del Board es la pose · offsets inventados del datasheet
```

**You are Claude Code.** Write the report only. Cursor reviews. Engineer ★ locks Buy / Defer / re-scope before any READY IC replaces the pose stub.

**Do not implement. Do not bump version. Do not weaken tests. Do not open fit/clearance/intersection/CAD/FEA. Do not invent mount-hole patterns or mm offsets without a cited primary source or an explicit declared-by-user / unknown honesty path. Do not make Board `localStorage` layout the geometric SoT. Do not reopen ESC mass, thrust H2/H3, Here3/Pixhawk, HD-004. Do not claim pose ≡ verification.**

---

## 0. Role split (do not invert)

```text
Engineer  → closed B2 smoke; asked for this investigation contract
Cursor    → this contract; review report; READY IC only after ★ Buy
Claude    → investigation_report_geometry_assembly_pose_b1plus.md
Engineer ★ → Buy lean / Defer / Skip pose (jump framing) — never silent implement
```

---

## 1. Why this investigation exists now

Shipped on the assembly rung:

| Slice | Status |
|---|---|
| `mounted_on` relation + Board text | CLOSED @ **2364** |
| Continuity IDLE declare/clear | CLOSED @ **2380** |
| Board edges B2 | CLOSED @ **2385** + Engineer smoke ACCEPT |

The queue placeholder IC for pose exists but is **not** READY. The prior assembly investigation already rejected numeric pose **for that cycle**. This investigation re-opens the question **with the relation layer now real**, and must answer whether anything changed — or whether pose stays deferred.

Wrong next step:

```text
add x_mm/y_mm/z_mm on ComponentSpec · Continuity “pon el FC a 10mm” · read card pixels as mm
```

Right question:

> What is the **smallest durable pose bag** (fields + reference frame + honesty) that can live in `ProjectState` next to `mounted_on`, project optionally to Board, and never imply “fits” — **or** is Defer still the only honest Buy?

---

## 2. Locked stances (inherit)

1. Board card `x`/`y`/`width`/`height` (and `localStorage` overlay) remain **layout only** — never physical pose SoT.
2. `mounted_on` stays the assembly **relation**; pose must be **orthogonal** (not overload `parent_key`).
3. No fit / clearance / “cabe” / collision in any recommended Buy.
4. Prefer **declared** user numbers or **cited** catalog/geometry sources over invented defaults.
5. If no reference frame can be named honestly, recommend **Defer** — do not paper over with “assume plate center.”
6. Continuity may later declare pose only if the model is locked; this investigation does **not** design the parser.

---

## 3. Baseline to inventory (cite live tree)

| Surface | Check |
|---|---|
| `ComponentSpec` | Confirm only `mounted_on` (+ `parent_key`) for assembly; zero pose/offset/orientation fields |
| Catalog seeds (Motor/Battery/ESC/FC/Frame/Prop) | Any mount pattern, hole spacing, CG offset, “mount face” fields today? |
| Frame parts (`frame_plate*`, `frame_arm`, …) | Any geometric origin, size usable as a reference frame without invention? |
| Board projector / edges | How `mountedOn` projects today; confirm no pose math |
| Continuity `mounted_on_declare_assist` | Confirm declare path is relation-only |
| Prior report §D / §F (assembly B1) | Re-state why B1+ was rejected; what evidence would reverse that |

---

## 4. Governing questions (answer all)

**A. Reference frame**

1. What **named origins** could be honest today (e.g. plate label centroid, arm root, frame root) without inventing CAD?
2. Is “user-declared origin string + numbers” enough, or must the origin be a component key already in `components`?
3. If origin target ≠ `mounted_on` target, is that allowed / required / forbidden?

**B. Pose bag minimum**

4. Smallest field set: translation only (`x_mm,y_mm[,z_mm]`)? + yaw? full attitude?  
5. Units locked to mm? Degrees?  
6. Must every mount have a pose, or is pose **optional** beside `mounted_on`?

**C. Honesty / provenance**

7. `source` values: `declared` (user) vs `catalog` (cited) vs `unknown` / omit — what is allowed in B1+?  
8. What copy is forbidden (ensamblado, cabe, verificado, “posición real”)?

**D. Board / Continuity (display only — no IC yet)**

9. If pose exists, may Board show it as text fields only (like `"montado en"`), or must it move glyphs? **Default lean: text-only first.**  
10. Is Continuity declare-of-pose in scope for a first Buy, or deferred like Continuity was for relation B1?

**E. Buy options**

Recommend exactly one default lean among:

| Option | Meaning |
|---|---|
| **B0 — Defer** | Pose stays stub; no schema; jump to fit investigation only if Engineer ★ says so |
| **B1 — Optional declared translation** | Minimal mm offsets + named origin; optional; text on Board |
| **B1+ — Translation + yaw** | Only if A/B are solid without invention |
| **Reject numeric pose** | Keep relation-only forever until catalog mount KNOW exists |

State what would make you change the lean.

---

## 5. Non-goals (explicit)

- Fit / clearance / intersection / “cabe”
- Auto-layout of Board cards from pose
- Reading pixel layout as mm
- Inventing mount holes / patterns for SKUs
- Changing `mounted_on` semantics or Board edges B2 behavior
- Conversation Engine / CAD / FEA / version bump
- Implementing Continuity pose phrases in this investigation

---

## 6. Deliverable shape (report)

1. Executive recommendation (Buy option + one paragraph why).  
2. Evidence table (schema / catalog / Board / Continuity) with file cites.  
3. Answers A–E.  
4. Risks if we Buy wrong.  
5. Explicit: does this investigation **supersede** or **reaffirm** the B1+ rejection in the assembly espacial report?  
6. If Buy ≠ B0: sketch of fields only (names + honesty) — **not** an IC; Cursor writes IC after ★.

---

## 7. Done criteria

- [ ] Report written at the path above  
- [ ] All governing questions answered with tree evidence  
- [ ] Default lean stated; Defer allowed and preferred when evidence thin  
- [ ] No code / no READY IC authored by the investigator  
- [ ] Cursor investigation review next; Engineer ★ before any implementation IC

---

## 8. Stop conditions

Stop and ask before: recommending Board layout as pose SoT, inventing catalog mount geometry, opening fit, or writing implementation code.
