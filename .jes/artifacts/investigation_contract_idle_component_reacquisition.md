# Investigation Contract — IDLE component re-acquisition

**Project:** Jarvis  
**Date:** 2026-09-04  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_idle_component_reacquisition.md`

**Status:** ★ RATIFIED (Engineer `procede` 2026-09-04) · IC ready  
**Report:** [investigation_report_idle_component_reacquisition.md](investigation_report_idle_component_reacquisition.md)  
**Review:** [investigation_review_idle_component_reacquisition.md](investigation_review_idle_component_reacquisition.md)  
**IC:** [implementation_contract_idle_frame_rebind_b2.md](implementation_contract_idle_frame_rebind_b2.md)  
**★:** [engineer_ratification_idle_component_reacquisition.md](engineer_ratification_idle_component_reacquisition.md)  
**Engineer mandate:** OK 2026-09-04 after Structure close + CLI walks (Armattan `└`, G-N1, free-text overwrite / recovery). Next product path = **re-adquisición de componentes en IDLE** (not more Structure geometry). Soft coherence (e.g. arms↔motors) is a **secondary fork to evaluate**, not the default Buy.

**Type:** Acquisition / Continuity / routing investigation. Answer how a user reopens catalog or component definition **after** architecture 4/4 and catalog bind — without lying, without MEASURE. **Not** an Implementation Contract. **Do not implement.**

**Parents (do not re-derive):**
- Structure block ★ CLOSED @ suite **2229** — [engineer_ratification_structure_block_closed.md](engineer_ratification_structure_block_closed.md)
- Post-close walk ACCEPT — [engineer_cli_walk_structure_block_post_close.md](engineer_cli_walk_structure_block_post_close.md)
- Catalog assist precedents: G21 motors · propeller · battery · Structure Catalog Foundation IC-3 frames
- FN-011 / FN-014 acquisition mention + `_next_pending_block` gate
- Structure B: `arm_count` ↔ `motor_count` claim-closing cross-check remains **forbidden**

**Checkpoint base:** tag **`v0.3.6`** / **`checkpoint-experimental-prop-energy-closed`** · commit `f70b278`  
**Live tree:** Structure honesty + parts graph + G-N1 are in product (suite **2229+**). Do not revert.

**You are Claude Code.** Write the report only. Cursor reviews. Engineer ★ locks Buy before any IC.

**Do not implement. Do not bump version. Do not weaken tests. Do not reopen Structure PASS meaning, MEASURE/CAD/FEA, Conversation Engine, or new architectural subsystems.**

---

## 0. Role split (do not invert)

```text
Engineer ★ → OK'd IDLE re-acquisition as next path after Structure close
Cursor     → this contract (later IC only after ★ on Buy)
Claude     → investigation_report_idle_component_reacquisition.md
Cursor     → investigation review
Engineer ★ → Buy lock / phrase matrix
Cursor     → IC if Buy ≠ investigation-only / B0
Claude     → implements from IC only
```

---

## 1. Why this investigation exists

Field evidence (Engineer CLI, 2026-09-04), architecture already **4/4**, frame **catalog-bound**:

| User phrase | Observed routing | Problem |
|---|---|---|
| `cambiar frame` | Iterate wizard (“¿Qué quieres modificar?”) | No catalog re-offer; parametric / structure-factor path |
| `definir frame` | Iterate confirm / not frame COMPONENT wizard | Same class of miss |
| `ayúdame a elegir` (IDLE) | Motor → propeller → battery assist chain | Bound frame never re-offered |
| `frame Armattan Quads Rooster 5"` | Low-completeness prompt for mass/material/class | Name string ≠ SKU bind |
| Free-text `fibra … 450g …, 4 brazos…` | Global component intercept **works** | Overwrites catalog_ref; mass change can flip sim PASS→fail |

Hypothesis to verify (not assume):

```text
Once _next_pending_block is None (architecture complete):
  FN-014 / acquisition-from-mention returns None
  → "definir|cambiar|declarar <component>" falls to iterate / engineering_intent
  → catalog assist exists only inside DEFINE_MISSING with expected_keys
  → _wants_catalog_help(spec) is False when catalog_ref is set
  → IDLE help-choose never reaches frame (or other done components)
```

Product gap: **first-time acquisition** is strong; **re-acquisition / SKU swap** after bind is weak or misleading.

---

## 2. Governing questions (answer all)

1. **Know** — For each of `frame`, `motors`, `propellers`, `battery` (and briefly `esc` / `flight_controller` / `sensors`): what IDLE / iterate / DEFINE paths exist today to (a) open numbered catalog, (b) free-text overwrite, (c) parametric iterate? Cite `file:line`.
2. **Claim** — Which user-facing sentences imply “you can change the frame/motor like at first bind” when the actual path is iterate, free-text-without-SKU, or dead-end? Phrase matrix required.
3. **Gate** — What exactly prevents reopening COMPONENT wizard when architecture is complete? Map `_next_pending_block`, FN-014 mismatch, `_wants_catalog_help`, IDLE `_try_start_assisted_*` order.
4. **Buy (primary)** — Smallest honest next purchase for **re-acquisition** (see §6 E options). Prefer frame-first slice if that unblocks the field walk with least risk; say if motors/battery already have a better pattern to mirror.
5. **Coherence fork (secondary)** — Given DSE can set `motor_count=3` while frame parts show `└ arm ×4` / quad SKU: may Continuity emit a **soft non-blocking** note? Or must this stay debt because Structure forbids claim-closing cross-check? **Default lean: debt / B0 for coherence** unless you prove a Continuity-only warning that cannot be read as Structure validation. Do **not** recommend PASS gates or sim fail on arms↔motors.

---

## 3. Locked constraints (do not weaken)

1. Structure block stays **CLOSED**. No MEASURE, CAD, FEA, fit, clearance, tip-to-tip.
2. Do **not** introduce `arm_count` ↔ `motor_count` as a claim-closing or ERF/Structure PASS check.
3. Do **not** invent Conversation Engine / Decision Engine / new domain modules.
4. Do **not** weaken ASSEMBLY_READY / `_derive_overall` unless you prove a lying ready state caused solely by re-acquisition UX (unlikely — flag as Engineer ★ stop).
5. Free-text overwrite remaining legal is OK; investigation must say whether re-bind should **clear / replace / orphan** `frame_*` children (relate to debt **G-N4**, do not silently expand scope into orphan cleanup IC unless Buy requires it).
6. Do not implement fixes. Preserve Engineer workspaces; reconstruct in `tmp_path`.
7. H5 ESC catalog, FC/sensor catalog, G24-B, weak-OP Continuity as primary scope — **out**.

---

## 4. Surfaces to trace (file:line required)

| Surface | Find |
|---|---|
| Intent | `intent_resolver.py` — `cambiar`/`definir`/`modificar` + component nouns → `iterate` vs define_missing |
| Iterate entry | `iterate_interactive_session.py` / `iterate_domain.py` — valid variables; `estructura` vs `componentes` vs `frame` |
| FN-014 / mention | `acquisition_target.py`, `orchestrator._try_start_acquisition_from_mention` — behavior when `pending_block_key is None` |
| Pending block | `orchestrator._next_pending_block` — when None after 4/4 |
| Catalog help predicate | `_wants_catalog_help` — stub / no `catalog_ref` only |
| IDLE help-choose chain | `_try_start_assisted_motor_help` → propeller → battery — any frame hook? |
| Frame catalog offer/pick | `_offer_component_frame_catalog` / `_apply_component_frame_catalog_pick` — only under DEFINE_MISSING? |
| Global intercept | `_interceptable_component_specs` / `_handle_component_description` — free-text frame from IDLE when already bound |
| Bind / writers | `bind_frame_from_catalog`, `set_frame_material`, `upsert_frame_part` — overwrite semantics; children on re-bind |
| Continuity | Any CTA that tells user to “cambiar frame” / “revisa frame” without a working reopen path |
| Precedents | Motor/prop/battery IDLE assist when underspec or unbound — reusable pattern for **bound swap**? |

---

## 5. Field reconstruction (required)

Reproduce in `tmp_path` (do not mutate Engineer workspace projects):

### Fixture A — bound frame, architecture complete

```text
create aerial project → bind motors + props + battery + frame (catalog SKU) + FC + sensors
architecture 4/4, catalog_ref on frame set
IDLE phrases (record action + mode + whether catalog list opens):
  - "cambiar frame"
  - "definir frame"
  - "ayúdame a elegir"
  - "ayúdame a elegir frame" / "ayúdame a declarar estructura" (if recognized)
  - "frame <exact catalog display name>"
  - free-text root-only mass change
```

### Fixture B — G-N1 then root-only update

```text
frame free-text with parts → confirm └ children
then root-only free-text → confirm children persist (G-N4-adjacent)
```

### Fixture C — contrast (optional but useful)

```text
Same project, IDLE "cambiar batería" / "ayúdame a elegir" after battery bound
Record whether battery re-offer is better/worse than frame — drives "mirror which precedent"
```

Record exact CLI/orchestrator `action` names and Continuity lines.

---

## 6. Required report shape

### A. Executive answer (≤15 lines)

What can a user do today to swap a bound frame/motor/battery after 4/4, and what is the primary product lie or dead-end?

### B. Know table

| Component | Catalog reopen today? | Free-text overwrite? | Iterate path? | Authority (`file:line`) |

### C. Routing matrix (phrases × outcome)

| Phrase | Mode after | Opens numbered catalog? | Honest? | Desired (proposal only) |

### D. Gate analysis

Diagram or bullet chain: architecture complete → why FN-014 / help-choose / `_wants_catalog_help` block re-acquisition.

### E. Buy recommendation (exactly one primary)

| Option | Meaning |
|---|---|
| **B0** | No IC — docs/agenda only (debt) |
| **B1** | Continuity / CLI copy only — stop promising “cambiar frame” paths that open iterate; point to working free-text phrases |
| **B2** | IDLE / mention bridge: phrases like `cambiar frame` / `ayúdame a elegir frame` open **existing** frame COMPONENT catalog offer even when `catalog_ref` set (explicit **rebind** / swap) — mirror smallest existing assist |
| **B3** | B2 + extend same pattern to motors/propellers/battery (shared “rebind when bound” predicate) — only if B2 alone is proven insufficient or duplicated logic would rot |
| **B4** | Iterate wizard teaches `componentes` → catalog (heavier; justify if B2 is wrong seam) |
| **B5** | Soft Continuity coherence note arms↔motors / DSE motor_count vs frame config — **secondary only**; must be non-blocking; Engineer ★ if recommended as primary |

Justify. Prefer **smallest** option that fixes the field dead-end. Default Engineer lean: **B2 framed on frame-first**, coherence as non-primary.

### F. Rebind semantics (required if Buy ∈ {B2,B3})

On catalog re-pick after prior bind:

- Replace root `catalog_ref` / mass / material?
- Replace or clear `frame_*` children? (Armattan→TBS, free-text→SKU)
- Must recalc/sim be prompted? (observe current writers; do not invent physics)

Relate to G-N4 debt — in-scope note vs defer.

### G. Explicit non-goals confirmed

No Structure PASS widen · no arms↔motors gate · no MEASURE · no FC/sensor catalog · no H5 · no Conversation Engine · no Structure reopen.

### H. IC skeleton (only if Buy ≠ B0)

≤25 lines: files, behavior, tests (IDLE phrase → catalog list → pick → SKU + parts), forbidden. **Not** an IC.

---

## 7. Out of scope

- Implementing any fix
- Structure geometry / parts-graph ontology reopen
- DSE scoring rewrite (G24-B)
- Orphan cleanup as a standalone IC unless Buy F forces a one-line policy
- Version bump
- Lab / hardware campaigns

---

## 8. Done criteria

- Report at the path above with A–H filled
- Every factual routing claim cites `file:line` or named test on live tree / `v0.3.6`
- One primary Buy; coherence fork explicitly B0 or B5-secondary
- No `src/` edits

---

## 9. After review

Cursor writes investigation review. Engineer ★ on Buy / phrase matrix / rebind semantics. Only then Implementation Contract (if any).

**Success signal for a later IC walk:** on ASSEMBLY READY project with TBS or freeform frame, `cambiar frame` or `ayúdame a elegir frame` opens the numbered frame list; pick Armattan → `[armattan_rooster_5in]` + `└` parts; Continuity stays honest.
