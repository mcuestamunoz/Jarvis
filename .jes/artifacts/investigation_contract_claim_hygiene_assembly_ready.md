# Investigation Contract — Claim hygiene under ASSEMBLY READY

**Project:** Jarvis  
**Date:** 2026-09-04  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_claim_hygiene_assembly_ready.md`

**Status:** INVESTIGATION REVIEWED — PASS WITH NOTES · IC drafted · awaiting Engineer ★ / `procede`  
**Review:** [investigation_review_claim_hygiene_assembly_ready.md](investigation_review_claim_hygiene_assembly_ready.md)  
**Report:** [investigation_report_claim_hygiene_assembly_ready.md](investigation_report_claim_hygiene_assembly_ready.md)  
**IC:** [implementation_contract_claim_hygiene_assembly_ready.md](implementation_contract_claim_hygiene_assembly_ready.md)

**Type:** Knowledge / claim investigation. Map which sentences over-claim when
simulation is PASS with weak margin (`quality=risky`, warning `low_margin`)
and/or weak OP evidence, while ERF still says `ASSEMBLY_READY`. **Not** an
Implementation Contract. **Do not implement.**

**Checkpoint base:** tag **`v0.3.6`** / **`checkpoint-experimental-prop-energy-closed`** · commit `f70b278`  
**Suite last closed:** **2150**

**You are Claude Code.** This file is your work order. Cursor does not
investigate and does not implement this slice. You write the report. Cursor
reviews it. Engineer ★ locks the claim matrix before any IC.

**Do not implement. Do not bump version. Do not weaken tests. Do not invent
control physics, sensor catalogs, or new readiness subsystems.**

---

## 0. Role split (do not invert)

```text
Engineer ★ → chose claim hygiene (not control catalog, not C-A1 polish)
Cursor     → writes this contract (and later the IC, if any)
Claude     → investigates, writes investigation_report_claim_hygiene_assembly_ready.md
Cursor     → investigation review
Engineer ★ → locks allowed claim language / gates
Cursor     → IC only after ★
Claude     → implements from IC only
```

---

## 1. Why this investigation exists

After the experimental prop/energy walks (closed at `v0.3.6`), Jarvis can reach
`ASSEMBLY READY` with honest physical trade-offs — and still speak as if the
design were comfortably closed:

```text
sim.status = pass
sim.quality = risky          (margin band < 1.1 — verify file:line)
warnings   ⊇ low_margin      (threshold may differ from quality — verify)
Continuity situation ≈ "Diseño validado en simulación (PASS)…"
CLI / ERF  ≈ PROJECT STATUS: ASSEMBLY READY
```

That is a **Claim** problem in the Know / Claim / Measure / Buy protocol — not
a reason to polish Continuity autonomy copy, reopen fail-routing N1, or ship a
sensor catalog.

Related map debt (context only, **not** your authority to expand scope):

- System Map **C-081** / MISMATCHES **H5**: PASS+risky → Continuity next-step
  thread is 🟡 PARTIAL (WEAK). This investigation may **consume** that fact.
  It must **not** reopen H5 ESC catalog, Conversation Engine, or a goal-thread
  subsystem.

Prior honesty work already carved related cases (do not regress; cite):

- CLI feasibility: PASS thrust ≠ “Diseño validado” when autonomy undemonstrated
- autonomy-below: calculated minutes under target keep “Diseño validado” off

This thread asks the **margin / risk** analogue of those locks.

---

## 2. Governing questions (answer all four)

1. **Know** — Which deterministic fields already encode weak margin / risk
   (`quality`, `warnings`, `safety_margin_ratio`, OP evidence labels, block
   closure “evidencia débil”)? Cite `file:line` and thresholds.
2. **Claim** — Which user-facing sentences currently over-claim relative to
   those fields? Build a **claim matrix** (sentence × allowed when).
3. **Measure** — What would falsify or strengthen each claim without new
   physics (existing sim fields only vs explicit refuse-to-strengthen)?
4. **Buy** — Is the smallest honest next purchase **copy-only Continuity/CLI**,
   **a Continuity gate** (keep `ASSEMBLY_READY` unchanged), **an ERF /
   `_derive_overall` change**, or **investigation-only / no IC**?

Default stance: prefer claim language + Continuity gates over changing
`ASSEMBLY_READY` semantics. If you believe `_derive_overall` must change so
PASS+risky cannot be ASSEMBLY_READY, **stop and name it as an Engineer ★
gate** — do not treat that as a local IC default.

---

## 3. Locked constraints (do not weaken)

1. `simulation.status == "fail"` remains distinct from PASS+warnings (fail-routing
   honesty stays closed).
2. Do **not** change thrust, autonomy L1/L2 formulas, OP resolution, DSE scoring,
   catalog JSON, or Structure A class rules.
3. Do **not** open control/sensor/FC catalogs or control physics.
4. Do **not** reopen catalog honesty C-A1, P26/P27-A, HD-*, G24-B, Option B ERF,
   Tier 3, or broad `orchestrator.py` split.
5. Do **not** implement fixes in this investigation.
6. `ASSEMBLY_READY` today means (verify): zero HIGH gaps + 9 subsystem PASS
   (with accepted WARNING types). Report must state whether PASS+risky already
   satisfies that **by design** vs by accident of unused fields.
7. Preserve Engineer walk workspaces; reconstruct fixtures in `tmp_path` /
   in-memory.

---

## 4. Surfaces to trace (file:line required)

| Surface | Find |
|---|---|
| Sim quality bands | `simulator._resolve_quality` — when `risky` vs `acceptable` vs `good` |
| Warning `low_margin` | `simulator._resolve_warnings` + `LOW_MARGIN_THRESHOLD` — relation to `quality` |
| Continuity “Diseño validado” | `project_continuity.build_project_continuity` PASS branch; what it reads / ignores |
| Continuity next-step on PASS | same file — does it read `quality` / `warnings` / margin? (C-081 hypothesis) |
| CLI warning humanization | `main.WARNING_MESSAGES` / render path for `low_margin` |
| ERF overall | `engineering_readiness._derive_overall` — does margin/quality enter? |
| Subsystem validated | e.g. propulsion/energy/control `validated = sim_status == "pass"` — margin ignored? |
| Block closure / weak OP | any “CERRADO” / evidencia débil copy that can co-occur with ASSEMBLY READY |
| CLI readiness block | `main` ENGINEERING READINESS / PROJECT STATUS render |

Optional adjacent (one paragraph each, no deep dive unless contradictory):

- `phase_layer` quality use
- `suggestion_engine` margin thresholds vs Continuity
- autonomy-below / undemonstrated branches (already locked — confirm they still fire)

---

## 5. Field reconstruction (do not mutate Engineer workspace)

Reproduce **at least one** in-memory / `tmp_path` fixture where:

```text
sim.status              == "pass"
sim.can_fly             == True
sim.quality             == "risky"   OR warnings contain "low_margin"
ERF overall             == "ASSEMBLY_READY"   (if reachable; if not, explain why)
Continuity situation    contains "Diseño validado" OR prove it does not
```

Prefer reconstructing the walk shape that motivated the agenda (PASS + risky /
low_margin after battery↔thrust trade), not inventing a second product story.

Record: margin value, quality, warnings[], Continuity situation + next_step,
ERF overall, whether OP/block-closure language also over-claims.

---

## 6. Required report shape

Write `.jes/artifacts/investigation_report_claim_hygiene_assembly_ready.md` with:

### A. Executive answer (≤15 lines)

Is the over-claim real on `v0.3.6`? Which surface is primary (Continuity
situation vs next_step vs ASSEMBLY_READY label vs all)?

### B. Field table (Know)

| Field | Authority (`file:line`) | Threshold / meaning | Read by Continuity? | Read by `_derive_overall`? |
|---|---|---|---|---|

### C. Claim matrix (Claim)

Rows = user-visible sentences (quote exact strings). Columns at minimum:

| Sentence | Allowed when PASS+good | PASS+risky / low_margin | PASS+autonomy undemonstrated | FAIL |
|---|---|---|---|---|

Mark **current** vs **proposed** (proposed = recommendation only).

### D. Measure

For each over-claim: what existing signal falsifies it; what Jarvis must refuse
to claim without lab.

### E. Buy recommendation (one primary)

Pick **exactly one**:

| Option | Meaning |
|---|---|
| **B0** | No IC — documentation / Engineer lock only |
| **B1** | Continuity copy + gate only (`ASSEMBLY_READY` unchanged) |
| **B2** | Continuity + CLI readiness wording (still no `_derive_overall` change) |
| **B3** | Change `_derive_overall` / ASSEMBLY_READY eligibility — **requires Engineer ★ stop** |
| **B4** | Split: margin claim hygiene now; weak-OP claim language as a **separate** later IC |

Justify with seams already traced. Prefer the smallest option that stops the lie.

### F. Explicit non-goals confirmed

List what you did **not** propose (sensor catalog, C-A1, fail-routing N1,
control physics, H5 ESC, Conversation Engine, scoring rewrite).

### G. Suggested IC skeleton (only if Buy ≠ B0)

≤20 lines: files likely touched, behavior change, tests, forbidden edits.
**Not** an Implementation Contract.

---

## 7. Out of scope

- Implementing any fix
- Sensor / FC / ESC catalogs
- Control parity product model (next agenda thread — do not pre-solve)
- Catalog honesty C-A1 as a motor-list feature
- Changing simulation physics or margin **formulas** (thresholds may be cited;
  changing them is a separate ★ if you think they are wrong)
- Broad Continuity rewrite unrelated to PASS+risk / weak-evidence claims
- Hardware HD-* campaigns

---

## 8. Done criteria

- Report exists at the path above
- Every factual claim cites `file:line` or a named test/probe on `v0.3.6`
- Claim matrix + Buy option filled
- No `src/` edits from this investigation
- If B3 is recommended: report stops for Engineer ★ and does not draft an IC
  that silently changes ASSEMBLY_READY

---

## 9. After review

Cursor writes investigation review. Engineer ★ on claim matrix / Buy. Only then
may Cursor draft an Implementation Contract.
