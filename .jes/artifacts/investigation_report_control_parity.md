# Investigation Report — Control parity

**Project:** Jarvis
**Date:** 2026-09-04
**Investigator:** Claude Code
**Contract:** [investigation_contract_control_parity.md](investigation_contract_control_parity.md)
**Checkpoint:** tag `v0.3.6` / `checkpoint-experimental-prop-energy-closed`, commit `f70b278`; live tree includes claim-hygiene B4 (suite 2160, preserved, not reverted)
**Status:** OPEN — for Cursor review, then Engineer ★ on the claim matrix

Not an Implementation Contract. No `src/` edits were made. No sensor/FC catalog
JSON or schema was drafted. Reconstructions run in-memory against the live
tree (the claim-hygiene edits do not touch anything read here).

---

## A. Executive answer

The hypothesis is **confirmed, and understated**. `_control_evidence`
(`engineering_readiness.py:1077-1083`) is exactly as documented in
`implementation_contract_erf1.md:202`: `defined`/`calculated` collapse to one
bit ("FC not stub"), `simulated`/`validated` borrow the global thrust
simulation's flags — a pattern shared with every other subsystem
(`:195-204`), so this alone is not control-specific.

What **is** control-specific: none of control's four evidence flags are ever
grounded in anything control-related, because **no control calculation
exists at all** — confirmed by zero references to `flight_controller`,
`gps_model`, or `sensor_type` in `calculation_engine.py` or `simulator.py`,
and by `component_writers.py:127`'s own docstring: *"Sin physics bypass —
control no afecta cálculo en Fase 2.5."* Structure/propulsion/energy's
`defined`/`calculated` at least trace to numbers the simulation actually
consumes (mass, thrust, capacity); control's cannot, structurally.

I reconstructed the cheapest real input that reaches **`Control PASS`**,
**`Arquitectura 4/4 — completa ✓`**, a BOM line `✓ flight_controller: ...
(high)` — the same glyph/tier a physically-measured motor entry gets — and
overall **`ASSEMBLY READY`**: typing `"Pixhawk 4"` for the flight controller
and `"GPS M9N"` for sensors. Both are pure brand/model **name recognition**
(`domains/aerial.py`), with zero engineering property behind them beyond the
recognized string itself. `Control PASS` and `Arquitectura 4/4` are reachable
with even less: the bare words `"pixhawk"` + `"gps"` (no model number at
all) already clear the "present" bar (`component_presence_tier`,
`project_closure.py:410-425`, which "deliberately does NOT require
measurable data").

The over-claim is real but **fixable with claim copy alone** (Buy = **B1**):
the underlying facts (declared-only, no control physics) are already
computed and available; nothing needs a new predicate, a new gap type, or a
sensor/FC catalog. Recommending the predicate-honesty option (B2) turns out,
on inspection, to be equivalent to a **B3** given today's architecture —
flagged in §E, not recommended.

---

## B. Know table

| Fact | Authority (`file:line`) | Used by ERF? | Used by Continuity/CLI? |
|---|---|---|---|
| `control` block = `flight_controller` + `sensors` | `system_architecture_catalog.py:163` (`BLOCK_TO_COMPONENTS["control"]`), block type `"component"` (`:109`), block label `"Control (controladora + sensores)"` (`:40,49`) | Drives `arch_progress`/BOM `expected_keys` | Yes — feeds `"Arquitectura {progress} — completa ✓"` (`main.py:303,307`; `orchestrator.py:3493,3495,4527`) |
| `_control_evidence`: `defined=calculated=`FC not stub`; `simulated=bool(sim)`; `validated=sim_status=="pass"`; sensors never checked | `engineering_readiness.py:1077-1083`; documented design table `implementation_contract_erf1.md:195-204` (uniform `validated=sim pass` across nearly every subsystem — not control-unique) | Yes — feeds `subsystems["control"].verdict` | No (Continuity never names "control" specifically) |
| `component_presence_tier`: "present" needs completeness != `"low"` — explicitly **not** measurable data | `project_closure.py:410-425` (docstring: *"deliberately does NOT require measurable data"*) | Gates `defined` for control (and all component subsystems) | Gates architecture-block "complete" |
| `flight_controller` extraction: pure brand/model string match; `"high"` only if a matched alias contains a digit (confidence ≥ 0.85) | `domains/aerial.py:301-344` (`extract_flight_controller_properties`, `_flight_controller_completeness`); verified: `"pixhawk 4"` → high/0.9, `"pixhawk"` → medium/0.7, `"controladora"` → low/0 | `classify_component` → `"defined"` bucket iff high + `"model"` in `_MEASURABLE` (`project_closure.py:377`) | BOM `"✓ ... (high)"` line (`format_bom_lines`, `:713-733`) |
| `sensors` extraction: GPS/sensor-type keyword match; **never reaches `"high"`** — `_sensor_completeness` has only medium/low branches | `domains/aerial.py:349-380,436-445`; verified: `"gps"` (bare, confidence 0.6) and `"here3"` (confidence 0.9) both → `"medium"` | `classify_component` → capped at `"declared"` forever (never `"defined"`) — the one honest asymmetry in this surface | BOM `"◇ ... (declarativo)"` line, never `"✓"` |
| No control-loop/PID/fusion/failsafe computation anywhere | Verified: `grep -rn "flight_controller\|gps_model\|sensor_type"` over `calculation_engine.py`/`simulator.py` → zero hits; `component_writers.py:123-135` docstring states it explicitly | N/A | N/A |
| No FC/sensor catalog exists | `library/` contains only `esc/`, `motores/`, `materiales/`, `baterias/`, `helices/` — no sensor/FC folder | `catalog_bound` for control is always `False` in practice (informational field, not part of the PASS conjunction) | No "ayúdame a elegir" CTA for FC/sensors — confirmed below |
| No catalog-assist / rich Brief for FC/sensors | `acquisition_brief.py:55` (`_BRIEF_KEYS = frozenset(_BRIEF_BLURB)` excludes `flight_controller`/`sensors`); `:94` (`"ayúdame a elegir"` gated to `("motors", "propellers", "battery")` only) | N/A | FC/sensors get bare `COMPONENT_PROMPTS` free-text question only |
| BOM `"defined"`/`"✓"` bucket conflates measured physics with name-recognition | `classify_component`, `project_closure.py:428-456`; `_MEASURABLE` (`:360-378`) includes both real physics fields (`thrust_n`, `kv_rating`, `battery_capacity_wh`, …) **and** two identity-only fields, `"model"` (FC) and `"gps_model"`/`"sensor_type"` (sensors) | Feeds BOM bucket, not ERF directly | `format_bom_lines` renders identical `"✓ key: name (high)"` shape for both classes |

---

## C. Claim matrix

| Sentence / verdict | Allowed meaning today (honest) | Over-claims? | Proposed allowed meaning |
|---|---|---|---|
| `Control` line → `PASS` (readiness block, `main.py:107-118,130-158`) | "`flight_controller` is not a stub, AND some simulation ran, AND that (thrust) simulation passed." No control-specific computation occurred. | **Yes** — same bare `PASS` glyph as `Propulsion`/`Energy`/`Structure`, which trace to real physics inputs feeding that same simulation; a reader has no way to tell `Control PASS` means "declared" while `Propulsion PASS` means "computed." | Keep verdict value `PASS` (no ERF change); render with a distinguishing marker or footnote naming it declaration-only, e.g. `Control PASS *` + `* declaración, sin física de control` (exact copy: Engineer ★ to lock) |
| `Arquitectura {n}/4 — completa ✓` (`main.py:303,307`; `orchestrator.py:3493,3495,4527`) | "All 4 architecture blocks reached `_block_progress_status == "complete"`," where control's bar is *both* FC and sensors non-stub — a keyword match, nothing more. | **Yes**, for the control quarter of this count specifically — the aggregate "4/4" reads as full engineering completeness. | Keep the counter unchanged (safe, minimal); optionally note in Continuity evidence that "control" is declaration-only when it's the reason 4/4 was reached (copy-only) |
| BOM `✓ flight_controller: {name} (high)` (`format_bom_lines`, `project_closure.py:717-719`) | "`completeness == "high"` and a `_MEASURABLE` key is present with no missing fields" — for FC that key is `"model"`, a recognized **brand/model string**, not a physical quantity. | **Yes, the sharpest one** — visually identical to `✓ motors: ... (high)`, where `"high"` means a numeric thrust/KV value was captured. A reader cannot distinguish "we know the part number" from "we measured the part." | Keep the `"defined"`/`✓` bucket (no `classify_component` change — that's shared BOM plumbing, out of this thread's smallest scope); append an identity-only suffix for `flight_controller` specifically, e.g. `✓ flight_controller: pixhawk_4 (high — identidad, sin dato físico)` |
| BOM `◇ sensors: {name} (declarativo)` | "GPS model or sensor type keyword recognized; can never reach `"defined"` — `_sensor_completeness` has no high tier." | **No** — this is already the honest tier for sensors; the diamond glyph and "(declarativo)" label already read as provisional. Kept for contrast in this matrix. | Unchanged |
| `flight_controller`/`sensors` acquisition prompts (`acquisition_target.py:118-119`) | "Describe la controladora de vuelo. Ej: 'Pixhawk 4'..." — a free-text example, not a claim of physics. | No — these are honest prompts, not claims. | Unchanged |
| ERF `subsystems.control.catalog_bound == False` | "No FC is bound to a catalog SKU" — always true today, informational only. | No — accurately reflects reality and is not part of the PASS conjunction. | Unchanged |

---

## D. Measure

Two concrete, reproducible falsifiers, both verified by direct calls into
`domains/aerial.py` and `engineering_readiness.py` on the live tree (no
lab, no new physics):

1. **Cheapest input that reaches `Control PASS` + `Arquitectura 4/4`:**
   flight_controller text `"pixhawk"` (confidence 0.7 → `medium`,
   non-stub) + sensors text `"gps"` (confidence 0.6 → `medium`, non-stub).
   Neither carries a specific model, a serial, or any physical property.
2. **Cheapest input that reaches the strongest visual claim — BOM's
   `✓ ... (high)`, matching a numeric motor/battery/propeller entry:**
   flight_controller text containing a digit-bearing alias, e.g.
   `"Pixhawk 4"` (confidence 0.9 → `high`, `classify_component == "defined"`)
   — no numeric property is ever captured; `"model"` is a string identity
   field, counted as `_MEASURABLE` alongside real physics fields.

What Jarvis must refuse to claim without new work: that `Control PASS`,
architecture "control complete," or a BOM `"✓ ... (high)"` flight-controller
line mean anything about control-loop behavior, sensor accuracy, failsafe
readiness, or PID tuning. All of that would require actual control physics —
explicitly out of scope per the ratification and this contract. Falsifying
the *current* over-claim requires no such physics: it only requires
**naming**, in the copy, what the flags in §B already, honestly, are.

A sensor/FC catalog would **not** falsify or strengthen this claim on its
own — it would add identity/SKU rows (like ESC/motors have), but
`_control_evidence`'s `validated` flag would still borrow the unrelated
thrust simulation's pass/fail, so "Control PASS" would still not mean
"control validated" even with a full catalog. Catalog is therefore not the
Buy for this specific over-claim (consistent with the Engineer ratification).

---

## E. Buy recommendation

**B1 — Continuity / CLI claim copy only. ERF predicates (`_control_evidence`,
`_derive_subsystem_verdict`, `_derive_overall`) stay untouched.**

Justification:

- The lie is fully addressable by naming, in rendered copy, facts the code
  already computes (`completeness`, which bucket a component landed in,
  whether a subsystem's evidence includes any control-specific check at
  all). No new field, no new gap type, no catalog.
- **B2 (ERF `_control_evidence` honesty) is rejected for this cycle** because
  it is not the narrow fix it looks like. `_derive_subsystem_verdict`
  requires `defined AND calculated AND simulated AND validated` for `PASS`
  (`engineering_readiness.py:1193-1194`). Control's `validated` is
  `sim_status=="pass"` — the *only* signal available, because no
  control-specific simulation exists. Making `validated` honest for control
  (e.g., requiring an actual control computation) would make it
  **permanently false** given today's architecture, so control could never
  reach `PASS` again — only `UNVERIFIABLE`. Since `_derive_overall` requires
  every subsystem to be `PASS` (or an accepted `WARNING`), this would flip
  `ASSEMBLY_READY` to `NOT_ASSEMBLY_READY` for **every currently-passing
  real drone project**, silently, without ever touching
  `_derive_overall`'s own code. That is the practical effect of a **B3**
  change wearing a B2 costume — the contract's own default stance names
  exactly this ("prove a lying 4/4 or Control PASS that claim copy cannot
  fix — that is an Engineer ★ stop"), and I have not proven claim copy
  cannot fix it; I have shown it can. B2 is therefore named here as a
  **future Engineer ★ decision** (does Jarvis want "declaration-only"
  subsystems to ever gate `ASSEMBLY_READY`?), not a recommendation.
- **B0** would leave a reproducible, two-word-input over-claim
  (`"pixhawk"` + `"gps"` → `Control PASS` / `4/4`) undocumented for
  Engineer ★ to act on, with no path to fix it short of a future
  investigation re-deriving what this one already found.
- **B4**'s "optional later FC/sensor catalog IC" is not proven necessary —
  §D shows a catalog would not even fix the specific lie identified (it
  would add identity, not validation). Not recommending it, per Buy default
  stance and the Engineer ratification's own §2.

---

## F. Explicit non-goals confirmed

Not proposed by this investigation:
- Sensor / FC catalog JSON or schema (confirmed no catalog needed to fix the
  identified over-claim, per §D/§E).
- Control physics: loop rates, PID, sensor fusion, failsafe modeling.
- Reopening claim-hygiene N2 (PhaseLayer/quality-vs-phase mismatch) or N4
  (weak-OP Continuity wiring) as primary scope — neither interacts with
  control copy; not revisited beyond this one sentence.
- H5 ESC catalog, C-A1 catalog honesty, HD-* hardware campaigns,
  Conversation Engine, Structure CAD, or a broad `orchestrator.py` split.
- Any change to `classify_component`, `component_presence_tier`, or
  `_MEASURABLE` (shared plumbing well beyond control; touching it would
  affect structure/propulsion/energy/BOM too — out of this thread's scope).
- Any change to `_derive_overall`, gap types, or the PASS-eligibility
  4-flag conjunction in `_derive_subsystem_verdict` (see §E's B2 rejection).
- Version bump.

---

## G. Suggested IC skeleton (claim-copy slice only — not an Implementation Contract)

- **Files:** `src/jarvis/adapters/cli/main.py` (`_render_readiness_block`:
  append a locked footnote/marker distinguishing declaration-only verdicts —
  candidate scope: control only, or control+catalog+bom if Engineer ★ wants
  parity with catalog's own G9-B WARNING language); `src/jarvis/core/
  project_closure.py` (`format_bom_lines`: append an identity-only suffix for
  `flight_controller` when bucket is `"defined"`/`"✓"`, mirroring the
  existing `_bom_identity_suffix` pattern already used for SKU resolution).
- **Behavior change:** rendered copy only — `Control` verdict value,
  `Arquitectura n/4` counter, BOM bucket membership (`✓`/`◇`/`…`/`✗`),
  `ASSEMBLY_READY` eligibility: all byte-identical. Only the strings shown
  next to an already-`PASS`/already-`"defined"` control entry change.
- **Tests:** extend `tests/test_engineering_readiness_cli.py` (Control
  footnote present/absent per fixture) and `tests/test_project_closure_v1.py`
  / `tests/test_impl_d_sku_bom.py` (flight_controller `"high"` suffix present;
  motors/battery/propellers/frame `"high"` lines unchanged, no suffix).
- **Forbidden:** `_control_evidence`, `_derive_subsystem_verdict`,
  `_derive_overall`, `classify_component`, `component_presence_tier`,
  `_MEASURABLE`, any `library/` catalog addition, any control-loop
  computation, `ASSEMBLY_READY`/`NOT_ASSEMBLY_READY` string values.
- **Exact locked copy** (the footnote/suffix wording) is an Engineer ★ call,
  not this investigation's — §C's "Proposed allowed meaning" column gives
  candidates only.
