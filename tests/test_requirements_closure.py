"""Requirements Closure IC (G26 write path + ★3(b) explicit-none semantics).

Covers .jes/artifacts/implementation_contract_requirements_closure.md Req-5:
  - ★3(b): explicit "sin restricciones" satisfies requirements.defined
    without fabricating parsed_constraints.
  - Absent / unparseable restrictions stay INCOMPLETE (§2.3 — honest, not a
    silent PASS).
  - Fixture-2-shaped project (8/9 subsystems already PASS) flips to
    ASSEMBLY_READY once requirements is satisfied — the investigation's
    headline finding, reproduced here as a regression gate.
  - G26: a mid-session "cambia restrictions a X" turn persists
    current_parameters["restrictions"] (never a loose derived key), and the
    is_derived gate rejects a direct derived-param write.
  - P2-1 propulsion/OP resolution path is untouched by this IC.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.core.catalog_bind import bind_motor_from_catalog
from jarvis.core.component_writers import set_motor_component
from jarvis.core.engineering_readiness import build_engineering_readiness
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.knowledge.library import default_library
from jarvis.schemas.action_schema import CatalogRef, ComponentSpec, PropertyValue
from jarvis.schemas.state_schema import DesignProperties, ProjectState, restrictions_explicitly_none


class _RefuseLLM:
    """The Requirements Closure intercept must never reach the LLM."""

    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


# ── ★3(b) — restrictions_explicitly_none ────────────────────────────────────


def test_restrictions_explicitly_none_recognizes_closed_list():
    for text in ("no", "No", "ninguna", "ninguno", "n/a", "sin restricciones", " NINGUNA "):
        assert restrictions_explicitly_none(text) is True


def test_restrictions_explicitly_none_false_for_absent_or_ambiguous():
    assert restrictions_explicitly_none(None) is False
    assert restrictions_explicitly_none("") is False
    assert restrictions_explicitly_none("   ") is False
    assert restrictions_explicitly_none("tal vez") is False
    assert restrictions_explicitly_none("autonomia minima 15 min") is False


# ── Fixture: a Fixture-2-shaped ("almost ready") ProjectState ──────────────


def _spec(key, component_type, *, catalog_ref=None, properties=None):
    return ComponentSpec(
        name=key,
        component_type=component_type,
        suggested_key=key,
        completeness="high",
        source="declared",
        properties=properties or {},
        catalog_ref=catalog_ref,
    )


def _assembly_ready_shape_state(restrictions: str, *, autonomy_min: float = 5.0455) -> ProjectState:
    """8/9-subsystem-PASS shape (investigation_report_project_closure_
    assembly_ready.md §2.3, Fixture 2) — motor catalog-bound and covering
    requirements, every other family freeform-declared at non-low
    completeness. Only ``requirements`` varies with *restrictions*.
    """
    motors = _spec(
        "motors", "propulsion_active",
        catalog_ref=CatalogRef(family="motor", sku="emax_rs2205s_2300"),
        properties={
            "thrust_n": PropertyValue(value=9.7086, unit="N", confidence=0.98, source="declared"),
            "kv_rating": PropertyValue(value=2300, source="declared"),
            "power_w": PropertyValue(value=400.0, unit="W", source="declared"),
            "motor_count": PropertyValue(value=4, source="declared"),
        },
    )
    propellers = _spec("propellers", "propulsion_passive", properties={
        "diameter_in": PropertyValue(value=5.0, unit="in", source="declared"),
        "pitch_in": PropertyValue(value=4.5, unit="in", source="declared"),
    })
    esc = _spec("esc", "power_electronics")
    battery = _spec("battery", "energy_storage", properties={
        "battery_capacity_wh": PropertyValue(value=22.2, unit="Wh", source="declared"),
    })
    frame = _spec("frame", "structure", properties={
        "material": PropertyValue(value="carbono", source="declared"),
    })
    flight_controller = _spec("flight_controller", "control")
    sensors = _spec("sensors", "control")

    dp = DesignProperties(
        components={
            "motors": motors, "propellers": propellers, "esc": esc, "battery": battery,
            "frame": frame, "flight_controller": flight_controller, "sensors": sensors,
        },
        system_defined=True,
        system_blocks=["propulsion", "energy", "structure", "control"],
        system_priority=["propulsion", "energy", "structure", "control"],
    )

    return ProjectState(
        project_id="req-closure-fixture",
        project_slug="req-closure-fixture",
        objective="proyecto de prueba requirements closure",
        workspace_path="/tmp/req-closure-fixture",
        current_parameters={
            "vehicle_type": "dron",
            "restrictions": restrictions,
            "motor_count": 4,
            "per_motor_max_thrust_n": 9.7086,
            "motor_power_w": 400.0,
            "battery_capacity_wh": 22.2,
        },
        design_properties=dp,
        latest_results={
            "simulation": {"status": "pass", "autonomy_min": autonomy_min, "safety_margin_ratio": 1.2},
            "calculations": {
                "required_thrust_n": 20.0, "total_mass_kg": 1.72, "autonomy_min": autonomy_min,
            },
        },
    )


def test_requirements_pass_when_restrictions_explicitly_no():
    state = _assembly_ready_shape_state("no")
    result = build_engineering_readiness(state)
    assert result.subsystems["requirements"].verdict == "PASS"
    assert state.parsed_constraints == {}, "explicit-none must not fabricate numeric constraints"


def test_requirements_incomplete_when_restrictions_absent():
    state = _assembly_ready_shape_state("no")
    stripped_params = dict(state.current_parameters)
    stripped_params.pop("restrictions", None)
    state = state.model_copy(update={"current_parameters": stripped_params})
    result = build_engineering_readiness(state)
    assert result.subsystems["requirements"].verdict == "INCOMPLETE"


def test_requirements_incomplete_when_restrictions_unparseable():
    """Non-empty, not explicit-none, no numeric pattern -> honest INCOMPLETE
    (§2.3) — never a silent PASS just because *something* was typed."""
    state = _assembly_ready_shape_state("mantener el diseño actual, sin más")
    assert state.parsed_constraints == {}
    result = build_engineering_readiness(state)
    assert result.subsystems["requirements"].verdict == "INCOMPLETE"


def test_fixture2_shape_assembly_ready_after_req1_req2():
    """The investigation's headline finding as a regression gate: an
    8/9-PASS, 0-gap project reaches ASSEMBLY_READY once requirements is
    satisfied via ★3(b) — no other subsystem needed a code change."""
    state = _assembly_ready_shape_state("no")
    result = build_engineering_readiness(state)
    assert result.gaps == []
    assert all(sr.verdict == "PASS" for sr in result.subsystems.values())
    assert result.overall == "ASSEMBLY_READY"


def test_gap_requirements_unmet_autonomy_when_target_exceeds_sim():
    """An unachievable stated constraint must surface an honest gap, not a
    silent PASS or a silent failure to update — probe #3 negative arm."""
    state = _assembly_ready_shape_state("autonomia minima 15 min", autonomy_min=5.0455)
    result = build_engineering_readiness(state)
    gap_ids = {g.gap_id for g in result.gaps}
    assert "GAP-REQUIREMENTS-UNMET:autonomy" in gap_ids
    assert result.subsystems["requirements"].verdict == "INCOMPLETE"
    assert result.overall == "NOT_ASSEMBLY_READY"


def test_requirements_pass_with_achievable_stated_constraint():
    state = _assembly_ready_shape_state("autonomia minima 3 min", autonomy_min=5.0455)
    result = build_engineering_readiness(state)
    assert result.subsystems["requirements"].verdict == "PASS"
    assert result.overall == "ASSEMBLY_READY"


# ── G26 write path (orchestrator integration) ───────────────────────────────


def _fresh_orchestrator(tmp_path: Path) -> JarvisOrchestrator:
    orc = JarvisOrchestrator(workspace_root=tmp_path)
    orc.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "dron de prueba requirements closure",
            "payload_kg": 1.0,
            "restrictions": "ninguna",
            "detail_level": "conceptual",
            "motors": 4,
            "per_motor_max_thrust_n": 12.0,
            "structure_mass_factor": 0.5,
            "safety_factor": 1.2,
        },
    })
    return orc


def test_g26_restrictions_update_sets_parsed_constraints(tmp_path):
    orc = _fresh_orchestrator(tmp_path)
    llm = _RefuseLLM()

    result = orc.handle_user_text("cambia restrictions a autonomia minima 15 min", llm)
    assert result["status"] == "ok"

    state = orc.state_manager.load_active_project(orc.workspace_manager)
    assert "autonomia minima 15 min" in state.current_parameters["restrictions"]
    assert state.parsed_constraints.get("autonomy_min") == 15.0
    assert "autonomia" not in state.current_parameters


def test_g26_explicit_none_restatement_flips_requirements(tmp_path):
    orc = _fresh_orchestrator(tmp_path)
    llm = _RefuseLLM()

    result = orc.handle_user_text("restrictions: sin restricciones", llm)
    assert result["status"] == "ok"

    state = orc.state_manager.load_active_project(orc.workspace_manager)
    assert restrictions_explicitly_none(state.current_parameters["restrictions"])
    assert state.parsed_constraints == {}


def test_g26_derived_autonomia_rejected(tmp_path):
    """Req-4 defense-in-depth: a direct derived-param write (the original
    G26 symptom shape) must be rejected, never silently persisted as a loose
    current_parameters key."""
    orc = _fresh_orchestrator(tmp_path)
    before = orc.state_manager.load_active_project(orc.workspace_manager)

    result = orc.param_definition_session.apply_and_recalculate({"autonomia": 15.0})
    assert result["status"] == "error"

    after = orc.state_manager.load_active_project(orc.workspace_manager)
    assert after.current_parameters == before.current_parameters
    assert "autonomia" not in after.current_parameters


def test_extract_restrictions_update_ignores_unrelated_turns():
    from jarvis.core.param_definition_session import extract_restrictions_update

    assert extract_restrictions_update("4 motores") is None
    assert extract_restrictions_update("aumenta autonomia a 15") is None
    assert extract_restrictions_update("") is None
    assert extract_restrictions_update(None) is None


# ── P2-1 / propulsion path untouched (smoke) ────────────────────────────────


def test_p2_propulsion_resolution_unchanged(tmp_path):
    """Smoke: catalog-bound motor + propeller still resolve an exact
    operating point — this IC touches only the requirements subsystem and
    the restrictions/derived-param write paths, never component_writers'
    propulsion bridge or the library/OP resolver."""
    import json

    from jarvis.core.catalog_bind import bind_propeller_from_catalog
    from jarvis.core.component_writers import set_propeller_component

    orc = _fresh_orchestrator(tmp_path)
    ps = orc.state_manager.load_active_project(orc.workspace_manager)

    prop_spec = bind_propeller_from_catalog("hq_5045_bn")
    ps = set_propeller_component(ps, prop_spec)

    motor_suggestion = {
        "name": "emax_rs2205s_2300",
        "max_watts": default_library.get_motor("emax_rs2205s_2300").max_watts,
        "thrust_n": default_library.get_motor("emax_rs2205s_2300").thrust_n,
        "kv_rating": default_library.get_motor("emax_rs2205s_2300").kv_rating,
        "weight_g": default_library.get_motor("emax_rs2205s_2300").weight_g,
    }
    motor_spec = bind_motor_from_catalog(motor_suggestion)
    updated = set_motor_component(ps, motor_spec, motor_suggestion["max_watts"])

    raw = updated.current_parameters.get("propulsion_resolution")
    assert raw is not None
    resolution = json.loads(raw)
    assert resolution["resolution_type"] == "exact_operating_point"
