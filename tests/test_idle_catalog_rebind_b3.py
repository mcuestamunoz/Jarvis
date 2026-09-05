"""IDLE catalog rebind B3 — motors / propellers / battery named reopen.

Parent: implementation_contract_idle_catalog_rebind_b3.md
B2 regressions stay in test_idle_frame_rebind_b2.py.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.core.catalog_bind import (
    bind_battery_from_catalog,
    bind_frame_from_catalog,
    bind_motor_from_catalog,
    bind_propeller_from_catalog,
    frame_part_specs_from_catalog,
)
from jarvis.core.catalog_rebind_assist import (
    is_frame_rebind_phrase,
    resolve_idle_catalog_rebind,
)
from jarvis.core.component_writers import (
    set_battery_component,
    set_frame_material,
    set_motor_component,
    set_propeller_component,
    upsert_frame_part,
)
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.state_manager import OrchestratorMode
from jarvis.knowledge.library import default_library
from jarvis.schemas.action_schema import CatalogRef, ComponentSpec, PropertyValue


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


def _closed_bound(tmp_path: Path) -> JarvisOrchestrator:
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    motor = max(default_library.list_motors(), key=lambda x: x.thrust_n)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "idle catalog rebind b3",
            "payload_kg": 0.3,
            "restrictions": "ninguna",
            "detail_level": "conceptual",
            "structure_mass_factor": 0.3,
            "safety_factor": 1.1,
            "motors": 4,
            "per_motor_max_thrust_n": motor.thrust_n,
        },
    })
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    motor_bind = bind_motor_from_catalog({
        "idx": 1, "name": motor.name, "thrust_n": motor.thrust_n,
        "kv_rating": motor.kv_rating, "weight_g": motor.weight_g,
        "max_watts": motor.max_watts or 200, "is_generic": motor.is_generic,
    })
    ps = set_motor_component(ps, motor_bind, motor.max_watts or 200)
    ps = set_propeller_component(ps, bind_propeller_from_catalog("gemfan_5030"))
    ps = set_battery_component(ps, bind_battery_from_catalog("lipo_4s_5000mah"), 74.0)
    frame_bind = bind_frame_from_catalog("armattan_rooster_5in")
    ps = set_frame_material(
        ps,
        frame_bind.properties["mass_kg"].value,
        frame_bind.properties["material"].value,
        frame_bind.properties["size_class_inch"].value,
        catalog_ref=frame_bind.catalog_ref,
        component_name=frame_bind.name,
    )
    for key, spec in frame_part_specs_from_catalog("armattan_rooster_5in").items():
        ps = upsert_frame_part(ps, key, spec.properties, catalog_ref=spec.catalog_ref)
    fc = ComponentSpec(
        suggested_key="flight_controller", completeness="high", source="declared",
        properties={"model": PropertyValue(value="pixhawk_4", confidence=0.9)},
    )
    sensors = ComponentSpec(
        suggested_key="sensors", completeness="medium", source="declared",
        properties={"gps_model": PropertyValue(value="ublox_m9n")},
    )
    esc = ComponentSpec(
        suggested_key="esc", completeness="high", source="declared",
        properties={"current_a": PropertyValue(value=30.0)},
    )
    components = dict(ps.design_properties.components)
    components.update({"flight_controller": fc, "sensors": sensors, "esc": esc})
    dp = ps.design_properties.model_copy(update={
        "system_defined": True,
        "system_blocks": ["propulsion", "energy", "structure", "control"],
        "system_priority": ["propulsion", "energy", "structure", "control"],
        "components": components,
    })
    params = dict(ps.current_parameters)
    params.update({
        "motor_count": 4, "per_motor_max_thrust_n": motor.thrust_n,
        "battery_capacity_wh": 74.0, "motor_power_w": motor.max_watts or 200,
    })
    ps = ps.model_copy(update={"design_properties": dp, "current_parameters": params})
    orch.workspace_manager.save_state(ps)
    assert orch._next_pending_block(ps) is None
    return orch


def _reset_idle(orch: JarvisOrchestrator) -> None:
    session = orch.state_manager.get_runtime_session()
    idle = session.model_copy(update={
        "mode": OrchestratorMode.IDLE,
        "pending_missing_params": [],
        "pending_missing_reason": "",
        "pending_define_missing": False,
        "frame_suggestions": [],
        "motor_suggestions": [],
        "propeller_suggestions": [],
        "battery_suggestions": [],
    })
    orch.state_manager.set_runtime_session(idle)


@pytest.mark.parametrize("phrase,key", [
    ("cambiar frame", "frame"),
    ("cambiar motores", "motors"),
    ("cambiar motor", "motors"),
    ("ayúdame a elegir motor", "motors"),
    ("definir motores", "motors"),
    ("cambiar batería", "battery"),
    ("ayúdame a elegir batería", "battery"),
    ("cambiar hélice", "propellers"),
    ("ayúdame a elegir hélice", "propellers"),
    ("cambiar helices", "propellers"),
])
def test_resolve_idle_catalog_rebind_families(phrase, key):
    assert resolve_idle_catalog_rebind(phrase) == key


@pytest.mark.parametrize("phrase", [
    "ayúdame a elegir",
    "optimizar estructura",
    "cambiar material",
    "calcula",
    "definir bateria lipo_6s_10000mah",
    "cambia la bateria a lipo_6s_10000mah",
])
def test_resolve_idle_catalog_rebind_none(phrase):
    assert resolve_idle_catalog_rebind(phrase) is None


def test_is_frame_rebind_wrapper_still_frame_only():
    assert is_frame_rebind_phrase("cambiar frame") is True
    assert is_frame_rebind_phrase("cambiar motores") is False
    assert is_frame_rebind_phrase("cambiar batería") is False


def test_cambiar_motores_opens_motor_catalog(tmp_path: Path):
    orch = _closed_bound(tmp_path)
    _reset_idle(orch)
    result = orch.handle_user_text("cambiar motores", _RefuseLLM())
    assert result.get("motor_suggestions")
    assert not result.get("frame_suggestions")
    session = orch.state_manager.get_runtime_session()
    assert session.pending_missing_params == ["motors"]
    assert session.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS


def test_ayudame_elegir_motor_opens_motor_not_bare_triage(tmp_path: Path):
    orch = _closed_bound(tmp_path)
    _reset_idle(orch)
    result = orch.handle_user_text("ayúdame a elegir motor", _RefuseLLM())
    assert result.get("motor_suggestions")
    assert not result.get("frame_suggestions")
    assert not result.get("battery_suggestions")


def test_cambiar_bateria_opens_battery_catalog(tmp_path: Path):
    orch = _closed_bound(tmp_path)
    _reset_idle(orch)
    result = orch.handle_user_text("cambiar batería", _RefuseLLM())
    assert result.get("battery_suggestions")
    assert not result.get("frame_suggestions")
    assert orch.state_manager.get_runtime_session().pending_missing_params == ["battery"]


@pytest.mark.parametrize("phrase", ["cambiar hélice", "ayúdame a elegir hélice"])
def test_propeller_rebind_opens_propeller_catalog(tmp_path: Path, phrase):
    orch = _closed_bound(tmp_path)
    _reset_idle(orch)
    result = orch.handle_user_text(phrase, _RefuseLLM())
    assert result.get("propeller_suggestions")
    assert not result.get("motor_suggestions")
    assert orch.state_manager.get_runtime_session().pending_missing_params == ["propellers"]


def test_battery_rebind_pick_binds_new_sku(tmp_path: Path):
    orch = _closed_bound(tmp_path)
    _reset_idle(orch)
    offer = orch.handle_user_text("cambiar batería", _RefuseLLM())
    idx = next(
        s["idx"] for s in offer["battery_suggestions"] if s["name"] == "lipo_4s_10000mah"
    )
    pick = orch.handle_user_text(str(idx), _RefuseLLM())
    assert pick["status"] == "ok"
    state = orch.state_manager.load_active_project(orch.workspace_manager)
    battery = state.design_properties.components["battery"]
    assert battery.catalog_ref == CatalogRef(family="battery", sku="lipo_4s_10000mah")


def test_bare_ayudame_resolver_none_and_no_forced_family(tmp_path: Path):
    assert resolve_idle_catalog_rebind("ayúdame a elegir") is None
    orch = _closed_bound(tmp_path)
    _reset_idle(orch)
    result = orch.handle_user_text("ayúdame a elegir", _RefuseLLM())
    assert not result.get("frame_suggestions")
    assert not result.get("battery_suggestions")
    assert not result.get("propeller_suggestions")


def test_b2_cambiar_frame_still_opens_frame(tmp_path: Path):
    orch = _closed_bound(tmp_path)
    _reset_idle(orch)
    result = orch.handle_user_text("cambiar frame", _RefuseLLM())
    assert result.get("frame_suggestions")
    assert not result.get("motor_suggestions")


def test_mid_architecture_definir_motores_does_not_steal_via_b3(tmp_path: Path):
    """While a block is still pending, named phrases stay with FN-014 —
    B3 must not open a cross-family catalog reopen."""
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "fn014 gate",
            "payload_kg": 0.5,
            "restrictions": "ninguna",
            "detail_level": "conceptual",
            "motors": 4,
            "per_motor_max_thrust_n": 10.0,
            "structure_mass_factor": 0.3,
            "safety_factor": 1.2,
        },
    })
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    dp = ps.design_properties.model_copy(update={
        "system_defined": True,
        "system_blocks": ["propulsion", "energy", "structure", "control"],
        "system_priority": ["propulsion", "energy", "structure", "control"],
    })
    orch.workspace_manager.save_state(ps.model_copy(update={"design_properties": dp}))
    assert orch._next_pending_block(
        orch.state_manager.load_active_project(orch.workspace_manager)
    ) is not None
    _reset_idle(orch)
    result = orch.handle_user_text("definir batería", _RefuseLLM())
    assert not result.get("battery_suggestions"), (
        "B3 must not jump to battery while architecture still has a pending block"
    )
