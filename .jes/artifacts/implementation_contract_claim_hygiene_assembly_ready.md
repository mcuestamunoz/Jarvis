# Implementation Contract — Claim hygiene under ASSEMBLY READY

**Project:** Jarvis  
**Date:** 2026-09-04  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** IMPLEMENTED · REVIEWED **PASS WITH NOTES** · thread margin-slice **CLOSED**  
**Review:** [implementation_review_claim_hygiene_assembly_ready.md](implementation_review_claim_hygiene_assembly_ready.md)  
**Report:** [implementation_report_claim_hygiene_assembly_ready.md](implementation_report_claim_hygiene_assembly_ready.md)  
**Suite:** **2160**

**Parents:**
- [investigation_report_claim_hygiene_assembly_ready.md](investigation_report_claim_hygiene_assembly_ready.md)
- [investigation_review_claim_hygiene_assembly_ready.md](investigation_review_claim_hygiene_assembly_ready.md) — **PASS WITH NOTES**
- [engineer_ratification_claim_hygiene_assembly_ready.md](engineer_ratification_claim_hygiene_assembly_ready.md)

**Baseline:** tag **`v0.3.6`** / **`checkpoint-experimental-prop-energy-closed`** · commit `f70b278` · suite **2150**

**Buy locked:** **B4 margin/quality slice only.** Weak-OP follow-up is **not** this IC.

---

## 0. You

- Edit only files listed in §5.
- Do **not** change `engineering_readiness._derive_overall`, gap types, or subsystem verdicts.
- Do **not** change `simulator.py` formulas or any margin threshold constant.
- Do **not** wire `prop_energy_block_closure` into Continuity.
- Do **not** import `jarvis.adapters` from `jarvis.core`.
- Do **not** reopen PhaseLayer CLI visibility (FN-002 suppress stays).
- Do **not** open sensor/FC catalogs, C-A1, fail-routing N1, HD-*.
- Full suite green. Zero weakened tests.

---

## 1. Intent (field fixture)

In-memory / `tmp_path` shape matching the investigation appendix:

```text
sim.status = pass
sim.can_fly = True
sim.quality = risky
sim.safety_margin_ratio = 1.05
sim.warnings = [low_margin]
status_type = warning          # as build_startup_context derives today
ERF overall = ASSEMBLY_READY   # allowed; do not flip to NOT_ASSEMBLY_READY
```

After this IC, Continuity **must not** say `Diseño validado en simulación (PASS)`.  
CLI readiness **must** still show `PROJECT STATUS: ASSEMBLY READY` **and** one NOTE caveat.  
PASS + good/acceptable **without** margin/load warnings must keep today’s “Diseño validado” path unchanged.

---

## 2. Locked behavior

### 2.1 Continuity `situation` — `project_continuity.py`

After the existing autonomy-undemonstrated / autonomy-below situation guards, and **before** the plain:

```python
elif sim_status == "pass":
    situation = "Diseño validado en simulación (PASS). …"
```

insert a gate when `sim_status == "pass"` and `_margin_claim_weak(sim)` is true.

**Predicate `_margin_claim_weak(sim)`** (helper in the same file):

True if **any** of:

1. `(sim.get("quality") or "").lower() == "risky"`
2. `sim.get("warnings")` intersects  
   `{"low_margin", "high_actuator_load", "low_force_to_weight_ratio"}`

Do **not** treat `autonomy_below_restriction` here (already owned by autonomy branches).

**Locked situation string (verbatim):**

```text
Comprobación de empuje: PASS. Margen ajustado — el diseño no está validado con reserva cómoda.
```

Keep `"Diseño validado en simulación (PASS). Proyecto vivo — listo para el siguiente paso útil."` when PASS and **not** `_margin_claim_weak`.

Evidence bullet that already prints quality/margin: **unchanged**.

### 2.2 Continuity `next_useful_step` / `next_useful_why`

Keep the existing warning-branch next step:

```text
Corrige la causa del warning/fallo de simulación.
```

when that branch wins (including PASS+`low_margin` with `status_type=warning`).

`next_useful_why` may remain the raw warning code (e.g. `low_margin`). **Do not** import CLI maps into Continuity.

### 2.3 CLI — humanize `Por qué` — `adapters/cli/main.py`

In `render_startup_context`, when printing `Por qué: {continuity['next_useful_why']}`, if the why string is a key in `WARNING_SHORT` (or `WARNING_MESSAGES`), print the **short** human label (prefer `WARNING_SHORT`). Unknown codes stay verbatim.

### 2.4 CLI — ASSEMBLY READY caveat — same file

After the `PROJECT STATUS: ASSEMBLY READY` line from `_render_readiness_block`, when overall is `ASSEMBLY_READY` **and** the backing simulation is margin-weak (same predicate as Continuity: `quality==risky` **or** margin/load warning codes above), append **exactly one** line:

```text
NOTE: margen ajustado — ASSEMBLY READY no implica reserva cómoda.
```

When overall is `NOT_ASSEMBLY_READY`, or PASS without margin weakness, **no** NOTE.

**How to get simulation into the renderer (pick one; prefer the smaller diff):**

- **Preferred:** `build_startup_context` already loads `simulation`; add a thin `ctx["simulation"]` snapshot (`status`, `quality`, `warnings`, `safety_margin_ratio` only). `_render_readiness_block(readiness, simulation=…)` or the caller after it appends the NOTE.
- **Alt:** derive the same predicate from `ctx["status_type"]=="warning"` and `ctx["status_reason"]` in the margin/load set **plus** optional quality if you also thread it — must still cover the investigation fixture.

Do **not** change the `ASSEMBLY_READY` / `NOT_ASSEMBLY_READY` string values themselves.

### 2.5 PhaseLayer

No change. Situation string absorbs claim honesty for this slice.

---

## 3. Tests (mandatory)

| File | What |
|---|---|
| `tests/test_project_continuity.py` | PASS + `quality=risky` + `warnings=[low_margin]` + `status_type=warning` → situation is the §2.1 locked string; **not** `Diseño validado`. Evidence still mentions `risky` / margin. Next step still Corrige…; why may be `low_margin`. |
| same | PASS + `quality=good` (or acceptable) + empty warnings → still `Diseño validado en simulación (PASS)`. |
| same | Existing autonomy undemonstrated / below fixtures stay green (still not Diseño validado; still their locked strings). |
| `tests/test_engineering_readiness_cli.py` and/or `tests/test_main_cli.py` | Render ctx with ASSEMBLY_READY + risky/low_margin sim → text contains `PROJECT STATUS: ASSEMBLY READY` **and** the §2.4 NOTE; `Por qué` humanized if why=`low_margin`. |
| same | ASSEMBLY_READY + PASS good/no warnings → NOTE **absent**. |
| ERF unit | Optional smoke: same fixture still `overall == ASSEMBLY_READY` (regression: IC must not flip eligibility). |

Do not add catalog/DSE probes. Do not commit Engineer `workspace/`.

---

## 4. Explicit non-goals

- Changing `_derive_overall` or inventing a margin HIGH/MEDIUM gap type (that would be B3 ★)
- Unifying the four margin thresholds across simulator / reasoning / suggestions / goal_planner
- Wiring block-closure “evidencia débil” into Continuity (B4 follow-up)
- Showing PhaseLayer when Continuity situation is present
- Control parity / sensor catalog / C-A1 / HD-* / fail-routing N1 polish

---

## 5. Files you may edit

| Path | Role |
|---|---|
| `src/jarvis/core/project_continuity.py` | §2.1 gate + helper |
| `src/jarvis/adapters/cli/main.py` | §2.3 humanize why; §2.4 NOTE |
| `src/jarvis/core/orchestrator.py` | **Only if** needed for thin `ctx["simulation"]` snapshot (§2.4 preferred) |
| `tests/test_project_continuity.py` | Continuity fixtures |
| `tests/test_engineering_readiness_cli.py` and/or `tests/test_main_cli.py` | CLI NOTE + humanize |

---

## 6. Done criteria

- §2.1–§2.4 behavior locked above
- Mandatory tests green; full suite green
- `git diff` shows no edits to `simulator.py`, `engineering_readiness.py` gap/`_derive_overall` logic, catalog JSON, or block-closure Continuity wiring
- Implementation report lists files, behavior, tests run, residual risks (N2 PhaseLayer mismatch remains documented debt)

---

## 7. After implementation

Cursor reviews against this IC. Engineer may then open **control parity** investigation (agenda) — not automatic from this IC.
