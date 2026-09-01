from __future__ import annotations

import argparse
import json
from pathlib import Path

from jarvis.config import DEFAULT_LLM_LOG_ROOT, OLLAMA_BASE_URL, OLLAMA_MODEL
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.parameter_requirements import (
    DEFAULT_MISSING_FORCE_REASON,
    MISSING_COMPONENT_DEFINITION,
    MISSING_ENERGY_PARAMETERS,
    MISSING_PROPELLER_PARAMETERS,
    param_hint,
)
from jarvis.llm.llm_client import JarvisLLMInterface
from jarvis.llm.ollama_client import OllamaClient

# Reasons that justify auto-opening the define-missing wizard on project load.
_AUTO_DEFINE_REASONS = frozenset({
    MISSING_COMPONENT_DEFINITION,
    MISSING_ENERGY_PARAMETERS,
    MISSING_PROPELLER_PARAMETERS,
})


def should_auto_start_define_on_load(startup_ctx: dict) -> bool:
    """FN-001: only auto-open define wizard when there are real pending params.

    Do not start the wizard merely because proactive_question / continuity
    suggests a next step — that produced spurious "No hay parámetros pendientes".
    """
    missing = list(startup_ctx.get("missing_params") or [])
    if not missing:
        return False
    if startup_ctx.get("status_type") == "blocking":
        return True
    reason = startup_ctx.get("param_definition_reason") or ""
    return reason in _AUTO_DEFINE_REASONS


class DemoLLMClient:
    def __init__(self, responses: list[str]) -> None:
        self.responses = responses

    def complete(self, messages: list[dict[str, str]], json_mode: bool = True) -> str:
        if not self.responses:
            raise RuntimeError("No quedan respuestas demo del LLM.")
        return self.responses.pop(0)


SUGGESTION_LABELS = {
    "reduce_weight": "reducir peso",
    "increase_payload": "aumentar la carga útil",
    "improve_efficiency": "mejorar la eficiencia",
    "increase_thrust": "aumentar el empuje disponible",
    "improve_autonomy": "mejorar la autonomía",
}

# ── Warning translations ──────────────────────────────────────────────────────
# Full human-readable descriptions for simulation warning codes.
WARNING_MESSAGES: dict[str, str] = {
    "low_margin": (
        "Margen de seguridad ajustado — el sistema opera cerca del límite. "
        "Riesgo ante variaciones de carga o viento."
    ),
    "high_actuator_load": (
        "Los motores trabajan cerca de su capacidad máxima. "
        "Un pico de carga puede comprometer el vuelo."
    ),
    "low_force_to_weight_ratio": (
        "La relación empuje/peso es baja. "
        "El sistema tiene poca reserva para maniobras o peso extra."
    ),
    "autonomy_below_restriction": "Autonomía por debajo de la restricción definida.",
}
# Short labels for compact displays (startup context header).
WARNING_SHORT: dict[str, str] = {
    "low_margin": "margen ajustado",
    "high_actuator_load": "carga en motores elevada",
    "low_force_to_weight_ratio": "relación empuje/peso baja",
    "autonomy_below_restriction": "autonomía por debajo de restricción",
}


def _human_warning(code: str) -> str:
    """Return full human-readable description for a simulator warning code."""
    return WARNING_MESSAGES.get(code, code)

_STATUS_ICON = {
    "blocking": "⚠ ",
    "warning": "⚠ ",
    "nominal": "✓ ",
    "no_data": "○ ",
}

_PHASE_LABELS = {
    "definition": "Fase: definición del sistema",
    "physical_validation": "Fase: validación física",
    "optimization": "Fase: optimización",
    "complete": "Fase: completado",
}


# ERF-2 ★8 — canonical display order + labels for the nine readiness
# subsystems (ERF-1's eight + electronics).
_READINESS_SUBSYSTEM_LABELS: dict[str, str] = {
    "requirements": "Requirements",
    "architecture": "Architecture",
    "structure": "Structure",
    "propulsion": "Propulsion",
    "energy": "Energy",
    "electronics": "Electronics",
    "control": "Control",
    "catalog": "Catalog",
    "bom": "BOM",
}
_READINESS_SUBSYSTEM_ORDER: tuple[str, ...] = tuple(_READINESS_SUBSYSTEM_LABELS)


def _render_readiness_block(readiness: dict) -> list[str]:
    """ERF-1 Slice 5 / ERF-2 Slice 4 — 9 subsystem lines + overall + up to 3
    top gaps (verdict column shows INCOMPATIBLE verbatim — no new logic here,
    display only; the verdict string itself comes straight from
    engineering_readiness).

    Pure formatting over an already-computed readiness dict (from
    ``dataclasses.asdict(EngineeringReadinessResult)``) — no engineering
    logic here, only display.
    """
    subsystems = readiness.get("subsystems") or {}
    lines: list[str] = ["ENGINEERING READINESS", ""]
    for key in _READINESS_SUBSYSTEM_ORDER:
        entry = subsystems.get(key) or {}
        verdict = entry.get("verdict", "UNVERIFIABLE")
        label = _READINESS_SUBSYSTEM_LABELS[key]
        lines.append(f"{label:<14} {verdict}")

    overall = readiness.get("overall", "NOT_ASSEMBLY_READY")
    status_text = "ASSEMBLY READY" if overall == "ASSEMBLY_READY" else "NOT ASSEMBLY READY"
    lines.append("")
    lines.append(f"PROJECT STATUS: {status_text}")

    top_gaps = (readiness.get("prioritized_gaps") or [])[:3]
    if top_gaps:
        lines.append("")
        lines.append("TOP GAPS")
        for gap in top_gaps:
            lines.append("")
            lines.append(gap["gap_id"])
            lines.append(f"  {gap['title']}")
            blocks = ", ".join(gap.get("blocks") or [])
            lines.append(f"  {gap['severity']} — blocks: {blocks}")
            depends_on = ", ".join(gap.get("depends_on") or [])
            lines.append(f"  depends_on: [{depends_on}]")
            next_step = gap.get("recommended_next_step") or {}
            lines.append(f"  next: {next_step.get('action', '')}")
    return lines


def render_startup_context(ctx: dict) -> str:
    """Render a build_startup_context dict as a concise CLI block."""
    if not ctx.get("has_project"):
        return ""

    lines: list[str] = []
    lines.append(f"Proyecto: {ctx['project_slug']}")
    if ctx.get("objective"):
        lines.append(f"Objetivo: {ctx['objective']}")

    # ── A' Project Continuity: Situation / Evidence / Next useful step ───────
    continuity = ctx.get("continuity") or {}
    if continuity.get("situation") or continuity.get("next_useful_step"):
        lines.append("─" * 44)
        if continuity.get("situation"):
            lines.append(f"Situación: {continuity['situation']}")
        evidence = continuity.get("evidence") or []
        if evidence:
            lines.append("Evidencia:")
            for item in evidence[:6]:
                lines.append(f"   • {item}")
        if continuity.get("next_useful_step"):
            lines.append(f"Siguiente paso: {continuity['next_useful_step']}")
            if continuity.get("next_useful_why"):
                lines.append(f"   Por qué: {continuity['next_useful_why']}")
        lines.append("─" * 44)

    phase = ctx.get("phase")
    # FN-002: when Continuity is present, skip noisy "Fase: completado" — situation covers it.
    if phase and not continuity.get("situation"):
        lines.append(_PHASE_LABELS.get(phase, f"Fase: {phase}"))

    status_type = ctx.get("status_type", "no_data")
    icon = _STATUS_ICON.get(status_type, "  ")

    if status_type == "blocking":
        lines.append(f"{icon}Simulación incompleta")
        missing = ctx.get("missing_params") or []
        if missing:
            lines.append("   Faltan parámetros:")
            for p in missing:
                hint_text = param_hint(p)
                lines.append(f"   • {p}  {hint_text}".rstrip())
    elif status_type == "warning":
        reason = ctx.get("status_reason") or ""
        short = WARNING_SHORT.get(reason, reason) if reason else "warning activo"
        lines.append(f"{icon}Última simulación: WARNING ({short})")
    elif status_type == "nominal" and not continuity.get("situation"):
        lines.append(f"{icon}Última simulación: OK")
    elif status_type == "no_data" and not continuity.get("situation"):
        lines.append(f"{icon}Sin simulación previa")

    active_vars = ctx.get("active_variables") or {}
    if active_vars and not continuity.get("evidence"):
        var_str = "  ·  ".join(f"{k}={v}" for k, v in active_vars.items())
        lines.append(f"   {var_str}")

    # Secondary signals — only if they don't duplicate the continuity next step
    continuity_next = (continuity.get("next_useful_step") or "").strip()
    suggested = ctx.get("suggested_action")
    if suggested and suggested.get("label"):
        # Hide optimization suggestion when continuity already chose a higher-priority next
        if continuity_next and suggested["label"] not in continuity_next:
            pass  # competing hint — Continuity wins
        elif not continuity_next:
            lines.append("")
            lines.append(f"→  {suggested['label']}")
            if suggested.get("hint"):
                lines.append(f"   {suggested['hint']}")

    # Architecture progress — compact when Continuity already narrates gaps
    arch_progress = ctx.get("architecture_progress")
    arch_label = ctx.get("next_architecture_label")
    arch_block_status = ctx.get("next_block_status")
    if arch_progress and not continuity.get("next_useful_step"):
        lines.append("")
        if arch_label:
            status_tag = " (en progreso)" if arch_block_status == "in_progress" else ""
            lines.append(f"   Arquitectura {arch_progress} — Siguiente: {arch_label}{status_tag}")
        else:
            lines.append(f"   Arquitectura {arch_progress} — completa ✓")
    elif arch_progress and continuity.get("next_useful_step"):
        # One quiet line under Continuity
        if not arch_label:
            lines.append(f"   Arquitectura {arch_progress} — completa ✓")

    req_lines = ctx.get("physical_requirements_lines") or []
    if req_lines and not continuity.get("evidence"):
        lines.append("")
        lines.append("Requisitos físicos:")
        for line in req_lines:
            lines.append(f"   • {line}")

    # Impl D ★6/D4: BOM lines render whenever present, independent of
    # Continuity's own evidence state — previously this section was
    # suppressed any time Continuity had *any* evidence queued (physics
    # gaps, catalog gaps, the energy-model honesty note — all common
    # states), which meant a SKU-aware BOM (this IC's whole point) could be
    # correct and still invisible in `estado`. Presentation-only change: no
    # Continuity ranking/next_useful_step/evidence-block edit (★3 stays
    # untouched). The sibling `req_lines` gate above is deliberately left
    # as-is — out of this IC's ★6 scope.
    bom_lines = ctx.get("component_bom_lines") or []
    if bom_lines:
        lines.append("")
        lines.append("Componentes / gaps:")
        for line in bom_lines:
            lines.append(f"   {line}")

    # Phase 2 P2-1 (Lookup Operating Point) — honest evidence label for the
    # current per_motor_max_thrust_n. Never claims exact/manufacturer_test
    # for a fallback or legacy resolution (★6 resolver contract).
    propulsion_resolution = ctx.get("propulsion_resolution")
    if propulsion_resolution:
        resolution_type = propulsion_resolution.get("resolution_type")
        source_type = propulsion_resolution.get("source_type")
        thrust_n = propulsion_resolution.get("thrust_n")
        suffix = ""
        if resolution_type == "fallback_operating_point":
            suffix = " (sin hélice de catálogo)"
        lines.append("")
        label = f"Propulsión (evidencia): {resolution_type} · {source_type}"
        if thrust_n is not None:
            label += f" · {thrust_n} N"
        lines.append(label + suffix)

    # P2-2 (Operating Point Bridge) — distinct line for the OP's real
    # electrical measurement (power/current/rpm), never conflated with the
    # catalog rating shown via motor_power_w elsewhere. Only rendered when
    # an operating point was actually resolved (exact/fallback) — absent
    # for legacy_estimate/freeform, same honesty discipline as the
    # propulsion_resolution block above.
    op_electrical = ctx.get("motor_operating_point_electrical")
    if op_electrical:
        op_bits = []
        if op_electrical.get("power_w") is not None:
            op_bits.append(f"power={op_electrical['power_w']} W")
        if op_electrical.get("current_a") is not None:
            op_bits.append(f"current={op_electrical['current_a']} A")
        if op_electrical.get("rpm") is not None:
            op_bits.append(f"rpm={op_electrical['rpm']}")
        if op_bits:
            lines.append(f"Propulsión (OP eléctrico): {' · '.join(op_bits)}")

    # Phase 2.5 (Hover Flight Energy Model, ★★10/§2.4) — honest hover-regime
    # motor input power, distinct from the bench-max OP line above. Never
    # rendered as "real flight time" (Engineer naming lock) — always states
    # this is bench motor input power, not pack/system draw. Absent when no
    # calculation has run, or the bound motor has no Discrete OP Dataset for
    # its identity at all (honest omission, not a false "unverifiable").
    hover_energy = ctx.get("hover_energy")
    if hover_energy:
        source_type = hover_energy.get("source_type")
        power_w = hover_energy.get("power_w")
        autonomy_min = hover_energy.get("hover_energy_autonomy_min")
        if source_type == "unverifiable":
            lines.append(
                "Energía hover (evidencia): unverifiable · fuera del rango del dataset "
                f"({hover_energy.get('selection_reason')}) · sin hover_energy_autonomy_min"
            )
        else:
            bits = [source_type]
            if power_w is not None:
                bits.append(f"P_motor_input={power_w} W/motor (bench, no incluye ESC/sistema)")
            if autonomy_min is not None:
                bits.append(f"hover_energy_autonomy_min≈{round(autonomy_min, 2)} min")
            lines.append(f"Energía hover (evidencia): {' · '.join(bits)}")

    # ERF-1 Slice 5 — Engineering Readiness block (8 subsystems + overall + top gaps)
    readiness = ctx.get("readiness")
    if readiness:
        lines.append("")
        lines.extend(_render_readiness_block(readiness))

    return "\n".join(lines)


def render_response(result: dict) -> str:
    if result.get("status") == "error":
        return result.get("message") or "No he entendido la instrucción."

    if result.get("status") == "interactive":
        parts = []
        if result.get("error"):
            parts.append(f"Error: {result['error']}")
        if result.get("message"):
            parts.append(result["message"])
        if result.get("question"):
            parts.append("Siguiente paso:")
            parts.append(result["question"])
        return "\n".join(parts)

    if result.get("status") == "cancelled":
        return result.get("message", "Operación cancelada.")

    if result.get("action") == "project_status":
        ctx = result.get("startup_context") or {}
        rendered = render_startup_context(ctx)
        base = rendered if rendered else "No hay proyecto activo."
        # Edge case 1: dismiss with no active suggestion (no-op).
        if result.get("dismiss_noop"):
            return base + "\n\n(No había sugerencia activa que descartar.)"
        # Edge case 2: all non-blocked suggestions dismissed.
        if result.get("all_suggestions_dismissed"):
            return base + "\n\n(No hay más sugerencias relevantes en el estado actual.)"
        # Bug 51: if interrupted during iterate wizard, remind the user the wizard is waiting.
        reprompt = result.get("wizard_reprompt")
        if reprompt:
            return base + f"\n\n[Wizard activo] {reprompt}"
        return base

    if result.get("action") == "define_missing_params":
        if result.get("status") == "interactive":
            parts = []
            if result.get("error"):
                parts.append(result["error"])
            if result.get("question"):
                parts.append(result["question"])
            return "\n".join(parts)
        # completed — falls through to the generic "ok" handler below

    # global_command responses carry their own message; no "Acción ejecutada:" prefix.
    if result.get("action") == "global_command":
        return result.get("message") or ""

    if result.get("status") == "ok":
        if result.get("action") == "analyze":
            parts = []
        else:
            parts = [f"Acción ejecutada: {result.get('action')}"]
        if result.get("project_id"):
            parts.append(f"Proyecto: {result['project_id']}")
        if result.get("message"):
            parts.append(result["message"])

        calculations = result.get("calculations")
        if calculations:
            thrust_available = calculations.get("available_total_thrust_n")
            thrust_str = f"{thrust_available} N" if thrust_available is not None else "sin definir"
            autonomy_min = calculations.get("autonomy_min")
            autonomy_str = f", autonomía={round(autonomy_min, 1)} min" if autonomy_min is not None else ""
            parts.append(
                "Cálculos: "
                f"masa_total={calculations['total_mass_kg']} kg, "
                f"peso={calculations['weight_n']} N, "
                f"empuje_requerido={calculations['required_thrust_n']} N, "
                f"empuje_disponible={thrust_str}"
                f"{autonomy_str}"
            )

        simulation = result.get("simulation")
        if simulation:
            if simulation.get("physics_status") == "missing_parameters":
                missing_reason = (simulation.get("warnings") or ["parámetros ausentes"])[0]
                parts.append(f"Simulación: incompleta — {missing_reason}")
            else:
                raw_warnings = simulation.get("warnings", [])
                autonomy_min = simulation.get("autonomy_min")
                autonomy_str = f", autonomía={round(autonomy_min, 1)} min" if autonomy_min is not None else ""
                parts.append(
                    "Simulación: "
                    f"status={simulation['status']}, "
                    f"quality={simulation['quality']}, "
                    f"safety_margin_ratio={simulation['safety_margin_ratio']}"
                    f"{autonomy_str}"
                )
                for w in raw_warnings:
                    if w == "autonomy_below_restriction":
                        auto_label = f" ({round(autonomy_min, 1)} min)" if autonomy_min is not None else ""
                        parts.append(
                            f"⚠ RESTRICCIÓN INCUMPLIDA: autonomía calculada{auto_label} "
                            f"está por debajo de la restricción definida."
                        )
                    else:
                        parts.append(f"⚠ {_human_warning(w)}")

        suggestions = result.get("suggestions", [])
        if suggestions:
            if result.get("suggestion_context_note"):
                parts.append(result["suggestion_context_note"])
            parts.append("Sugerencias:")
            for suggestion in suggestions:
                label = SUGGESTION_LABELS.get(suggestion["type"], suggestion["type"])
                parts.append(f"- Podrías {label} ({suggestion['reason']})")

        next_step_hint = result.get("next_step_hint")
        if next_step_hint:
            parts.append("")
            parts.append(next_step_hint)

        # P4 Project Coherence: prefer Continuity footer over raw reasoning dump when present
        coherence = result.get("coherence_footer") or result.get("continuity")
        if not coherence:
            ctx = result.get("startup_context") or {}
            coherence = ctx.get("continuity")
        if coherence and (coherence.get("situation") or coherence.get("next_useful_step")):
            parts.append("")
            parts.append("─" * 44)
            if result.get("project_change_summary"):
                parts.append(f"Cambio: {result['project_change_summary']}")
            if coherence.get("situation"):
                parts.append(f"Estado: {coherence['situation']}")
            if coherence.get("next_useful_step"):
                parts.append(f"Siguiente paso: {coherence['next_useful_step']}")
                if coherence.get("next_useful_why"):
                    parts.append(f"   Por qué: {coherence['next_useful_why']}")
            return "\n".join(parts)

        reasoning = result.get("reasoning")
        if reasoning:
            if reasoning.get("explanation"):
                parts.append("Reasoning:")
                parts.append(reasoning["explanation"])
            insights = reasoning.get("insights") or []
            if insights:
                parts.append("Insights:")
                for insight in insights:
                    parts.append(f"- {insight}")
            tradeoffs = reasoning.get("tradeoffs") or []
            if tradeoffs:
                parts.append("Trade-offs:")
                for tradeoff in tradeoffs:
                    parts.append(f"- {tradeoff}")
            reasoning_actions = reasoning.get("suggested_actions") or []
            if reasoning_actions:
                critical = [a for a in reasoning_actions if a.get("is_critical") and not a.get("blocked")]
                secondary = [a for a in reasoning_actions if not a.get("is_critical") and not a.get("blocked")]
                blocked = [a for a in reasoning_actions if a.get("blocked")]
                if critical:
                    parts.append("PRIORIDAD CRÍTICA:")
                    for action in critical:
                        parts.append(f"→ {action['label']} ({action['reason']})")
                if secondary:
                    parts.append("Siguientes pasos:")
                    for action in secondary:
                        parts.append(f"- {action['label']} ({action['reason']})")
                if not critical and not secondary and blocked:
                    parts.append("No hay acciones recomendadas en el estado actual.")
                    parts.append("Revisa los parámetros base o ajusta los límites del diseño.")
                if blocked:
                    parts.append("Evitar:")
                    for action in blocked:
                        if action.get("block_reason"):
                            parts.append(f"✗ {action['label']} (bloqueado: {action['block_reason']})")
                        else:
                            parts.append(f"✗ {action['label']} ({action['reason']})")

        # Bug 51: if this response was an inline interruption of the iterate wizard,
        # remind the user the wizard is still active and what it is waiting for.
        reprompt = result.get("wizard_reprompt")
        if reprompt:
            parts.append(f"\n[Wizard activo] {reprompt}")

        return "\n".join(parts)

    return json.dumps(result, indent=2, ensure_ascii=False)


def run_demo() -> None:
    orchestrator = JarvisOrchestrator()
    llm_interface = JarvisLLMInterface(
        client=DemoLLMClient(
            [
                '{"action":"create_project","project_id":null,"parameters":{},"mode":null,"raw_user_input":null}',
                '{"action":"create_project","project_id":null,"parameters":{},"mode":"interactive","raw_user_input":"dron"}',
                '{"action":"create_project","project_id":null,"parameters":{},"mode":"interactive","raw_user_input":"levantar 2kg"}',
                '{"action":"create_project","project_id":null,"parameters":{},"mode":"interactive","raw_user_input":"2"}',
                '{"action":"create_project","project_id":null,"parameters":{},"mode":"interactive","raw_user_input":"sin restricciones críticas"}',
                '{"action":"create_project","project_id":null,"parameters":{},"mode":"interactive","raw_user_input":"conceptual"}',
                '{"action":"create_project","project_id":null,"parameters":{},"mode":"interactive","raw_user_input":"sí"}',
            ]
        )
    )
    transcript = [
        "quiero diseñar un dron",
        "dron",
        "levantar 2kg",
        "2",
        "sin restricciones críticas",
        "conceptual",
        "sí",
    ]
    for user_text in transcript:
        result = orchestrator.handle_user_text(user_text, llm_interface)
        print(json.dumps(result, indent=2, ensure_ascii=False))


def _list_existing_projects(orchestrator: JarvisOrchestrator) -> list[dict]:
    """Devuelve lista de proyectos existentes con id, slug y timestamp de modificación.

    Deduplica por ``project_id`` (keep newest mtime). If several rows share the
    same slug, the label includes a short id suffix so the CLI list is unambiguous.
    """
    state_paths = orchestrator.workspace_manager._list_state_paths()
    by_id: dict[str, dict] = {}
    for path in sorted(state_paths, key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            pid = str(data.get("project_id") or path.parent.name)
            if pid in by_id:
                continue  # newer first — skip older duplicates
            by_id[pid] = {
                "project_id": pid,
                "project_slug": data.get("project_slug", "?"),
                "objective": data.get("objective", ""),
                "workspace_path": str(path.parent),
            }
        except Exception:
            continue
    projects = list(by_id.values())
    slug_counts: dict[str, int] = {}
    for p in projects:
        slug_counts[p["project_slug"]] = slug_counts.get(p["project_slug"], 0) + 1
    for p in projects:
        if slug_counts.get(p["project_slug"], 0) > 1:
            short = p["project_id"][:8]
            p["display_slug"] = f"{p['project_slug']} ({short})"
        else:
            p["display_slug"] = p["project_slug"]
    return projects


def _print_welcome(projects: list[dict]) -> None:
    print("\nJarvis CLI")
    print("Escribe 'exit' o 'quit' para salir. Escribe 'help' para ejemplos.\n")
    if projects:
        print("Proyectos existentes:")
        for i, p in enumerate(projects, 1):
            label = p.get("display_slug") or p["project_slug"]
            if p["objective"]:
                label += f" — {p['objective']}"
            print(f"  {i}. {label}")
        print()
        print("Jarvis > ¿Qué quieres hacer?")
        print("  n  → crear nuevo proyecto")
        print("  1  → continuar con el proyecto más reciente")
        if len(projects) > 1:
            print(f"  2–{len(projects)} → continuar con otro proyecto de la lista")
    else:
        print("Jarvis > No hay proyectos todavía. Cuéntame qué quieres diseñar.")


def _handle_startup_selection(
    user_input: str,
    projects: list[dict],
) -> dict | None:
    """
    Gestiona la selección inicial.
    Retorna un resultado a mostrar si el input fue una selección de proyecto.
    Retorna None si el input debe procesarse normalmente como instrucción.
    """
    normalized = user_input.strip().lower()

    # Selección explícita de nuevo proyecto
    if normalized in {"n", "nuevo", "nuevo proyecto", "crear"}:
        return None  # caer al loop normal

    # Selección por texto: referencias a "el más reciente", "el primero", ordinal textual
    _TEXT_ORDINAL_MAP: dict[int, tuple[str, ...]] = {
        1: ("primero", "uno", "1ro", "first", "one", "reciente", "ultimo", "último",
            "mas reciente", "más reciente", "el ultimo", "el último", "el reciente",
            "el mas reciente", "el más reciente", "continuar", "el primero"),
        2: ("segundo", "dos", "second", "two", "el segundo"),
        3: ("tercero", "tres", "third", "three", "el tercero"),
        4: ("cuarto", "cuatro", "fourth", "four", "el cuarto"),
        5: ("quinto", "cinco", "fifth", "five", "el quinto"),
    }
    for rank, tokens in _TEXT_ORDINAL_MAP.items():
        if any(tok in normalized for tok in tokens):
            idx = rank - 1
            if 0 <= idx < len(projects):
                selected = projects[idx]
                state_path = Path(selected["workspace_path"]) / "state.json"
                state_path.touch()
                try:
                    data = json.loads(state_path.read_text(encoding="utf-8"))
                    iterations = data.get("active_iteration", 1)
                    objective = data.get("objective", "")
                    return {
                        "status": "ok",
                        "action": "load_project",
                        "project_id": data.get("project_id"),
                        "message": (
                            f"Proyecto cargado: {selected['project_slug']}\n"
                            f"Objetivo: {objective}\n"
                            f"Iteraciones: {iterations}\n"
                            "Puedes escribir 'itera', 'calcula', 'simula' o describir tu próximo cambio."
                        ),
                    }
                except Exception:
                    return {
                        "status": "error",
                        "message": f"No se pudo leer el proyecto {selected['project_slug']}.",
                    }
            break  # rank matched but index out of range → fall through to normal flow

    # Selección numérica de proyecto existente
    if normalized.isdigit():
        idx = int(normalized) - 1
        if 0 <= idx < len(projects):
            selected = projects[idx]
            state_path = Path(selected["workspace_path"]) / "state.json"
            # Touch: lo convierte en el proyecto más reciente para load_active_project
            state_path.touch()
            try:
                data = json.loads(state_path.read_text(encoding="utf-8"))
                iterations = data.get("active_iteration", 1)
                objective = data.get("objective", "")
                return {
                    "status": "ok",
                    "action": "load_project",
                    "project_id": data.get("project_id"),
                    "message": (
                        f"Proyecto cargado: {selected['project_slug']}\n"
                        f"Objetivo: {objective}\n"
                        f"Iteraciones: {iterations}\n"
                        "Puedes escribir 'itera', 'calcula', 'simula' o describir tu próximo cambio."
                    ),
                }
            except Exception:
                return {
                    "status": "error",
                    "message": f"No se pudo leer el proyecto {selected['project_slug']}.",
                }

    # Cualquier otra cosa → instrucción normal
    return None


def run_chat() -> None:
    orchestrator = JarvisOrchestrator()
    llm_interface = JarvisLLMInterface(client=OllamaClient())

    print(f"Modelo: {OLLAMA_MODEL}")
    print(f"Ollama: {OLLAMA_BASE_URL}")
    print(f"Logs LLM: {DEFAULT_LLM_LOG_ROOT}")

    existing_projects = _list_existing_projects(orchestrator)
    _print_welcome(existing_projects)

    startup_done = len(existing_projects) == 0  # si no hay proyectos, no hay selección inicial

    while True:
        try:
            user_input = " ".join(input("User > ").split())
        except (EOFError, KeyboardInterrupt):
            print("\nJarvis > Sesión cerrada.")
            break

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            print("Jarvis > Sesión cerrada.")
            break
        if user_input.lower() == "help":
            print("Jarvis > Prueba con frases como 'quiero diseñar un dron', 'reduce peso', 'calcula' o 'simula'.")
            continue

        # Gestionar selección inicial solo en el primer input cuando había proyectos
        if not startup_done:
            startup_done = True
            startup_result = _handle_startup_selection(user_input, existing_projects)
            if startup_result is not None:
                if startup_result.get("status") == "error":
                    print(f"Jarvis > {startup_result.get('message') or 'No he entendido la instrucción.'}")
                else:
                    orchestrator.state_manager.clear_conversation_history()
                    startup_ctx = orchestrator.build_startup_context()
                    if startup_ctx.get("has_project"):
                        print(f"Jarvis >\n{render_startup_context(startup_ctx)}\n")
                        # FN-001: only open define wizard when there are real pending params
                        if should_auto_start_define_on_load(startup_ctx):
                            missing = startup_ctx.get("missing_params") or []
                            reason = startup_ctx.get(
                                "param_definition_reason", DEFAULT_MISSING_FORCE_REASON
                            )
                            proactive = orchestrator.start_define_missing_params(
                                missing, reason=reason
                            )
                            print(f"Jarvis > {render_response(proactive)}")
                    else:
                        print(f"Jarvis > {render_response(startup_result)}")
                continue
            # Input not recognised as project selection (e.g. "n", "nuevo", free text)
            # → fall through to handle_user_text so the orchestrator processes it

        try:
            result = orchestrator.handle_user_text(user_input, llm_interface)
            result = orchestrator.attach_project_coherence(result)
        except Exception as error:
            print(f"Jarvis > Error interno: {error}")
            continue

        if result.get("status") == "error":
            print(f"Jarvis > {result.get('message') or 'No he entendido la instrucción.'}")
        else:
            print(f"Jarvis > {render_response(result)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Jarvis engineering assistant")
    parser.add_argument("--chat", action="store_true", help="Run minimal interactive CLI chat")
    args = parser.parse_args()

    if args.chat:
        run_chat()
        return

    run_demo()


if __name__ == "__main__":
    main()
