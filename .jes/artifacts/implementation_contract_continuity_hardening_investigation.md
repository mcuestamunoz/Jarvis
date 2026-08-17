# Implementation Contract — Continuity Hardening  
# Investigation + Design (System-Map–first)

**Project:** Jarvis  
**Date:** 2026-08-15  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)  

**Status:** READY FOR ENGINEER → send to Claude  

**Type:** **Investigation + Design only.** Zero intentional product `src/` / `library/` changes. No FN. No Conversation Engine. No dual-dispatch refactor. No Impl C. No G10 materials patch. No G9 Continuity honesty fix. No G13 opaque-slug fix in this cut.

**Checkpoint base:** tag **`checkpoint-g3`**  

**Working tree note:** G10 materials code may be present (uncommitted or committed). Treat current tree as ground truth for probes. **Do not** modify G10 materials modules to “help” Continuity — document interactions only.

**Findings register:** `.jes/artifacts/cli_findings_post_catalog_bind_v1.md`  
**Roadmap:** `docs/IMPLEMENTATION_TASKS.md` — Continuity Hardening ← AHORA; G10 PVC / `checkpoint-g10` deferred.

**Bundle in scope (must map to connections):**

| ID | One-line |
|---|---|
| **G14** 🔴 | Motors wizard + `1x 2306…` → “Hélices registradas” |
| **G15** | Catalog help incoherent + mid-wizard list-motors rejected |
| **G12** | DEFINE_MISSING sticky: `definir <otro>` → same wizard / wrong body |
| **G8** | DEFINE_MISSING swallows engineering/explore (SYS-MAP-004) |
| **G11** | Iterate preempt C-052 absorbs wizard answers / material→frame |
| **G7** | Related iterate fragility — cite only if shared symbols with G11 |

**Explicitly deferred (document boundary only):** G10 PVC acquisition CLI · G13 · G9 isolate · Impl C · H5/C-081 · Conversation Engine.

**Workflow:** Claude investigates (System Map + code + CLI evidence) → writes artifacts → Engineer locks ★ on design → **later** Implementation Contract for Continuity code.  
**No commit/push unless Engineer asks.**

---

## 0. Why this cut (read carefully)

G10 implementation closed materials identity for frame acquisition (`plastico 390g` CLI PASS). Further G10 micro-probes (PVC acquisition, G13) **cannot be validated cleanly** because session continuity collapses on a fresh project before the user reaches a stable frame wizard.

Engineer lock (2026-08-15):

> Restore Continuity first. Micro-details after the BOM walk works again.

### Smoking-gun CLI (proyecto nuevo `prueba`, 2026-08-15)

```text
Architecture A → DEFINE_MISSING thrust
User > ayúdame a elegir
→ "No tengo motor ≥ 37.7 N"  AND  "máximo catálogo ~55 N"   ← G15 incoherent

User > que motores tenemos en el catalogo
→ Error: no reconozco como valor …                         ← G15 absorb

User > 15   → accepted under-req; sim FAIL; arch still 0/4

User > definir propulsion → motors brief
User > 1x 2306 2400KV 50W
→ "Hélices registradas. Describe los motores…"             ← G14 CRITICAL
```

Prior sessions (same register): G12 sticky retarget; G8 engineering swallow; G11 iterate preempt loops. Engineer hypothesis:

> **These are not unrelated UX nits — they are connection / authority failures** between Runtime mode, Acquisition target, component intercept, Intent, and Iterate preempt. The System Map already claims to model those edges; Continuity breakage is where map claims and runtime authority disagree or underspecify.

```text
checkpoint-g3 ✅
G10 impl (+ plastico CLI) ✅ · PVC deferred
        │
        ▼
Continuity Hardening INVESTIGATION + DESIGN  ← you are here
        │
        ▼
Engineer ★ lock → Continuity Implementation Contract (later)
        │
        ▼
restore: n → propulsion → battery → frame without cancelar loops
        │
        ▼
resume G10 PVC / checkpoint-g10 · G13 · R3 remainder · …
```

---

## 1. Intent

Produce an **evidence-first** package that answers:

1. **Connection map of the Continuity failures** — for each of G14/G15/G12/G8/G11, which `C-xxx` edges fire (or fail to fire), in what order, with what authority owner.  
2. **Single vs multiple roots** — is there one Acquisition Target Authority gap (active gap vs inference/force vs Continuity next-block) with multiple faces, or several independent bugs?  
3. **Where the System Map is right, incomplete, or overclaiming** after Catalog Bind / F-1 / G5 / G3 / G10 — update proposals for `MISMATCHES.md` / connection caveats (doc-only recommendations; do not edit map unless Engineer later asks).  
4. **Design options** for a **minimal Continuity Hardening** cut that restores:
   ```text
   new project → A → declare motors as motors → propellers → battery → frame
   ```
   without requiring `cancelar` as normal procedure — **without** inventing a Conversation Engine.  
5. A **Design note** ready for Engineer ★ lock (recommended option + rejected alternatives + phased slices if the bundle is too large for one FN).

---

## 2. Source-of-truth order (mandatory)

```text
1. System Map (connections + subsystem maps + flows)   ← START HERE
2. Code (orchestrator turn order, acquisition, inference)
3. Tests (FN-011…021, propulsion composite, iterate preempt)
4. Runtime / CLI evidence (transcripts in findings register)
5. Prior audits (SYS-MAP-004, sticky engineering audit)
6. Findings / IMPLEMENTATION_TASKS narrative
```

If map and code disagree → **record as mismatch candidate**; do **not** change product code in this cut to make the map true.

---

## 3. HARD REQUIREMENT — Use the System Map

Claude **must** treat `docs/system_map/` as the primary navigation tool for this investigation. Do **not** grep the orchestrator blindly first.

### 3.1 Mandatory reading order

| Step | Artifact | Why |
|---|---|---|
| 0 | `docs/system_map/README.md` | Navigation contract |
| 1 | `docs/system_map/JARVIS_SYSTEM_MAP.md` (or `docs/JARVIS_SYSTEM_MAP.md` entry) | Whole-system shape |
| 2 | `docs/system_map/FLOWS.md` — especially acquisition / architecture / iterate journeys | User journeys ↔ C-xxx |
| 3 | `docs/system_map/CONNECTIONS.md` — **Canonical registry** + Detail for every C-xxx touched | Authority edges |
| 4 | `docs/system_map/AUTHORITY.md` | Who may decide what |
| 5 | `docs/system_map/03_acquisition/ACQUISITION_MAP.md` | Target / brief / wizards / FN-019 |
| 6 | `docs/system_map/01_runtime/RUNTIME_MAP.md` | Mode branch / checkpoints |
| 7 | `docs/system_map/02_intent/INTENT_MAP.md` | Intent → handlers |
| 8 | `docs/system_map/05_iteration/ITERATION_MAP.md` | C-052 preempt |
| 9 | `docs/system_map/08_continuity/CONTINUITY_MAP.md` | Next-step vs acquisition (C-036) |
| 10 | `docs/system_map/MISMATCHES.md` | Prior sticky lessons (FN-021 era) |
| 11 | `.jes/artifacts/sys_map_004_routing_audit.md` + review | G8 / C-040 mode-gate already audited |

### 3.2 Connection IDs Claude must explicitly status

For each ID below, report: map claim → code path (file/symbol) → status vs Continuity findings (`OK` | `OVERCLAIM` | `UNDER SPEC` | `MISWIRE` | `NEEDS EDGE`).

| ID | Suspected relevance |
|---|---|
| **C-013** | Global component intercept (any mode) — steals turns / wrong key? |
| **C-014** | Mode-branch dispatch |
| **C-020** | IntentResolver |
| **C-031–C-034** | IDLE/DEFINE_MISSING acquisition open / reprompt / cancel |
| **C-036** | Continuity ↔ `_next_pending_block` shared read |
| **C-037** | Wizard completion → next block / IDLE (FN-021) |
| **C-038** | Acquisition brief |
| **C-040** | Engineering intent (G8 — already caveat’d) |
| **C-052** | Iterate calibration preempt (G11) |
| **C-030** / motor assist paths | G15 `ayúdame a elegir` / catalog messaging |
| Inference / writers edges | `infer_component` / `infer_component_for_key` / `infer_components` / component_writers (G14) |

Also check **Forbidden transitions** in `CONNECTIONS.md` — does Continuity Hardening require a new allowed edge, or enforcement of an existing forbidden one?

### 3.3 Deliverable from map work (required section in report)

A section titled **“System Map ↔ Continuity failures”** containing:

1. Sequence diagrams (mermaid OK) for:
   - G14 motors→hélices turn
   - G12 `definir frame` while battery session sticky
   - G8 `reducir payload` mid-DEFINE_MISSING (cite SYS-MAP-004; don’t re-litigate unless delta)
   - G11-A `cambiar material` preempt
   - G15 list-motors mid-thrust-wizard
2. Table: Finding → primary C-xxx → authority owner → proposed fix layer (Runtime / Acquisition / Intent / Iterate / Continuity display-only).  
3. List of **map doc fixes recommended** (caveats, known-issues bullets) vs **code fixes** — clearly separated.

---

## 4. Out of scope (hard)

| Forbidden now |
|---|
| Any product `src/` / `library/` / test edits that change behavior |
| Implementing preempt policy, force-key fixes, list-motors intent |
| Patching G10 `materials.py` / frame keywords / mutation SoT |
| Fixing G9 Continuity catalog_ref honesty |
| Fixing G13 opaque `PVC 400g` iterate parse |
| Catalog Impl C / battery-prop UX / BOM |
| Conversation Engine / Step D / dual-dispatch rewrite |
| Weakening or deleting tests |
| Commit / push unless Engineer asks |
| Editing System Map files in this cut (propose text in the report only) |

**Allowed:** read-only probes, temporary scratch notes under `.jes/artifacts/`, RefuseLLM / PreferLLM diagnostic harnesses that **do not** land product commits.

---

## 5. Part A — Investigation checklist

Claude must verify against **map then code** (file + symbol; line numbers preferred). Status per item: `CONFIRMED` | `REFINED` | `NEW FINDING` | `NEEDS ENGINEER`.

### 5.1 Acquisition Target Authority (root hypothesis)

| # | Check |
|---|---|
| A1 | What is the live “active acquisition target”? (`pending_missing_params`, `expected_keys`, `_next_pending_block`, Continuity next-step text) — one authority or many? |
| A2 | When Continuity says “Siguiente: frame” but session still serves battery brief (G12) — which writer failed to clear/retarget? Cite C-037 / FN-021 invariants. |
| A3 | `definir <component>` / `definir propulsion` while DEFINE_MISSING open — which C-xxx should retarget? Which actually runs? |
| A4 | Relationship to historical sticky audit: `.jes/artifacts/audit_2026-08-10_engineering_intent_vs_sticky_session.md` — what FN-021 fixed vs what remains. |

### 5.2 G14 — motors phrase → hélices

| # | Check |
|---|---|
| A5 | Trace `_handle_component_description` for `expected_keys` containing `motors` + input `1x 2306 2400KV 50W`. |
| A6 | Does `infer_components` / FN-019 **force-propellers** (`infer_component_for_key(..., "propellers")`) fire even when motors is the open gap? |
| A7 | Exact confirmation string path for `"Hélices registradas"` (`orchestrator.py` ~writers). |
| A8 | Propulsion composite wizard tests (`test_propulsion_composite_wizard_flow.py`, FN-011/013/017) — do they cover this phrase? Gap? |
| A9 | Did G10 force-frame pattern increase risk of symmetric force-propellers over-firing? (Interaction note only — do not blame G10 without evidence.) |

### 5.3 G15 — catalog help / list mid-wizard

| # | Check |
|---|---|
| A10 | `motor_catalog_assist` / `ayúdame a elegir` path — why “no motor ≥37.7” while max ~55? Filter chain (thrust, prop diameter, KV, motor_count). |
| A11 | Message composition: is the contradiction a copy bug or a true empty candidate set with misleading max? |
| A12 | Mid-wizard `"que motores tenemos…"` — Intent vs param `answer` absorb. Compare to G10 ★8 list-materials (IDLE path). What edge is missing for DEFINE_MISSING? |
| A13 | Accepting under-requirement thrust (`15` vs ≥37.7) — by design? Should Continuity Hardening include a gate or only messaging? |

### 5.4 G12 / G8 — DEFINE_MISSING absorb & sticky retarget

| # | Check |
|---|---|
| A14 | Confirm SYS-MAP-004 G8 mechanism still accurate post-G10 (checkpoint order: DEFINE_MISSING before C-040). |
| A15 | G12 vs G8: same UX-C intercept? Different retarget missing edge? Argue one design or two. |
| A16 | `cancelar` (C-034) — why is it the only reliable recovery? What state does it clear that `definir X` does not? |

### 5.5 G11 — Iterate preempt

| # | Check |
|---|---|
| A17 | `_should_preempt_iterate_wizard` + `_ITERATE_PREEMPT_INTENTS` — exact predicates. |
| A18 | G11-A: why do prompt example phrases classify as preemptable iterate? |
| A19 | G11-B: component intercept / frame keywords vs open iterate material slot — order vs C-052. |
| A20 | Map claim for C-052 — overclaim / underspec for “answer vs new intent”? |

### 5.6 Mandatory probes (diagnostic only)

| # | Probe | Intent |
|---|---|---|
| P1 | Reproduce G14 with RefuseLLM: motors expected_keys + `1x 2306 2400KV 50W` | Confirm bind key |
| P2 | Same session: motors expected + bare `10x4.5` | Contrast FN-019 propeller force |
| P3 | Battery DEFINE_MISSING open → `definir frame` | G12 sequence + session fields dump |
| P4 | After battery complete, before clear: dump `pending_*` vs Continuity next block | Sticky mismatch |
| P5 | Thrust DEFINE_MISSING: `ayúdame a elegir` with motor_count=1, prop 5", req ≥37.7 | Candidate filters |
| P6 | Same: list-motors phrasing mid-wizard | Absorb vs intent |
| P7 | Iterate material step: `cambiar material` / `pvc` | G11-A/B |
| P8 | IDLE: `qué materiales tenemos` (G10 ★8) vs DEFINE_MISSING list-motors | Authority contrast |

Report raw session field dumps and call traces in the investigation artifact.

---

## 6. Part B — Design (draft for Engineer ★ lock)

### 6.1 Engineer preferences (stress-test — not yet CLOSED)

1. **Active acquisition target wins** over opportunistic `infer_component` / force-* when a DEFINE_MISSING / component wizard is open for a specific key — unless user explicitly retargets.  
2. **Explicit `definir <X>`** while a wizard is open should either (a) retarget to X with honest clear of incompatible collected state, or (b) refuse with a one-line “cancelar primero” — never show “Seguimos con X” + body of Y.  
3. **Do not** port `_should_preempt_iterate_wizard` verbatim into DEFINE_MISSING (collected_params hazard — SYS-MAP-004). Design a policy that fits both wizards without a Conversation Engine.  
4. **Catalog help mid-wizard** must be honest (no “max 55 but none cover 37.7” without explaining filters) and should allow a deterministic list/query escape (mirror list-materials pattern narrowly for motors — or document why not).  
5. Prefer **phased implementation** if bundle is large: e.g. Slice 1 = G14 target authority; Slice 2 = G12/G8 retarget policy; Slice 3 = G15 help/list; Slice 4 = G11 iterate answer-vs-intent — but investigation must still map **all** connections first.  
6. **Do not** weaken G10 materials vocabulary to hide G11-B.  
7. Success criterion for the eventual impl cut: Engineer can walk a **new** project from create → frame declare **without** `cancelar` as a required ritual.

### 6.2 Options Claude must compare

At minimum evaluate:

| Option | Sketch |
|---|---|
| **O1 — Force-key respect only (G14-first)** | When `expected_keys` set, never force another key; bind to active gap |
| **O2 — Acquisition Target Authority helper** | Single function: resolve active target + retarget rules; all open/answer paths call it |
| **O3 — Preempt policy pack (R3-lite)** | DEFINE_MISSING + Iterate policies for engineering / definir-X / in-wizard answers |
| **O4 — Messaging-only** | Fix copy (G15) + “cancelar primero” hints; no retarget — argue why insufficient |
| **O5 — Map-only** | Doc caveats without code — argue why insufficient given G14 |

Recommend **one** primary option (+ optional phased slices). Reject others with one-line reasons.

### 6.3 Design must specify (for later Implementation Contract)

- Authority rule: active gap vs inference vs Continuity next-step.  
- Retarget rule for `definir <component>` mid-wizard.  
- G14 exact gate change (symbols).  
- G15: filter honesty + list escape yes/no.  
- G11: answer-vs-intent predicate sketch (no full R3 novel architecture unless required).  
- Test plan sketch (P1–P8 become regression tests).  
- Blast radius (files).  
- Explicit non-goals (G9, G10 patch, G13, Impl C, Conversation Engine).  
- Whether Continuity Hardening **absorbs** R3 or leaves a remainder.

### 6.4 System Map implications (required)

Answer:

> Which C-xxx statuses should change (🟢 caveat / 🟡 / new ID), and which Known issues bullets belong in ACQUISITION_MAP / RUNTIME_MAP / ITERATION_MAP after the eventual fix?

Doc edits are **out of scope for Claude in this cut** — propose text only.

---

## 7. Deliverables (Claude writes)

| Artifact | Path |
|---|---|
| Investigation report | `.jes/artifacts/investigation_continuity_hardening.md` |
| Design draft (★-ready) | `.jes/artifacts/design_continuity_hardening.md` |
| Optional probe log | `.jes/artifacts/investigation_continuity_hardening_probes.md` |

### Investigation report must include

1. Executive summary (≤15 lines).  
2. **System Map ↔ Continuity failures** (section 3.3).  
3. Per-finding confirmation tables (G14/G15/G12/G8/G11).  
4. Root-cause synthesis (single tree or multiple).  
5. Interaction with G10 (force-frame / keywords) — evidence-based.  
6. Recommended design option + slice plan.  
7. Open questions for Engineer.

### Design draft must include

★ candidates numbered; recommended option; rejected options; out-of-scope; acceptance scenarios for later CLI; test sketch.

---

## 8. Review criteria (Cursor later)

| Gate | Fail if |
|---|---|
| System Map used | Report lacks C-xxx table / reading evidence |
| G14 explained | No code path for “Hélices registradas” on motors prompt |
| G12 ≠ handwave | Session fields / C-037 not cited |
| No scope creep | Proposes Impl C / Conversation Engine / G10 materials rewrite as required |
| Design actionable | No clear ★ lock surface for Engineer |
| Zero product edits | Diff touches `src/` behavior |

**PASS / PASS WITH NOTES / FAIL.**

---

## 9. Prompt block for Claude (copy-paste)

```text
Read and execute:
.jes/artifacts/implementation_contract_continuity_hardening_investigation.md

Type: Investigation + Design ONLY. Zero product src/ changes.

HARD RULE: Start from docs/system_map/ (README → FLOWS → CONNECTIONS canonical registry →
AUTHORITY → ACQUISITION/RUNTIME/INTENT/ITERATION/CONTINUITY maps → MISMATCHES →
.jes/artifacts/sys_map_004_routing_audit.md). Map every Continuity finding (G14, G15, G12, G8, G11)
to C-xxx edges before deep orchestrator grepping.

Findings: .jes/artifacts/cli_findings_post_catalog_bind_v1.md
Roadmap: docs/IMPLEMENTATION_TASKS.md (Continuity Hardening ← now; G10 PVC deferred)

Deliver:
- .jes/artifacts/investigation_continuity_hardening.md
- .jes/artifacts/design_continuity_hardening.md
(optional probes log)

Do not implement. Do not edit system_map files (propose text only). Do not patch G10 materials.
When done, summarize ★ candidates for Engineer lock.
```

---

## 10. Stop conditions

Stop and ask Engineer if investigation discovers that Continuity Hardening **requires** a new architectural subsystem (Conversation Engine / dual-dispatch rewrite) rather than Acquisition Target Authority + preempt policy within existing maps.

Otherwise complete the two artifacts and hand back for ★ lock.
