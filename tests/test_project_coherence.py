"""Project Coherence — FN-001…004 thin fixes."""
from __future__ import annotations

from types import SimpleNamespace
from pathlib import Path

import pytest

from jarvis.adapters.cli.main import (
    render_response,
    render_startup_context,
    should_auto_start_define_on_load,
)
from jarvis.core.intent_resolver import IntentResolver
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.parameter_requirements import (
    DEFAULT_MISSING_FORCE_REASON,
    MISSING_COMPONENT_DEFINITION,
)
from jarvis.core.project_closure import build_component_bom, format_bom_lines
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue


# ── FN-001: no auto-define on load when Continuity suffices ───────────────────


def test_should_auto_start_define_empty_missing_false():
    assert should_auto_start_define_on_load({
        "missing_params": [],
        "proactive_question": "Siguiente: declara hélices",
        "status_type": "nominal",
        "param_definition_reason": DEFAULT_MISSING_FORCE_REASON,
    }) is False


def test_should_auto_start_define_blocking_with_params_true():
    assert should_auto_start_define_on_load({
        "missing_params": ["per_motor_max_thrust_n"],
        "status_type": "blocking",
        "param_definition_reason": DEFAULT_MISSING_FORCE_REASON,
    }) is True


def test_should_auto_start_define_component_reason_true():
    assert should_auto_start_define_on_load({
        "missing_params": ["frame"],
        "status_type": "nominal",
        "param_definition_reason": MISSING_COMPONENT_DEFINITION,
    }) is True


def test_should_auto_start_define_proactive_only_false():
    """FN-001: Continuity next step alone must not open the wizard."""
    assert should_auto_start_define_on_load({
        "missing_params": [],
        "proactive_question": "¿Definimos parámetros pendientes?",
        "status_type": "nominal",
        "continuity": {"next_useful_step": "Declara hélices reales"},
    }) is False


# ── FN-002/003: detalles → project_status + Continuity-first render ───────────


@pytest.mark.parametrize(
    "text",
    [
        "dame detalles del proyecto",
        "dame detalles",
        "detalles del proyecto",
        "cuentame el proyecto",
        "cuéntame el proyecto",
        "resume el diseño",
    ],
)
def test_details_phrases_resolve_to_project_status(text):
    assert IntentResolver().resolve_intent(text) == "project_status"


def test_render_hides_fase_completado_when_continuity_present():
    text = render_startup_context({
        "has_project": True,
        "project_slug": "cam-800g",
        "objective": "transportar cámara",
        "phase": "complete",
        "status_type": "nominal",
        "suggested_action": {"label": "Aumentar carga útil", "hint": "margen"},
        "continuity": {
            "situation": "Diseño validado (PASS).",
            "evidence": ["Simulación pass"],
            "next_useful_step": "Declara hélices con diámetro real.",
            "next_useful_why": "BOM incompleto",
        },
    })
    assert "Situación:" in text
    assert "Siguiente paso:" in text
    assert "Fase: completado" not in text
    assert "Aumentar carga útil" not in text


# ── P2: motor_count in params ⇒ no “número de motores” BOM gap ────────────────


def test_bom_no_motor_count_gap_when_param_set():
    state = SimpleNamespace(
        current_parameters={"motor_count": 6},
        design_properties=SimpleNamespace(
            components={
                "motors": ComponentSpec(
                    name="motores",
                    component_type="propulsion_active",
                    completeness="medium",
                    missing_fields=["número de motores", "empuje"],
                    properties={"kv": PropertyValue(value=920)},
                )
            },
            system_blocks=["propulsion"],
            system_defined=True,
            system_priority=["propulsion"],
        ),
    )
    bom = build_component_bom(state)
    motors_entries = [e for e in (bom["incomplete"] + bom["defined"] + bom["declarative"]) if e["key"] == "motors"]
    assert motors_entries
    fields = motors_entries[0]["missing_fields"]
    assert "número de motores" not in fields
    assert "motor_count" not in fields
    assert "empuje" in fields
    lines = "\n".join(format_bom_lines(bom))
    assert "número de motores" not in lines.lower()
    assert "numero de motores" not in lines.lower()


# ── FN-004: structural confirm 6→4 ────────────────────────────────────────────


def _project_with_six_motors(tmp_path: Path) -> JarvisOrchestrator:
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "cámara 800g",
            "payload_kg": 0.8,
            "restrictions": "autonomía mínima 25 minutos",
            "detail_level": "conceptual",
            "motors": 6,
            "per_motor_max_thrust_n": 12.0,
            "structure_mass_factor": 0.5,
            "safety_factor": 1.2,
        },
    })
    return orch


def test_structural_confirm_asks_before_replacing_motor_count(tmp_path: Path):
    orch = _project_with_six_motors(tmp_path)
    result = orch.param_definition_session.apply_and_recalculate({"motor_count": 4})
    assert result["status"] == "interactive"
    assert result["action"] == "structural_confirm"
    assert "6" in result["message"] and "4" in result["message"]
    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    assert saved.current_parameters.get("motor_count") == pytest.approx(6.0)


def test_structural_confirm_yes_applies(tmp_path: Path):
    orch = _project_with_six_motors(tmp_path)
    orch.param_definition_session.apply_and_recalculate({"motor_count": 4})
    result = orch.handle_user_text("sí", llm_interface=None)
    assert result["status"] == "ok"
    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    assert saved.current_parameters.get("motor_count") == pytest.approx(4.0)
    assert orch.state_manager.get_runtime_session().pending_structural_change is None


def test_structural_confirm_no_preserves(tmp_path: Path):
    orch = _project_with_six_motors(tmp_path)
    orch.param_definition_session.apply_and_recalculate({"motor_count": 4})
    result = orch.handle_user_text("no", llm_interface=None)
    assert result["status"] == "cancelled"
    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    assert saved.current_parameters.get("motor_count") == pytest.approx(6.0)
    assert orch.state_manager.get_runtime_session().pending_structural_change is None


def test_four_motores_cli_asks_confirm(tmp_path: Path):
    """P0: natural CLI phrase must not silent-replace motor_count."""
    orch = _project_with_six_motors(tmp_path)
    result = orch.handle_user_text("4 motores", llm_interface=None)
    assert result["action"] == "structural_confirm"
    assert result["status"] == "interactive"
    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    assert saved.current_parameters.get("motor_count") == pytest.approx(6.0)

    confirmed = orch.handle_user_text("sí", llm_interface=None)
    assert confirmed["status"] == "ok"
    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    assert saved.current_parameters.get("motor_count") == pytest.approx(4.0)


def test_cancelar_clears_structural_confirm(tmp_path: Path):
    orch = _project_with_six_motors(tmp_path)
    orch.param_definition_session.apply_and_recalculate({"motor_count": 4})
    result = orch.handle_user_text("cancelar", llm_interface=None)
    assert result["status"] == "cancelled"
    assert orch.state_manager.get_runtime_session().pending_structural_change is None
    saved = orch.state_manager.load_active_project(orch.workspace_manager)
    assert saved.current_parameters.get("motor_count") == pytest.approx(6.0)


def test_structural_confirm_clears_pending_define_missing(tmp_path: Path):
    orch = _project_with_six_motors(tmp_path)
    session = orch.state_manager.get_runtime_session()
    orch.state_manager.set_runtime_session(
        session.model_copy(
            update={
                "pending_define_missing": True,
                "pending_missing_params": ["propellers"],
            }
        )
    )
    orch.param_definition_session.apply_and_recalculate({"motor_count": 4})
    assert orch.state_manager.get_runtime_session().pending_define_missing is False
    assert orch.state_manager.get_runtime_session().pending_structural_change
    orch.handle_user_text("sí", llm_interface=None)
    # Flag must stay cleared — next affirmative must not reopen define wizard
    assert orch.state_manager.get_runtime_session().pending_define_missing is False
    assert orch.state_manager.get_runtime_session().pending_structural_change is None


def test_iterate_motor_count_asks_confirm(tmp_path: Path):
    from jarvis.schemas.action_schema import ActionName, IterationDraft, IterationOperation

    orch = _project_with_six_motors(tmp_path)
    state = orch.state_manager.load_active_project(orch.workspace_manager)
    draft = IterationDraft(
        project_id=state.project_id,
        workspace_path=state.workspace_path,
        project_slug=state.project_slug,
        operation=IterationOperation.REDUCE,
        variable="motores",
        value="4",
        objective="reducir motores",
    )
    result = orch.router.resolve(ActionName.ITERATE).run({"iteration_draft": draft.model_dump()})
    assert result["action"] == "structural_confirm"
    assert result["status"] == "interactive"
    assert orch.state_manager.load_active_project(orch.workspace_manager).current_parameters[
        "motor_count"
    ] == pytest.approx(6.0)

    confirmed = orch.handle_user_text("sí", llm_interface=None)
    assert confirmed["status"] == "ok"
    assert orch.state_manager.load_active_project(orch.workspace_manager).current_parameters[
        "motor_count"
    ] == pytest.approx(4.0)


# ── P4: coherence footer on ok ops ────────────────────────────────────────────


def test_attach_project_coherence_on_define_ok(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "prueba coherencia",
            "payload_kg": 1.0,
            "restrictions": "ninguna",
            "detail_level": "conceptual",
            "structure_mass_factor": 0.5,
            "safety_factor": 1.2,
        },
    })
    raw = orch.param_definition_session.apply_and_recalculate(
        {"motor_count": 4, "per_motor_max_thrust_n": 15.0}
    )
    assert raw["status"] == "ok"
    attached = orch.attach_project_coherence(raw)
    assert attached.get("coherence_footer") or attached.get("continuity")
    footer = attached.get("coherence_footer") or attached.get("continuity")
    assert footer.get("situation") or footer.get("next_useful_step")

    rendered = render_response({
        **attached,
        "project_change_summary": attached.get("project_change_summary") or "motores → 4",
    })
    assert "Estado:" in rendered or "Siguiente paso:" in rendered
    assert "Cambio:" in rendered


def test_attach_skips_interactive_and_errors(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    assert orch.attach_project_coherence({"status": "interactive", "action": "define_missing_params"}) == {
        "status": "interactive",
        "action": "define_missing_params",
    }
    assert orch.attach_project_coherence({"status": "error", "action": "iterate"})["status"] == "error"
