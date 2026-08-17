# Investigation — G10 Material Catalog / Frame Acquisition Misalignment

**Type:** Investigation only. Zero product `src/` changes.
**Contract:** Implementation Contract — G10 Investigation + Design (2026-08-15)
**Checkpoint base:** `checkpoint-g3` (`a3b72b8`)
**Companion doc:** [design_g10_materials_frame.md](design_g10_materials_frame.md)

---

## 1. Executive verdict

The CLI rejection of `plastico`/`PVC` is a **keyword-coverage gap** in the frame `ComponentRule`
(§3) — but that is the shallow symptom. The deep finding is a **three-vocabulary identity
split**: the library (`library/materiales/_datos.json`) speaks Spanish canonical names, the frame
acquisition path (`aerial.MATERIAL_MAP`) speaks a separate, incomplete set of English slugs
(`carbon_fiber`/`aluminum`/`plastic`), and the iterate path (`iterate_domain._KNOWN_MATERIALS`)
speaks a *third*, mostly-library-aligned table that already covers `pvc` and includes one material
(`madera`) the library doesn't have. These three tables never call into each other. The frame
wizard's canonical write (`set_frame_material`) stores the English slug into
`components["frame"].properties["material"]` — the declared Single Read Point
(`get_frame_material`) — while a legacy field (`design_properties.structure.material`) still holds
the library-Spanish name from `create_project` and is *never updated* by the wizard. `mutation_engine.apply_material_mutation`
reads that stale legacy field in preference to the canonical one. §5 reproduces, with real code,
a case where this silently computes the **wrong mass** after an iterate material change — not a
crash, a wrong number that looks correct.

---

## 2. Layer map (library ↔ MATERIAL_MAP ↔ keywords ↔ writers ↔ iterate/mutation)

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ library/materiales/_datos.json  (8 entries, Spanish keys, ground truth)     │
│   aluminio · fibra de carbono · titanio · acero · kevlar · magnesio ·       │
│   plástico · pvc                                                            │
└───────────────┬───────────────────────────────────────────────────────────┘
                 │ ComponentLibrary.get_material/list_materials/has_material
                 │ (knowledge/library.py — the ONLY _datos.json reader, A3)
     ┌───────────┼──────────────────────────────┬───────────────────────────┐
     │           │                              │                            │
     ▼           ▼                              ▼                            ▼
create_project.py  mutation_engine.py       iterate_interactive_session.py  (nobody else)
_DEFAULT_MATERIAL  apply_material_mutation  _estimate_material_impact
= "aluminio"       get_material(current)    get_material(new/current)
writes             get_material(new)        graceful KeyError→"aluminio"
structure.material  → hard KeyError          fallback (Bug 44 handling)
= spec.name (Spanish)  if either name isn't
structure.density      a library key
= spec.density_kg_m3

                 ╔══════════════════════════════════════════╗
                 ║  aerial.py — SEPARATE vocabulary (A6)     ║
                 ║  MATERIAL_MAP: alias → ENGLISH slug        ║
                 ║    carbono/fibra de carbono/carbon/cf      ║
                 ║      → "carbon_fiber"                      ║
                 ║    aluminio/aluminum/aluminium/alu          ║
                 ║      → "aluminum"                           ║
                 ║    plastico/plástico/abs/nylon              ║
                 ║      → "plastic"                            ║
                 ║  NOT library keys. No pvc/titanio/acero/    ║
                 ║  kevlar/magnesio entries at all.            ║
                 ╚═══════════════┬════════════════════════════╝
                                 │ extract_frame_properties()
                                 ▼
                 frame ComponentRule keywords (A5):
                   frame, chasis, estructura, armazon/armazón,
                   carbon, carbono, aluminio
                   → matches only 2 of 8 library materials
                                 │
                                 ▼
                 component_writers.set_frame_material()
                   writes components["frame"].properties["material"]
                   = MATERIAL_MAP output (English slug) — CANONICAL
                     per design_utils.py's own docstring (A9)
                   does NOT touch structure.material

                 ╔══════════════════════════════════════════╗
                 ║  iterate_domain.py — THIRD vocabulary      ║
                 ║  _KNOWN_MATERIALS: alias → LIBRARY name    ║
                 ║    fibra de carbono/carbon fiber/carbono   ║
                 ║      → "fibra de carbono"                  ║
                 ║    kevlar/magnesio/titanio/titanium/        ║
                 ║    aluminio/aluminum/madera/acero/steel/    ║
                 ║    plastico/plástico/pvc → library name     ║
                 ║      (madera has NO library entry — gap)    ║
                 ╚═══════════════┬════════════════════════════╝
                                 │ _extract_material_from_text()
                                 ▼
                 iterate_interactive_session material-change flow
                   → passed as draft.value to mutation_engine

design_utils.get_frame_material()  ← "Single Read Point" (docstring claim)
   reads ONLY components["frame"].properties["material"]
   → returns the English MATERIAL_MAP slug once frame is wizard-declared
   → used by actions/iterate.py:_build_mutable_state (state["material"])

mutation_engine.apply_material_mutation()
   current_material = structure.get("material")            ← LEGACY, PREFERRED
                       or state.get("material")             ← canonical, fallback only
                       or "aluminio"
   → reads the STALE legacy field first, ignoring the declared frame material
   writes result to new_state["material"] = spec_new.name (library Spanish name)
   → routed by actions/iterate.py:_apply_design_property_mutation back into
     structure.material ONLY — never into components["frame"]
   → the two fields diverge permanently after the first material iterate
```

---

## 3. CLI root-cause reconstruction — `plastico 390g`

Turn: frame wizard open (`expected_keys == ["frame"]`, `MISSING_COMPONENT_DEFINITION`).

```text
1. orchestrator._handle_component_description("plastico 390g", session)
2. specs = infer_components("plastico 390g", registry=aerial_registry)
     → infer_component() → aerial_registry.match(normalized, name_lc)
     → ComponentRule.matches(): checks keywords
         ("frame","chasis","estructura","armazon","armazón","carbon","carbono","aluminio")
       against "plastico 390g" → NO MATCH (aerial.py:482)
     → falls through registry (no other rule's keywords match either)
     → generic fallback: suggested_key="generic_component", completeness="low"
       (component_inference.py:78-88, "390g" alone doesn't reach the ≥2-word
       "medium" bar meaningfully — either way suggested_key stays generic)
3. "propellers" not in expected_keys → the ONLY existing force-inference branch
   (orchestrator.py:1753-1758, FN-019) does not fire — it is scoped to
   suggested_key="propellers" exclusively. No analogous force exists for "frame".
4. processable = [] (generic_component filtered out by FN-017 B4 guard,
   orchestrator.py:1764-1768, because expected_keys is set)
5. Falls to the "low completeness" branch (orchestrator.py:1898-1920):
   expected_keys[0] == "frame" → frame's fine-grained probe:
     has_material=False, has_mass=True (mass_g regex still matched "390g")
     → msg = "¿De qué material es? Ej: 'fibra de carbono' o 'aluminio'"
6. User sees a re-prompt with an example, not an error — matches the observed
   "re-prompt (example only)" behavior in the CLI transcript.
```

Even `infer_component_for_key(user_input, "frame", registry=aerial_registry)` — the FN-019-style
bypass that *would* fix this if it existed for frame — only partially rescues the situation
(§4, coverage matrix): it re-runs `extract_frame_properties` directly, bypassing the keyword gate,
but that extractor still consults `MATERIAL_MAP`, which has **no entry for `plastico`'s missing
siblings** (`pvc`, `titanio`, `acero`, `kevlar`, `magnesio`) — only `plástico` itself would resolve.
`pvc 390g` and `PPC 390g` fail at *both* layers: no frame keyword, and no `MATERIAL_MAP` alias.

---

## 4. Coverage matrix (P2 — executed against live code)

For every one of the 8 library materials, `f"{name} 400g"` was run through the real
`infer_component`, `infer_component_for_key(..., "frame")`, and both alias tables:

| library name       | in `MATERIAL_MAP`? | in frame keywords? | `infer_component` result | forced-for-key material (English slug) | in `_KNOWN_MATERIALS`? |
|---|---|---|---|---|---|
| acero               | False | False | `generic_component` | — | True |
| aluminio             | True  | True  | `frame`              | `aluminum`     | True |
| fibra de carbono     | True  | True  | `frame`              | `carbon_fiber` | True |
| kevlar               | False | False | `generic_component` | — | True |
| magnesio             | False | False | `generic_component` | — | True |
| plástico             | True  | **False** | `generic_component` | `plastic`  | True |
| pvc                  | False | False | `generic_component` | — | True |
| titanio              | False | False | `generic_component` | — | True |

**Reading it:**
- Only `aluminio` and `fibra de carbono` work today (2/8) — matches the CLI transcript exactly
  (`fibra de carbono 450g` → OK, everything else → re-prompt).
- `plástico` is the interesting middle case: `MATERIAL_MAP` has it, but the frame **keyword list**
  doesn't (`aerial.py:482` has no `"plastico"`/`"plástico"` keyword) — so a bare `force-frame`
  fix alone (bypassing keywords) would rescue `plástico` immediately.
- `acero`, `kevlar`, `magnesio`, `pvc`, `titanio` (5/8) are missing from **both** layers — a
  force-frame fix alone does *not* rescue these; `MATERIAL_MAP` itself must gain entries (or be
  replaced) for `extract_frame_properties`'s material-detection loop to ever find them, regardless
  of how the wizard dispatches.
- `_KNOWN_MATERIALS` (iterate path) already recognizes all 8 by name (plus `madera`, which isn't
  in the library at all — see §5's gap). It is the *closer-to-correct* table but lives in a
  different module, is invoked from a different entry point, and is never consulted by
  `extract_frame_properties`/`MATERIAL_MAP`.

---

## 5. Dual-name / canonical hazard (A4 / A9 / A11 / P4)

### 5.1 Three places a "current frame material" can live

| Field | Written by | Vocabulary | Read by |
|---|---|---|---|
| `design_properties.structure.material` | `create_project.py` (init: `spec.name`, Spanish); `actions/iterate.py:_apply_design_property_mutation` (post-mutation: `spec_new.name`, Spanish) | Library Spanish | `mutation_engine.apply_material_mutation` (**preferred** read, line 244-246) |
| `components["frame"].properties["material"]` | `component_writers.set_frame_material` (frame wizard: `MATERIAL_MAP` English slug) | English slug | `design_utils.get_frame_material` — the documented "Single Read Point" (design_utils.py:1-11, "Fase 3 completada") |
| `state["material"]` (ephemeral, per-turn) | `actions/iterate.py:_build_mutable_state` via `get_frame_material()` | Mirrors row 2 | `mutation_engine.apply_material_mutation` (fallback read, only if row 1 absent) |

Row 1 and row 2 are **never synchronized with each other**. `set_frame_material` (the frame
wizard's writer) touches only `components["frame"]` and `current_parameters` — confirmed by
reading `component_writers.py:47-102`, it never touches `design_properties.structure`.
`_apply_design_property_mutation` (the iterate mutation's writer) touches only
`structure.material` — confirmed at `actions/iterate.py:481-482` — never `components["frame"]`.

### 5.2 Reproduced with real code (P4)

Executed against the actual `set_frame_material`, `get_frame_material`, and
`MutationEngine.apply_material_mutation`:

```text
Step 1 — create_project (simulated): structure.material = "aluminio"  (library Spanish)

Step 2 — frame wizard declares "fibra de carbono 450g":
  set_frame_material(state, 0.45, "carbon_fiber")   # MATERIAL_MAP output, English slug
  → components["frame"].material  = "carbon_fiber"
  → structure.material (legacy)   = "aluminio"        ← UNCHANGED, now stale
  → get_frame_material()          = "carbon_fiber"    ← "canonical" read disagrees with legacy

Step 3 — iterate: "cambiar material a pvc"
  apply_material_mutation() reads current_material from structure.material FIRST
  → current_material = "aluminio"   (should have been "carbon_fiber" / "fibra de carbono")
  → spec_old = get_material("aluminio")   ρ=2700 kg/m³   ← WRONG base material
  → spec_new = get_material("pvc")        ρ=1380 kg/m³
  → new_state = {"masa_total": 4.3889, "material": "pvc"}
  → impact    = {"masa_total": -12.222%}
```

The `-12.22%` mass change is computed from an **aluminio→pvc** density ratio when the drone's
actual declared frame material was carbon fiber (ρ=1600). The correct **carbon_fiber→pvc** ratio
is a different, smaller magnitude change. This is not a crash — `get_material("aluminio")` and
`get_material("pvc")` both succeed — it is a **silently wrong physical result**, computed with
full confidence, from a state field (`structure.material`) that a design-time comment already
calls legacy ("ese campo se eliminará en el Commit 5 de Fase 3", `design_utils.py:11`) but that
`mutation_engine.py` was never updated to stop reading.

After this mutation, `structure.material = "pvc"` while `components["frame"].material` remains
`"carbon_fiber"` — the two fields have now diverged in **both directions** simultaneously, and
`get_frame_material()` (still reading only `components["frame"]`) will keep reporting
`"carbon_fiber"` to every future caller (`_build_mutable_state`, any future Continuity/analyze
context) regardless of the iterate change the user just confirmed.

### 5.3 Secondary gap found while probing: `madera`

`iterate_domain._KNOWN_MATERIALS` recognizes `"madera"` (wood) as a valid material name and maps
it to itself as if it were a library canonical key. `library/materiales/_datos.json` has no
`"madera"` entry. `ComponentLibrary.has_material("madera")` returns `False`. If a user types
"cambiar material a madera" in the iterate wizard, `mutation_engine.apply_material_mutation`'s
`get_material(new_material)` call raises `KeyError`, which the docstring marks as
"→ propagates" — i.e. this is an **unhandled hard error path** for a material the system's own
vocabulary claims to know, distinct from the graceful `_estimate_material_impact` preview path
(§5.4), which does catch this case. This is a **new finding**, not previously registered.

### 5.4 Where the hazard is already handled gracefully (contrast case)

`iterate_interactive_session._estimate_material_impact` (lines 664-717) is the one call site that
*already* anticipates a `KeyError` from `get_material` — Bug 44 handling explicitly distinguishes
"unknown material" from "recognised but no physics data" and never crashes; it degrades to an
informative message. This shows the codebase already has the right instinct for this exact class
of problem in one place (materials with no library backing) but not for the other (materials with
inconsistent identity across state fields) — `apply_material_mutation` itself has no equivalent
guard for the current_material lookup and would crash if `structure.material` ever held a
non-library string (it currently never does, only because nothing writes non-library strings into
`structure.material` today — but nothing prevents it structurally).

---

## 6. G10 vs G9 / Design 3A boundary

- **G9** (Continuity catalog-gap blind to `catalog_ref`) is entirely inside
  `orchestrator.build_startup_context`'s motor catalog-gap block (`~:2747-2794`) and the motors
  library (`library/motores/_datos.json`, `MotorSpec`, `find_motors_for_requirements`). No
  `MaterialSpec`, `MATERIAL_MAP`, `_KNOWN_MATERIALS`, or frame `ComponentRule` symbol appears in
  that code path. Fixing G10 does not touch any G9 symbol, and vice versa — confirmed by
  independent grep, no shared functions.
- **Design 3A** ("material alias bug") in `PHYSICAL_COMPONENT_CATALOG_V1.md:104-105,212` is the
  narrow acquisition-keyword symptom (§3-§4 of this report). G10 is the broader finding: the
  alias gap is a *symptom* of a deeper three-vocabulary identity split (§5) that also produces a
  live, silent mass-calculation bug in the iterate path — something 3A's scope (documented as a
  "micro-fix") never anticipated.

---

## 7. Risks of a naive alias-only patch

If the next cut only expands `MATERIAL_MAP` and the frame keyword list to cover all 8 materials
(closing the coverage matrix in §4) without touching the identity model in §5:

1. **The dual-truth bug in §5.2 remains live and gets more exposure.** More materials become
   declarable through the wizard → more chances for `structure.material` and
   `components["frame"].material` to diverge → more silently-wrong mass computations on the next
   iterate material change.
2. **`MATERIAL_MAP`'s English-slug vocabulary would need to grow to 8 buckets**, permanently
   cementing a translation layer between acquisition and `get_material()` that the iterate path
   (`_KNOWN_MATERIALS`) has already shown is unnecessary — the library's own Spanish names work
   fine as the stored value there today.
3. **Two alias tables stay unreconciled** (`MATERIAL_MAP` vs `_KNOWN_MATERIALS`), doubling future
   maintenance (a 9th library material requires editing both, in two different vocabularies) and
   leaving the `madera` ghost-entry gap (§5.3) undiscovered/unfixed.
4. **No regression test would catch §5.2** — coverage-matrix tests (acquisition accepts all 8
   materials) would pass while the mutation-engine identity bug ships unnoticed, since that bug
   only manifests when a wizard-declared frame material is later changed via iterate — a
   cross-module interaction a narrow "did the keyword match" test wouldn't exercise.

---

## 8. Investigation checklist status (A1–A15)

| # | Status | Note |
|---|---|---|
| A1 | CONFIRMED | 8 materials, densities listed §Library data above |
| A2 | CONFIRMED | `_normalize_name` (library.py:24-27) strips accents/case — `plastico` already matches `plástico` at the library layer |
| A3 | CONFIRMED | `ComponentLibrary` is the sole `_datos.json` reader; callers: `mutation_engine.py`, `iterate_interactive_session.py`, `create_project.py` |
| A4 | CONFIRMED | `create_project`/`iterate.py` writers pass/produce library Spanish names; `aerial.py`/`component_writers.set_frame_material` pass/produce English `MATERIAL_MAP` slugs — two disjoint vocabularies feed the same conceptual field |
| A5 | CONFIRMED | Frame keywords (`aerial.py:482`) miss `plastico`/`pvc`/`titanio`/`acero`/`kevlar`/`magnesio` entirely |
| A6 | CONFIRMED | Gap table in §4; `MATERIAL_MAP` covers 3 of 8 library materials, under different (English) names |
| A7 | CONFIRMED | §4 matrix — `infer_component` vs `infer_component_for_key(...,"frame")` divergence measured directly |
| A8 | CONFIRMED | §3 turn-by-turn trace; propeller force exists (`orchestrator.py:1753-1758`), frame analogue absent |
| A9 | CONFIRMED | `set_frame_material` (`component_writers.py:71-74`) writes exactly the `material` argument it's given (the `MATERIAL_MAP` English slug) with no library round-trip |
| A10 | CONFIRMED + NEW FINDING | `_extract_material_from_text` uses `_KNOWN_MATERIALS`, a third, library-name-aligned table; contains `madera`, absent from the library (§5.3) |
| A11 | CONFIRMED (reproduced) | §5.2 — stale `structure.material` silently drives the wrong density ratio |
| A12 | CONFIRMED | `create_project._DEFAULT_MATERIAL = "aluminio"` matches `get_frame_material`'s hardcoded fallback string — consistent only by coincidence (independent literals, not a shared constant) |
| A13 | CONFIRMED | No deterministic list-materials intent; `intent_resolver.py` only treats `"material"`/`"materiales"` as an iterate-variable keyword (line 439), never a catalog query |
| A14 | NOT NEEDED FOR THIS CUT | Continuity startup-context display of "material estructural" not probed — out of scope per G9 boundary (§6); no G10-relevant dependency found |
| A15 | CONFIRMED | No shared symbols between G9's motor catalog-gap block and G10's material layers (§6) |

---

## 9. Probe log (P1–P5)

- **P1** — `default_library.list_materials()` → 8 `MaterialSpec` rows, names/densities listed §1 of design doc / library data above.
- **P2** — Coverage matrix, §4, executed against live `infer_component`/`infer_component_for_key`/`MATERIAL_MAP`/`_KNOWN_MATERIALS`.
- **P3** — Turn-by-turn trace of `"plastico 390g"` through `_handle_component_description`, §3 (static trace confirmed against the coverage matrix — `pvc`/`PPC` fail identically, `fibra de carbono` succeeds via keyword `"carbono"`).
- **P4** — Dual-name hazard reproduced end-to-end with real `ProjectState`/`set_frame_material`/`MutationEngine`, §5.2.
- **P5** — Real CLI LLM log (`src/jarvis/runtime/llm_logs/20260815T065705620512Z.json`) confirms `"que materiales tenemos en el catalogo?"` was routed to `mode: analyze, analyze_type: explanation` — the LLM path — never `list_materials()`.
