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


_ASSEMBLY_READY_READINESS = {
    "subsystems": {
        key: {"verdict": "PASS", "warning_type": None}
        for key in (
            "requirements", "architecture", "structure", "propulsion",
            "energy", "electronics", "control", "catalog", "bom",
        )
    },
    "overall": "ASSEMBLY_READY",
    "prioritized_gaps": [],
}

_NOT_ASSEMBLY_READY_READINESS = {
    **_ASSEMBLY_READY_READINESS,
    "overall": "NOT_ASSEMBLY_READY",
}


def test_cli_note_shown_when_assembly_ready_and_margin_claim_weak():
    """Claim hygiene under ASSEMBLY READY IC §2.4: ASSEMBLY READY + a
    precomputed margin_claim_weak flag must append the locked NOTE line —
    the flag is consumed verbatim, never re-derived in the CLI."""
    text = render_startup_context({
        "has_project": True,
        "project_slug": "demo",
        "readiness": _ASSEMBLY_READY_READINESS,
        "margin_claim_weak": True,
    })
    assert "PROJECT STATUS: ASSEMBLY READY" in text
    assert "NOTE: margen ajustado" in text


def test_cli_note_absent_when_assembly_ready_and_margin_not_weak():
    text = render_startup_context({
        "has_project": True,
        "project_slug": "demo",
        "readiness": _ASSEMBLY_READY_READINESS,
        "margin_claim_weak": False,
    })
    assert "PROJECT STATUS: ASSEMBLY READY" in text
    assert "NOTE:" not in text


def test_cli_note_absent_when_margin_claim_weak_key_missing():
    """Backward compatibility: ctx without the new key renders exactly as
    before this IC (no NOTE, no KeyError)."""
    text = render_startup_context({
        "has_project": True,
        "project_slug": "demo",
        "readiness": _ASSEMBLY_READY_READINESS,
    })
    assert "PROJECT STATUS: ASSEMBLY READY" in text
    assert "NOTE:" not in text


def test_cli_note_absent_when_not_assembly_ready_even_if_margin_weak():
    text = render_startup_context({
        "has_project": True,
        "project_slug": "demo",
        "readiness": _NOT_ASSEMBLY_READY_READINESS,
        "margin_claim_weak": True,
    })
    assert "PROJECT STATUS: NOT ASSEMBLY READY" in text
    assert "NOTE:" not in text


def test_cli_humanizes_next_useful_why_for_known_warning_code():
    """Claim hygiene under ASSEMBLY READY IC §2.3/N1: Continuity keeps the
    raw warning code; the CLI maps it through WARNING_SHORT for display."""
    text = render_startup_context({
        "has_project": True,
        "project_slug": "demo",
        "continuity": {
            "situation": "Comprobación de empuje: PASS. Margen ajustado.",
            "evidence": ["Simulación: pass — calidad risky — margen 1.05"],
            "next_useful_step": "Corrige la causa del warning/fallo de simulación.",
            "next_useful_why": "low_margin",
        },
    })
    assert "Por qué: margen ajustado" in text
    assert "Por qué: low_margin" not in text


def test_cli_leaves_unknown_next_useful_why_verbatim():
    text = render_startup_context({
        "has_project": True,
        "project_slug": "demo",
        "continuity": {
            "situation": "Última simulación: fail.",
            "evidence": [],
            "next_useful_step": "Corrige la causa del warning/fallo de simulación.",
            "next_useful_why": "un texto libre no catalogado",
        },
    })
    assert "Por qué: un texto libre no catalogado" in text


def test_cli_control_pass_gets_declaration_asterisk_and_footnote():
    """Control parity IC §2.1: Control PASS is marked with an asterisk and a
    footnote naming it declaration-only — no other subsystem is marked, and
    the verdict value itself (PASS) is untouched."""
    text = render_startup_context({
        "has_project": True,
        "project_slug": "demo",
        "readiness": _ASSEMBLY_READY_READINESS,
    })
    assert "Control        PASS *" in text
    assert "* Control: declaración — sin física de control" in text
    assert "Propulsion     PASS *" not in text
    assert "Energy         PASS *" not in text


def test_cli_control_not_pass_has_no_asterisk_or_footnote():
    readiness = {
        **_ASSEMBLY_READY_READINESS,
        "subsystems": {
            **_ASSEMBLY_READY_READINESS["subsystems"],
            "control": {"verdict": "INCOMPLETE", "warning_type": None},
        },
        "overall": "NOT_ASSEMBLY_READY",
    }
    text = render_startup_context({
        "has_project": True,
        "project_slug": "demo",
        "readiness": readiness,
    })
    assert "Control        INCOMPLETE" in text
    assert "Control        PASS *" not in text
    assert "* Control: declaración — sin física de control" not in text


def test_cli_structure_pass_gets_declaration_asterisk_and_footnote():
    """Structure honesty IC §2.1: Structure PASS is marked with an asterisk
    and a footnote naming it identity/LEVEL-A-only — mirrors Control parity.
    Blanket rule: fires regardless of whether a class check actually ran."""
    text = render_startup_context({
        "has_project": True,
        "project_slug": "demo",
        "readiness": _ASSEMBLY_READY_READINESS,
    })
    assert "Structure      PASS *" in text
    assert "* Structure: identidad / clase nivel A — sin geometría de chasis" in text


def test_cli_structure_not_pass_has_no_asterisk_or_footnote():
    readiness = {
        **_ASSEMBLY_READY_READINESS,
        "subsystems": {
            **_ASSEMBLY_READY_READINESS["subsystems"],
            "structure": {"verdict": "INCOMPLETE", "warning_type": None},
        },
        "overall": "NOT_ASSEMBLY_READY",
    }
    text = render_startup_context({
        "has_project": True,
        "project_slug": "demo",
        "readiness": readiness,
    })
    assert "Structure      INCOMPLETE" in text
    assert "Structure      PASS *" not in text
    assert "* Structure: identidad / clase nivel A — sin geometría de chasis" not in text


def test_cli_structure_and_control_both_pass_show_both_footnotes_in_order():
    text = render_startup_context({
        "has_project": True,
        "project_slug": "demo",
        "readiness": _ASSEMBLY_READY_READINESS,
    })
    assert "Structure      PASS *" in text
    assert "Control        PASS *" in text
    structure_footnote_pos = text.index("* Structure: identidad / clase nivel A — sin geometría de chasis")
    control_footnote_pos = text.index("* Control: declaración — sin física de control")
    assert structure_footnote_pos < control_footnote_pos
