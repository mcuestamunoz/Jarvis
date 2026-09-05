# 03 — Acquisition

**Purpose.** Owns "what gap is missing and how do we ask about it" — mention resolution, the thin Brief, and the component/param wizards themselves. This is the subsystem FN-011 through FN-021 built up incrementally.

**Inbound:** C-031-C-035 (from Runtime IDLE/DEFINE_MISSING checkpoints), C-036 (from Continuity, shared read). **Outbound:** C-091 (writes via component_writers), C-037 (session lifecycle back to Runtime).

## Key modules

| Path | Role |
|---|---|
| `core/acquisition_target.py` | Mention/phrase resolution (FN-011…016, FN-ESC): `resolve_acquisition_mention`, `is_mention_on_active_gap`, `is_define_missing_confusion_phrase` (G23 — anti-LLM confusion gate only; formerly `is_help_define_pending_phrase`/FN-015, the acquisition-help *feature* built on it was removed in full), `is_navigation_back_phrase`, `COMPONENT_TERM_ALIASES` (includes `esc`), `COMPONENT_PROMPTS` (includes `esc`) |
| `core/acquisition_brief.py` | Thin Brief composer (FN-018): `build_acquisition_brief` |
| `core/param_definition_session.py` | `ParamDefinitionSession` — the numeric-param **and** component-definition wizard (`start`, `answer`, `try_ingest`, `apply_and_recalculate`) |
| `core/system_definition_session.py` | `SystemDefinitionSession` — architecture-block selection wizard, bridges into `param_definition_session` on completion |
| `core/motor_catalog_assist.py` | FN-005/009 assisted motor acquisition (catalog search, pick, honest no-candidate messaging) |
| `core/battery_catalog_assist.py` | IC 2 — assisted battery acquisition (numbered SKU list from `ComponentLibrary.list_batteries`, pick → `bind_battery_from_catalog`) |
| `core/frame_catalog_assist.py` | Structure Catalog IC-3 — assisted frame acquisition (numbered SKU list / pick → bind + part projection) |
| `core/catalog_rebind_assist.py` | IDLE rebind B2+B3 — `resolve_idle_catalog_rebind(phrase)` maps pure component phrases to family reopen after architecture 4/4 |
| `core/catalog_bind.py` | `bind_motor_from_catalog` / `bind_propeller_from_catalog` / `bind_battery_from_catalog` / `bind_frame_from_catalog` / `frame_part_specs_from_catalog` — shared bind primitive; projects arm thickness + curated ordinal plates when seeded; `invalidate_diverged_catalog_refs` (G5 / G24D / frame diverge) |

## Important functions (Level 2)

- `orchestrator._try_start_acquisition_from_mention` / `_continue_block_acquisition` — the Bug54/FN-011/013/014 bridge, reused by every acquisition-opening path (never duplicated — grep for `_set_pending_next_block` call sites to find all of them).
- `orchestrator._next_pending_block(project_state) -> (block_key, status) | None` — the closest thing to a real "Acquisition Target Authority"; shared with Continuity (C-036) and with `_set_pending_next_block`'s FN-021 clear-to-IDLE gate (C-037).
- `orchestrator._handle_component_description` — the component-wizard turn handler; as of FN-017/018/019 it: reads `expected_keys` defensively (B1), never silently writes `generic_component` when scoped (B4), shows a key-aware low-completeness follow-up via `acquisition_brief` instead of a generic prompt (B3/B5), and (FN-019) forces inference against the propellers rule directly when a bare size like `"10x4.5"` has no keyword to trigger the normal registry match. **Polish S4 (G17):** when `"motors" in expected_keys` and inferred completeness is `"high"`, force-motors bind runs before force-propellers (mirror FN-019 / G10 force-frame). **FN-ESC (ERF-2):** out-of-scope explicit save via `OUT_OF_SCOPE_EXPLICIT_SAVE_KEYS = {"esc"}` — when wizard expects a different key but user says `"esc 30a"`, ESC is saved anyway (C-112); narrow `user_explicitly_named_component()` gate avoids cross-contamination. **Structure B G-N1 (2026-09-04):** when applying a frame spec, raw user text may also upsert `frame_*` part children (`extract_all_frame_part_properties` + `upsert_frame_part`); a parts-only follow-up (existing non-low frame, no new root mass/size/config/wheelbase) upserts children without rewriting root material. Free-text plate clauses stay single-key (no ordinal siblings — N4 debt). Residual: some IDLE paths still need `motores` keyword prefix.
- **IDLE catalog rebind B2+B3 (2026-09-04):** after architecture 4/4, pure phrases (`"cambiar frame"`, motors/propellers/battery equivalents) via `resolve_idle_catalog_rebind` reopen that family’s catalog assist. Frame re-pick runs `clear_frame_part_children` then `frame_part_specs_from_catalog` → `upsert_frame_part` (arms thickness + curated plates when seeded). Pure-phrase only (no trailing SKU); mid-architecture FN-014 preserved.
- `orchestrator._fresh_pending_keys_for_block` — **polish S5 (FN-013):** syncs `pending_param_definitions` to the named architecture block before building reprompt briefs (fixes stale motors body when header says energy/battery).
- `orchestrator._handle_list_motors` / `_handle_list_materials` — deterministic catalog listings (G10 ★8 / polish S2); 0 LLM; orchestrator soft-interrupt before analyze in wizard and IDLE.
- **Catalog pick UX (G21 / v0.3.0 propeller / IC 2 battery):** `_offer_component_motor_catalog` / `_apply_component_motor_catalog_pick`, `_offer_component_propeller_catalog` / `_apply_component_propeller_catalog_pick`, `_offer_component_battery_catalog` / `_apply_component_battery_catalog_pick` — numbered list → pick N → `bind_*_from_catalog` → `set_*_component`. Orchestrator battery pick calls `set_battery_component` only; that writer's tail may **conditionally** re-call `set_motor_component` when stored OP was never voltage-validated or pack voltage is incompatible (v0.3.4 MOP-2 — preserves P2-2/IC2 when already validated at same voltage). IDLE `"ayúdame a elegir"` paths mirror component-wizard shape.
- `param_definition_session.apply_and_recalculate` — **IC 1 (G26):** mid-session write of `current_parameters["restrictions"]` for constraint phrases; **`is_derived` gate** rejects direct writes of derived params (e.g. loose `autonomia=15`). Re-derives `parsed_constraints` via `ProjectState.model_copy` on save.
- `param_definition_session.start(missing_params, reason)` — opens a wizard; for `MISSING_COMPONENT_DEFINITION` reasons, keeps `pending_missing_params` coherent with the live wizard (FN-017 B1) and uses `build_acquisition_brief` for the opening question (FN-018 C1b).
- `param_definition_session.answer(user_input)` — the numeric-wizard turn handler; guards component keys from ever receiving a bare float (FN-016), handles skip phrases, keyword-bidirectional parsing, and clears to IDLE on its own completion (`clear_runtime_session` at the "all params answered" branch — this is why C-043's iterate-side symptom is *not* replicated here; this wizard already self-clears).

## Local state touched

`InteractiveSessionState.pending_param_definitions`, `.collected_params`, `.param_definition_reason`, `.pending_define_missing`, `.pending_missing_params`, `.pending_missing_reason`, `.motor_suggestions`.

## LLM

NO — zero LLM involvement anywhere in this subsystem (verified: every FN-011…021 report explicitly used `_RefuseLLM` fixtures that raise on any LLM call, and all passed).

## Known issues owned by this subsystem

- **G8 (SYS-MAP-004)** — while `DEFINE_MISSING_PARAMETERS` is open with `MISSING_COMPONENT_DEFINITION`, UX-C's `_handle_component_description` intercept swallows turns that classifiers already resolve as engineering intent / explore (`reducir payload`, `optimiza payload`, `explora opciones`), so Runtime never reaches C-040. Cross-cutting with Runtime (mode branch owns the return). **Registered only** — needs R3 preempt-policy design before any FN; do not port C-052 verbatim (`collected_params`). See `.jes/artifacts/cli_findings_post_catalog_bind_v1.md` G8 and `CONNECTIONS.md` C-040 caveat.
- **G12 (partial S5, 2026-08-18)** — `definir bateria` → battery body fixed via `_fresh_pending_keys_for_block`; other acquisition→acquisition retarget paths may still require `cancelar` (R3).
- **G17 residual** — force-motors in wizard; bare `4x 2306…` at IDLE may still route to analyze.
- **G14** — bare `10x4.5` at IDLE may route to analyze instead of propellers acquisition (prefix `helices` works).
- Historical note: C-025/C-044 (help+goal) were Intent/Engineering-owned and are now 🟢 (FN-025).

## Tests

`tests/test_fn005_*`, `test_assisted_acquisition.py`, `test_fn011_propulsion_declare_routing.py`, `test_fn013_active_block_declare_routing.py`, `test_fn014_acquisition_target_idle.py`, `test_fn015_pending_help.py`, `test_fn016_navigation_parse_safety.py`, `test_fn017_component_acquisition_plumbing.py`, `test_fn018_acquisition_brief.py`, `test_fn019_bare_propeller_size.py`, `test_fn021_session_hygiene.py`, `test_d4_param_gatekeeper.py`, `test_propulsion_composite_wizard_flow.py`, `test_system_definition_session.py`, **`tests/test_cli_polish.py`**, **`tests/test_fn_esc_acquisition.py`** (ERF-2 FN-ESC, 6 tests), **`tests/test_propeller_catalog_bind_ux.py`**, **`tests/test_battery_catalog_bind_ux.py`**, **`tests/test_requirements_closure.py`**, **`tests/test_frame_catalog_bind_ux.py`**, **`tests/test_idle_frame_rebind_b2.py`**, **`tests/test_idle_catalog_rebind_b3.py`**, **`tests/test_frame_parts_graph_v1.py`**, **`tests/test_frame_parts_freetext_gn1.py`**.
