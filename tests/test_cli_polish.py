"""CLI Polish Bundle (Implementation Contract acceptance tests).

Covers S1-S8 per .jes/artifacts/implementation_contract_cli_polish.md:
  T1-T2   S1 — G9-B catalog-gap ranking (demote on PASS + declared covers floor)
  T3-T6   S2 — G16-A/B list-motors global + CTA dedupe
  T7-T8   S3 — G18 aerial vs terrestrial "definir motores"
  T9-T10  S4 — G17 force-motors (+ G14/FN-019 regression guard)
  T11     S5 — G12/FN-013 stale pending vs fresh block
  T12-T13 S7 — G19 Continuity CTA bridge (genuine gap + demoted PASS)
  T14     S8 — G13 verification probe (closed as fixed by G10 ★2)
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from jarvis.core.intent_resolver import IntentResolver
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.parameter_requirements import MISSING_COMPONENT_DEFINITION, MISSING_PROPULSION_PARAMETERS
from jarvis.core.project_continuity import build_project_continuity
from jarvis.core.state_manager import OrchestratorMode
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue


class _FakeLLM:
    """Raises if called — proves a handler is 0-LLM."""

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called for this path")


_CREATE_PARAMS = {
    "vehicle_type": "dron",
    "objective": "dron de prueba cli polish",
    "payload_kg": 1.0,
    "restrictions": "ninguna",
    "detail_level": "conceptual",
    "motors": 4,
    "per_motor_max_thrust_n": 12.0,
    "structure_mass_factor": 0.5,
    "safety_factor": 1.2,
}


def _fresh_orchestrator(tmp_path):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    orchestrator.handle({"action": "create_project", "parameters": _CREATE_PARAMS})
    return orchestrator


def _open_component_wizard(orchestrator, pending_keys: list[str]):
    session = orchestrator.state_manager.runtime_state.session
    updated = session.model_copy(update={
        "mode": OrchestratorMode.DEFINE_MISSING_PARAMETERS,
        "pending_missing_reason": MISSING_COMPONENT_DEFINITION,
        "pending_missing_params": pending_keys,
        "pending_define_missing": False,
    })
    orchestrator.state_manager.set_runtime_session(updated)


def _open_thrust_wizard(orchestrator):
    session = orchestrator.state_manager.runtime_state.session
    updated = session.model_copy(update={
        "mode": OrchestratorMode.DEFINE_MISSING_PARAMETERS,
        "param_definition_reason": MISSING_PROPULSION_PARAMETERS,
        "pending_param_definitions": ["per_motor_max_thrust_n"],
    })
    orchestrator.state_manager.set_runtime_session(updated)


def _continuity_state(**kwargs):
    defaults = dict(
        latest_results={
            "simulation": {
                "status": "pass",
                "quality": "good",
                "safety_margin_ratio": 9.101,
                "can_fly": True,
                "warnings": [],
            },
            "calculations": {},
        },
        current_parameters={"motor_count": 6, "per_motor_max_thrust_n": 30.0},
        design_properties=SimpleNamespace(components={}),
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# ── S1 — G9-B catalog-gap ranking ──────────────────────────────────────────

def test_t1_pass_with_declared_thrust_covering_floor_demotes_gap():
    cont = build_project_continuity(
        project_state=_continuity_state(),
        status_type="nominal",
        status_reason=None,
        phase="complete",
        architecture_progress=None,
        next_architecture_label=None,
        next_block_status=None,
        proactive_question=None,
        suggested_action=None,
        physical_requirements={"thrust_per_motor_needed_n": 3.3},
        component_bom={"defined": [], "incomplete": [], "missing": [], "declarative": []},
        energy_model_note=None,
        motor_catalog_gap="Necesitas empuje ≥ 3.3 N/motor; no tengo un motor en el catálogo.",
        motor_catalog_matches=[],
    )
    assert "Declara empuje" not in cont["next_useful_step"]
    assert any("Catálogo:" in e for e in cont["evidence"])


def test_t2_pass_with_declared_thrust_under_floor_gap_still_wins():
    cont = build_project_continuity(
        project_state=_continuity_state(
            current_parameters={"motor_count": 6, "per_motor_max_thrust_n": 2.0}
        ),
        status_type="nominal",
        status_reason=None,
        phase="complete",
        architecture_progress=None,
        next_architecture_label=None,
        next_block_status=None,
        proactive_question=None,
        suggested_action=None,
        physical_requirements={"thrust_per_motor_needed_n": 3.3},
        component_bom={"defined": [], "incomplete": [], "missing": [], "declarative": []},
        energy_model_note=None,
        motor_catalog_gap="Necesitas empuje ≥ 3.3 N/motor; no tengo un motor en el catálogo.",
        motor_catalog_matches=[],
    )
    assert "Declara empuje" in cont["next_useful_step"]


# ── S2 — G16-A/B list-motors global + CTA dedupe ───────────────────────────

def test_t3_list_motors_phrases_resolve_deterministically():
    r = IntentResolver()
    assert r.resolve_intent("que motores tenemos en el catalogo?") == "list_motors"
    assert r.resolve_intent("¿qué motores hay?") == "list_motors"


def test_t4_idle_list_motors_is_deterministic_no_llm(tmp_path):
    orchestrator = _fresh_orchestrator(tmp_path)
    llm = _FakeLLM()

    for phrase in ("que motores tenemos en el catalogo", "¿que motores tenemos en el catalogo?"):
        result = orchestrator.handle_user_text(phrase, llm)
        assert result["status"] == "ok"
        assert result["action"] == "list_motors"
        assert result.get("motors")


def test_t5_list_motors_mid_thrust_wizard_keeps_wizard_open(tmp_path):
    orchestrator = _fresh_orchestrator(tmp_path)
    _open_thrust_wizard(orchestrator)

    result = orchestrator.handle_user_text(
        "que motores tenemos en el catalogo?", _FakeLLM()
    )

    assert result["action"] == "list_motors"
    sess = orchestrator.state_manager.runtime_state.session
    assert sess.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS
    assert sess.pending_param_definitions == ["per_motor_max_thrust_n"]


def test_t6_offer_catalog_help_cta_not_duplicated(tmp_path):
    orchestrator = _fresh_orchestrator(tmp_path)
    _open_thrust_wizard(orchestrator)

    result = orchestrator.param_definition_session.offer_catalog_help()

    assert "Elige un número" not in (result.get("message") or "")
    assert "Elige un número" in (result.get("question") or "")


# ── S3 — G18 aerial vs terrestrial "definir motores" ───────────────────────

def test_t7_aerial_definir_motores_not_terrestrial_transmission(tmp_path):
    orchestrator = _fresh_orchestrator(tmp_path)

    result = orchestrator.handle_user_text("definir motores", _FakeLLM())

    assert result.get("action") != "missing_transmission_parameters"
    message = (result.get("message") or "") + (result.get("question") or "")
    assert "par de torsión" not in message
    sess = orchestrator.state_manager.runtime_state.session
    assert sess.param_definition_reason != "missing_transmission_parameters"


def test_t8_terrestrial_definir_motores_still_opens_transmission_wizard(tmp_path):
    orchestrator = _fresh_orchestrator(tmp_path)
    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    project_state.current_parameters["vehicle_type"] = "robot"
    orchestrator.workspace_manager.save_state(project_state)

    result = orchestrator.handle_user_text("definir motores", _FakeLLM())

    sess = orchestrator.state_manager.runtime_state.session
    assert sess.param_definition_reason == "missing_transmission_parameters"
    assert "par de torsión" in (result.get("question") or "")


# ── S4 — G17 force-motors (+ G14/FN-019 regression guard) ──────────────────

def test_t9_composite_motor_shaped_phrase_forces_motors(tmp_path):
    orchestrator = _fresh_orchestrator(tmp_path)
    _open_component_wizard(orchestrator, ["motors", "propellers"])

    result = orchestrator.handle_user_text("4x 2306 2400KV 50W", _FakeLLM())

    assert "Motores registrados" in (result.get("message") or "")
    state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    assert state.design_properties.components.get("motors") is not None
    assert state.design_properties.components.get("propellers") is None


def test_t9b_singleton_motors_forces_bare_motor_phrase(tmp_path):
    orchestrator = _fresh_orchestrator(tmp_path)
    _open_component_wizard(orchestrator, ["motors"])

    result = orchestrator.handle_user_text("4x 2306 2400KV 50W", _FakeLLM())

    assert "Motores registrados" in (result.get("message") or "")
    state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    assert state.design_properties.components.get("motors") is not None


def test_t10_composite_bare_propeller_size_still_forces_propellers(tmp_path):
    """Regression guard (G14/FN-019): force-motors must not steal a bare 'NxP'
    propeller size just because the motors extractor's own motor_count regex
    also matches it (completeness='medium', not 'high' — see orchestrator.py)."""
    orchestrator = _fresh_orchestrator(tmp_path)
    _open_component_wizard(orchestrator, ["motors", "propellers"])

    result = orchestrator.handle_user_text("10x4.5", _FakeLLM())

    assert "Hélices registradas" in (result.get("message") or "")
    state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    assert state.design_properties.components.get("propellers") is not None
    assert state.design_properties.components.get("motors") is None


# ── S5 — G12/FN-013 stale pending vs fresh block ───────────────────────────

def test_t11_stale_pending_motors_rebuilds_fresh_battery_body(tmp_path):
    orchestrator = _fresh_orchestrator(tmp_path)
    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    motors_spec = ComponentSpec(
        component_type="propulsion_active",
        suggested_key="motors",
        completeness="high",
        properties={
            "motor_count": PropertyValue(value=4, unit=None),
            "kv_rating": PropertyValue(value=2400.0, unit="KV"),
            "power_w": PropertyValue(value=50.0, unit="W"),
        },
        source="declared",
    )
    dp = project_state.design_properties.model_copy(update={
        "system_defined": True,
        "system_priority": ["energy"],
        "components": {"motors": motors_spec},
    })
    orchestrator.workspace_manager.save_state(
        project_state.model_copy(update={"design_properties": dp})
    )
    session = orchestrator.state_manager.runtime_state.session.model_copy(update={
        # Stale: left over from a propulsion wizard turn that never advanced
        # past "motors" (e.g. propulsion became complete via a DSE apply /
        # component_sync that bypassed the wizard's own chaining).
        "pending_param_definitions": ["motors"],
    })
    orchestrator.state_manager.set_runtime_session(session)

    result = orchestrator._try_reprompt_active_block_declaration("definir bateria")

    assert result is not None
    message = (result.get("message") or "") + (result.get("question") or "")
    assert "batería" in message.lower() or "bateria" in message.lower()
    assert "motors" not in (result.get("pending") or [])


# ── S7 — G19 Continuity CTA bridge ─────────────────────────────────────────

def test_t12_genuine_gap_cta_mentions_list_motors_and_explore():
    cont = build_project_continuity(
        project_state=_continuity_state(
            current_parameters={"motor_count": 6, "per_motor_max_thrust_n": 2.0}
        ),
        status_type="nominal",
        status_reason=None,
        phase="complete",
        architecture_progress=None,
        next_architecture_label=None,
        next_block_status=None,
        proactive_question=None,
        suggested_action=None,
        physical_requirements={"thrust_per_motor_needed_n": 3.3},
        component_bom={"defined": [], "incomplete": [], "missing": [], "declarative": []},
        energy_model_note=None,
        motor_catalog_gap="Necesitas empuje ≥ 3.3 N/motor; no tengo un motor en el catálogo.",
        motor_catalog_matches=[],
    )
    assert "qué motores" in cont["next_useful_why"].lower()
    assert "explora opciones" in cont["next_useful_why"].lower()


def test_t13_demoted_pass_cta_mentions_list_motors_and_explore_no_declara():
    cont = build_project_continuity(
        project_state=_continuity_state(),
        status_type="nominal",
        status_reason=None,
        phase="complete",
        architecture_progress=None,
        next_architecture_label=None,
        next_block_status=None,
        proactive_question=None,
        suggested_action=None,
        physical_requirements={"thrust_per_motor_needed_n": 3.3},
        component_bom={"defined": [], "incomplete": [], "missing": [], "declarative": []},
        energy_model_note=None,
        motor_catalog_gap="Necesitas empuje ≥ 3.3 N/motor; no tengo un motor en el catálogo.",
        motor_catalog_matches=[],
    )
    assert "Declara empuje" not in cont["next_useful_step"]
    assert "qué motores" in cont["next_useful_why"].lower()
    assert "explora opciones" in cont["next_useful_why"].lower()


# ── S8 — G13 verification probe ────────────────────────────────────────────

def test_t14_iterate_material_compound_pvc_400g_extracts_and_estimates():
    """G13 re-verification (audit §4.2): could not reproduce the originally
    filed failure against current code — G10 ★2's single shared
    MATERIAL_ALIASES table already resolves 'pvc 400g' -> 'pvc' at both
    iterate-material entry points. Locks the fix as a regression test; no
    iterate_interactive_session.py change made (per contract S8 gating)."""
    from jarvis.core.iterate_interactive_session import IterateInteractiveSession
    from jarvis.schemas.action_schema import InteractiveSessionState, IterationDraft

    def _session_from_response(response: dict) -> InteractiveSessionState:
        return InteractiveSessionState(
            mode=OrchestratorMode(response["mode"]),
            step=response["step"],
            iteration_draft=IterationDraft.model_validate(response["iteration_draft"]),
        )

    session = IterateInteractiveSession()
    start = session.start({
        "project_id": "abc123",
        "project_slug": "dron-base",
        "workspace_path": "/tmp/dron-base-abc123",
        "objetivo": "peso",
        "operacion": "reducir",
    })
    current = _session_from_response(start)
    current = _session_from_response(session.answer(current, "sí"))
    current = _session_from_response(session.answer(current, "material"))
    current = _session_from_response(session.answer(current, "cambiar material"))

    named = session.answer(current, "PVC 400g")
    assert named["iteration_draft"]["value"] == "pvc"
    current = _session_from_response(named)

    impact = session.answer(current, "ninguna")
    assert "-12.2%" in impact["message"]
    assert "pvc" in impact["message"].lower()
    assert "no tengo datos físicos" not in impact["message"].lower()
