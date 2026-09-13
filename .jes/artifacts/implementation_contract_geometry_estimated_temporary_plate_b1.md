# Implementation Contract — Estimated-temporary plate envelope B1 (`B1-estimated-temporary-plate`)

**Project:** Jarvis  
**Date:** 2026-09-13  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer smoke

**Status:** READY FOR ★ — architecture-validation path for plate L×W **without** contaminating engineering claims  
**Parents:**
- Plate-box B0 hold — [report](implementation_report_geometry_plate_box_b1.md) · [review](implementation_review_geometry_plate_box_b1.md) — empty caliper bag; this Buy is the **honest provisional** reopen  
- Declared plate envelope B1 **CLOSED** — Continuity already writes L×W×H as `source=declared`  
- `PropertyValue.source` today: `declared | inferred | calculated` (`action_schema.py`) — **extend minimally**  
- Assembly root already ships when `frame_plate` is a box  
- Fit / `cabe` screening — [pose_envelope_screening](../src/jarvis/core/pose_envelope_screening.py) already says “screening, no verificado”; still insufficient alone if copy cites invented mm as fact  
- Feature lock Continuity — no silent invent; Engineer-typed provisional **with gates** is in-philosophy  
- Full taxonomy (`UNKNOWN|VERIFIED|SECONDARY|INFERRED|ESTIMATED_TEMPORARY`) — **OUT** of this Buy (named debt only)

**Type:** First-class **`estimated_temporary`** provenance on plate box dims + Continuity declare + **hard gates** so UI/layout/root work while physics/validation claims refuse or refuse-to-speak.  
**Not** catalog Class A seed of provisional mm. **Not** quiet upgrade to `verified`. **Not** full evidence enum. **Not** stack-rule / layout-pack invent. **Not** version bump. **Not** silent `workspace/` unless ★ apply-live.

**Output:** `.jes/artifacts/implementation_report_geometry_estimated_temporary_plate_b1.md`

**Replaces / relates:** Reopens plate-box **only** via provisional path; measured replace later closes toward plate-box Path C (calibre) without keeping estimate as SoT.

**Checkpoint:** package **`0.4.1`** · suite ≥**2763** · UI ≥**99**

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-estimated-temporary-plate`** — provisional Main-plate L×W for **architecture / UI / layout** validation |
| 2 | Scope of keys | **Only** `is_frame_plate_key` box dims (`length_mm` / `width_mm` / `height_mm`). **Not** motors/props/battery/ESC/FC in this Buy (follow-on) |
| 3 | Schema | Extend `PropertyValue.source` with literal **`estimated_temporary`** (minimal). Do **not** add the full five-tier taxonomy yet |
| 4 | Continuity declare | New / extended IDLE phrase family that sets plate L×W (and H from thickness if omitted) with `source=estimated_temporary` — e.g. Spanish triggers including `estimada` / `temporal` / `provisional` + placa + mm. Existing plain declare stays `declared` (measured/Engineer-asserted without provisional mark) |
| 5 | §0.1 numbers | Engineer ★ supplies the provisional L×W (and optional H) in the bag — **not** copied from body 225×200 / 175×173 / wheelbase. Agent must not invent if bag empty → B0 hold |
| 6 | Allowed uses | Board solid + assembly root · Situar origin · rough layout / architecture tests · development |
| 7 | Forbidden uses (gates) | (a) **`cabe` bridge:** if child **or** origin box uses any `estimated_temporary` dim → **refuse** with honest message (do not answer fit with provisional mm). (b) **`declaro verificado` / fit attestation SET:** refuse when fingerprint inputs include estimated dims. (c) Catalog bind / Class A seed: never write provisional plate L×W into `library/`. (d) Copy must never say “cabe porque la placa mide X” using provisional numbers |
| 8 | Board / Continuity copy | Mandatory disclosure block (Spanish), e.g. `PLACA MAIN · GEOMETRÍA ESTIMADA TEMPORAL · evidencia: ninguna · sustituir al llegar el frame: SÍ` — on declare success message and Board field/badge if thin UI hook exists; else Continuity message + projector `fields` note sufficient for B1 |
| 9 | Replace path | Later measured declare (`source=declared` or clear provisional) **overwrites** estimated dims; clear any fit attestation on that plate / dependents per existing fingerprint-clear rules. Document in report |
| 10 | Live apply | ★ picks project(s) or **tests-only**. Default recommend one live project for architecture smoke |
| 11 | Out | Full evidence taxonomy · estimated battery/ESC/etc. · auto-pose · claiming Product B silhouette as verified · version bump |

**Product sentence:**

```text
Declaro L×W provisional de la placa main solo para probar layout/root;
Jarvis lo marca ESTIMATED_TEMPORARY, deja usar el Board, y se niega a
validar “cabe”/VERIFIED con esos mm. Cuando mida el frame, lo sustituyo.
```

### 0.1 Provisional bag — **Engineer fills under ★**

```text
### frame_plate estimated_temporary
purpose: architecture_validation
evidence: none
replace_when_frame_arrives: YES
length_mm: ?          # Engineer number — required
width_mm: ?           # Engineer number — required
height_mm: ?          # or use existing thickness_mm
projects: autonomía-de-5min | autonomía-15min | tests-only
forbidden_body_copy: do NOT use MY5 225×200 or GEP 175×173 as these values
```

Empty `length_mm`/`width_mm` → **B0 hold** (same discipline as plate-box).

**Rejected without override:**

| Source | Why |
|---|---|
| Body / Dimensions retail | Envelope ≠ plate (MY5/GEP locks) |
| Silent `declared` without provisional mark | Contaminates “sé esto” |
| Catalog `verified` row with these mm | Knowledge pollution |

---

## 1. You (Claude)

1. Schema: add `estimated_temporary` to `PropertyValue.source`.  
2. Writer path: plate envelope set with that source (extend `set_component_declared_box_envelope` or thin wrapper — prefer one clear entry point; do not weaken non-plate keys in this Buy).  
3. Continuity parse + IDLE bridge: provisional phrase → write estimated dims + disclosure message.  
4. Gates: `cabe` refuse; fit-attestation SET refuse when estimated dims in play; tests for both.  
5. Board: expose provenance on plate fields and/or short badge if DTO already carries property source (no Three.js rewrite).  
6. Tests: T1–T7 below. No catalog JSON plate L×W. No version bump.  
7. Report: list exact gate strings; note full taxonomy as debt.

**STOP if** forced to treat body footprint as plate or to skip gates.

---

## 2. Tests

| ID | Behavior |
|---|---|
| T1 | Provisional declare → `frame_plate` L×W with `source=estimated_temporary`; geometry box; root-capable |
| T2 | Plain (non-provisional) plate declare still `source=declared` |
| T3 | `cabe` with estimated plate as origin → refuse message (no overlap/no_overlap verdict) |
| T4 | Fit attestation SET with estimated dims involved → refuse / no write |
| T5 | Success copy includes ESTIMADA/TEMPORAL + replace-when-arrives signal |
| T6 | Measured/declared overwrite clears estimated sources on those keys |
| T7 | Full pytest green; package `0.4.1`; `library/frames` MY5/GEP unchanged (no plate L×W seed) |

---

## 3. Smoke (Engineer)

1. On ★ project: provisional declare with §0.1 mm → Board shows plate box at root + disclosure.  
2. Ask `cabe` involving that plate → Jarvis **refuses** validation (not “cabe/no cabe”).  
3. Try `declaro verificado` → refused.  
4. Situar / pose a boxed avionics onto plate → layout works.  
5. Confirm catalog MY5 still has no plate L×W.

---

## 4. Out of scope (named debt)

| Item | Note |
|---|---|
| Full enum UNKNOWN / VERIFIED / SECONDARY / INFERRED / ESTIMATED_TEMPORARY | Later investigation / Buy |
| Estimated dims for non-plate families | Separate ★ |
| Auto-invalidate energy/Structure PASS graphs | Only fit/cabe gates this Buy unless a test proves a silent physics read of plate L×W — if found, STOP and extend gate in-report |
| Product B silhouette claim | Still needs honest stack; provisional plate alone ≠ Product B verified |

---

## 5. Done when

- [ ] ★ + filled §0.1  
- [ ] Schema + declare + gates + T1–T7 + report  
- [ ] Engineer smoke ACCEPT  

---

## 6. Handoff

```text
Engineer → ★ + fill §0.1 L×W (not body envelope) + project target
Claude   → implement + report
Cursor   → review
Engineer → smoke §3 · later replace with caliper → declared
```
