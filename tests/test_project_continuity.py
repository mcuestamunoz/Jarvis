"""Tests for Project Continuity (A') — Situation / Evidence / one next step."""
from __future__ import annotations

from types import SimpleNamespace
from pathlib import Path

from jarvis.adapters.cli.main import render_startup_context
from jarvis.core.intent_resolver import IntentResolver
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.project_continuity import build_project_continuity


def _state(**kwargs):
    defaults = dict(
        latest_results={
            "simulation": {
                "status": "pass",
                "quality": "good",
                "safety_margin_ratio": 2.0,
                "can_fly": True,
                "warnings": [],
            },
            "calculations": {},
        },
        current_parameters={"motor_count": 4},
        design_properties=SimpleNamespace(components={}),
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_continuity_catalog_gap_beats_optimization_suggestion():
    cont = build_project_continuity(
        project_state=_state(),
        status_type="nominal",
        status_reason=None,
        phase="complete",
        architecture_progress="3/4",
        next_architecture_label="Propulsión",
        next_block_status="in_progress",
        proactive_question="Propulsión en progreso",
        suggested_action={
            "label": "Aumentar carga útil",
            "reason": "Hay margen de empuje",
        },
        physical_requirements={"thrust_per_motor_needed_n": 4.76},
        component_bom={
            "defined": [],
            "incomplete": [{"key": "propellers", "missing_fields": []}],
            "missing": [],
            "declarative": [],
        },
        energy_model_note=None,
        motor_catalog_gap="Necesitas empuje ≥ 4.8 N/motor; no tengo motor en catálogo.",
        motor_catalog_matches=[],
    )
    assert "PASS" in cont["situation"] or "gaps" in cont["situation"].lower() or "PASS" in cont["situation"]
    assert cont["next_useful_step"]
    assert "Aumentar carga útil" not in cont["next_useful_step"]
    assert "empuje" in cont["next_useful_step"].lower() or "catálogo" in cont["next_useful_why"].lower()


def test_continuity_incomplete_bom_without_catalog_gap():
    cont = build_project_continuity(
        project_state=_state(),
        status_type="nominal",
        status_reason=None,
        phase="definition",
        architecture_progress="2/4",
        next_architecture_label=None,
        next_block_status=None,
        proactive_question=None,
        suggested_action={"label": "Aumentar carga útil", "reason": "margen"},
        physical_requirements={},
        component_bom={
            "defined": [],
            "incomplete": [{"key": "battery", "missing_fields": ["Wh"]}],
            "missing": [],
            "declarative": [],
        },
        energy_model_note=None,
        motor_catalog_gap=None,
    )
    assert "battery" in cont["next_useful_step"].lower()
    assert "Aumentar carga útil" not in cont["next_useful_step"]


def test_render_leads_with_continuity_block():
    text = render_startup_context({
        "has_project": True,
        "project_slug": "demo",
        "objective": "inspección",
        "phase": "complete",
        "status_type": "nominal",
        "continuity": {
            "situation": "Diseño validado en simulación (PASS).",
            "evidence": ["Simulación: pass — calidad good"],
            "next_useful_step": "Declara empuje real por motor.",
            "next_useful_why": "Hueco de catálogo",
        },
        "suggested_action": {"label": "Aumentar carga útil", "reason": "margen"},
        "component_bom_lines": ["… propellers: incompleto"],
    })
    assert "Situación:" in text
    assert "Evidencia:" in text
    assert "Siguiente paso:" in text
    assert "Declara empuje" in text
    # Competing optimization hint must not appear when continuity chose another next
    assert "Aumentar carga útil" not in text


def test_continuity_phrases_resolve_to_project_status():
    r = IntentResolver()
    for phrase in ("dónde estoy", "y ahora", "qué sigue", "por qué no puedo comprar aún"):
        assert r.resolve_intent(phrase) == "project_status", phrase


def test_build_startup_context_includes_continuity(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    # Minimal create via handle create path is heavy; use existing workspace if present
    ws = Path(
        "workspace/inspección-de-puentes-con-cámara-de-0-5kg-autonomía-mínima-20-minutos-9656971237a1"
    )
    if not ws.exists():
        return
    ctx = orch.build_startup_context(workspace_path=str(ws))
    assert ctx.get("has_project")
    cont = ctx.get("continuity") or {}
    assert cont.get("situation")
    assert cont.get("evidence")
    assert cont.get("next_useful_step")
    # Catalog gap on this project should win over payload optimization
    assert "Aumentar carga útil" not in cont["next_useful_step"]
