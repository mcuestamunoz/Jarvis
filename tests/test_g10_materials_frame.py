"""G10 — Material catalog / frame acquisition (Implementation Contract acceptance tests).

Covers ★1–★8 per .jes/artifacts/design_g10_materials_frame.md:
  T1 acquisition coverage (all 8 library materials via frame wizard)
  T2 the exact CLI-reported failures (plastico/pvc/PVC)
  T3 force-frame bypass (★3) in isolation from keyword expansion (★4)
  T4 dual-name mutation regression (investigation §5.2 — the core bug)
  T5 legacy English-slug read shim (★5)
  T6 madera removed from the alias table (★7)
  T7 deterministic list-materials, 0 LLM (★8)
  T8 existing happy paths still work (no regression)
"""
from __future__ import annotations

import pytest

from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.parameter_requirements import MISSING_COMPONENT_DEFINITION
from jarvis.core.state_manager import OrchestratorMode
from jarvis.core.component_writers import set_frame_material
from jarvis.core.mutation_engine import MutationEngine
from jarvis.domains.materials import MATERIAL_ALIASES, resolve_material_alias
from jarvis.knowledge.library import default_library
from jarvis.schemas.action_schema import IterationDraft, IterationOperation
from jarvis.schemas.state_schema import ProjectState
from jarvis.utils.design_utils import get_frame_material


class _FakeLLM:
    """Raises if called — proves a handler is 0-LLM."""

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called for this path")


_CREATE_PARAMS = {
    "vehicle_type": "dron",
    "objective": "dron de prueba g10",
    "payload_kg": 1.0,
    "restrictions": "ninguna",
    "detail_level": "conceptual",
    "motors": 4,
    "per_motor_max_thrust_n": 12.0,
    "structure_mass_factor": 0.5,
    "safety_factor": 1.2,
}


def _project_with_frame_wizard_open(tmp_path):
    """Create a project and force the session into the scoped frame wizard
    (DEFINE_MISSING_PARAMETERS / MISSING_COMPONENT_DEFINITION, expected_keys=["frame"])."""
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    orchestrator.handle({"action": "create_project", "parameters": _CREATE_PARAMS})
    session = orchestrator.state_manager.runtime_state.session
    updated = session.model_copy(update={
        "mode": OrchestratorMode.DEFINE_MISSING_PARAMETERS,
        "pending_missing_reason": MISSING_COMPONENT_DEFINITION,
        "pending_missing_params": ["frame"],
        "pending_define_missing": False,
    })
    orchestrator.state_manager.set_runtime_session(updated)
    return orchestrator


# ── T1: acquisition coverage — all 8 library materials ────────────────────────

@pytest.mark.parametrize("material_name", [m.name for m in default_library.list_materials()])
def test_t1_all_library_materials_declarable_via_frame_wizard(tmp_path, material_name):
    orchestrator = _project_with_frame_wizard_open(tmp_path)
    result = orchestrator.handle_user_text(f"{material_name} 400g", _FakeLLM())

    assert result["status"] == "ok", f"{material_name!r} was rejected: {result}"

    state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    frame = state.design_properties.components.get("frame")
    assert frame is not None
    stored = frame.properties["material"].value
    # Must round-trip through the library with no translation layer.
    assert default_library.has_material(stored), f"stored {stored!r} not accepted by get_material()"


# ── T2: exact CLI-reported failures ────────────────────────────────────────────

@pytest.mark.parametrize("phrase", ["plastico 390g", "pvc 390g", "PVC 390g"])
def test_t2_cli_reported_failures_now_accepted(tmp_path, phrase):
    orchestrator = _project_with_frame_wizard_open(tmp_path)
    result = orchestrator.handle_user_text(phrase, _FakeLLM())

    assert result["status"] == "ok", f"{phrase!r} still re-prompts: {result}"
    assert result["action"] == "component_description_saved"


# ── T3: force-frame (★3) in isolation from keyword expansion (★4) ────────────

def test_t3_bare_mass_has_no_keyword_match():
    """Sanity premise for the next test: '400g' alone matches NO rule's keywords
    (no 'frame'/'chasis'/material stem) — only ★3's force-frame bypass
    (infer_component_for_key) can recover it inside a scoped frame wizard."""
    from jarvis.domains.aerial import aerial_registry

    rule = aerial_registry.match("400g", "400g")
    assert rule is None


def test_t3_force_frame_recovers_bare_mass(tmp_path):
    orchestrator = _project_with_frame_wizard_open(tmp_path)
    result = orchestrator.handle_user_text("400g", _FakeLLM())

    assert result["status"] == "ok", f"force-frame did not recover bare mass: {result}"
    state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    frame = state.design_properties.components.get("frame")
    assert frame is not None
    assert frame.properties["mass_kg"].value == pytest.approx(0.4)
    assert "material" not in frame.properties


# ── T4: dual-name mutation regression (investigation §5.2 — the core bug) ─────

def test_t4_material_mutation_uses_declared_frame_material_not_stale_mirror():
    """Reproduces investigation §5.2: wizard declares 'fibra de carbono' while the
    legacy structure.material mirror is left stale at 'aluminio' (set_frame_material
    never touches it). apply_material_mutation must use the declared frame material
    (carbon fiber, ρ=1600) as the density-ratio base — NOT the stale mirror
    (aluminio, ρ=2700). Before ★6 this silently computed the wrong mass."""
    ps = ProjectState.model_validate({
        "project_id": "p1", "project_slug": "p1", "workspace_path": "/tmp/p1",
        "objective": "test",
        "current_parameters": {"payload_kg": 1.0, "masa_total": 5.0},
        "design_properties": {
            "structure": {"material": "aluminio", "density": 2700, "volume": 1.0},
            "components": {},
        },
    })
    ps2 = set_frame_material(ps, 0.45, "fibra de carbono")
    assert ps2.design_properties.structure.material == "aluminio"  # stale, unchanged
    assert get_frame_material(ps2.design_properties) == "fibra de carbono"

    state_dict = {
        "material": get_frame_material(ps2.design_properties),  # what _build_mutable_state seeds
        "masa_total": 5.0,
        "design_properties": ps2.design_properties.model_dump(),
    }
    me = MutationEngine()
    draft = IterationDraft(
        variable="material", operation=IterationOperation.DEFINE, value="pvc", strategy="material"
    )
    new_state, impact = me.apply_material_mutation(state_dict, draft)

    # Correct base: fibra de carbono (1600) -> pvc (1380), NOT aluminio (2700) -> pvc.
    structural_fraction = 0.25
    expected_factor = (1 - structural_fraction) + structural_fraction * (1380 / 1600)
    expected_mass = round(5.0 * expected_factor, 4)
    assert new_state["masa_total"] == pytest.approx(expected_mass)

    # The old (buggy) aluminio-based result would have been a materially
    # different number — assert we are NOT that.
    wrong_factor = (1 - structural_fraction) + structural_fraction * (1380 / 2700)
    wrong_mass = round(5.0 * wrong_factor, 4)
    assert new_state["masa_total"] != pytest.approx(wrong_mass)


# ── T5: legacy English-slug read shim (★5) ─────────────────────────────────────

@pytest.mark.parametrize("legacy_slug,expected", [
    ("carbon_fiber", "fibra de carbono"),
    ("aluminum", "aluminio"),
    ("plastic", "plástico"),
])
def test_t5_legacy_slug_shim(legacy_slug, expected):
    from jarvis.schemas.action_schema import ComponentSpec, PropertyValue
    from jarvis.schemas.state_schema import DesignProperties

    frame = ComponentSpec(
        name="frame", component_type="structure", suggested_key="frame",
        completeness="medium",
        properties={"material": PropertyValue(value=legacy_slug, unit=None, confidence=0.9, source="declared")},
    )
    dp = DesignProperties(components={"frame": frame})
    assert get_frame_material(dp) == expected
    # Translated value must itself be library-accepted.
    assert default_library.has_material(get_frame_material(dp))


# ── T6: madera removed from the alias table (★7) ───────────────────────────────

def test_t6_madera_not_a_known_alias():
    assert "madera" not in MATERIAL_ALIASES
    assert resolve_material_alias("madera 300g") is None
    assert not default_library.has_material("madera")


# ── T7: deterministic list-materials, 0 LLM (★8) ───────────────────────────────

@pytest.mark.parametrize("phrase", [
    "que materiales tenemos en el catalogo?",
    "qué materiales hay disponibles",
    "catalogo de materiales",
])
def test_t7_list_materials_is_deterministic(tmp_path, phrase):
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    orchestrator.handle({"action": "create_project", "parameters": _CREATE_PARAMS})

    result = orchestrator.handle_user_text(phrase, _FakeLLM())  # raises if LLM invoked

    assert result["status"] == "ok"
    assert result["action"] == "list_materials"
    for spec in default_library.list_materials():
        assert spec.name in result["message"]


def test_t7_list_materials_works_mid_frame_wizard(tmp_path):
    """Materials catalog query is a soft interrupt — wizard stays intact."""
    orchestrator = _project_with_frame_wizard_open(tmp_path)
    result = orchestrator.handle_user_text("que materiales tenemos en el catalogo?", _FakeLLM())
    assert result["status"] == "ok"
    assert result["action"] == "list_materials"


# ── T8: existing happy paths still work ────────────────────────────────────────

@pytest.mark.parametrize("phrase", ["fibra de carbono 450g", "aluminio 450g"])
def test_t8_existing_happy_paths_unchanged(tmp_path, phrase):
    orchestrator = _project_with_frame_wizard_open(tmp_path)
    result = orchestrator.handle_user_text(phrase, _FakeLLM())
    assert result["status"] == "ok"
    assert result["action"] == "component_description_saved"
