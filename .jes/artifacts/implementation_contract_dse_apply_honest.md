# Implementation Contract — DSE apply honesto (nameplate W + battery SKU)

**Project:** Jarvis  
**Date:** 2026-09-03  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** JES / Cursor against this IC after Claude reports

**Status:** RATIFIED (Engineer “Empecemos por DSE apply honesto”, 2026-09-03). **Claude implements this file only. JES does not edit `src/`.**

**Type:** Apply-path honesty. **Not** new physics. **Not** a new ranker. **Not** Impl C battery catalog DSE (C3). **Not** G24-B `_score_candidate`. **Not** Conversation Engine.

**Walk (Engineer CLI, `autonomia-15min`):** after watts-recovery pick `sunnysky_r2305_2500` (220 W nameplate) + `lipo_4s_5000mah` (74 Wh, `catalog_ref` set):

```text
modificar bateria → optimiza para autonomía → aplica la mejor
```

Applied mixed params-delta (`battery_capacity_wh_factor: 2.0`, `motor_power_w_factor: 0.75`):

```text
battery_capacity_wh: 74 → 148
battery_mass_kg: 0.498 → 0.987     (150 Wh/kg heuristic)
motor_power_w: 220 → 165            (invented, below nameplate)
battery name still lipo_4s_5000mah · properties 74 Wh · catalog_ref null
motor still sunnysky_r2305_2500 with catalog_ref · component still 220 W
L0 autonomía 13.5 min (4×165 W arithmetic, not hover OP)
```

148 Wh is the catalog energy of `lipo_4s_10000mah` (980 g). Apply did not bind that SKU. G5 cleared battery identity because params Wh ≠ component Wh. G5 does **not** compare `motor_power_w`, so the motor SKU survived next to invented watts.

---

## 0. You

- Edit only files in §5.
- Do **not** change `DesignExplorer` scoring, `EXPLORATION_GRIDS`, G24-B `_score_candidate`, or Impl C motor catalog candidate generation.
- Do **not** invent watts, SKUs, or packs. Do **not** add catalog JSON rows.
- Do **not** call `set_motor_component` as a side effect except the existing `set_battery_component` MOP-2 hook (already careful; do not weaken `test_battery_pick_does_not_regress_already_resolved_propulsion_op`).
- Do **not** mutate Engineer `workspace/`.
- Full suite green. Zero weakened tests.
- After you finish: write `implementation_report_dse_apply_honest.md`.

---

## 1. Intent

When the user applies a **params-only** DSE candidate (`best.params_delta`, not `components_delta`):

1. If a catalog motor is bound and that SKU **declares** `max_watts`, the applied `motor_power_w` **is the nameplate**. DSE must not write a lower (or different) consumption and keep the SKU.
2. If the applied `battery_capacity_wh` equals **exactly one** library pack `energy_wh`, bind that SKU (name, `catalog_ref`, catalog mass, cells). Do not leave `lipo_4s_5000mah` + 148 Wh + `catalog_ref: null`.
3. If Wh matches **no** pack: apply the parametric Wh (today’s `_apply_delta` + G5 clear). CLI must say it is parametric, not a pack.
4. If Wh matches **two or more** packs: **refuse** the apply (no state mutation). Do not pick a SKU in silence.

Explore list ranking may still show the mixed row as `#1`. This IC does **not** re-rank. Apply of that row is honest; the apply message discloses W kept at nameplate. Preview score ≠ post-apply L0 is expected and correct.

`components_delta` candidates (invented 300/500/800/1200 Wh, Impl C motors) stay on today’s apply path. C3 battery catalog DSE remains deferred.

---

## 2. Locked behavior

All of this runs inside `orchestrator._handle_apply_exploration`, **params-only branch only**, after `_apply_delta` produces `canonical_params` and **before** calculate/simulate/save.

Reuse existing writers. Prefer small pure helpers in `catalog_bind.py` (same family as `invalidate_diverged_catalog_refs` / `bind_battery_from_catalog`). Orchestrator calls them; do not duplicate bind/mass math in CLI.

### 2.1 Nameplate `motor_power_w`

**When** (all):

- params-only candidate;
- `components["motors"].catalog_ref.family == "motor"`;
- library `get_motor(sku).max_watts is not None`.

**Then:** set `canonical_params["motor_power_w"]` to that `max_watts` (float, same convention as bind/pick — do not invent a new rounding scheme). Ignore `motor_power_w_factor` / any delta that would change W.

**When false** (unbound motor, or bound SKU with `max_watts is None` such as `emax_rs2205s_2300`): leave `_apply_delta` watts as today. Do not invent a nameplate.

Do **not** clear motor `catalog_ref` because W was stripped. G5 thrust comparison stays as today.

Do **not** change `per_motor_max_thrust_n` here.

### 2.2 Battery SKU bind on exact Wh

Helper (name free), library via `default_library` / injected `ComponentLibrary` only — no second JSON reader:

```text
find unique battery SKU whose energy_wh matches params battery_capacity_wh
epsilon: 1e-6 (same order as G5)
return sku if exactly one match, else None
```

v1 seed energies are unique (`74.0` → `lipo_4s_5000mah`, `148.0` → `lipo_4s_10000mah`). Helper must still return `None` on 0 or 2+ matches.

**Exactly one SKU:**

1. `spec = bind_battery_from_catalog(sku, base=existing battery spec or None)`
2. `updated_project = set_battery_component(state, spec, capacity_wh=library energy_wh)`  
   Use the project state that already has current components (base `project_state` or `updated_project` if already copied). This is the **only** battery writer — catalog mass (`mass_g/1000`), cells, `catalog_ref`, name = SKU.
3. Refresh `canonical_params` from that state’s `current_parameters` (so calc sees catalog mass, not the 150 Wh/kg heuristic from `_apply_delta`).

Walk lock: 74 × 2.0 → 148.0 → `lipo_4s_10000mah`, `battery_mass_kg = 0.98` (980 g), `catalog_ref` set, component properties Wh = 148. **Not** name `lipo_4s_5000mah` with 148 Wh.

**Zero SKUs:** do not bind. Let existing `invalidate_diverged_catalog_refs` clear a stale pack identity. Parametric Wh and heuristic mass remain.

**Two or more SKUs:** return error from `_handle_apply_exploration` **before** save (same shape as index-out-of-range: `status=error`, `action=apply_exploration_result`, no disk write). Locked message:

```text
Hay más de un pack de catálogo con {Wh} Wh. No se aplica en silencio. Elige una batería del catálogo o un candidato sin ambigüedad.
```

(`{Wh}` = the applied capacity, formatted like other CLI numbers in this function — do not invent a new unit.)

### 2.3 Order vs G5

Keep G5 lock: `invalidate_diverged_catalog_refs` **before** `sync_motors_component_from_params`.

Insert §2.1 and §2.2 **before** G5 so that:

- nameplate W is in `canonical_params` before calc;
- a unique SKU bind writes component Wh = params Wh, so G5 **does not** clear the new `catalog_ref`;
- unmatched Wh still diverges vs old pack properties, so G5 still clears the old ref.

Do not change G5’s motor comparison (still `thrust_n` vs `per_motor_max_thrust_n`). Do not add `motor_power_w` to G5 in this IC.

### 2.4 Apply CLI disclosure (params-only)

Append to the existing apply confirmation (do not replace change lines):

**If** nameplate W was forced (§2.1) **and** `_apply_delta` would have written a different `motor_power_w`:

```text
El motor de catálogo {sku} declara {W} W de placa. No se ha escrito un consumo inferior.
```

**If** a unique battery SKU was bound:

```text
Batería vinculada a {sku} ({Wh} Wh, masa de catálogo).
```

**If** Wh changed **and** no unique SKU:

```text
{Wh} Wh no coinciden con un pack del catálogo. La capacidad es paramétrica; catalog_ref de batería no queda vinculado.
```

Do not emit the parametric sentence when Wh did not change.

### 2.5 Unchanged

- G24-A apply-by-index, explore generation, scoring, viable sort.
- Impl C motor `components_delta` apply.
- Watts-recovery IDLE, G21 covering-with-W, T1 / T1+2, stale-energy recalc Continuity.
- Block Closure formula, Option B, `_derive_overall`.
- `set_battery_component` MOP-2 voltage revalidation (do not make it unconditional).

---

## 3. Tests (mandatory)

Do not mutate Engineer `workspace/`. Use tmp projects.

| File | What |
|---|---|
| `tests/test_dse_apply_honest.py` **new** | **Walk mixed apply:** project with `sunnysky_r2305_2500` bound, `lipo_4s_5000mah` bound, `motor_power_w=220`, `battery_capacity_wh=74`. Seed `session.last_exploration_result` with a params-only viable[0] whose `params_delta` is `{battery_capacity_wh_factor: 2.0, motor_power_w_factor: 0.75}` (minimal `ExplorationResult` / candidate; reuse patterns from `tests/test_design_explorer.py` / `tests/test_impl_c_catalog_aware_dse.py`). `_handle_apply_exploration()` → `motor_power_w == 220`, battery `catalog_ref.sku == "lipo_4s_10000mah"`, `battery_capacity_wh == 148`, `battery_mass_kg == 0.98`, component name is the 10000 SKU not `lipo_4s_5000mah`, motor `catalog_ref` still r2305. Message contains the nameplate sentence and the battery-vinculada sentence. Does **not** leave `catalog_ref` null on battery. |
| same | **Unmatched Wh:** same fixture, delta `{battery_capacity_wh_factor: 2.5}` (185 Wh). Apply succeeds. `battery_capacity_wh == 185`, battery `catalog_ref is None`, motor W still 220. Message contains the parametric sentence. |
| same | **Wh-only bind:** delta `{battery_capacity_wh_factor: 2.0}` only. Bind `lipo_4s_10000mah`, `motor_power_w` unchanged 220. |
| same | **Unbound motor:** no motor `catalog_ref`; `motor_power_w=220`; same mixed delta. W **does** become 165 (today). Battery 148 still unique-binds `lipo_4s_10000mah` if Wh started at 74 with a bound 5000 pack **or** if you start unbound battery — pick one fixture and document it; do not accidentally require a catalog motor. |
| `tests/test_dse_apply_honest.py` or helper unit tests in same file | `find_unique_battery_sku_for_energy_wh(148.0) == "lipo_4s_10000mah"`; `74.0 == "lipo_4s_5000mah"`; `185.0 is None`. 2+ matches: helper returns `None`; orchestrator refuse path via monkeypatch of the helper to a 2-hit stand-in **or** a dedicated fake — apply `status=error`, state Wh/W unchanged. |
| `tests/test_design_explorer.py` | Existing `_handle_apply_exploration` edge cases **green** (no prior exploration, empty viable, bad index). |
| `tests/test_impl_c_catalog_aware_dse.py` | Impl C apply path **green** (motor `components_delta` identity). |
| `tests/test_battery_catalog_bind_ux.py` | `test_battery_pick_does_not_regress_already_resolved_propulsion_op` **green**. |
| `tests/test_dse_motor_op_dual_truth.py` | Apply still does not invent a Discrete OP. |

---

## 4. Non-goals

```text
EXPLORATION_GRIDS / _score_candidate / viable re-sort
Impl C C3 (battery catalog candidates in explore)
Tier 3 joint motor+prop+battery
Option B / _derive_overall / Energy PASS rewrite
Block Closure PARCIAL copy
G24-C explore CTA rewrite (apply disclosure only)
Inventing W as user CTA
Catalog JSON expansion
Mutating Engineer workspace/
Auto-calcular beyond today's apply (apply already calc+sim)
```

---

## 5. Files

| File | Role |
|---|---|
| `src/jarvis/core/catalog_bind.py` | Unique-Wh SKU helper; nameplate W restore helper (pure) |
| `src/jarvis/core/orchestrator.py` | `_handle_apply_exploration` params-only: §2.1–§2.4 then existing G5/sync/save |
| `src/jarvis/core/component_writers.py` | **Only if** `set_battery_component` must be called from apply — prefer **no** edit; call the existing writer |
| `tests/test_dse_apply_honest.py` | New |
| `docs/IMPLEMENTATION_TASKS.md` | Sync after report |
| `.jes/state/engineering_state.json` | Sync after report |

Do not add a new domain module. Do not put bind logic in `adapters/cli/main.py`.

---

## 6. Acceptance

Walk-equivalent tmp: `aplica la mejor` on mixed 2.0×Wh + 0.75×W with r2305 + 4S 5000 bound:

- `motor_power_w` stays **220**, not 165;
- battery is **`lipo_4s_10000mah`** with `catalog_ref`;
- mass is catalog **980 g**, not 0.987 heuristic;
- apply message names both facts;
- 185 Wh apply is parametric + `catalog_ref` null + W still 220;
- suite green.

---

## 7. After you finish

Write `.jes/artifacts/implementation_report_dse_apply_honest.md` (files, tests run, physics/scoring unchanged). Stop. JES reviews.
