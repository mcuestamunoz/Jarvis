# Investigation Report — Project Closure / Assembly Ready (Physical Catalog)

**Contract:** [`investigation_contract_project_closure_assembly_ready.md`](investigation_contract_project_closure_assembly_ready.md)
**Checkpoint base:** `v0.3.0` / `checkpoint-propeller-catalog-bind` (`2efe1c2`)
**Investigator:** Claude Code
**Status:** Complete. No `src/` changes, no test changes, no library rows added — investigation only, per contract §2.

---

## 1. Executive summary

`build_engineering_readiness` (`src/jarvis/core/engineering_readiness.py:1075`) was run live against two real fixtures in `workspace/`. Results:

- **Fixture 1** (`crear-un-dron-de-autonomia-con-payload-1kg-184eac8b7789`, the Engineer's post-v0.3.0 walk project): `NOT_ASSEMBLY_READY`. 6 subsystems INCOMPLETE (`requirements`, `architecture`, `structure`, `energy`, `electronics`, `control`, `bom`), 2 PASS (`propulsion`, `catalog`). 6 gaps, all MEDIUM severity — zero HIGH.
- **Fixture 2** (`1-324107ef7006`, an "almost ready" project): `NOT_ASSEMBLY_READY` with **8 of 9 subsystems PASS and zero gaps**. The **sole** blocker is `requirements` (`INCOMPLETE`) — because `parsed_constraints == {}` even though `objective`/`restrictions` exist and the sim already PASSes at 5.0455 min autonomy.

Fixture 2 is a direct, code-level proof of the contract's central worry: **a project can be physically complete, catalog-honest, and simulation-PASS, and still be permanently blocked from `ASSEMBLY_READY` by the Requirements/G26 gap alone.** No BOM work, no battery UX, no ESC catalog changes it.

**Recommended sequence (5 lines):**

1. **Cut 1 — Requirements closure** (G26 root cause + the underlying "no explicit constraint" design gap). Smallest, highest-leverage, unblocks Fixture-2-shaped projects outright.
2. **Cut 2 — Battery catalog UX** (bind_battery_from_catalog is already wired end-to-end to calc/energy; only a CLI pick surface is missing — mirrors the propeller-bind precedent exactly).
3. **Cut 3 — G27 hardening**, scoped narrowly to the free-text battery parser (independent of Cut 2's pick UX, but must land before or alongside it so a picked SKU can't be silently overwritten by a bad free-text follow-up).
4. **Cut 4 — Closure policy/BOM honesty tweaks** (propeller `sku_resolved` bug found live during this investigation; freeform-tolerant "assembly ready v1" rollup semantics ratified by Engineer ★).
5. **G24 stays deferred** — proven not a closure prerequisite (§1.11); it is an identity-honesty/UX debt item, not a rollup blocker.

This is **Option D** from §1.11 (split cuts by concern), not the assumed `G27 → G26 → battery UX` linear order.

---

## 2. ASSEMBLY READY blocker inventory (§1.1)

### 2.1 Entry point trace

```text
build_engineering_readiness(project_state)                 engineering_readiness.py:1075
  ├─ derive_physical_requirements(project_state)            project_closure.py:44
  ├─ build_component_bom(project_state)                     project_closure.py:268
  ├─ resolve_motor_catalog_surface(project_state, req)       engineering_readiness.py:198
  ├─ derive_architecture_progress(project_state)              engineering_readiness.py:385
  ├─ evaluate_electrical_compatibility(project_state)         electrical_compatibility.py:293
  ├─ 10 gap-builder calls → gaps: list[Gap]                   engineering_readiness.py:1094-1107
  ├─ prioritize_gaps(gaps)                                    engineering_readiness.py:836
  ├─ per-subsystem: _EVIDENCE_BUILDERS[key](ctx) → _derive_subsystem_verdict  engineering_readiness.py:1126-1128
  └─ _derive_overall(gaps, subsystems)                        engineering_readiness.py:1057
```

Inputs are exactly `project_state` plus deterministic authority calls made from inside the module — confirmed no I/O, no LLM, no Continuity-as-input (the module's own header docstring states the one-way rule; `_Context` at `engineering_readiness.py:866-877` is built entirely from `project_state`-derived values).

`_derive_overall` (`engineering_readiness.py:1057-1069`):

```python
if any(g.severity == "HIGH" for g in gaps):
    return "NOT_ASSEMBLY_READY"
for readiness in subsystems.values():
    if readiness.verdict == "PASS": continue
    if readiness.verdict == "WARNING" and readiness.warning_type in ACCEPTED_WARNING_TYPES: continue
    return "NOT_ASSEMBLY_READY"
return "ASSEMBLY_READY"
```

So `ASSEMBLY_READY` requires: **zero HIGH-severity gaps anywhere**, AND **every one of the 9 subsystems is PASS or the single accepted WARNING type** (`CATALOG-GAP-DEMOTED-POST-PASS`, `engineering_readiness.py:120`, restricted to `catalog`/`propulsion` only, `engineering_readiness.py:121`). There is no BOM-only or Requirements-only carve-out — this is a strict AND across 9 independently-computed lines.

### 2.2 Fixture 1 — live run (`crear-un-dron-de-autonomia-con-payload-1kg-184eac8b7789`)

| Subsystem | Verdict | Blocked by |
|---|---|---|
| requirements | INCOMPLETE | (no gap — `evidence.defined=False`, falls through `_derive_subsystem_verdict`'s `if not evidence.defined` branch, `engineering_readiness.py:1048`) |
| architecture | INCOMPLETE | `GAP-ARCH-BLOCK-INCOMPLETE` |
| structure | INCOMPLETE | `GAP-BOM-INCOMPLETE-COMPONENT:frame` |
| propulsion | **PASS** | — |
| energy | INCOMPLETE | `GAP-BOM-INCOMPLETE-COMPONENT:battery` |
| electronics | INCOMPLETE | `GAP-BOM-INCOMPLETE-COMPONENT:esc` |
| control | INCOMPLETE | `GAP-BOM-INCOMPLETE-COMPONENT:flight_controller`, `:sensors` |
| catalog | **PASS** | — |
| bom | INCOMPLETE | (all 5 incomplete-component gaps above) |

6 gaps, **all MEDIUM**. `requirements` is INCOMPLETE with **no gap object at all** — it's a silent "not yet defined" state, not a registered gap; `restrictions="no"` (a placeholder, correctly not matched by `_AUTONOMY_CONSTRAINT_RE`/`_WEIGHT_CONSTRAINT_RE`) and `objective` names no numeric target either, so `parsed_constraints={}` honestly — **this fixture has never had a constraint stated, which is different from G26's bug** (see §3).

**Blocker → root cause → fix class:**

| Blocker | Gap ID | Root cause | Fix class |
|---|---|---|---|
| requirements INCOMPLETE | none | no numeric constraint ever declared (or G26, if the user tried and failed) | routing (G26) + policy (no-constraint semantics, §7 ★) |
| architecture INCOMPLETE | GAP-ARCH-BLOCK-INCOMPLETE | `energy`/`structure`/`control` blocks not "complete" per `_block_progress_status` | UX (finish component wizards) |
| structure/energy/electronics/control INCOMPLETE | GAP-BOM-INCOMPLETE-COMPONENT:{frame,battery,esc,flight_controller,sensors} | components at `completeness="low"` (stub) | UX/catalog — declare or bind each |
| bom INCOMPLETE | (rollup of above) | same 5 stub components | same |

`propulsion` and `catalog` are already PASS here — motor+propeller are catalog-bound with an exact operating point (`propulsion_resolution.resolution_type == "exact_operating_point"`, thrust 9.7086 N/motor), proving the v0.3.0 propeller-bind checkpoint's physics claim end to end.

### 2.3 Fixture 2 — live run (`1-324107ef7006`, "almost ready")

| Subsystem | Verdict |
|---|---|
| requirements | **INCOMPLETE** (sole non-PASS line) |
| architecture / structure / propulsion / energy / electronics / control / catalog / bom | **PASS** (all 8) |

**Zero gaps of any kind.** `motors` is catalog-bound (`sunnysky_r2305_2500`); `battery` is **freeform**, `completeness="medium"`, `catalog_ref: null` — and `energy` still shows PASS (§5 discusses why). Sim: `status="pass"`, `autonomy_min=5.0455`. `objective="1"`, `restrictions="no"` — again no numeric constraint stated, so `parsed_constraints={}`.

This is the sharpest possible evidence for the contract's framing: **an otherwise fully-passing, honestly-declared, catalog-partial project is permanently `NOT_ASSEMBLY_READY` because of one line: `requirements`.** No propulsion fix, no BOM fix, no catalog expansion touches this. Only (a) the user stating a constraint, or (b) a routing fix that lets them state one mid-session (G26), changes this line.

I could not locate a workspace fixture named `autonomia-5540bda0ac16` (the project named in the G26/G27 finding docs) on disk — it does not exist in this checkout's `workspace/`. Fixture 2 is used as the "almost ready" comparison point instead; it is strictly cleaner (0 gaps vs. whatever `autonomia-5540bda0ac16` carried) and makes the same structural point more starkly.

---

## 3. G26 scope box (§1.2)

**What is the bug, precisely?** Two distinct things are conflated under "G26":

1. **No writer exists for "update the project-level `restrictions` constraint string mid-session."** `current_parameters["restrictions"]` is written exactly once, at project creation, by the initial wizard (`interactive_session.py:290`, `draft.model_copy(update={"restrictions": user_input})`). There is a second, unrelated `"restrictions"` concept — the iterate wizard's own per-iteration slot (`iterate_interactive_session.py:65`, prompt "¿Hay restricciones? (ej: mantener resistencia...)", written at `iterate_interactive_session.py:570` into `IterationDraft.restrictions`) — a DSE-candidate note, **not** wired back to `current_parameters["restrictions"]` or `parsed_constraints` at all. Neither path lets a user restate the top-level constraint after creation.
2. **The observed symptom** ("Parámetros aplicados: autonomia=15.0", `current_parameters["autonomia"]=15.0` invented) comes from `param_definition_session.py:862` (`f"Parámetros aplicados: {param_str}. Sistema recalculado."`) — a **different session flow** (the DEFINE_MISSING param-definition wizard used to fill missing architecture-block params) that writes whatever `param_str`/dict it is given directly into `current_parameters`. Grep confirms **zero** references to `is_derived` anywhere in `param_definition_session.py` — unlike `semantic_intent_adapter.adapt()` (`semantic_intent_adapter.py:151-159`), which does check `PARAMETER_REQUIREMENTS[canonical].is_derived` and correctly rejects `"autonomia"` with a redirect message (`parameter_requirements.py:171-184` registers `autonomia` as `is_derived=True` with a proper `derived_message`). The routing that got the user's turn into `param_definition_session` instead of the semantic-adapter-gated iterate path is upstream in `orchestrator.py`'s action classification and was not fully traced here (out of the contract's `src/` non-modification scope to chase further); what is confirmed is that **whichever path reaches `param_definition_session` bypasses the one place that already knows `autonomia` is derived.**

| Question | Answer |
|---|---|
| File:line, write path vs read path | Write: `param_definition_session.py:862` (no `is_derived` gate). Correct gate exists but isn't reached: `semantic_intent_adapter.py:151-159` + `parameter_requirements.py:171-184`. Read: `state_schema._parse_constraints`, `state_schema.py:20-54`, reads only `current_parameters["restrictions"]` / `objective`. |
| Subsystem/gap affected | `requirements` only. `_requirements_evidence.defined = bool(parsed_constraints)` (`engineering_readiness.py:882`) is the only reader of `parsed_constraints` in the whole readiness engine. |
| Does it affect calc/sim physics? | **NO.** `derive_physical_requirements` (`project_closure.py:44`) reads `parsed_constraints` only to populate `req["autonomy_target_min"]`/`req["max_mass_kg"]` — comparison targets for gap generation, not calculation inputs. `calculation_engine.py` never reads `parsed_constraints`. |
| Does it block ASSEMBLY READY alone? | **YES — Fixture 2 (§2.3) is a direct, live proof.** With 8/9 subsystems PASS and zero gaps, fixing G26 (or simply the user stating an achievable constraint) is the single remaining lever for that exact project shape. |
| Closure prerequisite or parallel polish? | **Closure prerequisite** — not optional polish. `_derive_overall` treats `requirements` exactly like every other subsystem; there is no "requirements is soft" carve-out in the rollup logic (`_derive_overall`, `engineering_readiness.py:1057-1069`) or in `ACCEPTED_WARNING_TYPES` (`engineering_readiness.py:120`, `requirements` is not `_G9B_ELIGIBLE_SUBSYSTEMS`). |

**G26 scope box:**

```text
Fixes:      the mid-session write path for the top-level constraint string
            (restrictions → parsed_constraints), and/or the is_derived gate
            gap in param_definition_session.
Unblocks:   requirements subsystem PASS for any project where the user states
            (or already stated) an achievable numeric constraint — including
            flipping Fixture-2-shaped projects straight to ASSEMBLY_READY.
Does NOT fix: any BOM/catalog/energy/electronics/control gap; does not
            change calc/sim physics at all.
```

**A second, related but distinct finding** (not "G26" per se, worth its own ★): even with G26 fixed, a project where the user genuinely **never states any constraint** (both fixtures: `restrictions="no"`, no numeric objective) stays `requirements.defined=False` forever — there is no "explicitly no constraint" satisfied state, only "not yet asked" and "asked and parsed." This is a closure-policy question, addressed in §7 (★9).

---

## 4. G27 role in closure (§1.3)

| Question | Answer |
|---|---|
| Root cause | Confirmed in `semantic_intent_adapter._parse_value` (`semantic_intent_adapter.py:259-276`): a bare regex `-?\d+(?:\.\d+)?` extracts the **first number found** in the LLM-proposed `valor`/`value` string, with no unit/context awareness. For input shaped like "LiPo 6S 10000mAh", if the LLM's own extraction places `"6"` (from "6S") into that field, this layer has no way to know "6" is a cell count, not Wh — it isn't a battery-chemistry parser, it's a generic numeric sanitizer shared by every iterate variable. |
| Catalog bind path — bypasses G27? | **Yes, cleanly.** `bind_battery_from_catalog(sku)` (`catalog_bind.py:78-123`) takes a **library key**, not free text — it reads `energy_wh`/`mass_g`/`chemistry`/`cells` straight from `library/baterias/_datos.json` via `ComponentLibrary.get_battery`. It shares zero code with `semantic_intent_adapter._parse_value`. A pick-UX battery flow (mirroring the propeller-bind pattern at `orchestrator.py:2579-2589`) would never touch G27's code path at all. |
| Energy subsystem — does catalog-bound battery work today? | **Yes, already wired end-to-end**, confirmed by test `test_bridge_battery_catalog_ref_voltage_takes_precedence` (`tests/test_phase2_lookup_operating_point.py:182-203`): `bind_battery_from_catalog(sku)` → `set_battery_component(ps, spec, spec_energy_wh)` writes `current_parameters["battery_capacity_wh"]`, `battery_mass_kg` (from the SKU's real `mass_g`, `component_writers.py:146-153`), and `battery_cell_count` (`component_writers.py:159-164`) atomically. §5 traces the rest of the chain. |
| Autonomy calc — inputs, honesty | `calculate_autonomy_min(battery_capacity_wh, total_power_w)` via `calculation_engine.py:164-178`. Inputs are `parameters["battery_capacity_wh"]` and `parameters["motor_power_w"] * motors`. It has no idea whether `battery_capacity_wh` came from a catalog SKU or a mis-parsed free-text "6" — **it is honest about its inputs, not about their provenance.** G27's silent-6-Wh bug corrupts the input before it ever reaches this function; the function itself is not the bug. |
| Closure role: before / after / parallel to battery UX? | **Parallel, with a coupling caveat.** Since bind bypasses G27's code path entirely, a battery pick UX (Cut 2, §8) can ship **without waiting for G27**. But G27 must still be fixed **before or alongside** that UX ships, because a user can follow up a correct catalog pick with a free-text iterate ("aumenta batería a 6S 10000mAh") that re-triggers the same silent-6-Wh corruption on top of a now-good bound value — i.e. G27 is not "in front of" the UX, it's a standing landmine next to it that a shipped UX would make *more* visible (a real SKU getting silently destroyed by a follow-up), not less. |

**Verdict:** **G27 in closure sequence: PARALLEL to battery catalog UX**, not a prerequisite gate. Recommend landing it in the same checkpoint window as the battery UX cut (Cut 2/3 together) rather than strictly sequencing them, precisely because the failure mode it prevents (silent corruption of a just-bound catalog value) becomes materially worse once binding is a live, reachable UX action.

---

## 5. Catalog battery → calc/energy chain (§1.4)

Full trace for a catalog-bound battery SKU (e.g. `lipo_2s_850mah`, `library/baterias/_datos.json`: `{chemistry: "lipo", energy_wh: 6.29, mass_g: 55, cells: 2, nominal_voltage: 7.4, capacity_mah: 850, c_rating: 75}`):

```text
bind_battery_from_catalog(sku)                          catalog_bind.py:78-123
  → ComponentSpec{properties: battery_capacity_wh, mass_g, chemistry,
                  cell_count (if spec.cells set)}, catalog_ref={battery, sku}
  ↓
set_battery_component(state, spec, spec.properties["battery_capacity_wh"].value)
                                                          component_writers.py:122-169
  → components["battery"] = spec                          (canonical)
  → current_parameters["battery_capacity_wh"] = capacity_wh
  → current_parameters["battery_mass_kg"] = mass_g/1000    (real SKU mass, not
                                                             the 150 Wh/kg heuristic —
                                                             component_writers.py:142-153)
  → current_parameters["battery_cell_count"] = cells       (component_writers.py:159-164)
  ↓
calculation_engine.CalculationEngine.build()               calculation_engine.py:35-190
  → total_mass includes battery_mass_kg (real SKU mass)     calculation_engine.py:53,61-63
  → autonomy_min = calculate_autonomy_min(battery_capacity_wh, motor_power_w × motors)
                                                            calculation_engine.py:164-178
  ↓
engineering_readiness._energy_evidence(ctx)                engineering_readiness.py:923-932
  → defined = component_presence_tier == "present"          (True, completeness=high from bind)
  → calculated = battery_capacity_wh present or autonomy_min present  → True
  → catalog_bound = _catalog_ref_set(project_state, "battery")  → True
  ↓
electrical_compatibility._battery_pack_limit_a / _battery_discharge
                                                            electrical_compatibility.py:183-267
  → I_pack_limit from spec.max_continuous_current_a or c_rating × capacity_ah
  → GAP-BATTERY-DISCHARGE-EXCEEDED if I_total > I_limit     engineering_readiness.py:777-803
  ↓
build_engineering_readiness → gaps / subsystem verdicts
```

| Question | Answer |
|---|---|
| Is bind API sufficient without UX? | **Yes.** `bind_battery_from_catalog` + `set_battery_component` is the exact two-call pattern used by `tests/test_phase2_lookup_operating_point.py:192-195` and `tests/test_catalog_bind_v1.py:297,375,411`. No production call site exists (`grep bind_battery_from_catalog src/` returns zero hits outside `catalog_bind.py` itself) — it is a fully test-callable, deterministic API waiting for a CLI/UX entry point identical in shape to the propeller-bind precedent (`orchestrator.py:2579-2589`). |
| Mass: SKU vs. 150 Wh/kg heuristic? | `component_writers.py:142-153`: when `spec.catalog_ref` is set and family is `"battery"` and `properties["mass_g"]` is present, `battery_mass_kg` comes from the real SKU mass (`round(mass_g/1000, 4)`). Otherwise (unbound, today's only live path), `estimate_battery_mass_kg(capacity_wh)` — the 150 Wh/kg heuristic — is used. |
| Does `invalidate_diverged_catalog_refs` cover battery drift? | **Yes** — `catalog_bind.py:229-241`. Compares `components["battery"].properties["battery_capacity_wh"]` against `current_parameters["battery_capacity_wh"]`; on divergence beyond `epsilon`, clears `catalog_ref` and reverts mass to the heuristic. Same pattern as motor divergence (`catalog_bind.py:215-227`). |
| What's missing for live CLI battery pick? | Mirroring the propeller pattern (`orchestrator.py:2579-2589`, plus its assist/list-suggestions surface): (1) a battery-suggestion/list helper analogous to `motor_catalog_assist`/whatever backs propeller suggestions, (2) a wizard step or Continuity-triggered prompt offering catalog SKUs, (3) wiring the confirmed pick through `bind_battery_from_catalog` + `set_battery_component` (already proven sufficient). No new calc/energy/readiness code is needed — this is a pure UX/routing addition on top of an already-correct data layer. |
| Does exact OP / propulsion need battery voltage for energy closure? | These are **separate concerns that happen to share the battery component**. Propulsion's operating-point resolution (P2-1, `component_writers.py:250-...`) reads `battery.catalog_ref` for **voltage** (to pick an exact vs. fallback OP) — already live and unaffected by whether energy/Wh binding exists. Energy closure (autonomy_min, discharge check) reads `battery_capacity_wh`/mass/current limits — a distinct set of fields on the same spec. A battery bind populates both simultaneously (one write, `component_writers.py:122-169`), so there is no ordering conflict, but they are conceptually two different consumers of one component. |

**Energy closure checklist — what works today vs. what an IC must add:**

| Works today (test-callable) | Missing for live CLI |
|---|---|
| `bind_battery_from_catalog` → `set_battery_component` bridge | User-facing pick surface (list/suggest/confirm) |
| `battery_capacity_wh`/`battery_mass_kg`/`battery_cell_count` bridge | Continuity/wizard prompt offering it |
| `calculate_autonomy_min` reads real Wh | — |
| Real-mass total-mass contribution when bound | — |
| `invalidate_diverged_catalog_refs` battery-divergence handling | — |
| `electrical_compatibility` discharge check against real `c_rating`/`max_continuous_current_a` | — |
| Voltage precedence for propulsion OP resolution | — |

---

## 6. "Real component" definitions (§1.5)

| Concept | Where it lives today | Sufficient for "real"? |
|---|---|---|
| `catalog_ref` (`family`, `sku`) | `ComponentSpec.catalog_ref: CatalogRef \| None` (`action_schema.py:130-141`). `CatalogRef.family` is a **closed `Literal["motor", "battery", "propeller"]`** — ESC/frame/flight_controller/sensors/materials cannot be represented by this field at all today without a schema change, independent of any library data existing for them. | Necessary but, alone, only an identity claim — see `sku_resolved` below. |
| Physical properties on `ComponentSpec` | `ComponentSpec.properties: dict[str, PropertyValue]` (`action_schema.py:150`) — mirrored into `current_parameters` by the family's writer (`component_writers.py`). | Yes, this is what calc/sim actually consume — the "physics-usable" layer. |
| Provenance / source | `PropertyValue.source: Literal["declared","inferred","calculated"]` (`action_schema.py:127`); library-side `manufacturer`/`source_url` exist on `MotorSpec` (`library.py:54,63`, e.g. `library/motores/_datos.json:172-174` `"manufacturer": "EMAX", "source_url": "https://..."`) but these are **not surfaced anywhere in BOM/CLI display** — confirmed no reader of `manufacturer`/`source_url` outside `library.py`'s own dataclass construction. | Exists in the library, invisible to the user today. |
| Manufacturer / model | Same as above — present in motor library rows, absent from battery/propeller rows in this seed, never displayed. | Data exists partially; not part of the "real" contract as implemented. |
| `completeness` high/low vs. BOM tier | `classify_component` (`project_closure.py:160-188`) returns `missing`/`stub`/`declared`/`defined`. **`defined` requires `completeness=="high"` AND measurable properties AND zero `missing_fields`** — strictly stronger than `catalog_ref` being set. A freeform component can reach `defined`; a catalog-bound one that's missing a required field cannot. |
| `catalog_bound` in readiness | `SubsystemEvidence.catalog_bound` is computed per subsystem (`_catalog_ref_set`, `engineering_readiness.py:861-863`) but **confirmed write-only** — `_derive_subsystem_verdict` (`engineering_readiness.py:999-1054`) never reads `evidence.catalog_bound`. A subsystem reaches PASS purely from `defined ∧ calculated ∧ simulated ∧ validated` plus absence of blocking gaps — **catalog binding is not required for any subsystem PASS today** (Fixture 2's freeform battery, §2.3, is live proof). |
| Freeform declare | Valid for closure **today, for every family** — nothing in the rollup distinguishes freeform from catalog-bound as long as `classify_component` reaches `declared`/`defined` and no HIGH gap fires. |

**Definition box (normative, ★-gated in §7):**

```text
"Componente real (catálogo)"  = catalog_ref is set AND the SKU currently
    resolves in the live library (has_motor/has_battery/has_propeller —
    the same live re-check G9-A already performs for motors, never a
    cached boolean). Its properties came from bind_*_from_catalog, not
    from a writer projecting freeform numbers.

"Componente declarado (freeform)" = catalog_ref is None. completeness is
    "medium" or "high" with measurable properties (classify_component
    tier "declared" or "defined"). Physics/sim may fully trust these
    numbers (★2) — only the SKU identity claim is absent, and none is
    made.

"Componente stub / incompleto" = completeness "low" (or absent), or
    missing_fields non-empty. Never contributes physics; always a real
    BOM/architecture gap.
```

★1 discipline check: nothing found in this trace lets a stub or frankenstein component present as `catalog_bound=True` without a resolvable `catalog_ref` — the one place this *could* silently mislead is BOM display's `[sku]` suffix, and that is governed by `sku_resolved`, which **is** computed from a live re-check (`_bom_sku_resolved`, `project_closure.py:204-228`) — **except for one family it currently omits entirely, found live below.**

### 6.1 Live finding — propeller `sku_resolved` is always `False`, even when correctly bound

`_bom_sku_resolved` (`project_closure.py:204-228`):

```python
family = catalog_ref.get("family")
if family == "motor":
    return default_library.has_motor(sku)
if family == "battery":
    return default_library.has_battery(sku)
return False  # no v1 resolve path for other families (★2)
```

`ComponentLibrary.has_propeller` exists (`library.py:450`) but is never called here. Reproduced live against Fixture 1's actually-bound, actually-resolving propeller:

```text
✓ propellers: hq_5045_bn (SKU sin resolver) qty=4 (high)
```

The propeller (`hq_5045_bn`, catalog-bound, resolves in `library/helices/_datos.json`) displays **"(SKU sin resolver)"** — the honest-uncertainty marker `_bom_identity_suffix` (`project_closure.py:395-406`) shows for a genuinely unresolved SKU — even though it is fully resolved. This predates the propeller-bind UX checkpoint: `_bom_sku_resolved`'s `★2` comment was written during Impl D, before propeller binding went live in `v0.3.0`, and nothing updated it afterward. It does not affect any gap or verdict (`sku_resolved` is BOM-display-only, per the Impl D investigation's confirmed finding that `catalog_bound` fields are unwired from verdicts), but it is a live, user-visible honesty regression in the opposite direction of ★1 — a real catalog part displaying as *less* certain than it is. **Recommend a one-line fix** (`if family == "propeller": return default_library.has_propeller(sku)`) bundled into whichever cut touches `project_closure.py` next (Cut 4, §8).

---

## 7. Freeform vs. catalog policy matrix (§1.6) + minimum requirements per family (§1.7)

| Family | Library data? | Bind helper? | Pick UX? | Freeform path | `catalog_ref` schema support | Recommend for closure v1 |
|---|---|---|---|---|---|---|
| motors | Yes, 22 (`library/motores/_datos.json`) | `bind_motor_from_catalog` (`catalog_bind.py:23-75`) | Yes (`orchestrator.py:2489-2500`, DEFINE_MISSING + iterate wizard) | Yes | `Literal` includes `"motor"` | `catalog_required` for the "catalog-evidence-strong" snapshot (B); `freeform_ok` for v1 baseline (A) |
| propellers | Yes, 16 (`library/helices/_datos.json`) | `bind_propeller_from_catalog` (`catalog_bind.py:126-171`) | Yes (`orchestrator.py:2579-2589`, v0.3.0) | Yes | `Literal` includes `"propeller"` | Same as motors |
| battery | Yes, 10 (`library/baterias/_datos.json`) | `bind_battery_from_catalog` (`catalog_bind.py:78-123`) | **No** — test-callable only | Yes (Fixture 2 proves it PASSes) | `Literal` includes `"battery"` | `freeform_ok` today; `catalog_required` for snapshot B once Cut 2 ships |
| esc | No library exists | No | No | Yes (only path) | **`Literal` excludes `"esc"` entirely** — a schema change, not just new library rows, is needed before this could ever be catalog-bound | `freeform_ok` / `stub_ok_for_physics_only` — H5-scale work, out of closure v1 per contract §0.4 |
| frame | Materials density library exists (`library/materiales/_datos.json`, 8 entries) but is **not** a `catalog_ref`-eligible family — frame material is read via `get_frame_material`/`design_utils.py:24`, a density lookup, not a SKU bind | No frame-SKU bind exists | No | Yes (only path) | `Literal` excludes `"frame"` | `freeform_ok` — materials density ≠ frame SKU catalog, correctly out of scope per contract §0.4 |
| flight_controller | No | No | No | Yes (only path) | `Literal` excludes it | `freeform_ok` |
| sensors | No | No | No | Yes (only path) | `Literal` excludes it | `freeform_ok` |

**Minimum `ComponentSpec` + params per family** (derived from `classify_component`/`_MEASURABLE`/`BLOCK_TO_COMPONENTS`):

| Family | To leave BOM `missing`→ not `missing` | To reach BOM `defined` (subsystem-PASS-eligible) | To contribute honestly to calc/sim |
|---|---|---|---|
| motors | any `ComponentSpec` present | `completeness="high"`, one of `_MEASURABLE` set (`thrust_n`/`kv_rating`/`power_w`/`motor_count`), zero `missing_fields` | `current_parameters["motor_power_w"]`, `motor_count`; `per_motor_max_thrust_n` if thrust known |
| propellers | any spec present | same shape, via `diameter_in`/`pitch_in` | `propeller_diameter_in`, feeds aerodynamic thrust inference if motor thrust absent |
| battery | any spec present | `completeness="high"`, `battery_capacity_wh` present, zero `missing_fields` | `current_parameters["battery_capacity_wh"]` (bridges via `set_battery_component`) |
| esc | any spec present | `completeness="high"`, `current_a` (or another `_MEASURABLE` key) present | Not consumed by `calculation_engine` at all today — only by `electrical_compatibility` (ESC-vs-motor check) |
| frame | any spec present | `completeness="high"`, `material` present, zero `missing_fields` | `structure_mass_kg` (via `structure_mass_factor`/override), density from `material` |
| flight_controller / sensors | any spec present | `completeness="high"`, zero `missing_fields` (measurability is name-only for these — `_control_evidence.calculated == defined`, `engineering_readiness.py:937`) | Not consumed by `calculation_engine` at all — control has no physics bridge in Phase 2.5 (`component_writers.py:111`) |

**Family policy matrix — Engineer ratification requested (★7):**

```text
motors, propellers, battery:  catalog_required for "catalog-evidence-strong" (snapshot B);
                               freeform_ok for "freeform-tolerant v1" (snapshot A)
esc:                          freeform_ok only — no catalog schema support exists (H5, explicitly deferred)
frame:                        freeform_ok only — materials density ≠ frame SKU (explicitly deferred)
flight_controller, sensors:   freeform_ok only — no catalog path exists or is planned in this arc
```

---

## 8. Existing catalog vs. expansion (§1.8)

| Family | Entries (live count) | Bind API | Pick UX | OP/calc hooks |
|---|---|---|---|---|
| motores | 22 | Yes | Yes | P2-1 exact/fallback OP |
| helices | 16 | Yes | Yes (v0.3.0) | P2-1 OP (propeller_sku input) |
| baterias | 10 | Yes | **No** | Autonomy/mass/discharge (all live, test-only) |
| materiales | 8 | N/A (density lookup, not SKU bind) | N/A | Frame density/mass |

**What % of closure v1 can ship without new SKUs?** All of it. Motor and propeller catalogs already cover the v0.3.0 propulsion-complete path; battery catalog (10 LiPo-first entries) is sufficient to prove a battery-bind UX end to end (Fixture-shaped projects don't need exotic chemistries to reach `ASSEMBLY_READY`). **Zero library expansion is required for the recommended sequence (§8/§11) — this is a pure code/UX gap, not a data gap.**

**What families require expansion before honest "catalog-bound" claims?** ESC and frame-as-SKU are the only families with **zero** library data — and both are explicitly out of scope for this arc (contract §0.4: H5 ESC catalog, frame SKU catalog). No expansion needed for motors/propellers/battery to support closure v1.

**Is battery UX + G27/G26 fix enough for energy closure, or are new gap types needed?** Enough, **no new gap types needed**. `GAP-BATTERY-DISCHARGE-EXCEEDED` (`engineering_readiness.py:777-803`) already exists and already reads real SKU discharge limits when bound (§5). The only missing piece is the UX to reach that bound state live.

---

## 9. Target closed-project snapshots A / B (§1.9)

### A — Assembly-ready (freeform-tolerant v1)

Achievable today, purely by completing the honest declaration of every stub component + stating an achievable constraint (no code changes required to reach this shape — Fixture 2 minus its one gap is exactly this):

```text
ENGINEERING READINESS
requirements   PASS
architecture   PASS
structure      PASS
propulsion     PASS
energy         PASS      ← battery may be freeform (medium/high completeness, no catalog_ref)
electronics    PASS      ← ESC freeform-declared, catalog_ref always null (no ESC catalog)
control        PASS
catalog        PASS      ← catalog subsystem reflects motor query state, not "every part is a SKU"
bom            PASS

PROJECT STATUS: ASSEMBLY READY

Componentes / gaps:
✓ motors: emax_rs2205s_2300 [emax_rs2205s_2300] qty=4 (high)
✓ propellers: hq_5045_bn [hq_5045_bn] qty=4 (high)      ← after §6.1 fix
… esc: "4-in-1 30A BLHeli_32" (declarado, sin SKU) — completo, no gap
◇ battery: "LiPo 4S 5000mAh" (declarativo) — completo, no gap
✓ frame: "carbono 220mm" (high)
✓ flight_controller: "F7 stack" (high)
✓ sensors: "GPS M10 + barómetro" (high)

Propulsión (evidencia): exact_operating_point · 9.7086 N/motor · emax_rs2205s_2300 + hq_5045_bn
```

### B — Assembly-ready (catalog-evidence-strong)

Same as A, but motors + propellers + battery are all catalog-bound where the library supports it; ESC/FC/sensors remain honestly freeform (no catalog exists for them):

```text
ENGINEERING READINESS
[... same 9 lines, all PASS ...]

PROJECT STATUS: ASSEMBLY READY

Componentes / gaps:
✓ motors: emax_rs2205s_2300 [emax_rs2205s_2300] qty=4 (high)
✓ propellers: hq_5045_bn [hq_5045_bn] qty=4 (high)
… esc: "4-in-1 30A BLHeli_32" (declarado, sin SKU) — completo, no gap    ← honestly not a catalog claim
✓ battery: lipo_4s_5000mah [lipo_4s_5000mah] qty=1 (high)               ← NEW after Cut 2
✓ frame: "carbono 220mm" (high)                                        ← still freeform (no frame SKU catalog)
✓ flight_controller: "F7 stack" (high)
✓ sensors: "GPS M10 + barómetro" (high)

Propulsión (evidencia): exact_operating_point · 9.7086 N/motor · emax_rs2205s_2300 + hq_5045_bn
Energía (evidencia): battery_capacity_wh=22.2 (lipo_4s_5000mah, real mass 570g) · autonomía 5.05 min
```

Both snapshots require **zero invented SKUs** and **zero fake PASS** — every line above is either already reachable in the fixtures inspected or reachable purely by wiring the already-proven `bind_battery_from_catalog`/`set_battery_component` pair to a UX.

---

## 10. Transition S0 → S1 → S2 (§1.10)

```text
S0: PHYSICS PASS + BOM INCOMPLETE + NOT ASSEMBLY READY   ← Fixture 1 shape
S1: PHYSICS PASS + BOM COMPLETE + NOT ASSEMBLY READY     ← declare/bind remaining stub
                                                              components (esc/battery/frame/FC/
                                                              sensors) to at least "declared" tier;
                                                              zero catalog required
S2: PHYSICS PASS + BOM COMPLETE + ASSEMBLY READY         ← additionally: requirements PASS
                                                              (state an achievable constraint, or
                                                              G26 fix + achievable target)
```

**Minimal mutations per transition:**

- **S0 → S1:** declare (freeform is sufficient) each stub component to `completeness="high"` with its family's minimum measurable field (§7 table, middle column). No catalog binding required. No calc/sim change. Directly closes `architecture`, `structure`, `energy`, `electronics`, `control`, `bom` gaps — this is exactly Fixture 1's remaining gap set (§2.2), all 6 gaps are `GAP-BOM-*`/`GAP-ARCH-*`, none touch `requirements`.
- **S1 → S2:** state a numeric constraint achievable by the current sim (`autonomy_min` ≤ actual, or `max_weight_kg` ≥ actual `total_mass_kg`) via `current_parameters["restrictions"]`, either at creation or (once G26 is fixed) mid-session. This is **entirely independent of S0→S1** — Fixture 2 is a live S2-adjacent project stuck only on this transition, with S0→S1 already done.

**Independence:** S0→S1 and S1→S2 are **fully independent** — neither reads the other's state (`_bom_evidence`/`_structure_evidence`/etc. never consult `parsed_constraints`; `_requirements_evidence` never consults `bom`). They can be worked, and shipped, in either order or in parallel by two different ICs.

---

## 11. Sequence options + recommendation (§1.11)

| Option | Sketch | Assessment |
|---|---|---|
| **A** | G27 → G26 → battery catalog UX → closure policy tweaks | **Rejected as literal order.** §4 shows G27 has no dependency relationship to G26 or to the battery UX at all (different code paths entirely) — sequencing it first buys nothing and delays the highest-leverage fix (G26). |
| **B** | Battery catalog UX first (bypasses G27 for pick path) → G26 → freeform policy | Technically valid (§4 confirms bind bypasses G27), but **defers the single highest-leverage, lowest-risk fix** (G26 — a pure parsing/routing bug, contained to `state_schema.py`/`param_definition_session.py`) behind a larger UX cut for no dependency reason. |
| **C** | Closure policy + BOM completeness first → then G26/G27 | Addresses S0→S1 (§10) first, which is real work but — per Fixture 2 — **does not, by itself, get any project to ASSEMBLY_READY**, since `requirements` is orthogonal. Risks a checkpoint that "does a lot" but still can't demo the headline outcome. |
| **D — recommended** | Split by concern, ship smallest/highest-leverage first: **Requirements closure** IC → **Energy catalog UX (+G27 hardening, same window)** IC → **Readiness/BOM honesty rollup** IC | Matches §10's proven independence, matches the contract's own §1.11 sketch, and lets the first cut alone demonstrably flip Fixture-2-shaped projects to `ASSEMBLY_READY` — the most convincing possible checkpoint gate. |

**Recommendation: Option D**, 4 cuts (one more than D's 3-cut sketch, splitting BOM-honesty separately from Requirements since they are unrelated code, per §10):

1. **Cut 1 — Requirements Closure.** Fix the G26 mid-session write gap (route free-text constraint updates into `current_parameters["restrictions"]`, or add the missing `is_derived` gate to whichever path reaches `param_definition_session`) **and** get an Engineer ★ ruling on the "no explicit constraint" semantics (§3, §12 ★9). Smallest possible diff, zero catalog/UX dependency, immediately unblocks the cleanest fixture in this investigation.
2. **Cut 2 — Battery Catalog UX.** Build the pick surface on top of the already-proven `bind_battery_from_catalog`/`set_battery_component` chain (§5), mirroring the propeller-bind precedent exactly (same shape as `orchestrator.py:2579-2589`).
3. **Cut 3 — G27 Hardening.** Land in the same checkpoint window as Cut 2 (not necessarily the same commit) — harden `_parse_value`/the upstream battery-chemistry extraction so "6S"/"10000mAh" text can't silently corrupt `battery_capacity_wh`, especially post-bind (§4's landmine argument).
4. **Cut 4 — Closure Policy + BOM Honesty.** Ratify the family policy matrix (§7) and the two snapshot definitions (§9) as the product's "assembly ready v1" contract; fix the propeller `sku_resolved` bug (§6.1); decide whether any `WARNING`-level accepted state should expand beyond the current single `CATALOG-GAP-DEMOTED-POST-PASS` type.

**G24:** stays deferred, confirmed **not** a closure prerequisite. `_bom_sku_resolved`/subsystem verdicts never require `catalog_ref` to survive a DSE apply — G24's damage is identity-*display* honesty (a stale `.name` next to a cleared `catalog_ref`, already correctly `sku_resolved=False` per §6's rule), not a rollup blocker. It belongs with future UX/DSE-ranking debt, not this arc.

---

## 12. CLI probe sketch (§1.12)

```text
1) Load Fixture-1-shaped project → `estado` → confirm 6 MEDIUM gaps, 0 HIGH,
   NOT ASSEMBLY READY, propulsion+catalog PASS (regression baseline for
   this investigation's own findings).

2) Load Fixture-2-shaped project → `estado` → confirm 8/9 PASS, 0 gaps,
   NOT ASSEMBLY READY (regression baseline — the "one line away" case).

3) Cut 1 applied: state an achievable autonomy constraint on the Fixture-2
   project (`autonomy_min` ≤ 5.0455, its live sim value) → requirements
   flips PASS → overall flips ASSEMBLY_READY. State an UNACHIEVABLE
   constraint (e.g. 15 min) instead → GAP-REQUIREMENTS-UNMET:autonomy
   (HIGH) fires honestly → still NOT_ASSEMBLY_READY, but now for the
   right, visible reason (matches the G26 finding doc's own prediction).

4) Cut 2 applied: bind a battery SKU via the new UX → estado shows
   `✓ battery: {sku} [sku] qty=1` and an energy evidence line with real
   Wh/mass; `estado` autonomy_min changes from the heuristic-mass value
   to the real-SKU-mass value.

5) Cut 3 applied: free-text "aumenta batería a LiPo 6S 10000mAh" on a
   freeform (unbound) project → either resolves to the correct ~22 Wh /
   refuses with clarification — never silently 6 Wh. Repeat on a
   catalog-bound battery from #4 → same guarantee, plus catalog_ref must
   not be silently dropped by a rejected/clarified parse.

6) Full walk, freeform-tolerant v1 (snapshot A, §9): create → architecture
   4/4 → declare esc/battery/frame/FC/sensors freeform (no SKUs) → state
   achievable constraint → `estado` → ASSEMBLY READY, zero invented SKUs,
   zero fake PASS.

7) Full walk, catalog-evidence-strong (snapshot B, §9): same as #6 but
   motor+propeller+battery all catalog-bound → `estado` → ASSEMBLY READY
   with `[sku]` on all three lines, `sku_resolved=true` on propellers too
   (post §6.1 fix).
```

---

## 13. ★ Decisions for Engineer

**★1 — Sequence:** adopt Option D (§11), 4 cuts, Requirements Closure first. *Recommended.*

**★2 — G26 fix scope:** repair the mid-session constraint-update write path (route into `current_parameters["restrictions"]` → `parsed_constraints` re-derivation) rather than adding a parallel `is_derived` gate only inside `param_definition_session.py`. The latter would stop the *symptom* (invented `autonomia` key) but still leave the user with no way to actually update the constraint. *Recommended: fix the write path, and add the `is_derived` gate as defense-in-depth, not instead of it.*

**★3 — "No explicit constraint" semantics (§3):** should a project that has genuinely never stated a numeric constraint (both live fixtures: `restrictions="no"`, no numeric objective) ever be able to reach `requirements` PASS, or must ASSEMBLY_READY always require an explicit, stated, achievable constraint? Ratify one:
  - (a) **Require explicit constraint always** (current de-facto behavior) — a truly unconstrained design can never be `ASSEMBLY_READY`.
  - (b) **Treat an explicit "no constraint" declaration as satisfied** (distinct from "not yet asked") — would need a small, deliberate `_requirements_evidence` change, out of this investigation's `src/` scope.
  *No recommendation offered — this is a genuine product-semantics call, not an engineering trade-off.*

**★4 — Battery/propeller pick UX pattern reuse:** Cut 2 should copy the propeller-bind UX's shape (`orchestrator.py:2579-2589` + its supporting assist/list helper) rather than inventing a new pattern. *Recommended.*

**★5 — G27 fix scope:** narrow to the battery free-text chemistry/cell-count parsing path (wherever the LLM's `valor` extraction happens upstream of `semantic_intent_adapter._parse_value`) — do not touch `_parse_value`'s generic numeric-sanitizer behavior for every other iterate variable, which is correct as-is for plain numeric params. *Recommended.*

**★6 — Propeller `sku_resolved` bug (§6.1):** fix as a one-line addition to `_bom_sku_resolved` (`project_closure.py:224-228`), bundled into Cut 4. *Recommended, low risk, already reproduced live.*

**★7 — Family policy matrix (§7):** ratify as written — motors/propellers/battery eligible for `catalog_required` in the "strong" snapshot; ESC/frame/FC/sensors `freeform_ok` only, no catalog work planned in this arc. *Recommended.*

**★8 — `ACCEPTED_WARNING_TYPES` scope:** leave at the current single type (`CATALOG-GAP-DEMOTED-POST-PASS`, catalog/propulsion only) for closure v1 — no other subsystem gets a "soft PASS" path. *Recommended, matches ERF-2's own deliberate narrowing (`engineering_readiness.py:133-140`).*

**★9 — G24:** confirmed not a closure prerequisite; leave deferred per existing roadmap categorization. *Recommended.*

---

## 14. Suggested Implementation Contract outline

*(Bullets only — names and gates, no code, per contract §1.11/§3.)*

**IC 1 — Requirements Closure**
- Fix mid-session `restrictions` write path (routes into `current_parameters["restrictions"]`, re-derives `parsed_constraints` via existing `model_copy` override, `state_schema.py:160-173`).
- Add `is_derived` gate to whichever routing surface reaches `param_definition_session` without going through `semantic_intent_adapter.adapt()` first (defense-in-depth per ★2).
- Engineer ★3 ruling incorporated (either fix nothing further, or add the "explicit no-constraint" satisfied state).
- Gate: CLI probe #3 (§12) — Fixture-2-shaped project flips to `ASSEMBLY_READY` on an achievable constraint, and surfaces an honest `GAP-REQUIREMENTS-UNMET` on an unachievable one.
- Regression: existing `parsed_constraints`/requirements-subsystem tests unchanged in assertion, `test_engineering_readiness_*` suite green.

**IC 2 — Battery Catalog UX + G27 Hardening**
- Battery pick surface (list/suggest/confirm), reusing `bind_battery_from_catalog` + `set_battery_component` (proven, §5) — no new calc/energy code.
- G27 fix scoped to battery free-text chemistry/cell-count extraction (★5), landed in the same checkpoint window.
- Gate: CLI probes #4, #5, #7 (§12).
- Regression: `tests/test_catalog_bind_v1.py`, `tests/test_phase2_lookup_operating_point.py`, `tests/test_impl_d_sku_bom.py` unchanged assertions; new tests for the pick UX and the hardened parser.

**IC 3 — Closure Policy + BOM Honesty**
- Ratify family policy matrix (§7) and snapshots A/B (§9) as the product-level "assembly ready v1"/"assembly ready strong" contract, documented in `docs/ENGINEERING_READINESS_VISION.md` per its own sync protocol (§10 of that doc).
- Fix propeller `sku_resolved` (★6, `project_closure.py:224-228`).
- Gate: CLI probes #6, #7 (§12) — full walks to both snapshots with zero invented SKUs.
- Regression: `tests/test_project_closure_v1.py`, `tests/test_fn020_completeness_coherence.py`, `tests/test_impl_d_sku_bom.py`.

**Out of scope for all three (carried forward):**
- G24 (DSE apply-by-index / scoring) — separate future UX/DSE debt, confirmed not a closure blocker (§11).
- H5 ESC catalog, frame SKU catalog — require a `CatalogRef.family` schema change before any bind work is even possible (§6, §7) — bigger than this arc.
- Conversation Engine / Step D.
- Version bump — Engineer call only, per contract.

---

**End of report.**
