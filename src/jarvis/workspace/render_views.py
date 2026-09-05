"""render_views
==============
Genera las vistas (views/*.md) a partir del estado del proyecto.

Regla: estos módulos SOLO leen estado — nunca lo modifican.
       WorkspaceManager es el único que llama a estas funciones y escribe en disco.
"""
from __future__ import annotations

from jarvis.schemas.state_schema import ProjectState


def render_objetivo(state: ProjectState) -> str:
    """Genera views/objetivo.md desde el estado actual."""
    p = state.current_parameters
    lines = [
        "# Objetivo",
        "",
        f"- Descripción: {state.objective}",
        f"- Tipo de vehículo: {p.get('vehicle_type', '—')}",
        f"- Carga útil objetivo: {p.get('payload_kg', '—')} kg",
        f"- Restricciones: {p.get('restrictions', '—')}",
        f"- Nivel de detalle: {p.get('detail_level', '—')}",
    ]
    return "\n".join(lines)


def render_sistema(state: ProjectState) -> str:
    """Genera views/sistema.md desde design_properties."""
    from jarvis.core.project_closure import build_component_bom, format_bom_lines

    dp = state.design_properties
    if not dp.system_defined:
        return "# Sistema\n\n_No definido aún. Usa la sesión interactiva para definir los bloques del sistema._\n"

    blocks = dp.system_blocks
    priority = dp.system_priority

    block_lines = "\n".join(f"- {b}" for b in blocks) or "- (ninguno)"
    priority_lines = "\n".join(f"{i + 1}. {b}" for i, b in enumerate(priority)) or "- (sin prioridad)"

    components_section = ""
    if dp.components:
        comp_lines = "\n".join(f"- {k}: {v.component_type}" for k, v in dp.components.items())
        components_section = f"\n## Componentes definidos\n{comp_lines}\n"

    bom = build_component_bom(state)
    bom_lines = format_bom_lines(bom, state)
    bom_section = ""
    if bom_lines:
        bom_section = "\n## BOM / gaps\n" + "\n".join(f"- {line}" for line in bom_lines) + "\n"

    return (
        "# Sistema\n\n"
        f"## Bloques\n{block_lines}\n\n"
        f"## Prioridad de diseño\n{priority_lines}\n"
        f"{components_section}"
        f"{bom_section}"
    )


def render_estado_actual(state: ProjectState) -> str:
    """Genera views/estado_actual.md con parámetros actuales + última simulación."""
    from jarvis.core.project_closure import (
        derive_physical_requirements,
        energy_model_honesty_note,
        format_requirements_lines,
    )

    p = state.current_parameters
    sim = state.latest_results.get("simulation")
    calc = state.latest_results.get("calculations")

    # Filtrar campos de configuración que no aportan al estado de diseño
    _skip = {"restrictions", "detail_level", "project_slug"}
    param_lines = "\n".join(
        f"- {k}: {v}" for k, v in p.items() if k not in _skip
    ) or "- (no definidos)"

    calc_section = ""
    if calc:
        calc_section = (
            "\n## Cálculos\n"
            f"- Masa total: {calc.get('total_mass_kg', '—')} kg\n"
            f"- Peso: {calc.get('weight_n', '—')} N\n"
            f"- Empuje requerido: {calc.get('required_thrust_n', '—')} N\n"
            f"- Empuje disponible: {calc.get('available_total_thrust_n', '—')} N\n"
        )

    sim_section = ""
    if sim:
        warnings_str = ", ".join(sim.get("warnings") or []) or "ninguno"
        sim_section = (
            "\n## Última simulación\n"
            f"- Estado: {sim.get('status', '—')}\n"
            f"- Puede volar: {sim.get('can_fly', '—')}\n"
            f"- Calidad: {sim.get('quality', '—')}\n"
            f"- Margen de seguridad: {sim.get('safety_margin_ratio', '—')}\n"
            f"- Warnings: {warnings_str}\n"
            f"- Resumen: {sim.get('summary', '—')}\n"
        )

    req = derive_physical_requirements(state)
    req_lines = format_requirements_lines(req)
    req_section = ""
    if req_lines:
        req_section = "\n## Requisitos físicos\n" + "\n".join(f"- {line}" for line in req_lines) + "\n"

    energy_note = energy_model_honesty_note(state)
    energy_section = f"\n## Nota energética\n- {energy_note}\n" if energy_note else ""

    return (
        "# Estado actual\n\n"
        f"## Parámetros\n{param_lines}\n"
        f"{calc_section}"
        f"{sim_section}"
        f"{req_section}"
        f"{energy_section}"
    )


def render_reasoning(reasoning_dict: dict) -> str:
    """Genera views/reasoning.md desde el último resultado de ReasoningLayer."""
    explanation = reasoning_dict.get("explanation", "—")
    insights = reasoning_dict.get("insights") or []
    tradeoffs = reasoning_dict.get("tradeoffs") or []
    suggested_actions = reasoning_dict.get("suggested_actions") or []

    insight_lines = "\n".join(f"- {i}" for i in insights) or "- (ninguno)"
    tradeoff_lines = "\n".join(f"- {t}" for t in tradeoffs) or "- (ninguno)"
    action_lines = (
        "\n".join(f"- {a.get('label', str(a))}" for a in suggested_actions)
        or "- (ninguno)"
    )

    return (
        "# Razonamiento\n\n"
        f"## Explicación\n{explanation}\n\n"
        f"## Insights\n{insight_lines}\n\n"
        f"## Tradeoffs\n{tradeoff_lines}\n\n"
        f"## Acciones sugeridas\n{action_lines}\n"
    )
