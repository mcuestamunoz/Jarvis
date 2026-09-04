# Cross-review — Implementations that correct the CLI walk

**Date:** 2026-09-03  
**Reviewer:** JES / Cursor  
**Authority:** Engineer request — “revisión de las implementaciones para corregir los CLI walk”  
**Walk fixture:** [engineer_cli_walk_fail_routing_coherence.md](engineer_cli_walk_fail_routing_coherence.md)  
**Project:** `workspace/autonomía-de-10-minutos-86f6a0e8effa` (preserved)

**Verdict:** **ROUTING LAYER ADEQUATE FOR A RE-WALK · CATALOG LAYER STILL OPEN**

Three ratified implementations close the walk's *guidance* failures (F1–F4).
Structure physics (Structure A + N1) was already sound during the walk.
Catalog honesty (F5–F6) and optimize entry (F7) were explicitly deferred and
remain open. A fresh CLI walk is justified; it will not be “green” end-to-end
until catalog honesty lands if the Engineer again picks a margin-only motor.

---

## 1. What this review covers

| Implementation | Review | Suite at close | Role vs this walk |
|---|---|---|---|
| Structure A (masa + clase) | PASS WITH NOTES | 2140 | Physics/class screening — **confirmed good** in the walk itself |
| Structure A N1 hotfix (mass mirror) | PASS WITH NOTE | 2143 | Prevented dual-truth on `"pvc 5 pulgadas"` — **confirmed good** |
| CLI fail-routing coherence | PASS WITH NOTES | 2150 | **Direct fix** for F1–F4 presentation/routing |

Earlier CLI ICs (feasibility semantics, autonomy-below, stale-energy recalc,
catalog-assist T1 / watts-recovery) are adjacent hygiene from prior walks.
They are **not** the package that answered this catastrophic walk's F1–F7.
They stay closed; this review does not reopen them.

---

## 2. Walk failure → implementation map

| ID | Failure observed | Covered by | Status now |
|---|---|---|---|
| F1 | After `PVC 650g`, asks mass/material again; class known as gap | fail-routing §2.1–§2.3 | **Closed** in wizard + Brief + startup. Residual N1: `_append_arch_progress_hint` in-progress can still say generic “parámetros” if structure is class-missing while another block completes — **not** the walk loop. |
| F2 | `sim.status=fail` painted as `WARNING` | fail-routing §2.6 | **Closed** — WARNING line gated on empty Continuity situation |
| F3 | “el empuje ya es PASS” with `32.0 < 32.373` | fail-routing §2.4 | **Closed** — PASS claim only when `can_fly is True` |
| F4 | 4/4 → “puedes optimizar o simular” on fail | fail-routing §2.4–§2.5 | **Closed** as next-action; evidence footer `Arquitectura 4/4 — completa ✓` correctly remains |
| F5 | IDLE `ayúdame a elegir` → bare status reprint | intentionally **not** in fail-routing (C-A1) | **Open** — honest Continuity next-step on status reprint only |
| F6 | Catalog ranks `emax` #1 (8.0 N) via `max_thrust_n=10` | intentionally **not** in fail-routing (C-A1) | **Open** — product semantics / ranking |
| F7 | `optimizar propulsión` → generic iterate wizard | out of scope (§4) | **Open** — copy/intent; no Conversation Engine |

---

## 3. Quality of the fail-routing implementation

### Strengths

- Shared authority `frame_next_missing_datum` / `frame_next_missing_question` in
  `project_closure.py` — Brief, wizard probe, and component prompt share copy.
- Real-orchestrator walk fixtures in `tests/test_cli_fail_routing_coherence.py`
  (7/7), not Continuity-only stubs for the critical paths.
- Locked Spanish sentences match the IC verbatim for size-class and the two
  thrust-fail next steps.
- Non-goals honored: no D8 change, no new `status_type` enum, no ERF change,
  no orchestrator split.

### Residual risks before a re-walk

1. **N1 (fail-routing review):** generic in-progress arch hint — low probability
   on the sequential walk path; watch for it if jumping blocks.
2. **F5/F6 still live:** if the Engineer again says `ayúdame a elegir` at 4/4
   with a D8-admitted undersized nominal motor, status reprint is honest about
   thrust fail, but the picker still will not open and the ranked list still
   prefers under-nominal SKUs if opened via `definir motor`.
3. **F7 still live:** optimize remains generic; Continuity now tells the user
   not to re-sim with the same inputs — that is enough for the next-step, not
   for the optimize wizard itself.
4. **Physics unchanged:** `32.0 < 32.373` will still FAIL. That is correct.
   The walk should feel guided, not suddenly PASS.

### Structure A / N1 in this package

The catastrophic walk already proved Structure A writes and N1 mass
preservation. Fail-routing did not reopen them. Treat them as **stable
preconditions** for the re-walk, not as unfinished walk fixes.

---

## 4. Recommended Engineer moves

**A — Re-walk now (recommended default)**  
Fresh project (or wipe workspace). Same objective shape: autonomía ~10 min,
catalog motors, frame with class. Expect:

- F1–F4 gone;
- F5–F7 still possible;
- sim may still fail on thrust/autonomy — Continuity should name it honestly.

**B — Open catalog-honesty investigation before re-walk**  
Only if the Engineer wants the next walk to also exercise an honest motor
list. That is C-A1, a separate IC, not a reopen of fail-routing.

**C — Tiny N1 hotfix for `_append_arch_progress_hint` in-progress**  
Optional polish; do not block A.

Do **not** open a broad orchestrator refactor from this review.

---

## 5. Evidence re-check (this review)

Re-ran:

```text
tests/test_cli_fail_routing_coherence.py
tests/test_structure_a.py
tests/test_frame_component.py
→ all passed
```

Authoritative per-IC reviews remain:

- [implementation_review_structure_a.md](implementation_review_structure_a.md)
- [implementation_review_structure_a_n1_hotfix.md](implementation_review_structure_a_n1_hotfix.md)
- [implementation_review_cli_fail_routing_coherence.md](implementation_review_cli_fail_routing_coherence.md)

---

## 6. Bottom line

The implementations that were supposed to correct **this** CLI walk's routing
catastrophes did their job. The product is ready for a guided re-walk of
F1–F4. It is **not** yet ready to claim the catalog path is honest (F5–F6).
That gap was a deliberate sequencing decision (C-A1), not an implementation
miss inside fail-routing.
