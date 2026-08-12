# Implementation Contract — SYS-MAP-003

**Project:** Jarvis  
**Date:** 2026-08-10  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)  

**Status:** READY FOR ENGINEER → send to Claude  

**Type:** Dual audit — (A) **System Map re-verification** against code · (B) **Code hygiene** (dead/residual/duplication).  
**Product behavior:** **Zero intentional changes.** No FN on C-042 / C-025 / C-044 / C-043 / C-081. No Create→BOM. No Conversation Engine / Step D. No orchestrator dual-dispatch refactor.

**Depends on:** SYS-MAP-002 tree (`docs/system_map/**`) · FN-014…023 on `main` · count audit (57 canonical)  

**Related:**  
- `.jes/artifacts/implementation_review_sys_map_002.md` (PASS WITH NOTES)  
- `.jes/artifacts/sys_map_002_count_audit.md` (57 ≠ 65)  
- Living map: `docs/system_map/README.md`  

**Workflow:** Claude audits → writes reports under `.jes/artifacts/` → Engineer forwards → Cursor reviews. **No commit/push unless Engineer asks.**

---

## 0. Why this cut

The Engineer wants confidence that the System Map is **correct as-is**, not merely complete as prose. Separately, before any handoff FN, we want a **hygiene picture** of residual / dead / duplicated code so future FNs do not build on rot.

```text
SYS-MAP-002 published (57 C-xxx)
        │
        ▼
SYS-MAP-003  ← you are here
  A) Map ↔ code verification
  B) Hygiene inventory (report-only)
        │
        ▼
Engineer: accept map + decide lifecycle + first RED C-xxx
        │
        ▼
FN handoff contract (later) → Create→BOM (later)
```

---

## 1. Intent

### Part A — Map re-verification

Re-read **code + tests + map** and produce a verification report that either:

- **Confirms** each critical claim in the map, or  
- **Corrects** the map (doc-only) when the map is wrong, or  
- Records a new **M-xxx DOCUMENTATION MISMATCH** when docs and code disagree and the resolution is not obvious.

Canonical count remains:

```text
57 unique C-xxx (Canonical registry in CONNECTIONS.md)
52 🟢 · 4 🔴 · 1 🟡
+ 8 Forbidden transitions (not C-xxx)
```

Do **not** revive “65 connections” as a registry total.

### Part B — Code hygiene audit

Inventory under `src/jarvis/` (and tests only as evidence of deadness):

- Dead / unreachable code  
- Residual leftovers from closed FNs/bugs (commented blocks, abandoned helpers, stale flags)  
- Duplications / near-duplications of non-trivial logic  
- Redundant abstractions (two paths that always do the same thing)  
- Obvious “orphan” modules or symbols with no callers  

**Part B is report-first.** Do not delete or refactor product code in this cut unless §6 allows a tiny safe doc-only or comment-only fix. Propose ranked cleanup candidates for a **future** hygiene FN if warranted.

---

## 2. Source-of-truth order (mandatory)

```text
1. Code
2. Tests
3. Runtime / CLI evidence (re-run probes where needed)
4. Architecture / system_map documentation
5. Continuity / JES contracts / prior reviews
```

If map and code disagree → fix map **or** add `MISMATCHES.md` entry. Never “fix” code to match a wrong map in this cut.

---

## 3. Out of scope (hard)

| Forbidden now |
|---|
| Implementing H1–H5 or repairing C-042 / C-025 / C-044 / C-043 / C-081 |
| Adding handoff-context / `last_engineering_goal` / new session fields |
| Create→BOM, Conversation Engine, Step D |
| Dual-dispatch unification refactor |
| Large opportunistic cleanup (“while I’m here”) |
| Weakening RED/YELLOW findings to make the map look healthier |
| Renumbering / collapsing C-xxx IDs |
| Changing product behavior to “make hygiene green” |
| Commit / push unless Engineer asks |

---

## 4. Part A — Map verification checklist

Claude must verify **against code** (cite file + symbol; line numbers preferred). For each item: `CONFIRMED` | `FIXED IN MAP` | `NEW MISMATCH` | `NEEDS ENGINEER`.

### 4.1 Registry & counts

| # | Check |
|---|---|
| A1 | Canonical registry in `CONNECTIONS.md` has **exactly 57** unique `C-xxx` |
| A2 | Status rollup is **52 🟢 / 4 🔴 / 1 🟡** (C-025, C-042, C-043, C-044 broken; C-081 partial) |
| A3 | Forbidden list is **8** and not counted as C-xxx |
| A4 | Derived tables that re-list IDs are labeled as derived (no false +8 connections) |
| A5 | `DIAGRAMS.md` + `jarvis-system-map.canvas.tsx` match the 57 IDs (no missing/extra vs canonical). If canvas drifts: update canvas **or** note drift in report — Canonical registry wins |

### 4.2 Headline RED / YELLOW (must re-probe or re-trace)

| # | ID | Required proof |
|---|---|---|
| A6 | **C-042** | Trace `"explora opciones"` after a goal plan: intent, `resolve_explore_goal` → `None`, `_handle_explore` → analyze/LLM. Confirm CTA still advertises that phrase |
| A7 | **C-025 / C-044** | Trace `"ayudame a mejorar la estabilidad"` (or ES equivalent): lands `analyze`; `is_engineering_intention` would detect goal if reached. Confirm single root, two IDs intentional |
| A8 | **C-043** | Trace plan lever (e.g. `incrementa safety_factor`) → iterate: lever not preseeded as `variable` |
| A9 | **C-081** | Confirm Continuity next-step stays generic on PASS+risky (weak, not falsely marked BROKEN) |

Re-run minimal CLI or orchestrator unit probes if cheaper than full CLI; record exact commands/assertions in the report.

### 4.3 Authority & routing

| # | Check |
|---|---|
| A10 | `ActionPolicy.ALLOWED_ACTIONS` still closed 4-verb set; LLM cannot choose acquisition/goal/DSE |
| A11 | Intent precedence in `AUTHORITY.md` matches `intent_resolver._resolve_strong_action_intent` order |
| A12 | FN-022 gate still only on `intent ∈ {iterate, unknown}` (explains C-025) |
| A13 | FN-023 guidance patterns still beat bare `ayúdame` for next-step phrasing (FLOW-006) without claiming to fix C-025 |

### 4.4 Structural claims

| # | Check |
|---|---|
| A14 | Checkpoint count in `01_runtime/RUNTIME_MAP.md` vs `_handle_user_text_inner` (expect ~25; update if wrong → M-001 style) |
| A15 | Dual-dispatch C-016 still accurate (`handle` vs `handle_user_text`) |
| A16 | Continuity / Acquisition shared next-gap read (C-036) still holds |
| A17 | Component write single point C-091 still holds (grep writers) |
| A18 | FLOW-001…007 still match code for happy paths; broken notes still accurate for 003/004 |

### 4.5 Design appendix (do not “decide”)

| # | Check |
|---|---|
| A19 | `MISMATCHES.md` H1–H5 still design-only; no accidental implementation recipe that mandates sticky goal without lifecycle |
| A20 | Open lifecycle questions still open — do not close them in this cut |

### 4.6 Allowed map edits (Part A only)

If verification finds errors:

- Edit `docs/system_map/**` (and stub redirect if needed)  
- Add/update `MISMATCHES.md` entries (`M-003+`)  
- Update `DIAGRAMS.md` / canvas if ID list or statuses wrong  
- **Do not** change `src/**` behavior to match a wrong map  

Report must list every file touched.

---

## 5. Part B — Hygiene audit checklist

Scope roots: `src/jarvis/` (primary). Optionally note test-only dead fixtures if clearly abandoned.

### 5.1 Categories (use these labels)

| Label | Meaning |
|---|---|
| **DEAD** | No callers / unreachable; safe candidate for future delete |
| **RESIDUAL** | Leftover from closed FN/bug; comment, flag, or path no longer used |
| **DUPLICATE** | Two+ implementations of the same non-trivial rule |
| **REDUNDANT** | Abstraction or branch that no longer earns its complexity |
| **SUSPECT** | Looks dead/duplicate but needs Engineer call (e.g. MCP-only entry) |

### 5.2 Method (minimum)

1. Inventory public modules under `src/jarvis/` and cross-check imports/callers (rg / AST as you prefer).  
2. Flag `# noqa`, large commented blocks, `TODO`/`FIXME`/`XXX` tied to closed bugs.  
3. Look for parallel classifiers / dual thresholds (historical FN-020 class) — confirm still unified or flag relapse.  
4. Compare `goal_planner` vs suggestion-engine / Continuity strings for duplicated “next step” logic (report only; H5 stays design).  
5. Note unused exports, unused Action verbs, dead IntentType branches if any.  

### 5.3 Hygiene deliverable shape

Each finding row:

| Field | Required |
|---|---|
| ID | `HYG-001`… |
| Label | DEAD / RESIDUAL / DUPLICATE / REDUNDANT / SUSPECT |
| Location | path + symbol |
| Evidence | why (no callers / identical logic / …) |
| Risk if wrong | e.g. “MCP entry looks unused but is public API” |
| Recommended next | leave / delete-in-future-FN / merge-later |
| Effort | S / M / L |

**Do not** implement cleanup in this cut except §6.

Rank top 10 by (confidence × value). Explicitly separate “cosmetic” from “blocks future handoff FNs”.

---

## 6. Allowed code / comment edits (narrow)

| Allowed | Not allowed |
|---|---|
| Docstring / comment corrections that remove **false** claims | Deleting modules or functions |
| Fixing typos in comments that cite wrong C-xxx / FN | Refactors for DRY |
| Map/doc fixes under Part A | Behavior, routing, schemas, session fields |

If Claude finds a one-line clearly dead private helper and is tempted to delete it: **list as HYG-*** only. Deletion needs a separate Engineer-approved hygiene FN.

---

## 7. Deliverables

| # | Artifact |
|---|---|
| 1 | `.jes/artifacts/implementation_report_sys_map_003.md` — executive summary + Part A results table + Part B top findings + files changed |
| 2 | `.jes/artifacts/sys_map_003_verification_matrix.md` — full A1–A20 (and any extra checks) with CONFIRMED/FIXED/MISMATCH/NEEDS ENGINEER + evidence pointers |
| 3 | `.jes/artifacts/sys_map_003_hygiene_inventory.md` — full HYG-xxx catalog (may be long) |
| 4 | Map/doc updates **only if** Part A required them (list in report) |
| 5 | Optional: 3–7 bullets in `docs/IMPLEMENTATION_TASKS.md` under a “SYS-MAP-003” note pointing at the reports — **no** unpausing FN-024 |

**No** Implementation Contract for H1/H2/H3/H4 from this report. Engineer picks RED after Cursor review.

---

## 8. Acceptance criteria (Cursor review)

PASS only if:

1. Part A matrix covers A1–A20 with evidence; headline RED/YELLOW re-confirmed or map corrected honestly.  
2. Canonical **57** preserved or explicitly corrected with Engineer-visible rationale (correction ≠ inventing edges).  
3. Part B inventory exists with HYG IDs, labels, evidence, ranked top 10.  
4. Zero product behavior changes in `src/` (diff empty or comments-only).  
5. No H1–H5 implementation; no new sticky handoff field.  
6. Report states residual risks and what remains for Engineer (lifecycle + first C-xxx).  

FAIL if:

- Silent map softening of RED edges  
- Hygiene “cleanup” that changes runtime behavior  
- Claims “65 connections” as canonical  
- Skips re-proof of C-042 / C-025 / C-043  

---

## 9. Implementation Report template (Claude fills)

```markdown
# Implementation Report — SYS-MAP-003

## Verdict (self)
PASS candidate | PASS WITH NOTES candidate | Issues found

## Part A — Map verification
- Counts: 57 / 52 / 4 / 1 / +8 — confirmed?
- Headline edges: C-042, C-025/044, C-043, C-081
- Matrix: link to sys_map_003_verification_matrix.md
- Map files changed: …

## Part B — Hygiene
- Findings count by label
- Top 10: …
- Full inventory: link to sys_map_003_hygiene_inventory.md
- Blocks future handoff FNs? yes/no + which

## Explicitly unchanged
- No FN on RED edges
- No Create→BOM
- No src behavior change

## Risks / open for Engineer
- Lifecycle still open
- First RED still open
- Hygiene follow-up FN recommended? …
```

---

## 10. Prompt to paste into Claude Code

> Execute Implementation Contract **SYS-MAP-003** (`.jes/artifacts/implementation_contract_sys_map_003.md`).
>
> **Part A:** Re-verify `docs/system_map/**` against current `src/jarvis/` code and tests. Confirm canonical **57** connections (52🟢 / 4🔴 / 1🟡 + 8 forbidden). Re-prove C-042, C-025/C-044, C-043, C-081 with evidence. Fix the **map** if wrong; do not change product behavior. Do not implement H1–H5.
>
> **Part B:** Audit `src/jarvis/` for dead/residual/duplicate/redundant code. Report-only (`HYG-xxx`); no cleanup refactors.
>
> Deliver the three artifacts under `.jes/artifacts/` named in §7. No commit/push unless asked. When done, return the Implementation Report for Cursor review.

---

## 11. After this cut (Engineer — not Claude)

1. Cursor Implementation Review of SYS-MAP-003.  
2. If map PASS: treat System Map as verified authority.  
3. Decide handoff-context **lifecycle**.  
4. Pick first RED `C-xxx` → separate Implementation Contract.  
5. Optionally schedule a hygiene FN from ranked HYG list.
