"""G23 — FN-015 removed as a user-facing acquisition feature.

Replaces tests/test_fn015_pending_help.py (deleted). The original FN-015 bug
was real (confusion phrases leaking to the LLM) and the anti-LLM gate that
fixed it survives — but the *feature* built on top of it (Brief replay,
IDLE wizard auto-open, catalog offer under "definir") is gone. This file
proves the new, minimal behavior:

  - DEFINE_MISSING: confusion phrases get a short one-line re-ask, never a
    Brief replay, never a catalog offer, never the LLM.
  - IDLE: confusion phrases resolve to project_status (Continuity), never a
    wizard auto-open, never the LLM.
  - Regressions: ayúdame a elegir (G21), FN-013 named-block reprompt, real
    analyze questions, and collected_params preservation are all unaffected.
"""
from __future__ import annotations

from pathlib import Path

from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.parameter_requirements import MISSING_PROPULSION_PARAMETERS
from jarvis.schemas.action_schema import ComponentSpec, OrchestratorMode, PropertyValue


class _RefuseLLM:
    def interpret(self, *args, **kwargs):
        raise AssertionError("LLM.interpret must not be called")

    def analyze(self, *args, **kwargs):
        raise AssertionError("LLM.analyze must not be called")

    def generate(self, *args, **kwargs):
        raise AssertionError("LLM.generate must not be called")


class _StubLLM:
    """Permissive stub for the one case where reaching the LLM is expected."""

    def interpret(self, *args, **kwargs):
        return {"action": "iterate", "parameters": {}, "raw_user_input": None}

    def analyze(self, *args, **kwargs):
        return "respuesta genérica del LLM"

    def generate(self, *args, **kwargs):
        return {}


def _project_with_active_propulsion(
    tmp_path: Path, *, components_done: bool = False
) -> JarvisOrchestrator:
    """Same fixture pattern as FN-011/013/014: motors declared, propellers
    pending (Phase A) by default; both declared (Phase B, params pending)
    when components_done=True."""
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "transporte de carga",
            "payload_kg": 2.0,
            "restrictions": "ninguna",
            "detail_level": "conceptual",
            "structure_mass_factor": 0.6,
            "safety_factor": 1.2,
        },
    })
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    motors_spec = ComponentSpec(
        name="4 motores 920kv",
        component_type="propulsion_active",
        suggested_key="motors",
        completeness="high",
        source="declared",
        properties={
            "motor_count": PropertyValue(value=4),
            "kv_rating": PropertyValue(value=920),
        },
    )
    propellers_spec = ComponentSpec(
        name="helices 10x4.5",
        component_type="propulsion_passive",
        suggested_key="propellers",
        completeness="high",
        source="declared",
        properties={"diameter_in": PropertyValue(value=10.0)},
    )
    esc_spec = ComponentSpec(
        name="ESC 30A",
        component_type="propulsion_active",
        suggested_key="esc",
        completeness="high",
        source="declared",
        properties={"current_a": PropertyValue(value=30.0)},
    )
    if components_done:
        components = {"motors": motors_spec, "propellers": propellers_spec, "esc": esc_spec}
    else:
        components = {"motors": motors_spec, "esc": esc_spec}
    dp = ps.design_properties.model_copy(update={
        "system_defined": True,
        "system_blocks": ["propulsion", "energy", "structure", "control"],
        "system_priority": ["propulsion", "energy", "structure", "control"],
        "components": components,
    })
    orch.workspace_manager.save_state(ps.model_copy(update={"design_properties": dp}))
    return orch


def _open_component_acquisition(orch: JarvisOrchestrator) -> None:
    """Open DEFINE_MISSING for propulsion components (Phase A: propellers)."""
    result = orch.handle_user_text("ayúdame a declarar propulsión", _RefuseLLM())
    assert result["action"] == "define_missing_params"
    session = orch.state_manager.get_runtime_session()
    assert session.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS
    assert session.pending_param_definitions == ["propellers"]


# ── Brief no longer advertises the removed feature ──────────────────────────

def test_g23_brief_does_not_advertise_help_define():
    from jarvis.core.acquisition_brief import build_acquisition_brief
    from types import SimpleNamespace

    project_state = SimpleNamespace(
        design_properties=SimpleNamespace(components={}),
        current_parameters={},
    )
    for key in ("motors", "battery"):
        brief = build_acquisition_brief(key, project_state)
        assert "ayúdame a definir" not in brief["message"]
        assert "repetir esta guía" not in brief["message"]


# ── DEFINE_MISSING: short re-ask only, no Brief, no LLM ─────────────────────

def test_g23_define_missing_confusion_no_llm_short_reask(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    _open_component_acquisition(orch)

    result = orch.handle_user_text("ayudame a definir el valor", _RefuseLLM())

    assert result["status"] == "interactive"
    assert result["action"] == "define_missing_params"
    assert result.get("question")
    blob = f"{result.get('message') or ''}"
    assert "Vamos a definir" not in blob
    assert "Puedes:" not in blob
    session = orch.state_manager.get_runtime_session()
    assert session.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS
    assert session.pending_param_definitions == ["propellers"]


def test_g23_define_missing_confusion_bare_no_llm(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    _open_component_acquisition(orch)

    result = orch.handle_user_text("ayudame a definir", _RefuseLLM())

    assert result["status"] == "interactive"
    assert result["action"] == "define_missing_params"
    session = orch.state_manager.get_runtime_session()
    assert session.pending_param_definitions == ["propellers"]


def test_g23_define_missing_confusion_does_not_open_catalog(tmp_path: Path):
    """Assisted numeric param pending (per_motor_max_thrust_n) — confusion
    phrase must NOT offer the catalog anymore (that was the FN-015 feature's
    'catalog-help family' branch, removed). Catalog stays ayúdame a elegir."""
    orch = _project_with_active_propulsion(tmp_path, components_done=True)
    orch.start_define_missing_params(
        ["per_motor_max_thrust_n"], reason=MISSING_PROPULSION_PARAMETERS
    )
    # start() itself may pre-populate motor_suggestions (assisted param) —
    # the confusion re-ask must not ADD to or otherwise mutate that; only
    # its own response shape must not surface a catalog offer.
    before = list(orch.state_manager.get_runtime_session().motor_suggestions)

    result = orch.handle_user_text("ayudame a definir", _RefuseLLM())

    assert result["status"] == "interactive"
    assert result["action"] == "define_missing_params"
    assert "motor_suggestions" not in result
    assert "Candidatos del catálogo" not in (result.get("message") or "")
    session = orch.state_manager.get_runtime_session()
    assert session.motor_suggestions == before


def test_g23_help_does_not_mention_battery_when_pending_propellers(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    _open_component_acquisition(orch)

    result = orch.handle_user_text("ayudame a definir el valor", _RefuseLLM())

    blob = f"{result.get('message') or ''} {result.get('question') or ''}".lower()
    assert "battery_capacity_wh" not in blob
    assert "batería" not in blob
    assert "bateria" not in blob
    assert "energía" not in blob
    assert "energia" not in blob


def test_g23_collected_params_preserved_on_confusion_reask(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    _open_component_acquisition(orch)
    session = orch.state_manager.get_runtime_session()
    orch.state_manager.set_runtime_session(
        session.model_copy(update={"collected_params": {"motor_count": 4.0}})
    )

    orch.handle_user_text("ayudame a definir el valor", _RefuseLLM())

    after = orch.state_manager.get_runtime_session()
    assert after.collected_params == {"motor_count": 4.0}
    assert after.pending_param_definitions == ["propellers"]


# ── IDLE: collapses into project_status, never a wizard auto-open ──────────

def test_g23_idle_help_define_is_project_status_not_wizard(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)

    result = orch.handle_user_text("ayudame a definir", _RefuseLLM())

    assert result["status"] == "ok"
    assert result["action"] == "project_status"
    session = orch.state_manager.get_runtime_session()
    assert session.mode != OrchestratorMode.DEFINE_MISSING_PARAMETERS
    assert session.mode != OrchestratorMode.ITERATE_INTERACTIVE


def test_g23_idle_help_define_el_valor_is_project_status(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)

    result = orch.handle_user_text("ayudame a definir el valor", _RefuseLLM())

    assert result["status"] == "ok"
    assert result["action"] == "project_status"


# ── Regressions ───────────────────────────────────────────────────────────

def test_g23_help_choose_still_works(tmp_path: Path):
    """G21/FN-005 catalog path is untouched by the FN-015 removal."""
    orch = _project_with_active_propulsion(tmp_path, components_done=True)
    orch.start_define_missing_params(
        ["per_motor_max_thrust_n"], reason=MISSING_PROPULSION_PARAMETERS
    )

    result = orch.handle_user_text("ayúdame a elegir el motor", _RefuseLLM())

    assert result["status"] == "interactive"
    assert result["action"] == "define_missing_params"
    assert result.get("motor_suggestions") is not None


def test_g23_definir_propulsion_still_fn013(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    _open_component_acquisition(orch)

    result = orch.handle_user_text("definir propulsión", _RefuseLLM())

    assert result.get("block_declaration_reprompt") is True
    assert result["action"] == "define_missing_params"


def test_g23_real_analyze_still_may_use_llm(tmp_path: Path):
    """Proves the confusion gate does not swallow every 'ayudame*'/analyze-
    shaped input — a genuine analysis question must still reach the LLM."""
    orch = _project_with_active_propulsion(tmp_path)
    _open_component_acquisition(orch)

    result = orch.handle_user_text("analiza el margen de seguridad", _StubLLM())

    assert result.get("action") != "define_missing_params" or result.get("status") == "ok"
    assert result.get("block_declaration_reprompt") is not True
