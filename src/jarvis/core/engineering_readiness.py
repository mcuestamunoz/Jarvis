"""ERF-1 — Engineering Readiness Aggregator.

Pure projection over ProjectState + existing authority helpers
(project_closure, system_architecture_catalog, latest_results["simulation"]).
No I/O, no LLM, no Decision/Conversation Engine.

Authority model (design_erf1_readiness_foundation.md §3): this module
COMPOSES outputs from existing authorities — it does not recompute BOM,
classification, or simulation logic differently, and it is never given
Continuity's own output as input (no circularity: Continuity -> Readiness is
forbidden; Readiness -> Continuity, one-way, is Slice 4's job).

Gap Registry (``gaps``) is the primary artifact (design ★2); the eight
subsystem lines and ``overall`` are derived rollups over it, never the other
way around.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from jarvis.core.project_closure import (
    build_component_bom,
    catalog_gap_covered_by_declared_thrust,
    classify_component,
    component_presence_tier,
    derive_physical_requirements,
)
from jarvis.core.system_architecture_catalog import (
    BLOCK_TO_COMPONENTS,
    get_block_type,
    get_domain_architecture,
    get_param_reason_for_block,
)
from jarvis.core.parameter_requirements import params_for_reason

# ── DTOs (contract §3) ──────────────────────────────────────────────────────


@dataclass
class GapEvidence:
    source: str
    fact: str


@dataclass
class RecommendedNextStep:
    action: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class Gap:
    gap_id: str
    gap_type: str
    instance_key: str | None
    title: str
    severity: Literal["HIGH", "MEDIUM", "LOW"]
    domain: str
    blocks: list[str]
    depends_on: list[str]
    evidence: list[GapEvidence]
    recommended_next_step: RecommendedNextStep
    resolved: bool = False


@dataclass
class SubsystemEvidence:
    defined: bool
    calculated: bool
    simulated: bool
    validated: bool
    catalog_bound: bool


@dataclass
class SubsystemReadiness:
    evidence: SubsystemEvidence
    verdict: Literal["PASS", "WARNING", "INCOMPLETE", "INCOMPATIBLE", "UNVERIFIABLE"]
    warning_type: str | None
    blocked_by_gap_ids: list[str]


@dataclass
class EngineeringReadinessResult:
    gaps: list[Gap]
    prioritized_gaps: list[Gap]
    top_gap: Gap | None
    subsystems: dict[str, SubsystemReadiness]
    overall: Literal["ASSEMBLY_READY", "NOT_ASSEMBLY_READY"]


# ── Canonical subsystem keys (§4.1 — exactly these eight) ──────────────────

SUBSYSTEM_KEYS: tuple[str, ...] = (
    "requirements",
    "architecture",
    "structure",
    "propulsion",
    "energy",
    "control",
    "catalog",
    "bom",
)

# ★1 / §5.3 — closed list. G9-B is the sole ERF-1 entry. Only "catalog" and
# "propulsion" subsystems are eligible for this demotion (bom is NOT, even
# though GAP-MOTOR-CATALOG-UNRESOLVED also lists "bom" in its own blocks[] —
# per the literal §5.3 table, which names only catalog/propulsion).
ACCEPTED_WARNING_TYPES: frozenset[str] = frozenset({"CATALOG-GAP-DEMOTED-POST-PASS"})
_G9B_ELIGIBLE_SUBSYSTEMS: frozenset[str] = frozenset({"catalog", "propulsion"})

# §4.2 — component key -> subsystem mapping for gap blocks[].
_COMPONENT_SUBSYSTEM_MAP: dict[str, str] = {
    "frame": "structure",
    "landing_gear": "structure",
    "motors": "propulsion",
    "propellers": "propulsion",
    "esc": "propulsion",
    "battery": "energy",
    "flight_controller": "control",
    "sensors": "control",
    "gps": "control",
}


def subsystem_for_component_key(component_key: str) -> str:
    """Return one of: structure | propulsion | energy | control | bom (fallback bom)."""
    return _COMPONENT_SUBSYSTEM_MAP.get(component_key, "bom")


def _dedupe_stable(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _gap_id(gap_type: str, instance_key: str | None) -> str:
    """§6.0 — stable id: bare type for singletons, ``type:instance_key`` for
    per-instance gaps. Extended beyond §6.0's own table (which only shows
    the two BOM types) to GAP-REQUIREMENTS-UNMET's three sub-triggers
    (mass/autonomy/blocking_params), which can co-occur and therefore need
    distinct stable ids of their own — a bare "GAP-REQUIREMENTS-UNMET" would
    collide if e.g. mass AND autonomy are both unmet simultaneously.
    """
    return f"{gap_type}:{instance_key}" if instance_key else gap_type


# ── §6.1 — shared helper: motor catalog surface ─────────────────────────────


def resolve_motor_catalog_surface(
    project_state: Any, physical_requirements: dict[str, Any]
) -> tuple[str | None, list[dict[str, Any]]]:
    """Returns (catalog_gap_message | None, catalog_matches). Pure.

    Ported byte-for-byte from ``orchestrator.build_startup_context``'s own
    catalog-gap computation (unchanged there) — same filters, same wording.
    """
    from jarvis.knowledge.library import default_library

    catalog_matches: list[dict[str, Any]] = []
    catalog_gap: str | None = None
    thrust_per = physical_requirements.get("thrust_per_motor_needed_n")
    kv_hint = None
    dp = getattr(project_state, "design_properties", None)
    motors_comp = (getattr(dp, "components", None) or {}).get("motors")
    if motors_comp is not None:
        kv_prop = (getattr(motors_comp, "properties", None) or {}).get("kv_rating")
        if kv_prop is not None:
            try:
                kv_hint = int(kv_prop.value)
            except (TypeError, ValueError):
                kv_hint = None
    prop_inch = None
    params_all = getattr(project_state, "current_parameters", None) or {}
    if params_all.get("propeller_diameter_in") is not None:
        try:
            prop_inch = float(params_all["propeller_diameter_in"])
        except (TypeError, ValueError):
            prop_inch = None

    if thrust_per is not None or kv_hint is not None:
        matches = default_library.find_motors_for_requirements(
            min_thrust_n=thrust_per,
            kv=kv_hint,
            prop_inch=prop_inch,
        )
        catalog_matches = [
            {
                "name": m.name,
                "thrust_n": m.thrust_n,
                "kv_rating": m.kv_rating,
                "weight_g": m.weight_g,
                "is_generic": m.is_generic,
            }
            for m in matches[:5]
        ]
        if not catalog_matches:
            parts = []
            if thrust_per is not None:
                parts.append(f"empuje ≥ {thrust_per:.1f} N/motor")
            if kv_hint is not None:
                parts.append(f"~{kv_hint}KV")
            if prop_inch is not None:
                parts.append(f"hélice ~{prop_inch:.0f}\"")
            need = ", ".join(parts) or "requisitos de motor"
            catalog_gap = (
                f"Necesitas {need}; no tengo un motor en el catálogo que cubra ese espacio."
            )

    return catalog_gap, catalog_matches


# ── §6.2 — shared helper: architecture progress ─────────────────────────────

_FALLBACK_BLOCK_LABELS: dict[str, str] = {
    "propulsion": "Propulsión",
    "energy": "Energía (batería)",
    "structure": "Estructura",
    "control": "Control",
    "actuation": "Actuación",
    "transmission": "Transmisión",
}


def _block_label_for(project_state: Any, block_key: str) -> str:
    """Simplified port of orchestrator._block_label_for — static labels only
    (no G20 dynamic in-progress refinement, which is a Continuity/CLI
    narration nicety, not a gap-evidence fact)."""
    params = getattr(project_state, "current_parameters", None) or {}
    vehicle_type = params.get("vehicle_type", "")
    arch = get_domain_architecture(vehicle_type) if vehicle_type else None
    if arch:
        label = arch.get("block_labels", {}).get(block_key)
        if label:
            return label
    return _FALLBACK_BLOCK_LABELS.get(block_key, block_key)


def _block_progress_status(block: str, design_properties: Any, params: dict[str, Any]) -> str:
    """Pure port of orchestrator._block_progress_status (unchanged logic) —
    self-contained here rather than imported from orchestrator.py to avoid a
    circular import (orchestrator imports engineering_readiness in Slice 5)
    and because orchestrator.py is not one of the "existing authorities"
    listed in the contract's allowed-imports table."""
    block_type = get_block_type(block)

    if block_type == "param":
        param_reason = get_param_reason_for_block(block)
        if not param_reason:
            return "not_started"
        required = params_for_reason(param_reason)
        if not required:
            return "not_started"
        defined = [p for p in required if params.get(p) is not None]
        if not defined:
            return "not_started"
        return "complete" if len(defined) == len(required) else "in_progress"

    if block_type == "composite":
        param_reason = get_param_reason_for_block(block)
        if param_reason:
            required = params_for_reason(param_reason)
            defined = [p for p in required if params.get(p) is not None] if required else []
            params_ok = bool(required) and len(defined) == len(required)
        else:
            params_ok = True

        component_keys = BLOCK_TO_COMPONENTS.get(block, [])
        components = design_properties.components
        non_low = [
            k for k in component_keys
            if k in components and component_presence_tier(components[k]) == "present"
        ]
        components_ok = bool(component_keys) and len(non_low) == len(component_keys)

        if not params_ok and not components_ok:
            return "not_started"
        if params_ok and components_ok:
            return "complete"
        return "in_progress"

    component_keys = BLOCK_TO_COMPONENTS.get(block, [])
    if not component_keys:
        return "not_started"
    components = design_properties.components
    non_low = [
        k for k in component_keys
        if k in components and component_presence_tier(components[k]) == "present"
    ]
    if not non_low:
        return "not_started"
    if len(non_low) == len(component_keys):
        return "complete"
    return "in_progress"


def derive_architecture_progress(project_state: Any) -> dict[str, Any]:
    """Returns {progress, next_block, next_label, next_block_status, is_complete}."""
    dp = getattr(project_state, "design_properties", None)
    priority = list(getattr(dp, "system_priority", None) or [])
    params = getattr(project_state, "current_parameters", None) or {}

    if not priority:
        return {
            "progress": "",
            "next_block": None,
            "next_label": None,
            "next_block_status": None,
            "is_complete": False,
        }

    completed = sum(1 for b in priority if _block_progress_status(b, dp, params) == "complete")
    progress = f"{completed}/{len(priority)}"

    next_block: str | None = None
    next_block_status: str | None = None
    for block in priority:
        status = _block_progress_status(block, dp, params)
        if status != "complete":
            next_block = block
            next_block_status = status
            break

    is_complete = next_block is None
    next_label = _block_label_for(project_state, next_block) if next_block else None
    return {
        "progress": progress,
        "next_block": next_block,
        "next_label": next_label,
        "next_block_status": next_block_status,
        "is_complete": is_complete,
    }


# ── §6 — gap catalog (six types) ────────────────────────────────────────────


def _motor_catalog_gaps(
    physical_requirements: dict[str, Any],
    catalog_gap: str | None,
) -> list[Gap]:
    """§6.3 GAP-MOTOR-CATALOG-UNRESOLVED."""
    if catalog_gap is None:
        return []
    evidence = [
        GapEvidence(
            source="engineering_readiness.resolve_motor_catalog_surface",
            fact="catalog_matches.empty",
        )
    ]
    thrust_per = physical_requirements.get("thrust_per_motor_needed_n")
    if thrust_per is not None:
        evidence.append(
            GapEvidence(
                source="project_closure.derive_physical_requirements",
                fact=f"thrust_per_motor_needed_n={thrust_per:.2f}",
            )
        )
        next_step = RecommendedNextStep(action="list_motors", params={})
    else:
        next_step = RecommendedNextStep(action="explore_design_space", params={})
    return [
        Gap(
            gap_id=_gap_id("GAP-MOTOR-CATALOG-UNRESOLVED", None),
            gap_type="GAP-MOTOR-CATALOG-UNRESOLVED",
            instance_key=None,
            title="Motor SKU unresolved",
            severity="MEDIUM",
            domain="catalog",
            blocks=["catalog", "propulsion", "bom"],
            depends_on=[],
            evidence=evidence,
            recommended_next_step=next_step,
        )
    ]


def _architecture_gaps(arch_progress: dict[str, Any]) -> list[Gap]:
    """§6.4 GAP-ARCH-BLOCK-INCOMPLETE."""
    if arch_progress["is_complete"]:
        return []
    next_block = arch_progress["next_block"]
    if next_block is None:
        evidence = [
            GapEvidence(
                source="engineering_readiness.derive_architecture_progress",
                fact="system_priority.empty",
            )
        ]
    else:
        evidence = [
            GapEvidence(
                source="engineering_readiness.derive_architecture_progress",
                fact=f"next_block={next_block}",
            ),
            GapEvidence(
                source="engineering_readiness.derive_architecture_progress",
                fact=f"next_label={arch_progress['next_label']}",
            ),
        ]
    return [
        Gap(
            gap_id=_gap_id("GAP-ARCH-BLOCK-INCOMPLETE", None),
            gap_type="GAP-ARCH-BLOCK-INCOMPLETE",
            instance_key=None,
            title="Architecture block incomplete",
            severity="MEDIUM",
            domain="architecture",
            blocks=["architecture"],
            depends_on=[],
            evidence=evidence,
            recommended_next_step=RecommendedNextStep(
                action="continue_architecture_block", params={"block": next_block}
            ),
        )
    ]


def _bom_missing_gaps(bom: dict[str, Any]) -> list[Gap]:
    """§6.5 GAP-BOM-MISSING-COMPONENT — one instance per missing key."""
    gaps: list[Gap] = []
    for key in bom.get("missing") or []:
        subsystem = subsystem_for_component_key(key)
        gaps.append(
            Gap(
                gap_id=_gap_id("GAP-BOM-MISSING-COMPONENT", key),
                gap_type="GAP-BOM-MISSING-COMPONENT",
                instance_key=key,
                title=f"{key} not defined",
                severity="HIGH",
                domain=subsystem,
                blocks=_dedupe_stable([subsystem, "bom"]),
                depends_on=[],
                evidence=[
                    GapEvidence(
                        source="project_closure.build_component_bom", fact=f"missing.{key}"
                    )
                ],
                recommended_next_step=RecommendedNextStep(
                    action="define_component", params={"component_key": key}
                ),
            )
        )
    return gaps


def _bom_incomplete_gaps(bom: dict[str, Any]) -> list[Gap]:
    """§6.6 GAP-BOM-INCOMPLETE-COMPONENT — one instance per incomplete entry."""
    gaps: list[Gap] = []
    for entry in bom.get("incomplete") or []:
        key = entry["key"]
        subsystem = subsystem_for_component_key(key)
        missing_fields = list(entry.get("missing_fields") or [])
        evidence = [
            GapEvidence(
                source="project_closure.build_component_bom",
                fact=f"incomplete.{key}.missing_fields={mf}",
            )
            for mf in missing_fields
        ] or [
            GapEvidence(source="project_closure.build_component_bom", fact=f"incomplete.{key}")
        ]
        gaps.append(
            Gap(
                gap_id=_gap_id("GAP-BOM-INCOMPLETE-COMPONENT", key),
                gap_type="GAP-BOM-INCOMPLETE-COMPONENT",
                instance_key=key,
                title=f"{key} incomplete",
                severity="MEDIUM",
                domain=subsystem,
                blocks=_dedupe_stable([subsystem, "bom"]),
                depends_on=[],
                evidence=evidence,
                recommended_next_step=RecommendedNextStep(
                    action="complete_component",
                    params={"component_key": key, "missing_fields": missing_fields},
                ),
            )
        )
    return gaps


def _is_status_blocking(sim: dict[str, Any]) -> bool:
    """Same signal orchestrator.build_startup_context uses for status_type ==
    "blocking" (signals["missing_physics_parameters"])."""
    return sim.get("physics_status") == "missing_parameters"


def _sim_not_pass_gaps(sim: dict[str, Any]) -> tuple[list[Gap], bool]:
    """§6.7 GAP-SIM-NOT-PASS. Returns (gaps, triggered) — ``triggered`` lets
    GAP-REQUIREMENTS-UNMET's trigger (c) know to suppress itself when this
    gap already covers the same "blocking, no sim" root cause."""
    sim_status = (sim.get("status") or "").lower()
    blocking = _is_status_blocking(sim)

    if sim_status in ("pass", "ok"):
        return [], False
    triggered = bool(sim_status) or blocking
    if not triggered:
        return [], False

    evidence = [GapEvidence(source="latest_results.simulation", fact=f"status={sim_status or 'none'}")]
    warnings = sim.get("warnings") or []
    if warnings:
        evidence.append(
            GapEvidence(source="latest_results.simulation", fact=f"warnings[0]={warnings[0]}")
        )
    gap = Gap(
        gap_id=_gap_id("GAP-SIM-NOT-PASS", None),
        gap_type="GAP-SIM-NOT-PASS",
        instance_key=None,
        title="Simulation not PASS",
        severity="HIGH",
        domain="requirements",
        blocks=["requirements", "propulsion", "energy"],
        depends_on=[],
        evidence=evidence,
        recommended_next_step=RecommendedNextStep(
            action="fix_simulation_blocker", params={"sim_status": sim_status}
        ),
    )
    return [gap], True


def _requirements_unmet_gaps(
    physical_requirements: dict[str, Any],
    sim: dict[str, Any],
    sim_not_pass_triggered: bool,
) -> list[Gap]:
    """§6.8 GAP-REQUIREMENTS-UNMET — (a) mass, (b) autonomy, (c) blocking params."""
    gaps: list[Gap] = []

    max_mass = physical_requirements.get("max_mass_kg")
    current_mass = physical_requirements.get("current_mass_kg")
    if max_mass is not None and current_mass is not None and current_mass > max_mass:
        gaps.append(
            Gap(
                gap_id=_gap_id("GAP-REQUIREMENTS-UNMET", "mass"),
                gap_type="GAP-REQUIREMENTS-UNMET",
                instance_key="mass",
                title="Mass limit exceeded",
                severity="HIGH",
                domain="requirements",
                blocks=["requirements"],
                depends_on=[],
                evidence=[
                    GapEvidence(
                        source="project_closure.derive_physical_requirements",
                        fact=f"current_mass_kg={current_mass:.2f}",
                    ),
                    GapEvidence(
                        source="project_closure.derive_physical_requirements",
                        fact=f"max_mass_kg={max_mass:.2f}",
                    ),
                ],
                recommended_next_step=RecommendedNextStep(
                    action="resolve_requirement", params={"kind": "mass"}
                ),
            )
        )

    autonomy_target = physical_requirements.get("autonomy_target_min")
    current_autonomy = physical_requirements.get("current_autonomy_min")
    if (
        autonomy_target is not None
        and current_autonomy is not None
        and current_autonomy < autonomy_target
    ):
        gaps.append(
            Gap(
                gap_id=_gap_id("GAP-REQUIREMENTS-UNMET", "autonomy"),
                gap_type="GAP-REQUIREMENTS-UNMET",
                instance_key="autonomy",
                title="Autonomy target not met",
                severity="HIGH",
                domain="requirements",
                blocks=["requirements"],
                depends_on=[],
                evidence=[
                    GapEvidence(
                        source="project_closure.derive_physical_requirements",
                        fact=f"current_autonomy_min={current_autonomy:.2f}",
                    ),
                    GapEvidence(
                        source="project_closure.derive_physical_requirements",
                        fact=f"autonomy_target_min={autonomy_target:.2f}",
                    ),
                ],
                recommended_next_step=RecommendedNextStep(
                    action="resolve_requirement", params={"kind": "autonomy"}
                ),
            )
        )

    if _is_status_blocking(sim) and not sim_not_pass_triggered:
        gaps.append(
            Gap(
                gap_id=_gap_id("GAP-REQUIREMENTS-UNMET", "blocking_params"),
                gap_type="GAP-REQUIREMENTS-UNMET",
                instance_key="blocking_params",
                title="Parameters blocking simulation",
                severity="MEDIUM",
                domain="requirements",
                blocks=["requirements"],
                depends_on=[],
                evidence=[
                    GapEvidence(
                        source="latest_results.simulation",
                        fact="physics_status=missing_parameters",
                    )
                ],
                recommended_next_step=RecommendedNextStep(
                    action="resolve_requirement", params={"kind": "blocking_params"}
                ),
            )
        )

    return gaps


# ── §6.10 — prioritization ───────────────────────────────────────────────────

_SEVERITY_ORDER: dict[str, int] = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def prioritize_gaps(gaps: list[Gap]) -> list[Gap]:
    """★5 — unlockable only (all depends_on resolved), sorted:
    severity HIGH>MEDIUM>LOW, greater downstream-unblock impact first,
    tiebreak gap_id lexicographic."""
    resolved_ids = {g.gap_id for g in gaps if g.resolved}
    unlockable = [g for g in gaps if all(dep in resolved_ids for dep in g.depends_on)]

    def sort_key(g: Gap) -> tuple[int, int, str]:
        return (_SEVERITY_ORDER[g.severity], -len(set(g.blocks)), g.gap_id)

    return sorted(unlockable, key=sort_key)


# ── §4.3 — evidence flag predicates ─────────────────────────────────────────


def _component(project_state: Any, key: str) -> Any:
    dp = getattr(project_state, "design_properties", None)
    return (getattr(dp, "components", None) or {}).get(key)


def _component_present(project_state: Any, key: str) -> bool:
    return component_presence_tier(_component(project_state, key)) == "present"


def _catalog_ref_set(project_state: Any, key: str) -> bool:
    spec = _component(project_state, key)
    return spec is not None and bool(getattr(spec, "catalog_ref", None))


@dataclass
class _Context:
    project_state: Any
    req: dict[str, Any]
    bom: dict[str, Any]
    sim: dict[str, Any]
    sim_status: str
    calc: dict[str, Any]
    params: dict[str, Any]
    arch_progress: dict[str, Any]
    catalog_gap: str | None
    catalog_matches: list[dict[str, Any]]


def _requirements_evidence(ctx: _Context) -> SubsystemEvidence:
    constraints = getattr(ctx.project_state, "parsed_constraints", None) or {}
    defined = bool(constraints)
    calculated = any(
        ctx.req.get(k) is not None
        for k in ("thrust_needed_n", "current_mass_kg", "current_autonomy_min")
    )
    simulated = bool(ctx.sim)
    validated = ctx.sim_status == "pass"
    return SubsystemEvidence(defined, calculated, simulated, validated, False)


def _architecture_evidence(ctx: _Context) -> SubsystemEvidence:
    dp = getattr(ctx.project_state, "design_properties", None)
    defined = bool(getattr(dp, "system_blocks", None))
    calculated = defined  # same as defined for ERF-1 (design table, v1 simplification)
    simulated = bool(ctx.sim)
    validated = ctx.arch_progress["is_complete"] and ctx.sim_status == "pass"
    return SubsystemEvidence(defined, calculated, simulated, validated, False)


def _structure_evidence(ctx: _Context) -> SubsystemEvidence:
    frame = _component(ctx.project_state, "frame")
    defined = classify_component("frame", frame, ctx.project_state) != "missing"
    calculated = ctx.calc.get("total_mass_kg") is not None
    simulated = bool(ctx.sim)
    validated = ctx.sim_status == "pass" and _component_present(ctx.project_state, "frame")
    catalog_bound = _catalog_ref_set(ctx.project_state, "frame")
    return SubsystemEvidence(defined, calculated, simulated, validated, catalog_bound)


def _propulsion_evidence(ctx: _Context) -> SubsystemEvidence:
    defined = _component_present(ctx.project_state, "motors")
    calculated = (
        ctx.req.get("thrust_needed_n") is not None
        or ctx.req.get("thrust_per_motor_needed_n") is not None
    )
    simulated = bool(ctx.sim)
    validated = ctx.sim_status == "pass"
    catalog_bound = _catalog_ref_set(ctx.project_state, "motors")
    return SubsystemEvidence(defined, calculated, simulated, validated, catalog_bound)


def _energy_evidence(ctx: _Context) -> SubsystemEvidence:
    defined = _component_present(ctx.project_state, "battery")
    calculated = (
        ctx.params.get("battery_capacity_wh") is not None
        or ctx.calc.get("autonomy_min") is not None
    )
    simulated = bool(ctx.sim)
    validated = ctx.sim_status == "pass"
    catalog_bound = _catalog_ref_set(ctx.project_state, "battery")
    return SubsystemEvidence(defined, calculated, simulated, validated, catalog_bound)


def _control_evidence(ctx: _Context) -> SubsystemEvidence:
    defined = _component_present(ctx.project_state, "flight_controller")
    calculated = defined  # "FC not stub" — same predicate as defined, per design table
    simulated = bool(ctx.sim)
    validated = ctx.sim_status == "pass"
    catalog_bound = _catalog_ref_set(ctx.project_state, "flight_controller")
    return SubsystemEvidence(defined, calculated, simulated, validated, catalog_bound)


def _catalog_evidence(ctx: _Context) -> SubsystemEvidence:
    query_attempted = ctx.catalog_gap is not None or bool(ctx.catalog_matches)
    simulated = bool(ctx.sim)
    validated = ctx.sim_status == "pass"
    catalog_bound = ctx.catalog_gap is None or catalog_gap_covered_by_declared_thrust(
        ctx.project_state, ctx.sim_status, ctx.req
    )
    return SubsystemEvidence(query_attempted, query_attempted, simulated, validated, catalog_bound)


def _bom_evidence(ctx: _Context) -> SubsystemEvidence:
    defined = bool(ctx.bom.get("defined")) or bool(ctx.bom.get("declarative"))
    calculated = True  # BOM was built to compute ctx.bom itself
    simulated = bool(ctx.sim)
    validated = ctx.sim_status == "pass"
    defined_entries = ctx.bom.get("defined") or []
    catalog_bound = all(
        _catalog_ref_set(ctx.project_state, e["key"]) for e in defined_entries
    )
    return SubsystemEvidence(defined, calculated, simulated, validated, catalog_bound)


_EVIDENCE_BUILDERS = {
    "requirements": _requirements_evidence,
    "architecture": _architecture_evidence,
    "structure": _structure_evidence,
    "propulsion": _propulsion_evidence,
    "energy": _energy_evidence,
    "control": _control_evidence,
    "catalog": _catalog_evidence,
    "bom": _bom_evidence,
}


def _accepted_warning_type_for_subsystem(subsystem_key: str, ctx: _Context) -> str | None:
    if subsystem_key not in _G9B_ELIGIBLE_SUBSYSTEMS:
        return None
    if ctx.catalog_gap is None:
        return None
    if catalog_gap_covered_by_declared_thrust(ctx.project_state, ctx.sim_status, ctx.req):
        return "CATALOG-GAP-DEMOTED-POST-PASS"
    return None


def _derive_subsystem_verdict(
    subsystem_key: str,
    evidence: SubsystemEvidence,
    prioritized_gaps: list[Gap],
    ctx: _Context,
) -> SubsystemReadiness:
    """§4.4 — verdict derivation. The accepted-warning path (★1/§5.3) takes
    priority over the generic "any blocking gap -> INCOMPLETE" rule exactly
    when every non-HIGH blocking gap for this subsystem is the demoted motor
    catalog gap — otherwise step 5 (WARNING) would be unreachable, since a
    genuine gap always blocks the subsystem it names in blocks[]."""
    blocking = sorted(
        (g for g in prioritized_gaps if subsystem_key in g.blocks),
        key=lambda g: g.gap_id,
    )
    blocked_by_gap_ids = [g.gap_id for g in blocking]
    high = [g for g in blocking if g.severity == "HIGH"]
    non_high = [g for g in blocking if g.severity != "HIGH"]
    accepted_type = _accepted_warning_type_for_subsystem(subsystem_key, ctx)

    if high:
        return SubsystemReadiness(evidence, "INCOMPLETE", None, blocked_by_gap_ids)

    if non_high:
        if accepted_type is not None and all(
            g.gap_type == "GAP-MOTOR-CATALOG-UNRESOLVED" for g in non_high
        ):
            return SubsystemReadiness(evidence, "WARNING", accepted_type, blocked_by_gap_ids)
        return SubsystemReadiness(evidence, "INCOMPLETE", None, blocked_by_gap_ids)

    if not evidence.defined:
        return SubsystemReadiness(evidence, "INCOMPLETE", None, blocked_by_gap_ids)

    if evidence.defined and evidence.calculated and evidence.simulated and evidence.validated:
        return SubsystemReadiness(evidence, "PASS", None, blocked_by_gap_ids)

    return SubsystemReadiness(evidence, "UNVERIFIABLE", None, blocked_by_gap_ids)


def _derive_overall(
    gaps: list[Gap], subsystems: dict[str, SubsystemReadiness]
) -> Literal["ASSEMBLY_READY", "NOT_ASSEMBLY_READY"]:
    """§4.5 rollup."""
    if any(g.severity == "HIGH" for g in gaps):
        return "NOT_ASSEMBLY_READY"
    for readiness in subsystems.values():
        if readiness.verdict == "PASS":
            continue
        if readiness.verdict == "WARNING" and readiness.warning_type in ACCEPTED_WARNING_TYPES:
            continue
        return "NOT_ASSEMBLY_READY"
    return "ASSEMBLY_READY"


# ── §3 — public entry point ──────────────────────────────────────────────────


def build_engineering_readiness(project_state: Any) -> EngineeringReadinessResult:
    """Pure projection over ProjectState + existing authority helpers. No I/O.

    Never accepts Continuity output as input (design ★7) — inputs are only
    ``project_state`` and deterministic authority calls made from within.
    """
    req = derive_physical_requirements(project_state)
    bom = build_component_bom(project_state)
    latest = getattr(project_state, "latest_results", None) or {}
    sim = latest.get("simulation") or {}
    calc = latest.get("calculations") or {}
    sim_status = (sim.get("status") or "").lower()
    params = getattr(project_state, "current_parameters", None) or {}
    catalog_gap, catalog_matches = resolve_motor_catalog_surface(project_state, req)
    arch_progress = derive_architecture_progress(project_state)

    gaps: list[Gap] = []
    gaps += _motor_catalog_gaps(req, catalog_gap)
    gaps += _architecture_gaps(arch_progress)
    gaps += _bom_missing_gaps(bom)
    gaps += _bom_incomplete_gaps(bom)
    sim_not_pass_gaps, sim_not_pass_triggered = _sim_not_pass_gaps(sim)
    gaps += sim_not_pass_gaps
    gaps += _requirements_unmet_gaps(req, sim, sim_not_pass_triggered)

    prioritized = prioritize_gaps(gaps)
    top_gap = prioritized[0] if prioritized else None

    ctx = _Context(
        project_state=project_state,
        req=req,
        bom=bom,
        sim=sim,
        sim_status=sim_status,
        calc=calc,
        params=params,
        arch_progress=arch_progress,
        catalog_gap=catalog_gap,
        catalog_matches=catalog_matches,
    )

    subsystems: dict[str, SubsystemReadiness] = {}
    for key in SUBSYSTEM_KEYS:
        evidence = _EVIDENCE_BUILDERS[key](ctx)
        subsystems[key] = _derive_subsystem_verdict(key, evidence, prioritized, ctx)

    overall = _derive_overall(gaps, subsystems)

    return EngineeringReadinessResult(
        gaps=gaps,
        prioritized_gaps=prioritized,
        top_gap=top_gap,
        subsystems=subsystems,
        overall=overall,
    )
