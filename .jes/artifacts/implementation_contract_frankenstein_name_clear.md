# Implementation Contract — Frankenstein `.name` Clear (IC D / Micro)

**Project:** Jarvis  
**Date:** 2026-08-31  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)

**Status:** READY FOR CLAUDE

**Type:** Trust/display micro-fix — when G5 clears a motor's `catalog_ref` due to param divergence, **also** replace a SKU-shaped `.name` with an honest non-catalog label. **Does not** change when/if G5 invalidates.

**Investigation:** [`.jes/artifacts/investigation_report_deferred_queue_post_v031.md`](investigation_report_deferred_queue_post_v031.md) — §6  
**Investigation review:** [`.jes/artifacts/investigation_review_deferred_queue_post_v031.md`](investigation_review_deferred_queue_post_v031.md) — **PASS WITH NOTES**  
**Checkpoint base:** tag **`v0.3.1`** · commit `30c9aec`

**Arc position:** IC **D** (parallel micro). **Independent** of IC C (`design_explorer.py`) — may ship before, after, or in the same checkpoint window as IC C. **Not** in IC C's diff.

**Workflow:** Claude implements **G24D-1 → G24D-5** + report → Cursor review → probe → checkpoint with IC C if Engineer asks.

---

## 0. Engineer ratification (locked)

| ★ | Decision |
|---|---|
| **★5** | **D — micro-IC now**, parallel to C, **not merged** into IC C. |
| **★6** | Version bump after **C+D PASS** — not in this diff alone. |

**Trust problem (live on v0.3.1, investigation §6.1):**

```text
catalog_ref  → None          (G5, correct)
.name        → sunnysky_…     (stale SKU string)
BOM/estado   → ✓ motors: sunnysky_… qty=6 (high)   — no [sku], but reads like a bound SKU
```

**Product contract (Engineer, locked):**

> G5's **decision** to clear `catalog_ref` is unchanged. Only the **resulting motor spec's `.name`** must not remain a misleading SKU-shaped label.

---

## 1. Problem / intent

### 1.1 Today

`invalidate_diverged_catalog_refs` (`catalog_bind.py:215-227`) on motor thrust divergence:

```python
updated_components["motors"] = motor.model_copy(update={"catalog_ref": None})
```

**Does not touch `.name`.** `sync_motors_component_from_params` (`component_sync.py`) also leaves `.name` unchanged by design.

`format_bom_lines` (`project_closure.py:408-416`) correctly omits `[sku]` when `catalog_ref is None`, but the bare name string is **indistinguishable in format** from a deliberate freeform declaration that happens to look like a SKU.

### 1.2 Target

When motor `catalog_ref` is cleared on divergence in `invalidate_diverged_catalog_refs`:

- Set `.name` to a **fixed, honest, non-SKU-shaped label** (implementation choice — examples: `"motor (parámetros divergentes)"`, `"motors"`, or `component_type`-based neutral string).
- **Only** on the motor divergence path where `catalog_ref` is cleared — not on battery divergence, not on unrelated writes.

After fix, investigation §6.1 repro → BOM/`estado` line must **not** show the old SKU as the component name.

---

## 2. Locked semantics (non-negotiable)

### 2.1 When to rename

**Only** inside `invalidate_diverged_catalog_refs`, in the existing motor branch where `catalog_ref` is set to `None` (thrust divergence). Same epsilon / comparison logic — **no new divergence rules**.

### 2.2 When NOT to rename

- Battery divergence branch — unchanged.
- `catalog_ref` still present — `.name` untouched.
- Freeform motors never bound — out of scope (no G5 clear on that path for catalog_ref).
- Component-driven DSE apply that replaces whole spec — out of scope (already different spec).

### 2.3 Identity / readiness unchanged

- `catalog_ref is None` after clear — **unchanged**
- `_bom_sku_resolved` → `sku_resolved=False` — **unchanged**
- `classify_component` / readiness verdicts — **unchanged**
- G5 **when** to invalidate — **unchanged**

### 2.4 Label string

Pick **one** constant string for the motor-diverged case; document in implementation report. Must **not** match a live library SKU (`default_library.has_motor(name)` must be false). Must **not** imply a resolved catalog binding.

---

## 3. Implementation slices (G24D-1 … G24D-5)

### G24D-1 — Motor name clear (`catalog_bind.py`)

In motor divergence `model_copy`, add `.name` update per §2.

### G24D-2 — Tests (`tests/test_impl_d_sku_bom.py` + minimal new cases)

1. **Update** `test_frankenstein_entry_after_g5_divergence_is_not_resolved`:
   - Still assert `catalog_ref is None`, `sku_resolved is False`, no `[sku]` in BOM line.
   - **Change** `.name` assertion: must **not** equal original SKU; must equal chosen honest label.
   - **Disclose** assertion change in report (required — existing test today encodes stale behavior).

2. **`test_motor_name_unchanged_when_catalog_ref_preserved`** — no divergence → name unchanged.

3. Optional: **`test_battery_divergence_does_not_rename_motor`** — battery branch untouched.

### G24D-3 — Integration smoke

Reuse investigation §6.1 path via orchestrator if lightweight, or unit-level `invalidate_diverged_catalog_refs` only (sufficient for micro-IC).

### G24D-4 — CLI probe (`scripts/cli_probe_frankenstein_name_clear.py`)

| Step | Pass criterion |
|---|---|
| 1 | Bind motor → explore → `"aplica la mejor"` abstract `#1` (diverges) |
| 2 | `catalog_ref is None` |
| 3 | Motor `.name` ≠ original SKU string |
| 4 | `estado`/`format_bom_lines` motor line does not display old SKU as name |
| 5 | `sku_resolved` still false; no `[sku]` bracket |

Target: **5/5 PASS**.

### G24D-5 — Implementation report

`.jes/artifacts/implementation_report_frankenstein_name_clear.md`

---

## 4. Files — expected touch set

| File | Change |
|---|---|
| `src/jarvis/core/catalog_bind.py` | G24D-1 only |
| `tests/test_impl_d_sku_bom.py` | G24D-2 |
| `scripts/cli_probe_frankenstein_name_clear.py` | G24D-4 (new) |

**Must NOT change:**

- `invalidate_diverged_catalog_refs` divergence **conditions**
- `design_explorer.py`, G24-A, G24C selection, `_score_candidate`
- `format_bom_lines` identity rules (display fix is at source `.name`, not BOM heuristics) — unless probe proves source fix insufficient (then disclose)
- `pyproject.toml` version

---

## 5. Explicit non-goals

- Clearing `.name` on every `catalog_ref=None` motor globally (only G5 divergence path)
- Renaming battery components on divergence
- Fixing Continuity catalog-gap suggestions (separate debt)
- IC C scope
- Version bump alone

---

## 6. Acceptance (Cursor review)

**PASS** if:

- §6.1 repro: post-divergence `.name` is honest; BOM/`estado` no longer show stale SKU as name
- G5 semantics preserved: `catalog_ref` cleared same as before; `sku_resolved=False`
- Existing frankenstein BOM test updated with **disclosed** assertion change
- Probe **5/5**; full suite green
- **Zero** changes outside touch set

**FAIL** if:

- G5 invalidate conditions change
- Readiness/BOM `[sku]` rules weakened
- Bundled with IC C in one undifferentiated diff without review clarity

---

## 7. Queue

```text
IC D PASS (may parallel IC C)
  ↓
Combined checkpoint with IC C → 0.3.x (Engineer ★6)
```

---

**End of contract.**
