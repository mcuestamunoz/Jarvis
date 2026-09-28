"""Tests T1-T6 for `B1-continuity-explain-cite-r3`.

Exercises the topic->cite bridge (`jarvis.intelligence.continuity_cite`),
Continuity's additive `explain_topics` tagging (`project_continuity.
_explain_topics_for_continuity` / `build_project_continuity`), and the
CLI's optional "Conceptos" render (`adapters.cli.main._render_concept_lines`).
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

from jarvis.adapters.cli.main import _render_concept_lines, render_startup_context
from jarvis.core.project_continuity import build_project_continuity
from jarvis.intelligence.continuity_cite import (
    cites_for_topics,
    format_continuity_cite_lines,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
PROJECT_CONTINUITY_PATH = REPO_ROOT / "src" / "jarvis" / "core" / "project_continuity.py"
CONTINUITY_CITE_PATH = REPO_ROOT / "src" / "jarvis" / "intelligence" / "continuity_cite.py"


def _imported_module_names(source_path: Path) -> set[str]:
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


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


def test_t1_topic_c_rate_resolves_to_solid_cite():
    cites = cites_for_topics(["c_rate"])
    assert len(cites) == 1
    assert cites[0].id == "c-rate-de-bateria"
    assert cites[0].estado == "solid"
    assert cites[0].definicion != ""


def test_t2_motor_catalog_gap_fixture_tags_motor_and_step_unchanged():
    """Reuses the exact fixture shape from
    test_continuity_catalog_gap_beats_optimization_suggestion
    (tests/test_project_continuity.py) — golden next_useful_step/why
    captured from the pre-R3 code before this Buy touched
    project_continuity.py, to prove the new explain_topics computation
    never altered ranking."""
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
    assert cont["next_useful_step"] == (
        "Declara empuje real por motor (≥ 4.8 N) o elige una pieza fuera "
        "de catálogo; Jarvis no inventará un SKU."
    )
    assert cont["next_useful_why"] == (
        "Necesitas empuje ≥ 4.8 N/motor; no tengo motor en catálogo. "
        "Di 'qué motores tenemos' para ver el catálogo, o 'explora "
        "opciones' para que Jarvis pruebe configuraciones alternativas."
    )
    assert cont["explain_topics"] == ["motor"]


def test_t2b_autonomy_fixture_tags_c_rate_and_operating_point_step_unchanged():
    """Reuses test_situation_thrust_feasibility_only_when_autonomy_unmet's
    fixture shape; golden next_useful_step/why captured pre-R3."""
    cont = build_project_continuity(
        project_state=_state(
            latest_results={
                "simulation": {
                    "status": "pass",
                    "quality": "acceptable",
                    "safety_margin_ratio": 1.28,
                    "can_fly": True,
                    "warnings": [],
                    "energy_status": "missing_energy_parameters",
                },
                "calculations": {},
            },
        ),
        status_type="nominal",
        status_reason=None,
        phase="complete",
        architecture_progress="4/4",
        next_architecture_label=None,
        next_block_status=None,
        proactive_question=None,
        suggested_action=None,
        physical_requirements={"autonomy_target_min": 5.0},
        component_bom={"defined": [], "incomplete": [], "missing": [], "declarative": []},
        energy_model_note=None,
        motor_catalog_gap=None,
        motor_catalog_matches=[],
    )
    assert cont["next_useful_step"] == (
        "Diseño en PASS — puedes iterar, explorar alternativas o documentar el cierre."
    )
    assert cont["next_useful_why"] == "No hay gaps bloqueantes en BOM/catálogo."
    assert cont["situation"] == (
        "Comprobación de empuje: PASS. Candidato inicial — la autonomía "
        "del objetivo no está demostrada."
    )
    assert cont["explain_topics"] == ["c_rate", "operating_point"]


def test_t2c_no_matching_signal_yields_empty_topics():
    cont = build_project_continuity(
        project_state=_state(),
        status_type="nominal",
        status_reason=None,
        phase="complete",
        architecture_progress="4/4",
        next_architecture_label=None,
        next_block_status=None,
        proactive_question=None,
        suggested_action=None,
        physical_requirements={},
        component_bom={"defined": [], "incomplete": [], "missing": [], "declarative": []},
        energy_model_note=None,
        motor_catalog_gap=None,
        motor_catalog_matches=[],
    )
    assert cont["explain_topics"] == []


def test_t3_continuity_module_does_not_import_intelligence():
    """AST-based only: the module's own docstrings legitimately *name*
    `ontology/`/`jarvis.intelligence` to document that it never touches
    them (the honesty-lock prose) — a raw text/substring search would
    false-fail on that documentation, so only real imports are checked."""
    imported = _imported_module_names(PROJECT_CONTINUITY_PATH)
    for module_name in imported:
        assert not (
            module_name == "jarvis.intelligence"
            or module_name.startswith("jarvis.intelligence.")
        ), f"project_continuity.py imports {module_name}"


def test_t4_continuity_cite_module_does_not_import_core():
    imported = _imported_module_names(CONTINUITY_CITE_PATH)
    for module_name in imported:
        assert not (
            module_name == "jarvis.core" or module_name.startswith("jarvis.core.")
        ), f"continuity_cite.py imports {module_name}"
    source = CONTINUITY_CITE_PATH.read_text(encoding="utf-8")
    assert "submit_command" not in source
    assert "JarvisOrchestrator" not in source


def test_t5_render_path_mentions_c_rate_and_jarvis_explain():
    lines = _render_concept_lines(["c_rate"])
    assert any("c-rate-de-bateria" in line for line in lines)
    assert any("jarvis explain" in line for line in lines)

    # Same check through the thin formatter directly.
    cites = cites_for_topics(["c_rate"])
    formatted = format_continuity_cite_lines(cites)
    assert formatted == lines

    # And through the full render_startup_context path.
    ctx = {
        "has_project": True,
        "project_slug": "demo",
        "objective": "demo",
        "continuity": {
            "situation": "Diseño validado en simulación (PASS).",
            "evidence": [],
            "next_useful_step": "Sigue.",
            "next_useful_why": "porque sí",
            "explain_topics": ["c_rate"],
        },
    }
    rendered = render_startup_context(ctx)
    assert "Conceptos (ontology):" in rendered
    assert "c-rate-de-bateria" in rendered
    assert "jarvis explain" in rendered


def test_t6_unknown_topic_no_crash_empty_cites():
    assert cites_for_topics(["not_a_real_topic"]) == []
    assert cites_for_topics(["not_a_real_topic", "c_rate"])[0].id == "c-rate-de-bateria"
    assert _render_concept_lines(["not_a_real_topic"]) == []
    assert _render_concept_lines([]) == []
    assert _render_concept_lines(None) == []


def test_pyproject_version_is_0_6_5():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.6.5"' in text
