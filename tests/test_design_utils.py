"""Tests Fase 3 — Single Read Point.

Valida que:
1. Los getters de design_utils leen exclusivamente de components (fuente canónica).
2. Cuando components y el mirror legacy divergen, los getters retornan el valor de components.
3. iterate._build_mutable_state usa el getter (no el mirror legacy).
4. Los fallbacks son correctos cuando el componente no existe o tiene completeness=low.
"""
from __future__ import annotations

import pytest

from jarvis.schemas.action_schema import ComponentSpec, PropertyValue
from jarvis.schemas.state_schema import DesignProperties, StructureProperties
from jarvis.utils.design_utils import (
    get_battery_capacity_wh,
    get_frame_mass_kg,
    get_frame_material,
)


# ── Helpers de construcción ───────────────────────────────────────────────────

def _make_frame_spec(material: str, mass_kg: float | None = None, completeness: str = "medium") -> ComponentSpec:
    props: dict[str, PropertyValue] = {
        "material": PropertyValue(value=material, unit=None, confidence=0.9, source="declared"),
    }
    if mass_kg is not None:
        props["mass_kg"] = PropertyValue(value=mass_kg, unit="kg", confidence=0.9, source="declared")
    return ComponentSpec(
        name="frame",
        component_type="structure",
        suggested_key="frame",
        completeness=completeness,
        properties=props,
    )


def _make_battery_spec(capacity_wh: float, completeness: str = "medium") -> ComponentSpec:
    return ComponentSpec(
        name="battery",
        component_type="energy_storage",
        suggested_key="battery",
        completeness=completeness,
        properties={
            "battery_capacity_wh": PropertyValue(value=capacity_wh, unit="Wh", confidence=0.9, source="declared"),
        },
    )


def _dp(frame: ComponentSpec | None = None, battery: ComponentSpec | None = None,
        mirror_material: str | None = None) -> DesignProperties:
    """Construye un DesignProperties con los componentes y el mirror indicados."""
    components: dict[str, ComponentSpec] = {}
    if frame is not None:
        components["frame"] = frame
    if battery is not None:
        components["battery"] = battery
    structure = StructureProperties(material=mirror_material)
    return DesignProperties(structure=structure, components=components)


# ── get_frame_material ────────────────────────────────────────────────────────

class TestGetFrameMaterial:

    def test_returns_material_from_components(self):
        """Caso normal: frame definido con material fibra de carbono (library Spanish, ★1)."""
        dp = _dp(frame=_make_frame_spec("fibra de carbono"))
        assert get_frame_material(dp) == "fibra de carbono"

    def test_fallback_when_no_frame(self):
        """Sin frame en components → fallback 'aluminio'."""
        dp = _dp()
        assert get_frame_material(dp) == "aluminio"

    def test_fallback_when_completeness_low(self):
        """Frame con completeness=low → tratar como ausente → fallback 'aluminio'."""
        dp = _dp(frame=_make_frame_spec("fibra de carbono", completeness="low"))
        assert get_frame_material(dp) == "aluminio"

    def test_getter_wins_over_mirror_when_inconsistent(self):
        """COHERENCIA CRÍTICA: components dice fibra de carbono, mirror dice aluminio.
        El getter debe retornar el valor de components (fuente canónica), no el mirror.
        Este es el test definitorio de Fase 3: si pasa, Single Read Point está correcto."""
        dp = _dp(
            frame=_make_frame_spec("fibra de carbono"),
            mirror_material="aluminio",  # mirror inconsistente
        )
        assert get_frame_material(dp) == "fibra de carbono"  # components gana siempre

    def test_mirror_value_irrelevant_when_components_has_data(self):
        """El mirror puede tener cualquier valor — si components tiene datos, gana."""
        dp = _dp(
            frame=_make_frame_spec("aluminio"),
            mirror_material="fibra de carbono",  # mirror incorrecto
        )
        assert get_frame_material(dp) == "aluminio"

    def test_fallback_to_aluminio_not_mirror_when_no_frame(self):
        """Sin frame en components → fallback es 'aluminio' explícito, nunca el mirror."""
        dp = _dp(mirror_material="fibra de carbono")  # mirror tiene algo, pero no hay frame
        assert get_frame_material(dp) == "aluminio"  # fallback explícito, ignora mirror

    def test_legacy_english_slug_translated_to_library_name(self):
        """G10 ★5: a ComponentSpec persisted before this fix (English MATERIAL_MAP
        slug) must read back as the library Spanish name — no state migration needed."""
        dp = _dp(frame=_make_frame_spec("carbon_fiber"))
        assert get_frame_material(dp) == "fibra de carbono"
        dp2 = _dp(frame=_make_frame_spec("aluminum"))
        assert get_frame_material(dp2) == "aluminio"
        dp3 = _dp(frame=_make_frame_spec("plastic"))
        assert get_frame_material(dp3) == "plástico"


# ── get_frame_mass_kg ─────────────────────────────────────────────────────────

class TestGetFrameMassKg:

    def test_returns_mass_from_components(self):
        """Masa en components → retorna el valor."""
        dp = _dp(frame=_make_frame_spec("carbon_fiber", mass_kg=0.45))
        assert get_frame_mass_kg(dp) == pytest.approx(0.45)

    def test_none_when_no_frame(self):
        """Sin frame → None."""
        dp = _dp()
        assert get_frame_mass_kg(dp) is None

    def test_none_when_completeness_low(self):
        """Frame con completeness=low → None."""
        dp = _dp(frame=_make_frame_spec("carbon_fiber", mass_kg=0.45, completeness="low"))
        assert get_frame_mass_kg(dp) is None

    def test_none_when_mass_not_in_properties(self):
        """Frame sin mass_kg en properties → None."""
        spec = ComponentSpec(
            name="frame", suggested_key="frame", completeness="medium",
            properties={"material": PropertyValue(value="carbon_fiber")},
        )
        dp = _dp(frame=spec)
        assert get_frame_mass_kg(dp) is None


# ── get_battery_capacity_wh ───────────────────────────────────────────────────

class TestGetBatteryCapacityWh:

    def test_returns_capacity_from_components(self):
        """Batería definida → retorna capacidad."""
        dp = _dp(battery=_make_battery_spec(111.0))
        assert get_battery_capacity_wh(dp) == pytest.approx(111.0)

    def test_none_when_no_battery(self):
        """Sin batería → None."""
        dp = _dp()
        assert get_battery_capacity_wh(dp) is None

    def test_none_when_completeness_low(self):
        """Batería con completeness=low → None."""
        dp = _dp(battery=_make_battery_spec(111.0, completeness="low"))
        assert get_battery_capacity_wh(dp) is None


# ── Integración: iterate._build_mutable_state usa getter ─────────────────────

class TestIterateBuildMutableStateUsesGetter:
    """Verifica que _build_mutable_state (iterate.py) usa get_frame_material,
    no structure.material. Si components y el mirror divergen, _build_mutable_state
    debe usar el valor de components."""

    def _make_iterate_action(self, orc):
        """Instancia IterateAction con los componentes del orchestrator dado."""
        from jarvis.actions.iterate import IterateAction
        from jarvis.core.mutation_engine import MutationEngine
        from jarvis.suggestions.suggestion_engine import SuggestionEngine
        from jarvis.core.reasoning_layer import ReasoningLayer
        return IterateAction(
            workspace_manager=orc.workspace_manager,
            state_manager=orc.state_manager,
            simulator=orc.simulator,
            calculation_engine=orc.calculation_engine,
            mutation_engine=MutationEngine(),
            suggestion_engine=SuggestionEngine(),
            reasoning_layer=orc.reasoning_layer,
        )

    def test_build_mutable_state_uses_components_material(self, tmp_path):
        """_build_mutable_state debe leer de components["frame"], no del mirror."""
        from jarvis.core.orchestrator import JarvisOrchestrator

        orc = JarvisOrchestrator(workspace_root=tmp_path)
        orc.handle({
            "action": "create_project",
            "parameters": {
                "vehicle_type": "dron",
                "objective": "test fase3",
                "payload_kg": 1.0,
                "restrictions": "ninguna",
                "detail_level": "conceptual",
                "motors": 4,
                "per_motor_max_thrust_n": 12.0,
                "structure_mass_factor": 0.5,
                "safety_factor": 1.2,
            },
        })

        state = orc.state_manager.load_active_project(orc.workspace_manager)

        # Frame con fibra de carbono en components, aluminio en mirror → inconsistencia deliberada
        frame_spec = _make_frame_spec("fibra de carbono", mass_kg=0.45)
        updated_components = {**state.design_properties.components, "frame": frame_spec}
        updated_structure = state.design_properties.structure.model_copy(
            update={"material": "aluminio"}  # mirror inconsistente
        )
        updated_dp = state.design_properties.model_copy(update={
            "components": updated_components,
            "structure": updated_structure,
        })
        state_with_inconsistency = state.model_copy(update={"design_properties": updated_dp})

        iterate_action = self._make_iterate_action(orc)
        mutable = iterate_action._build_mutable_state(state_with_inconsistency)

        # El getter debe retornar fibra de carbono (de components), no aluminio (del mirror)
        assert mutable["material"] == "fibra de carbono"

    def test_build_mutable_state_fallback_when_no_frame(self, tmp_path):
        """Sin frame en components, _build_mutable_state usa 'aluminio' como fallback."""
        from jarvis.core.orchestrator import JarvisOrchestrator

        orc = JarvisOrchestrator(workspace_root=tmp_path)
        orc.handle({
            "action": "create_project",
            "parameters": {
                "vehicle_type": "dron",
                "objective": "test fase3 fallback",
                "payload_kg": 1.0,
                "restrictions": "ninguna",
                "detail_level": "conceptual",
                "motors": 4,
                "per_motor_max_thrust_n": 12.0,
                "structure_mass_factor": 0.5,
                "safety_factor": 1.2,
            },
        })

        state = orc.state_manager.load_active_project(orc.workspace_manager)
        # Sin frame en components → fallback aluminio
        iterate_action = self._make_iterate_action(orc)
        mutable = iterate_action._build_mutable_state(state)
        assert mutable["material"] == "aluminio"


# ── Consistencia display: _build_analyze_context usa getter, no mirror ────────

class TestDisplayUsesGetterNotMirror:
    """Verifica que la capa de display (_build_analyze_context) usa el getter
    canónico y no el mirror legacy structure.material.

    Garantiza que cuando components y el mirror divergen, el LLM recibe
    el valor correcto (de components), no el valor stale del mirror.
    """

    _CREATE_PARAMS = {
        "vehicle_type": "dron",
        "objective": "test display getter",
        "payload_kg": 1.0,
        "restrictions": "ninguna",
        "detail_level": "conceptual",
        "motors": 4,
        "per_motor_max_thrust_n": 12.0,
        "structure_mass_factor": 0.5,
        "safety_factor": 1.2,
    }

    def test_display_uses_getter_not_mirror(self, tmp_path):
        """_build_analyze_context['material'] debe retornar el valor de components,
        no de structure.material, cuando ambos divergen.
        """
        from jarvis.core.orchestrator import JarvisOrchestrator

        orc = JarvisOrchestrator(workspace_root=tmp_path)
        orc.handle({"action": "create_project", "parameters": self._CREATE_PARAMS})

        state = orc.state_manager.load_active_project(orc.workspace_manager)

        # Inyectar inconsistencia: components dice fibra de carbono, mirror dice aluminio
        frame_spec = _make_frame_spec("fibra de carbono", mass_kg=0.45)
        updated_components = {**state.design_properties.components, "frame": frame_spec}
        updated_structure = state.design_properties.structure.model_copy(
            update={"material": "aluminio"}  # mirror stale
        )
        updated_dp = state.design_properties.model_copy(update={
            "components": updated_components,
            "structure": updated_structure,
        })
        state_inconsistent = state.model_copy(update={"design_properties": updated_dp})

        context = orc._build_analyze_context(state_inconsistent)

        # El display debe retornar fibra de carbono (de components), no aluminio (del mirror)
        assert context["material"] == "fibra de carbono"

    def test_display_fallback_when_no_frame(self, tmp_path):
        """Sin frame en components, _build_analyze_context['material'] retorna 'aluminio'."""
        from jarvis.core.orchestrator import JarvisOrchestrator

        orc = JarvisOrchestrator(workspace_root=tmp_path)
        orc.handle({"action": "create_project", "parameters": self._CREATE_PARAMS})

        state = orc.state_manager.load_active_project(orc.workspace_manager)
        # Eliminar frame de components para forzar fallback
        updated_components = {k: v for k, v in state.design_properties.components.items() if k != "frame"}
        updated_dp = state.design_properties.model_copy(update={"components": updated_components})
        state_no_frame = state.model_copy(update={"design_properties": updated_dp})

        context = orc._build_analyze_context(state_no_frame)

        assert context["material"] == "aluminio"
