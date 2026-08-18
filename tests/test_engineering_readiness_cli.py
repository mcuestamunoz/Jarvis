"""ERF-1 Slice 5 — CLI / status surface.

Covers .jes/artifacts/implementation_contract_erf1.md §7 Slice 5:
  - startup_context carries a JSON-serializable "readiness" block
  - render_startup_context renders the 8 subsystem lines + overall + top gaps
  - no electronics/communications/integration lines ever appear
"""
from __future__ import annotations

import json
from pathlib import Path

from jarvis.adapters.cli.main import render_startup_context
from jarvis.core.orchestrator import JarvisOrchestrator

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
        "energy", "control", "catalog", "bom",
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
        "Energy", "Control", "Catalog", "BOM",
    ):
        assert label in text
    assert "PROJECT STATUS:" in text


def test_render_startup_context_never_shows_forbidden_subsystem_lines(tmp_path):
    orchestrator = _fresh_orchestrator(tmp_path)
    ctx = orchestrator.build_startup_context()
    text = render_startup_context(ctx)

    for forbidden in ("Electronics", "Communications", "Integration"):
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
