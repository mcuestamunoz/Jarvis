# Investigation Contract — Control parity

**Project:** Jarvis  
**Date:** 2026-09-04  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_control_parity.md`

**Status:** INVESTIGATION REVIEWED — PASS WITH NOTES · IC drafted · awaiting Engineer `procede` on IC  
**Review:** [investigation_review_control_parity.md](investigation_review_control_parity.md)  
**Report:** [investigation_report_control_parity.md](investigation_report_control_parity.md)  
**IC:** [implementation_contract_control_parity.md](implementation_contract_control_parity.md)  
**★ thread:** [engineer_ratification_control_parity.md](engineer_ratification_control_parity.md)  
**Phase:** [engineer_ratification_phase_transition_knowledge_parity.md](engineer_ratification_phase_transition_knowledge_parity.md)  
**Agenda:** [engineer_agenda_knowledge_and_block_parity.md](engineer_agenda_knowledge_and_block_parity.md)  
**Prior thread (CLOSED):** claim hygiene — suite **2160**

**Type:** Knowledge / claim investigation. Answer what “control complete” /
Control PASS / architecture 4/4 may assert **without** control physics and
**without** assuming a sensor catalog. **Not** an Implementation Contract.
**Do not implement.**

**Checkpoint base:** tag **`v0.3.6`** / **`checkpoint-experimental-prop-energy-closed`** · commit `f70b278`  
**Live tree:** claim hygiene B4 is in product (suite **2160**). Do not revert it.

**You are Claude Code.** Write the report only. Cursor reviews. Engineer ★
locks the claim matrix / Buy before any IC.

**Do not implement. Do not bump version. Do not weaken tests. Do not invent
control physics, sensor/FC catalog JSON, ESC H5, or new architectural
subsystems.**

---

## 0. Role split (do not invert)

```text
Engineer ★ → chose control parity after claim hygiene; catalog not default Buy
Cursor     → this contract (later IC only after ★)
Claude     → investigation_report_control_parity.md
Cursor     → investigation review
Engineer ★ → claim matrix / Buy lock
Cursor     → IC if Buy ≠ investigation-only
Claude     → implements from IC only
```

---

## 1. Why this investigation exists

Propulsion / energy / Structure A / claim hygiene now show honest limits.
**Control** is still mostly declarative acquisition (`Pixhawk 4`, `GPS M9N`)
while ERF can still show Control **PASS** and architecture **4/4**.

Hypothesis to verify (not assume):

```text
_control_evidence:
  defined    = flight_controller present
  calculated = defined          # same bit — no control calculation
  simulated  = bool(sim)        # any sim, not control-specific
  validated  = sim_status==pass # thrust/sim PASS ≠ control validated
  catalog_bound = FC catalog_ref  # usually false; no FC catalog in library/
```

That is a **Claim** asymmetry vs prop/energy — not a reason to ship a sensor
catalog “like motors.”

Engineer already locked: sensor/FC catalog is **not** the default Buy for this
thread ([engineer_ratification_control_parity.md](engineer_ratification_control_parity.md)).

---

## 2. Governing questions (answer all four)

1. **Know** — Which variables / components exist today for control (`flight_controller`,
   `sensors`, GPS maps, completeness tiers)? What is **absent** (no physics vars,
   no catalog rows, sensors unused by `_control_evidence`)?
2. **Claim** — Which user-facing or ERF sentences over-claim when FC+sensors are
   merely declared? Build a **claim matrix** (sentence × allowed meaning).
3. **Measure** — What would falsify or strengthen a control claim **without** lab
   or invented physics (declaration only vs refuse-to-validate vs future catalog)?
4. **Buy** — Smallest honest next purchase: **copy/claim gates only**, **ERF
   evidence predicate honesty** (e.g. stop treating `calculated=defined` /
   `validated=sim pass` as if they meant control calculation), **documentation
   lock only (B0)**, or **catalog** (only if you prove claim language cannot be
   honest without identity rows — and even then recommend catalog as a **later**
   IC, not bundled with claim gates)?

Default stance: prefer claim/ERF honesty over catalog. Prefer not changing
`_derive_overall` / ASSEMBLY_READY eligibility unless you prove a lying 4/4 or
Control PASS that claim copy cannot fix — that is an **Engineer ★ stop**.

---

## 3. Locked constraints (do not weaken)

1. No control-loop / PID / fusion / failsafe physics.
2. No new `library/sensors/` or FC catalog JSON in this investigation; do not
   draft catalog schemas as the primary deliverable.
3. Do not reopen claim-hygiene N2 (PhaseLayer) or N4 (weak-OP Continuity) as
   the center of this report — one paragraph max if they interact with control
   copy.
4. Do not reopen H5 ESC catalog, C-A1, HD-*, G24-B, Conversation Engine,
   Structure CAD, or broad `orchestrator.py` split.
5. Do not implement fixes.
6. Preserve Engineer workspaces; reconstruct in `tmp_path` / in-memory.

---

## 4. Surfaces to trace (file:line required)

| Surface | Find |
|---|---|
| Architecture block `control` | `system_architecture_catalog` keys; `_block_progress_status` / presence tier for FC + sensors |
| Completeness | `_flight_controller_completeness`, `_sensor_completeness` in `domains/aerial.py` |
| Writers | `set_control_component` — what gets stored; any physics bypass note |
| ERF control | `_control_evidence` + how verdict becomes PASS / INCOMPLETE |
| Sensors vs evidence | Does `sensors` presence affect `_control_evidence` at all? |
| Continuity / CLI | Any “control complete” / architecture 4/4 / Control PASS wording |
| BOM / closure | How FC/sensors appear in BOM / declarative vs incomplete |
| Catalog assist | Confirm no G21-style help-choose for FC/sensors (or document if any) |
| Library | Confirm no FC/sensor rows under `library/` (ESC exists — out of scope) |

---

## 5. Field reconstruction

Reproduce at least one fixture:

```text
flight_controller declared (e.g. Pixhawk 4) → completeness medium/high
sensors declared (e.g. GPS M9N / Here3)
architecture control block → complete / 4/4 reachable
ERF control verdict → record PASS vs other
sim PASS (optional) → record whether control.validated flips with thrust PASS
```

Record exact Continuity / readiness lines that a user would read. State whether
“control complete” is **declaration-complete**, **physics-validated**, or
**ambiguous**.

---

## 6. Required report shape

### A. Executive answer (≤15 lines)

What may Jarvis claim today about control, and what is the primary over-claim
(if any)?

### B. Know table

| Fact | Authority (`file:line`) | Used by ERF? | Used by Continuity? |

### C. Claim matrix

Rows = exact strings or verdict labels (`Control PASS`, `Arquitectura 4/4`,
BOM lines, acquisition prompts). Columns at minimum:

| Sentence / verdict | Allowed meaning today (honest) | Over-claims? | Proposed allowed meaning |

### D. Measure

Declaration-only vs refuse-to-say-validated vs needs catalog/lab.

### E. Buy recommendation (exactly one primary)

| Option | Meaning |
|---|---|
| **B0** | No IC — Engineer lock in docs/agenda only |
| **B1** | Continuity / CLI claim copy only (ERF predicates unchanged) |
| **B2** | ERF `_control_evidence` honesty (e.g. calculated/validated semantics) ± copy — **no** `_derive_overall` change unless required |
| **B3** | Change ASSEMBLY_READY / gap types so undeclared or declaration-only control blocks ready — **Engineer ★ stop** if recommended |
| **B4** | Split: claim/ERF honesty now; **optional later** thin FC/sensor catalog IC only if Buy proves identity rows are required |

Justify. Prefer smallest option that stops the lie.

### F. Explicit non-goals confirmed

No sensor catalog as default · no control physics · no H5 · no claim-hygiene
reopen · no C-A1.

### G. IC skeleton (only if Buy ≠ B0)

≤20 lines: files, behavior, tests, forbidden. **Not** an IC.

---

## 7. Out of scope

- Implementing any fix
- Authoring catalog JSON or bind UX for FC/sensors
- ESC / electronics parity (separate block)
- Weak-OP Continuity (N4) as primary scope
- Version bump

---

## 8. Done criteria

- Report at the path above with A–G filled
- Every factual claim cites `file:line` or named test on live tree / `v0.3.6`
- Buy option chosen; if B3, stop for Engineer ★
- No `src/` edits

---

## 9. After review

Cursor writes investigation review. Engineer ★ on claim matrix / Buy. Only then
IC (if any). After control parity closes, Engineer plans to **end** the
knowledge/block-parity phase and open a new feature cycle.
