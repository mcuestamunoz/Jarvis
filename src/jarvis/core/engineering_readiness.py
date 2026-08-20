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

from jarvis.core.electrical_compatibility import (
    CompatibilityResult,
    evaluate_electrical_compatibility,
)
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
    # G9-A hygiene: motor catalog surface exposed so orchestrator/Continuity
    # consume readiness output instead of calling resolve_motor_catalog_surface again.
    motor_catalog_gap: str | None = None
    motor_catalog_matches: list[dict[str, Any]] = field(default_factory=list)
    motor_catalog_gap_fact: str | None = None


# ── Canonical subsystem keys (ERF-2 §4.2 — exactly these nine) ─────────────

SUBSYSTEM_KEYS: tuple[str, ...] = (
    "requirements",
    "architecture",
    "structure",
    "propulsion",
    "energy",
    "electronics",  # ERF-2 ★8 — new
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

# ERF-2 §8.2 — gap types whose blocking effect is INCOMPATIBLE (deterministic
# evidence of a real conflict), never merely INCOMPLETE. Checked before the
# generic HIGH/MEDIUM severity path in _derive_subsystem_verdict — otherwise
# their HIGH severity would just read as INCOMPLETE like any other gap.
_INCOMPATIBLE_CLASS_GAP_TYPES: frozenset[str] = frozenset({
    "GAP-ESC-UNDERSIZED",
    "GAP-BATTERY-DISCHARGE-EXCEEDED",
    "GAP-PROP-MOTOR-MISMATCH",
})

# ERF-2 design §6 — verdict impact can be narrower than blocks[] (e.g.
# GAP-ESC-UNDERSIZED blocks energy for dependency graph but only electronics
# + propulsion show INCOMPATIBLE on the subsystem line).
_INCOMPATIBLE_VERDICT_SUBSYSTEMS: dict[str, frozenset[str]] = {
    "GAP-ESC-UNDERSIZED": frozenset({"electronics", "propulsion"}),
    "GAP-BATTERY-DISCHARGE-EXCEEDED": frozenset({"energy", "propulsion"}),
    "GAP-PROP-MOTOR-MISMATCH": frozenset({"propulsion", "catalog"}),
}

# §4.2 — component key -> subsystem mapping for gap blocks[].
_COMPONENT_SUBSYSTEM_MAP: dict[str, str] = {
    "frame": "structure",
    "landing_gear": "structure",
    "motors": "propulsion",
    "propellers": "propulsion",
    "esc": "electronics",  # ERF-2 §3.2 — was "propulsion" in ERF-1
    "battery": "energy",
    "flight_controller": "control",
    "sensors": "control",
    "gps": "control",
}


def subsystem_for_component_key(component_key: str) -> str:
    """Return one of: structure | propulsion | energy | electronics | control | bom (fallback bom)."""
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


def _motor_catalog_matches_dicts(matches: list[Any]) -> list[dict[str, Any]]:
    return [
        {
            "name": m.name,
            "thrust_n": m.thrust_n,
            "kv_rating": m.kv_rating,
            "weight_g": m.weight_g,
            "is_generic": m.is_generic,
        }
        for m in matches[:5]
    ]


def resolve_motor_catalog_surface(
    project_state: Any, physical_requirements: dict[str, Any]
) -> tuple[str | None, list[dict[str, Any]], str | None]:
    """Returns (catalog_gap_message | None, catalog_matches, gap_evidence_fact | None). Pure.

    G9-A: catalog_ref-aware. A bound motor SKU (Impl B) is authoritative for
    catalog honesty:
      - Scenario B — bound SKU still covers current requirements: no gap, even
        when a fresh generic search would come back empty (the identity
        decision already made stands).
      - Scenario C — bound SKU no longer covers requirements (drift): gap
        names the stale SKU instead of implying nothing was ever bound;
        alternatives (if any) are still searched against current requirements.
      - Scenario D — bound SKU no longer resolves in the library: honest
        "no longer in the catalog" message, never a raw KeyError.
      - Unbound (no ``catalog_ref``): original ERF-1 behavior (Scenario A/F),
        byte-identical to the pre-G9-A generic search.
    """
    from jarvis.knowledge.library import _motor_covers_requirements, default_library

    catalog_matches: list[dict[str, Any]] = []
    catalog_gap: str | None = None
    gap_evidence_fact: str | None = None
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

    def _need_label() -> str:
        parts = []
        if thrust_per is not None:
            parts.append(f"empuje ≥ {thrust_per:.1f} N/motor")
        if kv_hint is not None:
            parts.append(f"~{kv_hint}KV")
        if prop_inch is not None:
            parts.append(f"hélice ~{prop_inch:.0f}\"")
        return ", ".join(parts) or "requisitos de motor"

    catalog_ref = getattr(motors_comp, "catalog_ref", None) if motors_comp is not None else None
    if catalog_ref is not None and catalog_ref.family == "motor":
        sku = catalog_ref.sku
        if not default_library.has_motor(sku):
            catalog_gap = f"El motor vinculado ({sku}) ya no está en el catálogo."
            gap_evidence_fact = f"bound_sku_missing:{sku}"
            return catalog_gap, catalog_matches, gap_evidence_fact

        bound = default_library.get_motor(sku)
        if _motor_covers_requirements(
            bound, min_thrust_n=thrust_per, kv=kv_hint, prop_inch=prop_inch
        ):
            # Report the bound SKU itself as the (only) match — not an empty
            # list. `_catalog_evidence`'s `query_attempted` flag (and thus the
            # catalog subsystem's PASS verdict) reads `bool(catalog_matches)`;
            # an empty list here would read as "nothing known," understating
            # a bound-and-sufficient identity as INCOMPLETE instead of PASS.
            return None, _motor_catalog_matches_dicts([bound]), None

        matches = default_library.find_motors_for_requirements(
            min_thrust_n=thrust_per, kv=kv_hint, prop_inch=prop_inch,
        )
        catalog_matches = _motor_catalog_matches_dicts(matches)
        need = _need_label()
        if catalog_matches:
            catalog_gap = f"El motor vinculado ({sku}) ya no cubre el hueco de diseño ({need})."
        else:
            catalog_gap = (
                f"El motor vinculado ({sku}) ya no cubre el hueco de diseño ({need}); "
                "no tengo otro motor en el catálogo que cubra ese espacio."
            )
        gap_evidence_fact = f"bound_sku_underspec:{sku}"
        return catalog_gap, catalog_matches, gap_evidence_fact

    if thrust_per is not None or kv_hint is not None:
        matches = default_library.find_motors_for_requirements(
            min_thrust_n=thrust_per,
            kv=kv_hint,
            prop_inch=prop_inch,
        )
        catalog_matches = _motor_catalog_matches_dicts(matches)
        if not catalog_matches:
            need = _need_label()
            catalog_gap = (
                f"Necesitas {need}; no tengo un motor en el catálogo que cubra ese espacio."
            )
            gap_evidence_fact = "catalog_matches.empty"

    return catalog_gap, catalog_matches, gap_evidence_fact


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
    *,
    gap_evidence_fact: str = "catalog_matches.empty",
) -> list[Gap]:
    """§6.3 GAP-MOTOR-CATALOG-UNRESOLVED.

    G9-A: ``gap_evidence_fact`` distinguishes *why* the gap fired — a plain
    empty search (``catalog_matches.empty``) vs. a bound SKU that no longer
    covers requirements (``bound_sku_underspec:{sku}``) vs. a bound SKU that
    vanished from the library (``bound_sku_missing:{sku}``) — without adding
    a new gap type (the message text carries the same distinction for humans;
    this carries it for evidence inspection).
    """
    if catalog_gap is None:
        return []
    evidence = [
        GapEvidence(
            source="engineering_readiness.resolve_motor_catalog_surface",
            fact=gap_evidence_fact,
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


# ── ERF-2 §7 — four gap types from CompatibilityResult ──────────────────────


def _esc_undefined_gap(compatibility: CompatibilityResult) -> list[Gap]:
    """§7.1 GAP-ESC-UNDEFINED. Mutually exclusive with GAP-ESC-UNDERSIZED —
    electrical_compatibility._esc_vs_motor already forces "unverifiable"
    whenever esc_presence != "defined", so both gaps can never fire together."""
    if compatibility.esc_presence != "missing":
        return []
    return [
        Gap(
            gap_id=_gap_id("GAP-ESC-UNDEFINED", None),
            gap_type="GAP-ESC-UNDEFINED",
            instance_key=None,
            title="ESC not defined",
            severity="HIGH",
            domain="electronics",
            blocks=["electronics", "propulsion", "bom"],
            depends_on=[],
            evidence=[
                GapEvidence(source="electrical_compatibility.evaluate", fact="esc_presence.missing")
            ],
            recommended_next_step=RecommendedNextStep(
                action="define_component", params={"component_key": "esc"}
            ),
        )
    ]


def _esc_undersized_gap(compatibility: CompatibilityResult) -> list[Gap]:
    """§7.2 GAP-ESC-UNDERSIZED (★3, ★4 — per-motor predicate, not x motor_count)."""
    if compatibility.esc_vs_motor != "undersized":
        return []
    return [
        Gap(
            gap_id=_gap_id("GAP-ESC-UNDERSIZED", None),
            gap_type="GAP-ESC-UNDERSIZED",
            instance_key=None,
            title="ESC current rating below per-motor demand",
            severity="HIGH",
            domain="electronics",
            blocks=["electronics", "propulsion", "energy"],
            depends_on=[],
            evidence=[
                GapEvidence(
                    source="electrical_compatibility.evaluate",
                    fact=f"esc_current_a={compatibility.esc_current_a}",
                ),
                GapEvidence(
                    source="electrical_compatibility.evaluate",
                    fact=f"i_motor_a={compatibility.i_motor_a}",
                ),
            ],
            recommended_next_step=RecommendedNextStep(action="revise_esc_rating", params={}),
        )
    ]


def _battery_discharge_exceeded_gap(compatibility: CompatibilityResult) -> list[Gap]:
    """§7.3 GAP-BATTERY-DISCHARGE-EXCEEDED."""
    if compatibility.battery_discharge != "exceeded":
        return []
    return [
        Gap(
            gap_id=_gap_id("GAP-BATTERY-DISCHARGE-EXCEEDED", None),
            gap_type="GAP-BATTERY-DISCHARGE-EXCEEDED",
            instance_key=None,
            title="Battery discharge limit exceeded",
            severity="HIGH",
            domain="energy",
            blocks=["energy", "propulsion"],
            depends_on=[],
            evidence=[
                GapEvidence(
                    source="electrical_compatibility.evaluate",
                    fact=f"i_total_a={compatibility.i_total_a}",
                ),
                GapEvidence(
                    source="electrical_compatibility.evaluate",
                    fact=f"battery_limit_a={compatibility.battery_limit_a}",
                ),
            ],
            recommended_next_step=RecommendedNextStep(action="revise_battery_or_load", params={}),
        )
    ]


def _prop_motor_mismatch_gap(compatibility: CompatibilityResult) -> list[Gap]:
    """§7.4 GAP-PROP-MOTOR-MISMATCH (★10 — exposes library.match_motor_propeller,
    no duplicate rule)."""
    if compatibility.prop_motor != "mismatch":
        return []
    return [
        Gap(
            gap_id=_gap_id("GAP-PROP-MOTOR-MISMATCH", None),
            gap_type="GAP-PROP-MOTOR-MISMATCH",
            instance_key=None,
            title="Motor and propeller catalog pairing incompatible",
            severity="HIGH",
            domain="propulsion",
            blocks=["propulsion", "catalog"],
            depends_on=[],
            evidence=[
                GapEvidence(source="library.match_motor_propeller", fact="match_false")
            ],
            recommended_next_step=RecommendedNextStep(
                action="revise_propeller_or_motor", params={}
            ),
        )
    ]


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


def _electronics_evidence(ctx: _Context) -> SubsystemEvidence:
    """ERF-2 §8.1 — NEW subsystem."""
    defined = _component_present(ctx.project_state, "esc")
    calculated = defined  # same as defined for ERF-2 MVP, per design table
    simulated = bool(ctx.sim)
    validated = ctx.sim_status == "pass"
    catalog_bound = _catalog_ref_set(ctx.project_state, "esc")  # likely False in MVP — honest, no ESC catalog (★7)
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
    "electronics": _electronics_evidence,
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
    genuine gap always blocks the subsystem it names in blocks[].

    ERF-2 §8.2: INCOMPATIBLE-class gaps (deterministic evidence of a real
    conflict — ★3) are checked FIRST, before the generic HIGH/MEDIUM path —
    they are all severity=HIGH like ordinary gaps, but must read as
    INCOMPATIBLE, not INCOMPLETE. Verdict impact uses
    ``_INCOMPATIBLE_VERDICT_SUBSYSTEMS`` when narrower than ``blocks[]``.
    """
    blocking = sorted(
        (g for g in prioritized_gaps if subsystem_key in g.blocks),
        key=lambda g: g.gap_id,
    )
    blocked_by_gap_ids = [g.gap_id for g in blocking]

    incompatible = [
        g
        for g in blocking
        if g.gap_type in _INCOMPATIBLE_CLASS_GAP_TYPES
        and subsystem_key
        in _INCOMPATIBLE_VERDICT_SUBSYSTEMS.get(g.gap_type, frozenset(g.blocks))
    ]
    if incompatible:
        return SubsystemReadiness(evidence, "INCOMPATIBLE", None, blocked_by_gap_ids)

    remaining = [g for g in blocking if g.gap_type not in _INCOMPATIBLE_CLASS_GAP_TYPES]
    high = [g for g in remaining if g.severity == "HIGH"]
    non_high = [g for g in remaining if g.severity != "HIGH"]
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
    catalog_gap, catalog_matches, catalog_gap_fact = resolve_motor_catalog_surface(
        project_state, req
    )
    arch_progress = derive_architecture_progress(project_state)
    compatibility = evaluate_electrical_compatibility(project_state)

    gaps: list[Gap] = []
    gaps += _motor_catalog_gaps(
        req, catalog_gap, gap_evidence_fact=catalog_gap_fact or "catalog_matches.empty"
    )
    gaps += _architecture_gaps(arch_progress)
    gaps += _bom_missing_gaps(bom)
    gaps += _bom_incomplete_gaps(bom)
    sim_not_pass_gaps, sim_not_pass_triggered = _sim_not_pass_gaps(sim)
    gaps += sim_not_pass_gaps
    gaps += _requirements_unmet_gaps(req, sim, sim_not_pass_triggered)
    gaps += _esc_undefined_gap(compatibility)
    gaps += _esc_undersized_gap(compatibility)
    gaps += _battery_discharge_exceeded_gap(compatibility)
    gaps += _prop_motor_mismatch_gap(compatibility)

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
        motor_catalog_gap=catalog_gap,
        motor_catalog_matches=catalog_matches,
        motor_catalog_gap_fact=catalog_gap_fact,
    )
