# Implementation Contract — Phase 2 P2-1 Lookup Operating Point

**Project:** Jarvis  
**Date:** 2026-08-21  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)

**Status:** READY FOR CLAUDE

**Type:** First Phase 2 slice — resolve thrust from curated `operating_points[]` with provenance; feed existing calc/sim via `per_motor_max_thrust_n`. No Physics Engine subsystem. No sim rewrite.

**Investigation:** [`.jes/artifacts/investigation_report_phase2_physical_propulsion.md`](investigation_report_phase2_physical_propulsion.md) — **CLOSED**  
**Investigation review:** [`.jes/artifacts/investigation_review_phase2_physical_propulsion.md`](investigation_review_phase2_physical_propulsion.md) — **PASS** · ★1–★5 RATIFIED  
**★6 dataset:** [`.jes/artifacts/phase2_star6_operating_point_validation_case.md`](phase2_star6_operating_point_validation_case.md) — **APPROVED (final)**  
**Checkpoint base:** tag **`checkpoint-impl-d`** · commit `24fa7ba`

**Workflow:** Claude implements **P2-1 → P2-6 in order** + report → Cursor review → CLI probe → commit/tag if Engineer asks. **No version bump in this cut.**

---

## 0. Engineer ratification (locked)

| ★ | Decision |
|---|---|
| **★1** | Provenance lives on Operating Point (`source_type`), **not** by widening `PropertyValue.source` |
| **★2** | **Option A — Lookup OP** (small curated table); defer bind-combo UX / full electro-mech |
| **★3** | G26/G27 **not** prerequisites — stay independent debt |
| **★4** | G24 **deferred** |
| **★5** | Provenance surface details in this IC (see §4) |
| **★6** | Dataset final in `phase2_star6_…md` — **only** those numbers; never invent |

**Additional locks (Engineer 2026-08-21 final):**

- EMAX test-table OPs attach to **`emax_rs2205s_2300`** (RS2205**S**), **not** `emax_rs2205_2300`.
- Keep `emax_rs2205_2300` and `sunnysky_r2305_2500` **unchanged** (legacy Model-1).
- Add **`sunnysky_r2205_2500`** for SunnySky OP-3.
- OP-0 is **`fallback_only`** — resolver must return `resolution_type=fallback_operating_point` (code rule, not docs-only).
- Multi exact match → **max `thrust_n`** + `selection_reason="v1_max_thrust"` (provisional).
- `efficiency_gf_per_w` is **g/W**, never η∈[0,1].
- **Do not** modify `calculation_engine` / `FeasibilitySimulator` control flow in this cut.
- **Do not** reopen Impl D BOM schema.
- **Do not** fix G24–G27 / Create-handoff / `req_lines` in this cut.
- **Do not** invent a parallel Physics Engine module.

**Architecture constraint:**

> Minimum change: seed data + pure lookup + extend existing thrust bridge. Populate `per_motor_max_thrust_n` from OP when resolved; otherwise preserve today’s numeric behavior (legacy estimate).

---

## 1. Problem / intent

Today: bound motor → bare `MotorSpec.thrust_n` → `per_motor_max_thrust_n` (context-free).

**Target P2-1:**

```text
catalog_ref (motor) [+ propeller catalog_ref] [+ voltage]
        ↓
resolve_operating_point → resolution_type + thrust + provenance
        ↓
per_motor_max_thrust_n  (existing calc/sim)
        ↓
estado shows quality of evidence (exact / fallback / legacy)
```

---

## 2. Slice P2-1 — Seed catalog data

### 2.1 Motors (`library/motores/_datos.json`)

**ADD** `emax_rs2205s_2300`:

- Point fields for Model-1 compatibility (kv/weight/watts/compatible_prop_inch consistent with RS2205S 2300KV class — use published class facts; **do not** invent a fake peak that conflicts with OP rows without labeling).
- Recommended Model-1 `thrust_n`: use **OP-0 thrust 10.042** only if also documented as headline max, **or** leave a conservative peak clearly subordinate to OP lookup — prefer setting `thrust_n` to the same headline **1024 gf → 10.042 N** with note that OP lookup supersedes when available.
- `manufacturer` / `model` / `source_url` from ★6 refs.
- `operating_points`: OP-0, OP-1, OP-2 exactly as ★6 final (dict rows).

**ADD** `sunnysky_r2205_2500`:

- Model-1 fields from published R2205 2500KV class (weight ~30 g, kv 2500, compatible 5").
- `operating_points`: OP-3 only.
- Do **not** modify `sunnysky_r2305_2500`.

**DO NOT MODIFY** `emax_rs2205_2300` OP-wise (no RS2205S table copy).

### 2.2 Propellers (`library/helices/_datos.json`)

**ADD:**

| SKU | Fields (minimal) |
|---|---|
| `hq_5045_bn` | `diameter_in: 5.0`, `pitch_in: 4.5`, `tags: ["hq5045","bn","5inch"]`, `mass_g` if known else omit/heuristic small |
| `gf_5045x3` | `diameter_in: 5.0`, `pitch_in: 4.5`, `tags: ["gf5045","tri-blade"]` |

No fabricated `ct`/`cp` required for P2-1 (lookup does not use aero model).

### 2.3 OP row JSON shape (in `operating_points[]`)

Each dict must include at least:

```text
propeller_sku | null
voltage_v
thrust_n
rpm | null
current_a | null
power_w | null
efficiency_gf_per_w | null
fallback_only: bool
source_type: "manufacturer_test" | ...
confidence: float
source_reference: str
source_note: str
```

Use ★6 final numbers verbatim (OP-1…OP-3, OP-0).

**Acceptance:** library loads; `default_library.get_motor("emax_rs2205s_2300")` returns 3 OP rows; `sunnysky_r2205_2500` returns 1; legacy SKUs still load.

---

## 3. Slice P2-2 — `resolve_operating_point` (`library.py`)

### 3.1 API (pure)

```python
@dataclass(frozen=True)
class ResolvedOperatingPoint:
    thrust_n: float
    resolution_type: Literal[
        "exact_operating_point",
        "fallback_operating_point",
        "legacy_estimate",
    ]
    source_type: str
    confidence: float
    selection_reason: str | None  # e.g. "v1_max_thrust" | None
    voltage_v: float | None
    rpm: float | None
    current_a: float | None
    power_w: float | None
    efficiency_gf_per_w: float | None
    propeller_sku: str | None
    fallback_only: bool
    source_reference: str | None
    source_note: str | None
    motor_sku: str


def resolve_operating_point(
    motor_sku: str,
    *,
    propeller_sku: str | None = None,
    voltage_v: float | None = None,
    library: ComponentLibrary | None = None,
) -> ResolvedOperatingPoint | None:
    ...
```

Return `None` only if motor SKU missing from library. If motor exists but no OP match → still return **`legacy_estimate`** from `MotorSpec.thrust_n` (so callers always get a typed resolution for known motors).

### 3.2 Match rules

1. **Exact:** `fallback_only is not True` AND `propeller_sku` equals row’s `propeller_sku` AND (`voltage_v` is None **or** abs(voltage − row.voltage_v) ≤ ε, ε=0.05 default).  
   If multiple → pick **max `thrust_n`**, set `selection_reason="v1_max_thrust"`, `resolution_type="exact_operating_point"`.
2. **Fallback:** rows with `fallback_only is True`; prefer voltage match if `voltage_v` given; else any fallback row for motor. `resolution_type="fallback_operating_point"`.
3. **Legacy:** `MotorSpec.thrust_n`, `resolution_type="legacy_estimate"`, `source_type="estimated"`, `fallback_only=False`, confidence low (e.g. 0.5), `source_note` explaining bare catalog peak.

**Hard rule:** a `fallback_only` row must **never** be returned as `exact_operating_point`.

### 3.3 Acceptance

- OP-1 alone match → 9.1986 N exact.  
- OP-1+OP-2 both match → 9.7086 N + `v1_max_thrust`.  
- Motor bound, no prop → OP-0 → `fallback_operating_point`, 10.042 N.  
- `emax_rs2205_2300` (legacy, no OP) → `legacy_estimate` with its existing `thrust_n`.  
- `sunnysky_r2305_2500` unchanged behavior path → legacy.

---

## 4. Slice P2-3 — Bridge in `set_motor_component`

File: `component_writers.py` (only at existing Impl C thrust-bridge site).

When applying a motor `spec`:

1. If `spec.catalog_ref` is motor family and sku present → call `resolve_operating_point(sku, propeller_sku=…, voltage_v=…)`.
2. **Propeller sku:** from `components["propellers"].catalog_ref.sku` if bound; else `None`.
3. **Voltage:** best-effort from bound battery (`cells×3.7` or `nominal_voltage`) or `current_parameters` if a clear voltage key already exists; else `None` (still allow fallback/exact without V when row matches).
4. Write `per_motor_max_thrust_n = resolved.thrust_n`.
5. Also update `spec.properties["thrust_n"]` to the resolved thrust when resolution is exact or fallback (so component and params stay coherent) — **with care:** do not clear `catalog_ref`. Prefer updating the property value while keeping catalog identity.
6. Persist inspectable provenance **without** widening `PropertyValue.source` Literal:
   - Preferred: `current_parameters["propulsion_resolution"] = { resolution_type, source_type, confidence, selection_reason, source_reference, fallback_only, … }` (plain dict, JSON-serializable).
   - Optional mirror: `components["motors"].properties["operating_point_summary"]` as a string PropertyValue for views — only if cheap; params dict is enough for P2-1.

**On OP miss / freeform motor:** keep today’s Impl C bridge behavior (spec `thrust_n` → params) and set `propulsion_resolution` to `legacy_estimate` when catalog_ref present but only legacy path used.

**Acceptance:** Binding `emax_rs2205s_2300` without propeller → params thrust = 10.042, resolution=`fallback_operating_point`. With propeller `hq_5045_bn` + ~16 V → exact path (max of OP-1/2 if both match).

---

## 5. Slice P2-4 — Surface in `estado` / CLI

Minimal, honest display when `propulsion_resolution` present, e.g. under Continuity evidence or near BOM/motors:

```text
Propulsión (evidencia): exact_operating_point · manufacturer_test · 9.71 N
```

or for fallback:

```text
Propulsión (evidencia): fallback_operating_point · manufacturer_test · 10.04 N (sin hélice de catálogo)
```

or legacy:

```text
Propulsión (evidencia): legacy_estimate · estimated · …
```

**Do not** claim “dato de ensayo completo” for fallback/legacy.  
Prefer extending `render_startup_context` only — no Continuity ranking changes.

---

## 6. Slice P2-5 — Tests

New file e.g. `tests/test_phase2_lookup_operating_point.py`:

1. Exact OP-1 match (single row conditions).  
2. Dual OP-1/OP-2 → max thrust + `v1_max_thrust`.  
3. Fallback OP-0 when no propeller.  
4. Legacy path for `emax_rs2205_2300` / unbound OP motor.  
5. `fallback_only` never classified as exact.  
6. Bridge: `set_motor_component` writes params + `propulsion_resolution`.  
7. Regression: existing bind of `sunnysky_r2305_2500` still works (legacy), no accidental R2205 data.

Named regressions from Impl C/D catalog bind / thrust bridge must stay green.

---

## 7. Slice P2-6 — CLI probe

`scripts/cli_probe_phase2_lookup_op.py`:

1. Create project → bind **`emax_rs2205s_2300`** (wizard pick by number once listed).  
2. `estado` → fallback resolution visible; thrust ≈ 10.04 N.  
3. Declare/bind propeller `hq_5045_bn` if path exists; else set catalog_ref on propellers via test harness inside probe — prefer real UX if available, else documented state patch **only in probe**.  
4. Assert exact resolution and thrust ∈ {9.1986, 9.7086} with max policy → **9.7086**.  
5. Confirm `sunnysky_r2305_2500` still bindable as legacy (optional short check).

---

## 8. Forbidden

- Parallel `physics_engine.py` / second calc authority  
- Changing sim formulas / ERF verdict wiring / Continuity ranking  
- Copying RS2205S OPs onto `emax_rs2205_2300`  
- Overwriting `sunnysky_r2305_2500` with R2205 datasheet  
- Treating `efficiency_gf_per_w` as 0–1 η  
- Presenting OP-0 as exact OP  
- G24–G27 / Create-handoff / version bump  
- Inventing additional OP rows beyond ★6  

---

## 9. Implementation report (required)

`.jes/artifacts/implementation_report_phase2_lookup_operating_point.md`:

1. Files changed  
2. Behavior changed / unchanged  
3. ★ compliance + SKU add list  
4. Tests + commands + results  
5. CLI probe result  
6. Remaining risks (multi-OP current limits → future Phase 2.x; propeller bind UX)

---

## 10. Exit criterion

P2-1 complete when:

1. Seeds + resolver + bridge + surface + tests + probe green.  
2. Exact / fallback / legacy distinctions enforced in code.  
3. Cursor review PASS (or PASS WITH NOTES).  
4. Engineer may checkpoint / later version bump — **not part of this IC**.

---

## 11. Queue after implementation

```text
Claude implements P2-1…P2-6
        ↓
Cursor review
        ↓
Engineer CLI walk (optional) → checkpoint / decide version bump
        ↓
Later: propeller-bind UX · ESC · current-limited OP selection · G27
```

---

**End of contract.**
