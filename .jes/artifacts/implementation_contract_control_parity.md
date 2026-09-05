# Implementation Contract — Control parity (claim copy B1)

**Project:** Jarvis  
**Date:** 2026-09-04  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** IMPLEMENTED · REVIEWED **PASS WITH NOTES** · thread **CLOSED**  
**Review:** [implementation_review_control_parity.md](implementation_review_control_parity.md)  
**Report:** [implementation_report_control_parity.md](implementation_report_control_parity.md)  
**Suite:** **2164**

**Type:** Claim-language / CLI + BOM display. **Not** ERF predicates. **Not** catalog. **Not** control physics.

**Parents:**
- [investigation_report_control_parity.md](investigation_report_control_parity.md)
- [investigation_review_control_parity.md](investigation_review_control_parity.md) — **PASS WITH NOTES**
- [investigation_contract_control_parity.md](investigation_contract_control_parity.md)
- Thread ★: [engineer_ratification_control_parity.md](engineer_ratification_control_parity.md) (opened investigation; Buy locked here)

**Baseline:** tag **`v0.3.6`** · claim hygiene in tree · suite **2160**

**Buy:** **B1** — Continuity untouched; ERF `_control_evidence` / `_derive_*` untouched.

---

## 0. You

- Edit only files in §5.
- Do **not** change `_control_evidence`, `_derive_subsystem_verdict`, `_derive_overall`, gap types.
- Do **not** change `classify_component`, `component_presence_tier`, `_MEASURABLE`.
- Do **not** add FC/sensor catalog JSON or bind UX.
- Do **not** invent control physics.
- Do **not** change `ASSEMBLY_READY` / `NOT_ASSEMBLY_READY` eligibility or those enum strings.
- Do **not** change Arquitectura `n/4` counter logic or “Arquitectura completa” CTAs.
- Full suite green. Zero weakened tests.

---

## 1. Intent

After declaring only name-recognition control (e.g. `"Pixhawk 4"` + `"GPS M9N"`, or even `"pixhawk"` + `"gps"`):

- ERF may still show Control **PASS** and overall **ASSEMBLY_READY** (unchanged).
- The **rendered** Control line and the BOM `✓ flight_controller… (high)` line must make clear this is **declaration / identity**, not control physics or a measured quantity like motor thrust.

Sensors BOM `◇ … (declarativo)` already honest — **unchanged**.

---

## 2. Locked behavior

### 2.1 CLI readiness — `adapters/cli/main.py` `_render_readiness_block`

When rendering subsystem `control` and `verdict == "PASS"`:

- Line format becomes (14-char label column preserved as today):

```text
Control        PASS *
```

- After the nine subsystem lines (and **before** the blank line + `PROJECT STATUS:`), append **exactly one** footnote if any `PASS *` was emitted for control:

```text
* Control: declaración — sin física de control
```

When control verdict is not `PASS`, no asterisk and no footnote.

Do **not** mark Propulsion / Energy / Structure / etc. Other subsystems unchanged.

Margin NOTE from claim hygiene (`NOTE: margen ajustado…`) stays independent; both may appear.

### 2.2 BOM — `project_closure.format_bom_lines`

For entries in the **`defined`** bucket with `key == "flight_controller"` only, change the completeness tail from:

```text
(high)
```

to:

```text
(high — identidad, sin dato físico)
```

(Use the actual `completeness` string from the entry — typically `high`; if somehow another completeness appears in `defined`, still append ` — identidad, sin dato físico` after it inside the parentheses.)

Exact shape today:

```text
✓ flight_controller: {name}{sku_suffix}{qty} ({completeness})
```

After:

```text
✓ flight_controller: {name}{sku_suffix}{qty} ({completeness} — identidad, sin dato físico)
```

**Unchanged:** motors, battery, propellers, frame, ESC, sensors (declarative/incomplete/missing), `_bom_identity_suffix` SKU behavior.

Prefer a tiny helper next to `_bom_identity_suffix` if it keeps `format_bom_lines` clear — same file only.

### 2.3 Out of this IC

- Continuity situation / evidence / next-step (does not name control today).
- Arquitectura 4/4 strings and counters.
- Orchestrator “Arquitectura completa” hints.
- Any ERF JSON field values (verdict stays `PASS`).

---

## 3. Tests (mandatory)

| File | What |
|---|---|
| `tests/test_engineering_readiness_cli.py` | Render readiness with control PASS → line contains `PASS *` and footnote `* Control: declaración — sin física de control`. Control non-PASS → no `*` / no footnote. Propulsion PASS line has no `*`. |
| `tests/test_project_closure_v1.py` (or adjacent BOM test file already covering `format_bom_lines`) | `defined` flight_controller high → line contains `identidad, sin dato físico`. Motor/battery/propeller defined high lines **lack** that suffix. Sensors declarative still `◇` / `(declarativo)` without the new FC suffix. |
| ERF smoke (optional) | Same fixture still `subsystems["control"].verdict == "PASS"` and overall can remain `ASSEMBLY_READY` — IC must not flip eligibility. |

Do not add catalog probes. Do not commit `workspace/`.

---

## 4. Explicit non-goals

- B2/B3 ERF honesty or ASSEMBLY_READY gating on declaration-only control  
- FC/sensor catalog  
- Changing sensors to reach `"high"`  
- claim-hygiene N2/N4, C-A1, H5, HD-*  
- Version bump  

---

## 5. Files you may edit

| Path | Role |
|---|---|
| `src/jarvis/adapters/cli/main.py` | §2.1 |
| `src/jarvis/core/project_closure.py` | §2.2 |
| `tests/test_engineering_readiness_cli.py` | CLI |
| `tests/test_project_closure_v1.py` and/or existing BOM format tests | BOM |

---

## 6. Done criteria

- §2.1–§2.2 locked strings present  
- Mandatory tests + full suite green  
- `git diff` shows no `engineering_readiness` evidence/verdict/`_derive_overall` edits, no `library/` catalog, no Continuity edits  
- Implementation report: files, behavior, tests, residual (B2 future ★; 4/4 still declaration-complete for control quarter)

---

## 7. After implementation

Cursor reviews against this IC. On PASS, control parity thread closes; Engineer may then **close the knowledge/block-parity phase** and open a new feature cycle (per prior plan). N4 weak-OP / C-081 / C-108 not automatic.
