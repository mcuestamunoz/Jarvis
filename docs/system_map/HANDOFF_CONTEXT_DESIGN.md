# Handoff Context — Architectural Design

**Status:** DESIGN ACCEPTED — §5 lifecycle **CLOSED** (Engineer 2026-08-10)  
**Date:** 2026-08-10  
**Author:** JES / Cursor (Engineer Interface)  
**Authority:** Engineer checkpoint post SYS-MAP-002  

**Derived exclusively from:**  
- `CONNECTIONS.md` — **C-042**, **C-043**, **C-025** / **C-044** (and related C-040/C-041/C-045/C-046)  
- Precedents: `session.last_exploration_result` (C-046), FN-021 session hygiene (C-037)  
- `MISMATCHES.md` design appendix (H1–H5)  
- Engineer decision: do **not** patch RED edges as three independent FNs before this contract  

**Explicitly not this document:** Full product implementation · sticky `last_engineering_goal` · Create→BOM · Continuity data shape for C-081 (H5 remains separate)

**First Implementation Contract:** `.jes/artifacts/implementation_contract_fn024_h1_h2_handoff_dse.md` (C-042 / H1+H2)

---

## 0. Checkpoint decision (Engineer)

```text
FN-014…023     ✅ closed
System Map     ✅ living authority (59 unique C-xxx · 58🟢 / 0🔴 / 1🟡)
Handoff §5     ✅ CLOSED — Hybrid Operation-Scoped Context (below)
FN-024 H1+H2   ✅ C-042 (+ CTA honesty)
FN-025 H3      ✅ C-025 / C-044
FN-026 H4      ✅ C-043
Create→BOM     ⏸️ paused
H5 / C-081     ⏸️ deferred (own Continuity data contract later)

Next (Engineer decision — not an automatic FN):
  H5 / C-081 design  vs  Create→BOM
```

**Process rule:**

```text
CLI fails → System Map → C-xxx → Authority → Handoff contract → Implementation Contract → code → tests/CLI → update System Map
```

---

## Decision log — §5 CLOSED (2026-08-10)

### Policy name

**Hybrid Operation-Scoped Context**

> Handoff Context = **operation-scoped**, **runtime-only**, **capability-consumable**, **project-scoped**.  
> Created when a valid `goal_plan` is produced. Stays active for the engineering operation. Consumers (H1/H3/H4) consume **specific capabilities**, not the whole object. DSE may consume its capability without destroying `goal_key` / levers needed for Iterate. Levers may be marked consumed/reconciled individually. Full invalidation only on project switch, explicit cancel, incompatible/new plan, or operation end/incompatibility. **Not** persisted to disk. **Not** general conversational memory. **Not** a global `last_engineering_goal`.

### Create

After a successful `engineering_intent` that produces a `goal_plan` (C-040/C-041).  
Authority: `goal_planner` / orchestrator plan path only.

**Do not create** from bare analyze, arbitrary user text, isolated explore without plan, or LLM.

### Remain active

While a **coherent engineering operation** continues (multi-turn). **Not** one-turn-only (rejects pure L1).

Example spanning one operation:  
`aumentar empuje` → plan → `explora opciones` → DSE → apply → `incrementa safety_factor` → iterate.

### Consume = capability, not whole context

```text
Context
├── goal_key
├── plan / levers[]     (statuses ACTIVE | CONSUMED | RECONCILED)
├── DSE capability      ACTIVE → CONSUMED after successful DSE bind/run
└── Iterate capability  ACTIVE (FN-026 / H4 may preseed; do not wipe on DSE)
```

After `"explora opciones"` → DSE: mark **DSE capability CONSUMED**; keep `goal_key` + levers for Iterate (C-043 / H4 — implemented FN-026).

### Hard invalidation (whole context)

| Event | Action |
|---|---|
| Project switch / load | **Invalidate** (absolute boundary) |
| Explicit cancel / abandon operation | **Invalidate** |
| New `engineering_intent` → new plan | **Replace** |
| Operation completed / terminal | **Invalidate** |
| Context incompatible with current state | **Invalidate** |
| Simple turn advance | **Keep** |
| DSE executed | Consume **DSE capability** only |
| One lever applied | Mark that lever consumed/reconciled — not necessarily whole context |
| Simulation | **Keep** while operation active |
| Continuity / `project_status` | **Keep** — reading must not destroy context |

### After mutation

Prefer **RECONCILED** (lever marked used; operation may continue) over blanket INVALIDATED. If post-sim state makes the plan untenable, deterministic layers may invalidate/replace — not Continuity-by-side-effect of a status read.

### Storage

| Rule | Value |
|---|---|
| Tier | `InteractiveSessionState` only |
| Persist to `state.json` / snapshot | **No** (same family as `last_exploration_result`) |
| Project boundary | Always clear |

### Consumer map (order completed for H1–H4)

```text
Handoff Context
       ├── H1/H2 → Plan → DSE     (FN-024)  ✅ consume DSE capability
       ├── H3    → Help + Goal    (FN-025)  ✅ enter/continue operation via plan
       └── H4    → Plan → Iterate (FN-026)  ✅ preseed lever ∈ plan levers only
```

H5 / C-081 stays **out** of this policy — sole remaining non-green edge (🟡), design-only, deferred.
### Checklist (was §10) — now satisfied

- [x] Lifecycle policy chosen (hybrid operation-scoped)  
- [x] Consumer order H1+H2 → H3 → H4  
- [x] H5 deferred  
- [x] Naive sticky goal rejected  

---

## 1. Problem statement

Until FN-023, routing was framed as:

```text
Intent → corresponding layer
```

That is necessary but **insufficient**. The System Map shows a missing cross-layer piece:

```text
User
  ↓
Intent
  ↓
Engineering Intent (FN-022)
  ↓
Goal Plan (deterministic, stateless strategies)
  ↓
┌─────────────────┐
│ Handoff Context │  ← MISSING (conceptual + runtime)
└────────┬────────┘
         │
    ┌────┼────┐
    ↓    ↓    ↓
   DSE  Iterate  ( Continuity thread — later / H5 )
```

**Handoff Context** is the temporary answer to:

> “This user turn continues the operation we just started.”

Without it, each turn restarts too close to zero — even when the previous turn just showed a plan and CTAs that claim continuity.

### 1.1 Three REDs, one root

| Edge | Symptom | What continuity would supply |
|---|---|---|
| **C-042** Plan → DSE | `"explora opciones"` after a plan → explore without `goal_key` → analyze/LLM | Bound `goal_key` from the plan just shown |
| **C-025 / C-044** Help → Goal | `"ayúdame" + named goal` → analyze before FN-022 | Correct routing into engineering intent / plan (may *create* context, not only consume it) |
| **C-043** Plan → Iterate | Named plan lever → iterate asks “¿qué modificar?” | Trustworthy lever **∈ current plan’s lever list** |

These are **not** three independent bugs. They are three **consumers** (or entry paths) of the same continuity concept.

Therefore: **no FN-024 that only patches C-042** until Handoff Context is designed. Later FNs implement consumers of one contract.

---

## 2. What Handoff Context is (and is not)

### 2.1 Is

- **Conversational / operational continuity** between turns about an engineering intention that already produced a Goal Plan (or is about to).  
- **Runtime-tier** state (same family as `last_exploration_result`), not engineering truth in `ProjectState`.  
- **Authoritative for binding**, not for inventing goals: payload comes from deterministic `goal_planner` / plan already shown.  
- **Invalidatable** — must die when the conversation is no longer “about that operation.”

### 2.2 Is not

- A persistent “project priority” / engineering goal stored in `state.json` (that would be a **separate** future concept if ever needed).  
- An LLM-chosen next target.  
- A replacement for Continuity’s acquisition gap authority (`next_useful_step` / `_next_pending_block`).  
- A naive `last_engineering_goal: str` with no lifecycle (explicitly **rejected** — FN-021 class).

### 2.3 Separation of concerns

```text
Engineering meaning (optional future)
  e.g. "this project’s stated priority is stability"
  → ProjectState / explicit field / own lifecycle
  → NOT this document’s object

Handoff Context (this document)
  e.g. "we just showed a mejorar_estabilidad plan with these levers"
  → InteractiveSessionState (recommended) / cleared on project switch
  → temporary bridge Plan → DSE / Iterate / (maybe Continuity later)
```

---

## 3. Authority

| Decision | Authority | Forbidden |
|---|---|---|
| Whether a turn is “in” an engineering operation | Deterministic rules over Handoff Context + intent | LLM |
| `goal_key` / levers in context | `goal_planner` output from a plan that was **shown** (or equivalent deterministic detection that would have shown a plan) | Free-text invent / LLM |
| When context is created | Orchestrator after successful engineering-intent → plan path (C-040/C-041); possibly also after H3 routes help+goal into that path | Ad-hoc sets in DSE/Iterate |
| When context is cleared | Explicit invalidation matrix (§5–§6) — same discipline as FN-021 | “Forget to clear on one path” |
| DSE grid / explore configs | `DesignExplorer` given bound `goal_key` | LLM / context inventing grids |
| Iterate variable preseed | Lever ∈ context.plan levers only (H4) | Generic NLP guess of variable names |
| Acquisition next gap | Continuity / Acquisition (unchanged) | Handoff Context must not usurp |

**LLM role:** unchanged — narrate / bounded interpret. Must not create, extend, or choose Handoff Context.

---

## 4. Sketch payload (non-normative)

Fields below are a **design sketch** for discussion. They are **not** an approved schema and must not be copied into code as-is.

```text
HandoffContext  (sketch)

  origin          # e.g. engineering_intent | help_plus_goal  (how we entered)
  goal_key        # e.g. mejorar_estabilidad  (from goal_planner)
  # plan snapshot — enough for consumers, not a second planner:
  levers[]        # lever ids from GOAL_STRATEGIES[goal_key] as shown
  # optional: strategy indices / CTA mode for H2 honesty

  created_turn    # monotonic turn id or timestamp in-session
  status          # active | consumed | disposed

  # lifecycle policy (chosen in §5 — not hardcoded here):
  #   consumption_mode: one_shot_dse | persistent_within_operation | …
```

**Minimum useful payload for the three REDs:**

| Consumer | Needs at least |
|---|---|
| DSE (C-042) | `goal_key` while status=active |
| Iterate (C-043) | `goal_key` + `levers[]` to validate preseed |
| Help+goal (C-025) | Mostly **routing** into plan path; may **create** context after plan — not a separate store of “help” |

Do not add fields that encode Continuity gaps or BOM — wrong authority.

---

## 5. Lifecycle — CLOSED

See **Decision log — §5 CLOSED** at the top of this file.

Historical candidate table (L1–L6) is superseded by **Hybrid Operation-Scoped Context**. Do not reopen L1–L5 as equals; cite the Decision log in Implementation Contracts.

### 5.2 Storage — decided

| Choice | Decision |
|---|---|
| Runtime vs disk | **Runtime-only** (`InteractiveSessionState`) |
| Snapshot / `state.json` | **Exclude** (never restore a zombie handoff) |
| Project switch | **Always invalidate** |

### 5.3 Invalidation matrix — normative for implementers

| Event | Whole context | Capability / lever |
|---|---|---|
| Project load / switch | **Invalidate** | — |
| Explicit cancel / abandon | **Invalidate** | — |
| New engineering_intent → new plan | **Replace** | — |
| Operation terminal / incompatible | **Invalidate** | — |
| Turn advance / Continuity / status | **Keep** | — |
| Simulation | **Keep** | — |
| Successful DSE for bound goal | **Keep** | DSE capability → **CONSUMED** |
| Apply exploration | **Keep** (default) | (DSE already consumed) |
| Iterate applies one lever (H4+) | **Keep** / reconcile | That lever → consumed/reconciled |
| Component acquisition write | **Keep** unless operation declared incompatible | — |

Every FN that touches Handoff Context must **prove** each row (FN-021 style): clear, consume, or justify inert.

---

## 6. Precedents to mirror (not copy blindly)

### 6.1 `last_exploration_result` (C-046)

- Set when DSE produces a result.  
- Consumed by an **explicit** later user action (apply).  
- Runtime session field; documented as not the long-term engineering store.  
- **Lesson:** handoff-shaped state already exists; new context should feel like a sibling, not a parallel sticky string.

### 6.2 FN-021 / C-037

- Wizard mode left sticky when “nothing left to acquire.”  
- Fix: clear to IDLE with proven untouched paths.  
- **Lesson:** any “last thing we were talking about” field is a liability until every stale path clears or is proven safe.

Handoff Context **inherits this lesson**. Implementation without an invalidation matrix is rejected by design.

---

## 7. Consumers → future FNs (shape only)

Do **not** schedule three unrelated patches:

```text
❌ FN-024 patch C-042
❌ FN-025 patch C-025
❌ FN-026 patch C-043
```

Prefer:

```text
                 HANDOFF CONTEXT (design accepted + lifecycle chosen)
                            │
           ┌────────────────┼────────────────┐
           ↓                ↓                ↓
        H1+H2             H3               H4
        C-042             C-025/C-044      C-043
        Plan→DSE + CTA    Help→Goal        Plan→Iterate
```

| Future cut | Closes | Depends on |
|---|---|---|
| **H1 + H2** | C-042 + CTA honesty (M-002) | Context create + DSE bind + invalidation matrix |
| **H3** | C-025 / C-044 | Intent precedence vs analyze; may create context via plan path |
| **H4** | C-043 | Context levers[] membership check for preseed |
| **H5** | C-081 | **Separate** Continuity data contract — not blocked on Handoff Context, not first |

Order **proposed** (Engineer may reorder): design accept → H1+H2 → H3 → H4 → H5 → Create→BOM.

Each Implementation Contract must:

1. Cite `C-xxx` repaired  
2. Cite this design doc + chosen lifecycle ID (L*)  
3. Update `CONNECTIONS.md` status  
4. Show invalidation matrix proof  

---

## 8. Relationship to C-025 (help + goal)

C-025 is partly an **intent-precedence** bug (ANALYZE before engineering gate), not only missing session state.

Handoff Context still matters because:

- After help+goal correctly reaches a plan, the **same** context should enable C-042/C-043.  
- Fixing only regex order without context leaves Plan→DSE/Iterate broken.

So H3 may ship as “route into FN-022 path” **plus** “create context when plan is shown” — not as a third ad-hoc sticky field.

---

## 9. Forbidden in any follow-on implementation

- `last_engineering_goal` (or rename) without §5 policy + §5.3 matrix  
- Persisting handoff as project engineering truth  
- LLM writing context fields  
- Context choosing acquisition targets or Continuity gaps  
- Preseed iterate variables from free text not ∈ plan levers  
- Softening RED rows in the map to avoid this design  
- Implementing Create→BOM as a substitute for handoff continuity  

---

## 10. Acceptance of this design doc (Engineer)

**Accepted 2026-08-10** with Hybrid Operation-Scoped Context (§ Decision log).

Implementation Contracts may now cite this document + Decision log. First cut: **FN-024 / H1+H2 / C-042**.

Optional parallel: SYS-MAP-003 verification/hygiene — does not block FN-024.

---

## 11. Pointers

| Doc | Role |
|---|---|
| [`CONNECTIONS.md`](CONNECTIONS.md) | C-042 / C-043 / C-025 / C-044 evidence |
| [`AUTHORITY.md`](AUTHORITY.md) | Intent precedence; LLM bounds |
| [`MISMATCHES.md`](MISMATCHES.md) | H1–H5; FN-021 lesson |
| [`FLOWS.md`](FLOWS.md) | FLOW-002 → 003 / 004 broken journeys |
| [`DIAGRAMS.md`](DIAGRAMS.md) | Visual rollup |

When §5 is decided, append a short **Decision log** section here (date + chosen L* + invalidation summary) — then open the first Implementation Contract citing that decision.

**Done:** Decision log at top; FN-024 contract issued.
