# Implementation Contract — Structure honesty (`PASS *`)

**Project:** Jarvis  
**Date:** 2026-09-04  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** IMPLEMENTED · REVIEWED **PASS WITH NOTES** · honesty thread **CLOSED** (suite **2200**)  
**Review:** [implementation_review_structure_honesty_pass_star.md](implementation_review_structure_honesty_pass_star.md)  
**Report:** [implementation_report_structure_honesty_pass_asterisk.md](implementation_report_structure_honesty_pass_asterisk.md)  
**Type:** Claim-language / CLI readiness display only. **Not** ERF predicates. **Not** Structure B. **Not** graph.

**Parents:**
- [investigation_report_structure_a_pass_meaning.md](investigation_report_structure_a_pass_meaning.md) — Buy (b) honesty IC
- [investigation_review_structure_a_pass_meaning.md](investigation_review_structure_a_pass_meaning.md) — **PASS WITH NOTES**
- [investigation_report_structure_b_parts_graph.md](investigation_report_structure_b_parts_graph.md) — Buy (b) honesty **before** graph
- [investigation_review_structure_b_parts_graph.md](investigation_review_structure_b_parts_graph.md) — **PASS WITH NOTES**
- ★ sequencing: [engineer_ratification_structure_b_parts_graph.md](engineer_ratification_structure_b_parts_graph.md)

**Baseline:** tag **`v0.3.6`** · suite **2197** · Control parity `PASS *` already shipped

**Buy:** Close the readiness asymmetry: `Structure PASS` bare next to `Control PASS *` despite Structure asserting no chassis geometry.

**Ship order:** **This IC first.** Graph model IC second ([implementation_contract_structure_b_parts_graph.md](implementation_contract_structure_b_parts_graph.md)).

---

## 0. You

- Edit only files in §5.
- Do **not** change `_structure_evidence`, `_derive_subsystem_verdict`, `_derive_overall`, gap types, LEVEL A predicates.
- Do **not** change `classify_component`, `_frame_completeness`, `BLOCK_TO_COMPONENTS`.
- Do **not** add `parent_key`, frame parts, wheelbase, configuration, seed edits (graph IC).
- Do **not** change Control’s existing asterisk/footnote strings.
- Do **not** bump version.
- Full suite green. Zero weakened tests.

---

## 1. Intent

When Structure’s ERF verdict is `PASS`, the CLI readiness line must carry the same honesty signal Control already has: asterisk + footnote. Verdict JSON stays `"PASS"`. `ASSEMBLY_READY` eligibility unchanged.

Reproduced target shape (both declaration-only Control and Structure PASS):

```text
Structure      PASS *
Control        PASS *
* Structure: identidad / clase nivel A — sin geometría de chasis
* Control: declaración — sin física de control
```

---

## 2. Locked behavior

### 2.1 CLI — `adapters/cli/main.py` `_render_readiness_block`

**Blanket rule** (report lean; matches Control): whenever subsystem key `structure` has `verdict == "PASS"`, render:

```text
Structure      PASS *
```

Do **not** condition on `frame_class_compatibility_state` / `catalog_bound` / gaps.

After the nine subsystem lines (before blank line + `PROJECT STATUS:`), append footnotes for every `PASS *` emitted, in readiness subsystem order:

1. If structure PASS → exactly:

```text
* Structure: identidad / clase nivel A — sin geometría de chasis
```

2. If control PASS → existing:

```text
* Control: declaración — sin física de control
```

Introduce a module constant e.g. `_STRUCTURE_DECLARATION_FOOTNOTE` next to `_CONTROL_DECLARATION_FOOTNOTE`. Prefer a small ordered list of `(subsystem_key, footnote)` rather than duplicating if/else sprawl — keep Control string **byte-identical**.

When structure verdict is not `PASS`: no Structure asterisk, no Structure footnote.

Other subsystems unchanged. Margin NOTE from claim hygiene stays independent; may coexist.

### 2.2 Out of this IC

- BOM / Continuity / graph / catalog / seed  
- Any ERF field value change (verdict remains `PASS`)  
- Exact graph model  

---

## 3. Tests (mandatory)

| File | What |
|---|---|
| `tests/test_engineering_readiness_cli.py` | Structure PASS → line `PASS *` + footnote `* Structure: identidad / clase nivel A — sin geometría de chasis`. Structure non-PASS → no Structure `*` / no Structure footnote. Control PASS still has its own `*` + footnote. Propulsion PASS has no `*`. Both Structure+Control PASS → both footnotes present, Structure footnote before Control. |
| Optional ERF smoke | Same fixture: `subsystems["structure"].verdict == "PASS"` unchanged; overall eligibility unchanged. |

Do not commit `workspace/`.

---

## 4. Explicit non-goals

- Widening Structure PASS meaning  
- Graph / `parent_key` / parts  
- Version bump  

---

## 5. Files you may edit

| Path | Role |
|---|---|
| `src/jarvis/adapters/cli/main.py` | §2.1 |
| `tests/test_engineering_readiness_cli.py` | §3 |

---

## 6. Done criteria

- Locked strings present  
- Mandatory tests + full suite green  
- `git diff` shows **no** `engineering_readiness` / Continuity / schema / `library/` / `project_closure` edits  
- Implementation report: files, behavior, tests, residual (graph IC next)

---

## 7. After implementation

Cursor reviews against this IC. On PASS → Engineer may `procede` the graph IC.
