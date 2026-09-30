"""Tests T1-T5 for `B1-continuity-explain-topics-expand` (A8).

Wires the `current` topic (seeded but unused since R3) to a real,
already-distinguished Continuity signal: `current_parameters
["motor_op_current_a"] is not None` — never from watts-recovery alone
or a generic energy/catalog gap.
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

from jarvis.core.project_continuity import build_project_continuity
from jarvis.intelligence.continuity_cite import cites_for_topics

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


def _neutral_continuity(**overrides):
    kwargs = dict(
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
    kwargs.update(overrides)
    return build_project_continuity(**kwargs)


def test_t1_op_current_present_tags_current_and_resolves_to_solid_cite():
    cont = _neutral_continuity(
        project_state=_state(
            current_parameters={"motor_count": 4, "motor_op_current_a": 12.5}
        )
    )
    assert "current" in cont["explain_topics"]

    cites = cites_for_topics(cont["explain_topics"])
    matching = [c for c in cites if c.id == "corriente-y-circuitos"]
    assert len(matching) == 1
    assert matching[0].estado == "solid"


def test_t2_op_current_absent_no_current_tag():
    cont = _neutral_continuity(project_state=_state())
    assert "current" not in cont["explain_topics"]
    assert cont["explain_topics"] == []

    # And with a motor_op_current_a explicitly set to None (present key,
    # null value) — still must not tag, per the IC's own "is not None" lock.
    cont_null = _neutral_continuity(
        project_state=_state(
            current_parameters={"motor_count": 4, "motor_op_current_a": None}
        )
    )
    assert "current" not in cont_null["explain_topics"]


def test_t2b_current_not_tagged_from_watts_recovery_or_generic_energy_alone():
    """IC §1 'Forbidden': current must not be tagged from watts-recovery
    activity or a generic energy_model_note — only from the distinguished
    motor_op_current_a signal. Neither of these fixtures sets that field."""
    cont_energy = _neutral_continuity(
        project_state=_state(),
        energy_model_note="Nota de energía genérica sin corriente distinguida.",
    )
    assert "current" not in cont_energy["explain_topics"]
    assert "c_rate" in cont_energy["explain_topics"]
    assert "operating_point" in cont_energy["explain_topics"]

    cont_gap = _neutral_continuity(
        project_state=_state(),
        motor_catalog_gap="Necesitas empuje ≥ 4.8 N/motor; no tengo motor en catálogo.",
    )
    assert "current" not in cont_gap["explain_topics"]
    assert cont_gap["explain_topics"] == ["motor"]


def test_t3_ranking_regression_golden_strings_unchanged():
    """Reuses the exact R3 golden fixture — next_useful_step/next_useful_why
    must still match byte-for-byte after A8's addition, proving the new
    kwarg/tag is purely additive."""
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


def test_t4_fences_hold_ast():
    imported = _imported_module_names(PROJECT_CONTINUITY_PATH)
    assert not any(
        m == "jarvis.intelligence" or m.startswith("jarvis.intelligence.")
        for m in imported
    ), "project_continuity.py imports jarvis.intelligence"

    imported_cite = _imported_module_names(CONTINUITY_CITE_PATH)
    assert not any(
        m == "jarvis.core" or m.startswith("jarvis.core.") for m in imported_cite
    ), "continuity_cite.py imports jarvis.core"


def test_t5_cites_for_topics_current_has_definicion():
    cites = cites_for_topics(["current"])
    assert len(cites) == 1
    assert cites[0].id == "corriente-y-circuitos"
    assert cites[0].definicion != ""


def test_pyproject_version_is_0_6_10():
    """Bumped forward by T2 (B1-capability-registry-product-fill) per
    established pattern."""
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.6.18"' in text
