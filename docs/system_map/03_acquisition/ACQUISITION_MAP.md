# 03 — Acquisition

**Purpose.** Owns "what gap is missing and how do we ask about it" — mention resolution, the thin Brief, and the component/param wizards themselves. This is the subsystem FN-011 through FN-021 built up incrementally.

**Inbound:** C-031-C-035 (from Runtime IDLE/DEFINE_MISSING checkpoints), C-036 (from Continuity, shared read). **Outbound:** C-091 (writes via component_writers), C-037 (session lifecycle back to Runtime).

## Key modules

| Path | Role |
|---|---|
| `core/acquisition_target.py` | Mention/phrase resolution (FN-011…016): `resolve_acquisition_mention`, `is_mention_on_active_gap`, `is_help_define_pending_phrase`, `is_navigation_back_phrase`, `COMPONENT_TERM_ALIASES`, `COMPONENT_PROMPTS` |
| `core/acquisition_brief.py` | Thin Brief composer (FN-018): `build_acquisition_brief` |
| `core/param_definition_session.py` | `ParamDefinitionSession` — the numeric-param **and** component-definition wizard (`start`, `answer`, `try_ingest`, `apply_and_recalculate`) |
| `core/system_definition_session.py` | `SystemDefinitionSession` — architecture-block selection wizard, bridges into `param_definition_session` on completion |
| `core/motor_catalog_assist.py` | FN-005/009 assisted motor acquisition (catalog search, pick, honest no-candidate messaging) |

## Important functions (Level 2)

- `orchestrator._try_start_acquisition_from_mention` / `_continue_block_acquisition` — the Bug54/FN-011/013/014 bridge, reused by every acquisition-opening path (never duplicated — grep for `_set_pending_next_block` call sites to find all of them).
- `orchestrator._next_pending_block(project_state) -> (block_key, status) | None` — the closest thing to a real "Acquisition Target Authority"; shared with Continuity (C-036) and with `_set_pending_next_block`'s FN-021 clear-to-IDLE gate (C-037).
- `orchestrator._handle_component_description` — the component-wizard turn handler; as of FN-017/018/019 it: reads `expected_keys` defensively (B1), never silently writes `generic_component` when scoped (B4), shows a key-aware low-completeness follow-up via `acquisition_brief` instead of a generic prompt (B3/B5), and (FN-019) forces inference against the propellers rule directly when a bare size like `"10x4.5"` has no keyword to trigger the normal registry match.
- `param_definition_session.start(missing_params, reason)` — opens a wizard; for `MISSING_COMPONENT_DEFINITION` reasons, keeps `pending_missing_params` coherent with the live wizard (FN-017 B1) and uses `build_acquisition_brief` for the opening question (FN-018 C1b).
- `param_definition_session.answer(user_input)` — the numeric-wizard turn handler; guards component keys from ever receiving a bare float (FN-016), handles skip phrases, keyword-bidirectional parsing, and clears to IDLE on its own completion (`clear_runtime_session` at the "all params answered" branch — this is why C-043's iterate-side symptom is *not* replicated here; this wizard already self-clears).

## Local state touched

`InteractiveSessionState.pending_param_definitions`, `.collected_params`, `.param_definition_reason`, `.pending_define_missing`, `.pending_missing_params`, `.pending_missing_reason`, `.motor_suggestions`.

## LLM

NO — zero LLM involvement anywhere in this subsystem (verified: every FN-011…021 report explicitly used `_RefuseLLM` fixtures that raise on any LLM call, and all passed).

## Known issues owned by this subsystem

None currently open — this is the subsystem with the most FN coverage (FN-005, FN-009, FN-011, FN-013, FN-014, FN-015, FN-016, FN-017, FN-018, FN-019, FN-021) and the fewest remaining gaps. The only cross-subsystem gap it participates in is **C-025/C-044** (owned by Intent/Engineering, not Acquisition).

## Tests

`tests/test_fn005_*`, `test_assisted_acquisition.py`, `test_fn011_propulsion_declare_routing.py`, `test_fn013_active_block_declare_routing.py`, `test_fn014_acquisition_target_idle.py`, `test_fn015_pending_help.py`, `test_fn016_navigation_parse_safety.py`, `test_fn017_component_acquisition_plumbing.py`, `test_fn018_acquisition_brief.py`, `test_fn019_bare_propeller_size.py`, `test_fn021_session_hygiene.py`, `test_d4_param_gatekeeper.py`, `test_propulsion_composite_wizard_flow.py`, `test_system_definition_session.py`.
