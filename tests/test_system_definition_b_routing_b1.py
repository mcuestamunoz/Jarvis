"""SYSTEM_DEFINITION B routing vs global intercept B1
(`B1-system-definition-b-routing`).

Covers implementation_contract_system_definition_b_routing_b1.md §2:

  T1  Fresh create -> B -> "payload" via orchestrator -> message contains
      "añadido" (block), not "Estoy definiendo payload_bay" / not
      component_description_saved
  T2  Same path -> "manipulador" -> block añadido
  T3  "ruedas" -> "actuation" añadido (alias path)
  T4  "gearbox" -> "transmission" añadido
  T5  Mid step 1: "añadir bloques" -> no new entry in custom_blocks;
      message still asks for blocks/listo; not "bloque custom"
  T6  After "listo", components include payload_bay/arm/wheels/gearbox
  T7  IDLE regression: with system already defined, free-text identity
      still reaches component save/intercept as before
  T8  Full pytest green (checked at the repo level)
"""
from __future__ import annotations

from pathlib import Path

from jarvis.core.orchestrator import JarvisOrchestrator


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


def _orch_in_mode_b(tmp_path: Path, objective: str = "prueba") -> JarvisOrchestrator:
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": objective, "payload_kg": 1.0,
            "restrictions": "no", "detail_level": "detallado",
            "structure_mass_factor": 0.5, "safety_factor": 1.2,
        },
    })
    project_state = orch.state_manager.load_active_project(orch.workspace_manager)
    orch.system_definition_session.start("dron", project_state)
    orch.system_definition_session.answer("b")
    return orch


# ── T1 ────────────────────────────────────────────────────────────────────


def test_t1_payload_via_orchestrator_routes_to_block_not_component(tmp_path: Path):
    orch = _orch_in_mode_b(tmp_path)
    result = orch.handle_user_text("payload", _RefuseLLM())
    assert "añadido" in result["message"]
    assert "Estoy definiendo" not in result["message"]
    assert result.get("action") != "component_description_saved"
    assert result.get("action") != "component_description_prompt"


# ── T2 ────────────────────────────────────────────────────────────────────


def test_t2_manipulador_via_orchestrator_routes_to_block(tmp_path: Path):
    orch = _orch_in_mode_b(tmp_path)
    result = orch.handle_user_text("manipulador", _RefuseLLM())
    assert "añadido" in result["message"]
    assert "manipulation" in result["message"]
    assert result.get("action") != "component_description_saved"


# ── T3 ────────────────────────────────────────────────────────────────────


def test_t3_ruedas_via_orchestrator_routes_to_actuation_block(tmp_path: Path):
    orch = _orch_in_mode_b(tmp_path)
    result = orch.handle_user_text("ruedas", _RefuseLLM())
    assert "añadido" in result["message"]
    assert "actuation" in result["message"]
    assert result.get("action") != "component_description_saved"


# ── T4 ────────────────────────────────────────────────────────────────────


def test_t4_gearbox_via_orchestrator_routes_to_transmission_block(tmp_path: Path):
    orch = _orch_in_mode_b(tmp_path)
    result = orch.handle_user_text("gearbox", _RefuseLLM())
    assert "añadido" in result["message"]
    assert "transmission" in result["message"]
    assert result.get("action") != "component_description_saved"


# ── T5 ────────────────────────────────────────────────────────────────────


def test_t5_meta_add_more_phrase_is_noop(tmp_path: Path):
    orch = _orch_in_mode_b(tmp_path)
    result = orch.handle_user_text("añadir bloques", _RefuseLLM())
    assert "bloque custom" not in result["message"].lower()
    assert result["status"] == "interactive"

    session = orch.state_manager.get_runtime_session()
    assert session.memory_context.get("custom_blocks") == []

    # Still asking for a block name / listo, not silently exited
    assert "listo" in result["message"].lower()


def test_t5_meta_phrases_english_and_variants_all_noop(tmp_path: Path):
    for phrase in ("add blocks", "add block", "más bloques", "mas bloques", "otro bloque", "anadir bloques"):
        orch = _orch_in_mode_b(tmp_path / phrase.replace(" ", "_"))
        result = orch.handle_user_text(phrase, _RefuseLLM())
        session = orch.state_manager.get_runtime_session()
        assert session.memory_context.get("custom_blocks") == [], phrase
        assert result["status"] == "interactive", phrase


def test_t5_payload_still_works_right_after_meta_phrase(tmp_path: Path):
    orch = _orch_in_mode_b(tmp_path)
    orch.handle_user_text("añadir bloques", _RefuseLLM())
    result = orch.handle_user_text("payload", _RefuseLLM())
    assert "añadido" in result["message"]


# ── T6 ────────────────────────────────────────────────────────────────────


def test_t6_all_four_stubs_present_after_listo(tmp_path: Path):
    orch = _orch_in_mode_b(tmp_path)
    for phrase in ("payload", "manipulador", "ruedas", "gearbox"):
        orch.handle_user_text(phrase, _RefuseLLM())
    orch.handle_user_text("listo", _RefuseLLM())

    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    components = ps.design_properties.components
    assert "payload_bay" in components
    assert "arm" in components
    assert "wheels" in components
    assert "gearbox" in components
    # Base architecture also applied
    assert "motors" in components


# ── T7 ────────────────────────────────────────────────────────────────────


def test_t7_idle_freetext_identity_regression_unaffected(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": "prueba", "payload_kg": 1.0,
            "restrictions": "no", "detail_level": "detallado",
            "structure_mass_factor": 0.5, "safety_factor": 1.2,
        },
    })
    project_state = orch.state_manager.load_active_project(orch.workspace_manager)
    orch.system_definition_session.start("dron", project_state)
    orch.system_definition_session.answer("a")  # finish base -> clears to IDLE

    result = orch.handle_user_text("bahía de carga", _RefuseLLM())
    assert result["status"] == "ok"
    assert result["action"] == "component_description_saved"

    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    assert "payload_bay" in ps.design_properties.components


def test_t7_idle_camera_identity_regression_unaffected(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": "prueba", "payload_kg": 1.0,
            "restrictions": "no", "detail_level": "detallado",
            "structure_mass_factor": 0.5, "safety_factor": 1.2,
        },
    })
    project_state = orch.state_manager.load_active_project(orch.workspace_manager)
    orch.system_definition_session.start("dron", project_state)
    orch.system_definition_session.answer("a")

    result = orch.handle_user_text("cámara RunCam", _RefuseLLM())
    assert result["status"] == "ok"
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    assert "cameras" in ps.design_properties.components
