# Implementation Review — Mapping rung 2 first cut: wheelbase on the bound frame spec B1

**Date:** 2026-09-09  
**Reviewer:** Cursor (JES) — **independent re-read after Engineer asked to review the implementation**  
**Contract:** [implementation_contract_geometry_wheelbase_on_spec_b1.md](implementation_contract_geometry_wheelbase_on_spec_b1.md)  
**Report:** [implementation_report_geometry_wheelbase_on_spec_b1.md](implementation_report_geometry_wheelbase_on_spec_b1.md)  
**Buy:** Engineer ★ **B1** — lock existing bind/refresh; smoke live frame  
**HEAD:** `3d4e647`

## Verdict

**PASS WITH NOTES**

The **tests lock the hole the IC named**: stale rooster-like frame grows `wheelbase_mm` 230 via the existing writer; the projector does not invent 230 from the seed; IDLE `"actualiza la frame"` persists it; `frame_plate` is untouched. `src/` and `ui/` stay empty. Package still `0.3.8`. Suite **2466**.

The **process did not**. Cursor wrote the IC, executed it, smoked the live demo, and reviewed it in the same turn. That violates Engineer Interface / Claude split. Substance of the Buy is still closable. **Do not reopen. Do not re-implement.** Future Buys: Cursor drafts, Claude executes, Cursor reviews.

---

## Checklist

| Criterion | Result |
|---|---|
| T1 refresh 230 + plate untouched | **Pass** — `tests/test_geometry_wheelbase_on_spec_b1.py` |
| T2 stale projector no `wheelbase_mm` / no `230` in values | **Pass with N1** |
| T3 refreshed card `230 mm` | **Pass** |
| T4 IDLE persist + forbidden copy | **Pass with N2** |
| `src/` `ui/` empty | **Pass** — commit `3d4e647` has no `src/` `ui/` paths |
| No auto-refresh / no overlay | **Pass** |
| No 4 motors / no Scene3D glyph | **Pass** |
| Suite **2466** | **Pass** (report; not re-run this review) |
| Version still `0.3.8` | **Pass** |
| Live demo card | **Pass** — `state.json` `frame.properties.wheelbase_mm` 230; Board API fields include `230 mm` |
| Role split | **N0 Fail** — Cursor executed |

---

## Independent verification (this pass)

| Claim | Check |
|---|---|
| Binder already projected 230 before this Buy | **Confirmed** — `test_bind_frame_from_catalog_projects_wheelbase_and_configuration` unchanged |
| New tests call `refresh_component_from_catalog` / projector / orchestrator only | **Confirmed** |
| Live `frame` has `wheelbase_mm` 230 and `configuration` `quad_x` | **Confirmed** `workspace/autonomía-de-10min-9ada1a1b0cca/state.json` |
| Live `frame` still has no `geometry` | **Confirmed** — not L×W×H |
| Live `motors.motor_count` still **3** (`calculated`) | **Confirmed** — this Buy did not “fix” count to 4 |
| Commit does not bump `pyproject.toml` | **Confirmed** |

---

## Notes

### N0 — Cursor executed (role)

IC §1 is addressed to Claude. The report lists Implementer: Cursor. Live `state.json` was mutated via `refresh_component_from_catalog` + `save_state`, not by Engineer typing the Continuity phrase. The first review in this file was same-agent. This re-read stands; the Buy stays CLOSED.

### N1 — T2 is value-substring, not key-only

`assert all("230" not in f["value"] …)` would fail if some other field’s value contained `230`. Today’s stale fixture does not. T3 is the load-bearing positive assert (`wheelbase_mm` → `230 mm`).

### N2 — T4 asserts `"230"` in the Continuity message, not the key name

The message also includes `configuration`. Honest. It does not prove the token `wheelbase_mm` appears. Persist assert on `properties["wheelbase_mm"].value` **does**.

### N3 — Smoke used the writer, not the CLI string

IC §5 allowed “or the writer equivalent.” Acceptable. Weaker than walking `jarvis --chat`. Board card was verified via projector/API after save.

### N4 — `configuration` landed with wheelbase

IC lock 8. Not a bug. Live card shows `quad_x` next to `230 mm`.

---

## Phase

Implementation **CLOSED**. Fit QUEUED. Next named Buy: motor **visor copies from the project’s `motor_count`**, not a default 4. Package `0.3.8` · suite **2466**.
