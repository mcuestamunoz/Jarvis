# Implementation Contract — SYS-MAP-004 Routing / System Map Audit

**Project:** Jarvis  
**Date:** 2026-08-14  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)  

**Status:** READY FOR ENGINEER → send to Claude  

**Type:** **Audit only** — System Map re-verification + focused routing diagnosis against live CLI evidence.  
**Product behavior:** **Zero intentional `src/` changes.** No FN. No Conversation Engine. No dual-dispatch refactor. No G1/H5/Impl C. No G3/G6/G7 implementation work in this cut.

**Checkpoint base:** `checkpoint-g5-dse-component-sync`  
**Working tree note:** G3 (`explore_continuity.py` + orchestrator wiring) may be **present but uncommitted**. Treat G3 as part of “current code under review” if the files exist; do **not** invent a checkpoint for it.

**Depends on:**  
- Living map: `docs/system_map/**` (SYS-MAP-002 tree; last bulk re-verify SYS-MAP-003)  
- Prior audit: `.jes/artifacts/implementation_contract_sys_map_003.md` + reports  
- Field evidence (this cut’s trigger): CLI transcript 2026-08-14 — sticky mid-arch acquisition  
- Related findings register: `.jes/artifacts/cli_findings_post_catalog_bind_v1.md`  
- Prior sticky audit: `.jes/artifacts/audit_2026-08-10_engineering_intent_vs_sticky_session.md` (FN-021 era)

**Workflow:** Claude audits → writes report(s) under `.jes/artifacts/` → Engineer forwards → Cursor reviews. **No commit/push unless Engineer asks.**

---

## 0. Why this cut (read carefully)

G3 CLI probe was blocked before Goal Plan / explore continuity could be tested.

### Observed (Engineer CLI, project `cf5304c6004a`, workspace cleaned then recreated)

```text
[architecture open — motors+propellers done, battery next]
User > simula          → simulate OK (DEFINE_MISSING soft-interrupt exists)
User > reducir payload → "Vamos a definir la batería…"   ← WRONG
```

Expected for `reducir payload` (post F-1 / FN-022):

```text
Goal Plan — reducir_payload + handoff (C-040 / C-041 / C-105)
```

Actual: turn swallowed by the **battery acquisition wizard** (DEFINE_MISSING / component-description path).

### Engineer hypothesis (to validate or refute — do not assume)

```text
The System Map’s turn-order / authority picture is incomplete or stale
for the interaction between:

  mid-architecture DEFINE_MISSING (legitimate next block via C-037)
        vs
  engineering_intention (C-040) / explore (C-042/C-106)

FN-021 fixed "zombie after arch complete".
It did NOT create a DEFINE_MISSING preempt for engineering goals
(compare C-052 preempt on ITERATE_INTERACTIVE).

Map claims such as ACQUISITION_MAP "Known issues: None"
and C-040 🟢 "CONNECTED" may overstate reachability when mode ≠ IDLE.
```

Secondary symptom in the same session (also audit, do not merge into one root cause without evidence):

```text
Motor already bound: sunnysky_r2305_2500
Continuity next-step still says:
  "no tengo un motor en el catálogo que cubra ese espacio"
```

That may be Continuity / catalog-bind honesty (C-080/C-081 family), not the sticky-wizard bug.

```text
SYS-MAP-003 (map↔code + hygiene)     ← done earlier
Catalog A/B · F-1 · G5 · G3 (code)   ← landed since map last bulk-audited
        │
        ▼
SYS-MAP-004  ← you are here (audit only)
  A) Focused routing diagnosis (CLI finding)
  B) Map ↔ code re-verification (delta since SYS-MAP-003)
  C) Finding register + ranked next cuts (no implement)
        │
        ▼
Engineer + Cursor: decide FN vs design-only vs map-only fix
```

---

## 1. Intent

Produce an **evidence-first audit** that answers:

1. **Why** did `reducir payload` not reach C-040 while DEFINE_MISSING was open on battery?  
2. Is that **by design** (documented), a **map mismatch**, a **missing edge**, or a **bug**?  
3. What does the System Map currently claim about this path — and is that claim true in code?  
4. What else drifted in the map since Catalog Bind / F-1 / G5 / G3?  
5. What should the Engineer authorize **next** (map doc fix only / new FN / design note) — ranked, without implementing.

---

## 2. Source-of-truth order (mandatory)

```text
1. Code
2. Tests
3. Runtime / CLI evidence (transcript above + optional replay)
4. Architecture / system_map documentation
5. Continuity / JES contracts / prior reviews
```

If map and code disagree → fix map **or** add `MISMATCHES.md` entry.  
**Never** “fix” product code to match a wrong map in this cut.

---

## 3. Out of scope (hard)

| Forbidden now |
|---|
| Implementing a DEFINE_MISSING preempt / engineering-intent escape |
| Changing orchestrator checkpoint order |
| G3 CLI “fix”, G6, G7, G1/H5, Catalog Impl C, BOM |
| Conversation Engine / Step D / dual-dispatch unification |
| Large opportunistic cleanup |
| Flipping C-xxx 🟢→🔴 (or reverse) **without** citing code + proposing the row text |
| Inventing new architectural subsystems |
| Weakening tests |
| Commit / push unless Engineer asks |

**Allowed doc-only edits (optional, prefer report-first):**

- Correct stale claims in `docs/system_map/**` when code proof is clear  
- Add `MISMATCHES.md` **M-xxx** entries  
- Add a **Suspected missing edge** row in `CONNECTIONS.md` (flagged, not fabricated as 🟢)  
- Update finding register `.jes/artifacts/cli_findings_post_catalog_bind_v1.md` with a new ID (e.g. **G8**)

If unsure whether a map edit is interpretive vs factual → **report only**, leave map untouched.

---

## 4. Part A — Focused routing diagnosis (primary)

### 4.1 Reproduce the authority chain in code

Trace `handle_user_text` / `_handle_user_text_inner` for input `"reducir payload"` when:

```text
session.mode == DEFINE_MISSING_PARAMETERS
param_definition_reason / pending_missing_reason == MISSING_COMPONENT_DEFINITION
pending_missing_params includes "battery" (or next arch block)
project has active state + motors catalog_ref bound
```

Deliver a **turn path table**:

| Step | Checkpoint # (RUNTIME_MAP) | Branch taken | Why not C-040 |
|---|---|---|---|

Cite file + symbol (+ line numbers preferred).

### 4.2 Compare to adjacent preempt patterns

| Mode | Soft-interrupt / preempt today | Engineering goal reachability |
|---|---|---|
| IDLE | C-040 gate | ? |
| ITERATE_INTERACTIVE | C-052 calibration preempt | ? |
| DEFINE_MISSING | simulate/calculate/project_status/FN-013/015/016… | ? for `is_engineering_intention` |
| SYSTEM_DEFINITION | ? | ? |

Answer explicitly:

> Does DEFINE_MISSING have an analogue of C-052 for `is_engineering_intention` / `explore_design_space`?  
> If no: is that absence documented in the map?

### 4.3 FN-021 boundary check

Prove from code + `test_fn021_session_hygiene.py` what FN-021 clears:

```text
_clear when _next_pending_block() is None  (arch complete)
vs
_chain to next block when pending is not None  (mid-arch — C-037)
```

State whether the CLI failure is:

| Classification | Meaning |
|---|---|
| **A — Designed sticky** | Mid-arch wizard intentionally owns the turn; map should say so; product may still want a future FN |
| **B — Map overclaim** | C-040/ACQUISITION claim global reachability; code is mode-gated |
| **C — Bug** | Code violates an explicit written invariant (cite the invariant) |
| **D — Mixed** | Split: sticky-by-design + dishonest Continuity next-step, etc. |

Pick one primary label; allow secondary labels with evidence.

### 4.4 Mandatory probes (code or tiny scripts / tests — no product change)

| # | Probe | Pass criterion for *understanding* |
|---|---|---|
| P1 | `is_engineering_intention("reducir payload")` | Returns `reducir_payload` (F-1) |
| P2 | `resolve_intent("reducir payload")` | Record actual intent string |
| P3 | Orchestrator with forced DEFINE_MISSING+battery session + `"reducir payload"` | Observe action/message — expect battery prompt today |
| P4 | Same session + `"cancelar"` then `"reducir payload"` | Expect Goal Plan after IDLE |
| P5 | Same session + `"simula"` | Soft-interrupt still works |
| P6 | Same session + `"explora opciones"` / `"optimiza payload"` | Record whether swallowed (relevant to G3 probe blockage) |
| P7 | After motors catalog bind + propellers declared, call Continuity / project_status | Does next-step still claim “no motor in catalog”? |

Use existing test harnesses / RefuseLLM patterns where possible. Do **not** land new permanent product tests unless they are **audit-only** files under `tests/` that the Engineer may later promote — prefer reporting probe results inside the audit artifact. If you add a temporary test file, say so clearly and keep it diagnostic.

### 4.5 Secondary: Continuity vs catalog honesty

Separate finding if confirmed:

```text
State: motors.catalog_ref set
Continuity text: "no tengo un motor en el catálogo…"
```

Trace `project_continuity` / next_useful_step authority. Relate to C-080 / C-081 / catalog bind — **do not** fold into the sticky-wizard root cause without shared symbols.

---

## 5. Part B — Map ↔ code re-verification (delta since SYS-MAP-003)

SYS-MAP-003 confirmed the tree as of ~2026-08-10. Since then: Catalog A/B, F-1, G5, G3 (and possibly uncommitted map drift).

### 5.1 Counts & registry

| # | Check |
|---|---|
| B1 | Canonical unique `C-xxx` count in `CONNECTIONS.md` vs README/DIAGRAMS/canvas claims |
| B2 | Status rollup 🟢/🔴/🟡 — especially C-081 still 🟡? Any silent flips? |
| B3 | Forbidden transitions list still accurate |
| B4 | `RUNTIME_MAP.md` 25-checkpoint table vs current `_handle_user_text_inner` — **re-derive if drifted** (new checkpoints from catalog/G3/F-1?) |

### 5.2 High-risk rows for this finding (must verify)

For each: `CONFIRMED` | `STALE` | `NEW MISMATCH` | `MISSING EDGE` | `NEEDS ENGINEER`

| ID | Why |
|---|---|
| C-014 | Mode branch — DEFINE_MISSING before IDLE gates |
| C-037 | Next-block chain vs IDLE clear (FN-021) |
| C-040 | Engineering intent — **reachability when mode ≠ IDLE** |
| C-041 / C-105 | Plan + handoff create |
| C-042 / C-106 | Explore bind (G3 may have changed consumer) |
| C-052 | Iterate preempt — contrast case |
| C-033–C-035 | DEFINE_MISSING soft paths (what *is* allowed mid-wizard) |
| C-080 / C-081 | Continuity next-step honesty post catalog bind |

### 5.3 Subsystem map claims to challenge

| File | Suspicious claim to verify |
|---|---|
| `03_acquisition/ACQUISITION_MAP.md` | “Known issues owned by this subsystem: **None**” |
| `04_engineering/ENGINEERING_MAP.md` | Implies C-040 available whenever intent says so |
| `09_state/STATE_MAP.md` | engineering_intent / explore are “single-turn from IDLE” — is DEFINE_MISSING interaction documented? |
| `AUTHORITY.md` | Goal authority vs acquisition authority precedence mid-wizard |
| `FLOWS.md` FLOW-002 | Does any flow show engineering intent **during** open acquisition? |

### 5.4 New modules since SYS-MAP-003 (inventory only)

Confirm whether map mentions (or needs a note for):

| Module | Context |
|---|---|
| `core/component_sync.py` | G5 |
| `core/explore_continuity.py` | G3 |
| Catalog bind / invalidation helpers | Impl B |
| Any new C-xxx that should exist but don’t | report as suspected missing edges |

Do **not** invent a full Catalog connection registry in this cut unless evidence forces a `CONNECTIONS.md` suspected-edge note.

---

## 6. Deliverables (required)

Write under `.jes/artifacts/`:

### 6.1 Primary report (mandatory)

**Path:** `.jes/artifacts/sys_map_004_routing_audit.md`

Must include:

1. **Executive verdict** (≤10 lines) — primary classification A/B/C/D from §4.3  
2. **CLI finding reconstruction** — turn path table (§4.1)  
3. **Map vs code** — table for §5.2 rows  
4. **Secondary Continuity/catalog finding** — separate subsection  
5. **Drift since SYS-MAP-003** — checkpoint table drift, new modules, count mismatches  
6. **Recommended next cuts** (ranked, no implementation):

```text
R1 — map-only doc correction (if any)
R2 — new Finding ID (G8/…) for sticky mid-arch engineering intent
R3 — Design note needed? (preempt policy: when may acquisition yield?)
R4 — Implementation Contract candidate (only if Engineer should authorize a FN)
R5 — What NOT to do next (especially: do not conflate with G3/G6/G7/Impl C)
```

7. **G3 probe implication** — one short paragraph: can G3 CLI proceed with workaround (`cancelar`) only, or is a routing FN a prerequisite?

### 6.2 Optional companion artifacts

| Path | When |
|---|---|
| `.jes/artifacts/sys_map_004_verification_matrix.md` | If Part B is large |
| `docs/system_map/MISMATCHES.md` M-xxx | Only with clear code proof |
| `.jes/artifacts/cli_findings_post_catalog_bind_v1.md` | Add G8 (or chosen ID) — registered, no implement |

### 6.3 Explicit non-deliverables

- No Implementation Contract for a preempt FN (that is a **later** cut after Engineer accepts this audit)  
- No code fix  
- No checkpoint tag

---

## 7. Pass criteria (for Cursor review)

| # | Criterion |
|---|---|
| 1 | Root path of `"reducir payload"` under DEFINE_MISSING+battery explained with code citations |
| 2 | Primary classification A/B/C/D chosen with evidence |
| 3 | C-040 reachability clarified: IDLE-only vs global |
| 4 | FN-021 scope vs mid-arch chain distinguished |
| 5 | Continuity “no motor” symptom separated or proven same-root |
| 6 | Map drift since SYS-MAP-003 listed (even if “none”) |
| 7 | Ranked next cuts; **zero** silent product code changes |
| 8 | G3 probe guidance clear (workaround vs blocker) |

**Review grades:** PASS / PASS WITH NOTES / FAIL.

---

## 8. Suggested Claude working order

```text
1. Read this contract fully
2. Read RUNTIME_MAP nested DEFINE_MISSING + C-014/C-037/C-040/C-052 in CONNECTIONS.md
3. Read audit_2026-08-10_engineering_intent_vs_sticky_session.md (context only)
4. Trace orchestrator code for DEFINE_MISSING branch vs C-040 gate
5. Run probes P1–P7
6. Diff map claims vs code for §5.2 / §5.3
7. Write sys_map_004_routing_audit.md
8. Optionally register G8 in cli_findings + M-xxx if proven
9. STOP — do not implement a fix
```

---

## 9. Engineer framing (normative product stance — for evaluation only)

Treat as **preferences to stress-test**, not as approved design:

1. Mid-architecture acquisition may guide the user — but a **clear engineering goal phrase** (`reducir payload`, `aumentar autonomía`, …) should not be silently reinterpreted as a battery description.  
2. Prefer **reusing** patterns (C-052 preempt, FN-016 cancel, Bug 56 soft-interrupt) over a new Conversation Engine.  
3. Map must not mark C-040 🟢 in a way that implies the Goal Plan is reachable from every mode if code disagrees.  
4. Do **not** propose pausing all acquisition until architecture is complete — acquisition chaining (C-037) is valuable; the question is **preemption policy**, not deleting the wizard.

Challenge these preferences if code/tests show a better framing.

---

## 10. Handoff back to Engineer

When finished, Claude’s closing message should contain:

```text
VERDICT: <A|B|C|D + one sentence>
REPORT: .jes/artifacts/sys_map_004_routing_audit.md
G3 PROBE: <workaround OK | blocked until FN>
NEXT: <top recommended cut only>
CODE CHANGES: none (or list doc-only files if any)
```
