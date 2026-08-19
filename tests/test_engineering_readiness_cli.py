"""ERF-1 Slice 5 / ERF-2 Slice 4 — CLI / status surface.

Covers .jes/artifacts/implementation_contract_erf1.md §7 Slice 5 and
implementation_contract_erf2.md §9 Slice 4:
  - startup_context carries a JSON-serializable "readiness" block
  - render_startup_context renders the 9 subsystem lines + overall + top gaps
  - Electronics line present; communications/integration never appear
  - INCOMPATIBLE verdict shown verbatim when a subsystem carries one
"""
from __future__ import annotations

import json
from pathlib import Path

from jarvis.adapters.cli.main import render_startup_context
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue

_CREATE_PARAMS = {
    "vehicle_type": "dron",
    "objective": "dron de prueba erf1 cli surface",
    "payload_kg": 1.0,
    "restrictions": "ninguna",
    "detail_level": "conceptual",
    "motors": 4,
    "per_motor_max_thrust_n": 12.0,
    "structure_mass_factor": 0.5,
    "safety_factor": 1.2,
}


def _fresh_orchestrator(tmp_path: Path) -> JarvisOrchestrator:
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    orchestrator.handle({"action": "create_project", "parameters": _CREATE_PARAMS})
    return orchestrator


def test_startup_context_includes_readiness_block(tmp_path):
    orchestrator = _fresh_orchestrator(tmp_path)
    ctx = orchestrator.build_startup_context()

    assert "readiness" in ctx
    readiness = ctx["readiness"]
    assert set(readiness["subsystems"].keys()) == {
        "requirements", "architecture", "structure", "propulsion",
        "energy", "electronics", "control", "catalog", "bom",
    }
    assert readiness["overall"] in ("ASSEMBLY_READY", "NOT_ASSEMBLY_READY")

    # JSON-serializable (dataclasses.asdict output, no stray objects).
    json.dumps(readiness)


def test_startup_context_readiness_is_json_dataclass_dict(tmp_path):
    orchestrator = _fresh_orchestrator(tmp_path)
    ctx = orchestrator.build_startup_context()
    readiness = ctx["readiness"]
    assert isinstance(readiness, dict)
    assert isinstance(readiness["gaps"], list)
    assert isinstance(readiness["prioritized_gaps"], list)


def test_render_startup_context_shows_readiness_block(tmp_path):
    orchestrator = _fresh_orchestrator(tmp_path)
    ctx = orchestrator.build_startup_context()
    text = render_startup_context(ctx)

    assert "ENGINEERING READINESS" in text
    for label in (
        "Requirements", "Architecture", "Structure", "Propulsion",
        "Energy", "Electronics", "Control", "Catalog", "BOM",
    ):
        assert label in text
    assert "PROJECT STATUS:" in text


def test_render_startup_context_never_shows_forbidden_subsystem_lines(tmp_path):
    """ERF-2 ★8: Electronics is now expected; Communications/Integration stay forbidden."""
    orchestrator = _fresh_orchestrator(tmp_path)
    ctx = orchestrator.build_startup_context()
    text = render_startup_context(ctx)

    assert "Electronics" in text
    for forbidden in ("Communications", "Integration"):
        assert forbidden not in text


def test_render_startup_context_top_gaps_capped_at_three(tmp_path):
    orchestrator = _fresh_orchestrator(tmp_path)
    ctx = orchestrator.build_startup_context()
    text = render_startup_context(ctx)

    if "TOP GAPS" in text:
        gap_id_lines = [
            line for line in text.splitlines() if line.startswith("GAP-")
        ]
        assert len(gap_id_lines) <= 3


def test_cli_shows_electronics_line(tmp_path):
    orchestrator = _fresh_orchestrator(tmp_path)
    ctx = orchestrator.build_startup_context()
    text = render_startup_context(ctx)
    assert "Electronics" in text


def test_cli_shows_incompatible_label(tmp_path):
    """ERF-2: an ESC genuinely undersized for its per-motor demand must render
    the literal 'INCOMPATIBLE' verdict in the CLI block."""
    orchestrator = _fresh_orchestrator(tmp_path)
    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)

    motors = ComponentSpec(
        suggested_key="motors", completeness="high", source="declared",
        properties={"motor_count": PropertyValue(value=4)},
    )
    battery = ComponentSpec(
        suggested_key="battery", completeness="high", source="declared",
        properties={"battery_capacity_wh": PropertyValue(value=50.0)},
    )
    esc = ComponentSpec(
        suggested_key="esc", completeness="high", source="declared",
        properties={"current_a": PropertyValue(value=5.0)},  # well under demand
    )
    dp = project_state.design_properties.model_copy(update={
        "components": {"motors": motors, "battery": battery, "esc": esc},
    })
    params = dict(project_state.current_parameters or {})
    params.update({"motor_power_w": 222.0, "battery_cell_count": 2})
    updated = project_state.model_copy(update={"design_properties": dp, "current_parameters": params})
    orchestrator.workspace_manager.save_state(updated)

    ctx = orchestrator.build_startup_context()
    assert ctx["readiness"]["subsystems"]["electronics"]["verdict"] == "INCOMPATIBLE"

    text = render_startup_context(ctx)
    assert "INCOMPATIBLE" in text
