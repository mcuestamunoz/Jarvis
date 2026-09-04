"""Option A — show ESTIMATIVO in chat (product writer, 4S, ephemeral).

implementation_contract_option_a_estimative_visibility.md
"""
from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from jarvis.core.calculation_engine import CalculationEngine
from jarvis.core.catalog_bind import (
    bind_battery_from_catalog,
    bind_motor_from_catalog,
    bind_propeller_from_catalog,
)
from jarvis.core.component_writers import (
    set_battery_component,
    set_motor_component,
    set_propeller_component,
)
from jarvis.core.endurance_sweep_writer import build_product_endurance_sweep
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.knowledge.library import default_library


def _bind_combo_a(orch: JarvisOrchestrator, *, payload_kg: float = 1.718, motor_count: int = 4):
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "option a estimative visibility",
            "payload_kg": payload_kg,
            "restrictions": "no",
            "detail_level": "conceptual",
            "motors": motor_count,
            "structure_mass_factor": 0.5,
            "safety_factor": 1.2,
        },
    })
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    ps = ps.model_copy(update={
        "current_parameters": {**ps.current_parameters, "motor_count": motor_count},
    })
    ps = set_propeller_component(ps, bind_propeller_from_catalog("gf_5045x3"))
    battery_spec = bind_battery_from_catalog("lipo_4s_1500mah")
    wh = battery_spec.properties["battery_capacity_wh"].value
    ps = set_battery_component(ps, battery_spec, wh)
    m = default_library.get_motor("sunnysky_r2205_2500")
    motor_spec = bind_motor_from_catalog({
        "name": m.name, "max_watts": m.max_watts, "thrust_n": m.thrust_n,
        "kv_rating": m.kv_rating, "weight_g": m.weight_g, "is_generic": m.is_generic,
    })
    ps = set_motor_component(ps, motor_spec, m.max_watts)
    orch.workspace_manager.save_state(ps)
    return orch.state_manager.load_active_project(orch.workspace_manager)


def test_combo_a_calculate_shows_envelope_without_persisting_sweep(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    _bind_combo_a(orch)
    result = orch.handle({"action": "calculate", "parameters": {}})
    assert result["status"] == "ok"

    calcs = result["calculations"]
    envelope = calcs["battery_endurance_envelope"]
    assert envelope is not None
    assert len(envelope) == 2
    assert all(row["source_type"] == "assumed" for row in envelope)
    outcomes = {row["outcome"] for row in envelope}
    assert outcomes == {"sustainable", "infeasible"}
    assert calcs["hover_energy_autonomy_min"] == pytest.approx(1.3237, abs=0.01)

    state = result["state"]
    assert "battery_endurance_sweep" not in (state.get("current_parameters") or {})

    reloaded = orch.state_manager.load_active_project(orch.workspace_manager)
    assert "battery_endurance_sweep" not in (reloaded.current_parameters or {})

    from jarvis.adapters.cli.main import render_response

    rendered = render_response(result)
    assert "ESTIMATIVO" in rendered
    assert "INVIABLE" in rendered
    assert "autonomía real" not in rendered.lower()
    assert "n×I_hover" in rendered
    assert "no es I_pack" in rendered


def test_six_s_omits_envelope(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    ps = _bind_combo_a(orch)
    ps = ps.model_copy(update={
        "current_parameters": {**ps.current_parameters, "battery_cell_count": 6},
    })
    orch.workspace_manager.save_state(ps)

    result = orch.handle({"action": "calculate", "parameters": {}})
    calcs = result["calculations"]
    assert calcs["battery_endurance_envelope"] is None
    # Hover L1 can still compute (identity/OP unchanged); we only skip L2.
    assert calcs["hover_energy_autonomy_min"] == pytest.approx(1.3237, abs=0.01)

    from jarvis.adapters.cli.main import render_response

    rendered = render_response(result)
    assert "ESTIMATIVO" not in rendered


def test_writer_skips_when_hover_current_missing():
    params = {
        "battery_cell_count": 4,
        "battery_capacity_wh": 22.2,
        "motor_count": 4,
    }
    bundle = CalculationEngine().build({
        "vehicle_type": "dron",
        "payload_kg": 1.0,
        "structure_mass_factor": 0.5,
        "safety_factor": 1.2,
        "motor_count": 4,
        "battery_capacity_wh": 22.2,
        "motor_power_w": 220.0,
        "per_motor_max_thrust_n": 9.5,
        "battery_cell_count": 4,
    })
    assert bundle.motor_hover_current_a is None
    assert build_product_endurance_sweep(params, bundle) is None
    assert bundle.battery_endurance_envelope is None


def test_design_explorer_does_not_call_writer():
    from jarvis.core import design_explorer

    source = inspect.getsource(design_explorer)
    assert "endurance_sweep_writer" not in source
    assert "build_with_estimative_sweep" not in source
    assert "build_product_endurance_sweep" not in source
    assert "battery_endurance_sweep" not in source
