"""
jarvis.knowledge.library
========================
Deterministic access to the component/material library stored under
library/.

This module is the ONLY place that reads _datos.json files.
All callers (mutation_engine, iterate_interactive_session, create_project)
must use ComponentLibrary – never read JSON directly.
"""
from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

# Root of the knowledge base relative to this file:
# src/jarvis/knowledge/ → ../../../../library/
_LIBRARY_ROOT = Path(__file__).resolve().parent.parent.parent.parent / "library"


def _normalize_name(name: str) -> str:
    """Lowercase and strip diacritics so 'plastico' matches 'plástico'."""
    nfd = unicodedata.normalize("NFD", name.strip().lower())
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


@dataclass(frozen=True)
class MaterialSpec:
    name: str
    density_kg_m3: float


@dataclass(frozen=True)
class MotorSpec:
    """Catalog entry: a real product that covers a physical design-space region (D8)."""

    name: str
    thrust_n: float
    kv_rating: int
    weight_g: float
    compatible_prop_inch: tuple[int, ...]
    # Design-space region this product satisfies (defaults derived from point values).
    min_thrust_n: float = 0.0
    max_thrust_n: float = 0.0
    kv_min: int = 0
    kv_max: int = 0
    is_generic: bool = False
    # Catalog v1 (Impl A) — optional enrichment fields. Absent in existing rows;
    # loader defaults keep every pre-existing motor loading unchanged.
    max_watts: float | None = None
    manufacturer: str | None = None
    model: str | None = None
    max_current_a: float | None = None
    voltage_min: float | None = None
    voltage_max: float | None = None
    compatible_prop_ids: tuple[str, ...] = ()
    # Optional operating envelope samples. No consumer code reads this in
    # Impl A/B — present only so the shape exists before it's needed.
    operating_points: tuple[dict[str, Any], ...] = ()
    source_url: str | None = None
    part_number: str | None = None
    identity_status: str | None = None
    source_note: str | None = None


def _motor_covers_requirements(
    m: MotorSpec,
    *,
    min_thrust_n: float | None,
    kv: int | None,
    prop_inch: float | None,
) -> bool:
    """Design-space predicate (D8) for a single motor — the per-candidate filter
    ``find_motors_for_requirements`` applies during a full scan, factored out so
    G9-A can run the same check against one already-bound ``MotorSpec`` without
    re-scanning the whole library."""
    if min_thrust_n is not None:
        if m.max_thrust_n < min_thrust_n and m.thrust_n < min_thrust_n:
            return False
    if kv is not None:
        if not (m.kv_min <= kv <= m.kv_max):
            return False
    if prop_inch is not None and m.compatible_prop_inch:
        if not any(abs(p - prop_inch) <= 1.0 for p in m.compatible_prop_inch):
            return False
    return True


@dataclass(frozen=True)
class BatterySpec:
    """Catalog v1 (Impl A) entry: a real battery pack.

    Canonical mass unit is grams (``mass_g``), matching ``MotorSpec.weight_g``'s
    convention. Voltage identity is carried via ``cells`` and/or
    ``nominal_voltage`` — at least one is required by the loader (validated at
    load time, not enforced by the frozen dataclass itself).
    """

    name: str
    chemistry: str
    energy_wh: float
    mass_g: float
    cells: int | None = None
    nominal_voltage: float | None = None
    capacity_mah: float | None = None
    max_continuous_current_a: float | None = None
    c_rating: float | None = None
    design_space: dict[str, float] | None = None
    operating_points: tuple[dict[str, Any], ...] = ()
    # Optional identity / provenance — absent in legacy rows; loader defaults unchanged.
    manufacturer: str | None = None
    model: str | None = None
    part_number: str | None = None
    source_url: str | None = None
    identity_status: str | None = None
    pack_configuration: str | None = None
    max_continuous_current_source: str | None = None
    source_note: str | None = None


@dataclass(frozen=True)
class EscSpec:
    """Catalog entry: a real ESC (electronic speed controller)."""

    name: str
    continuous_current_a: float
    burst_current_a: float | None = None
    continuous_current_source: str | None = None
    voltage_min: float | None = None
    voltage_max: float | None = None
    cells_min: int | None = None
    cells_max: int | None = None
    esc_topology: str | None = None
    channels: int | None = None
    mass_g: float | None = None
    manufacturer: str | None = None
    model: str | None = None
    part_number: str | None = None
    source_url: str | None = None
    identity_status: str | None = None
    source_note: str | None = None


@dataclass(frozen=True)
class PlateSeed:
    """Structure B Frame Assembly Physical Model B2 — one curated, named
    plate on a frame's seed row. ``label`` is a verbatim-from-source display
    string (e.g. ``"Bottom"``, ``"Main Plate"``) — never a closed role
    vocabulary, never compared across SKUs or manufacturers (investigation
    report §B7: no source states one manufacturer's plate name is
    equivalent to another's). All fields optional/additive; a curated entry
    with none set would be pointless but is not itself forbidden here — the
    seed data (§3.2 of the IC) always sets at least ``thickness_mm``.
    """

    label: str | None = None
    thickness_mm: float | None = None
    material: str | None = None


@dataclass(frozen=True)
class FrameSpec:
    """Structure Catalog Foundation IC-1/IC-2 + Structure B Parts Graph
    (Fase 1) — catalog entry: a real frame kit, optionally with declared
    part-level composition.

    ``mass_g`` and ``size_class_inch`` are the two Structure A fields
    (``_frame_completeness``, ``frame_class_compatibility_state``) bind
    projects onto the root — required here so no incomplete seed row can
    silently exist. The Fase 1 part/assembly fields below are all optional
    and additive (default ``None``) — never a strength/fit/geometry field,
    never invented when a source doesn't state them (Structure B Parts
    Graph investigation §6/§7; every non-``None`` value in the current seed
    traces to the row's own ``source_url``).
    """

    name: str
    mass_g: float
    size_class_inch: float
    manufacturer: str | None = None
    model: str | None = None
    material: str | None = None
    part_number: str | None = None
    source_url: str | None = None
    identity_status: str | None = None
    source_note: str | None = None
    # Structure B Parts Graph (Fase 1) — additive, all optional/None default.
    wheelbase_mm: float | None = None
    configuration: str | None = None
    arm_count: int | None = None
    arm_material: str | None = None
    arm_thickness_mm: float | None = None
    plate_count: int | None = None
    plate_material: str | None = None
    cage_material: str | None = None
    standoff_count: int | None = None
    standoff_material: str | None = None
    # Frame Assembly Physical Model B2 — curated, ordinal plate list.
    # Legacy scalar fallback: kept when this is None/empty (N2). Canonical
    # over the scalar plate_count/plate_material once non-empty.
    plates: list[PlateSeed] | None = None


@dataclass(frozen=True)
class PropellerSpec:
    """Catalog v1 (Impl A) entry: a real propeller."""

    name: str
    diameter_in: float
    pitch_in: float
    mass_g: float | None = None
    ct: float | None = None
    cp: float | None = None
    compatible_kv_band: tuple[int, int] | None = None
    tags: tuple[str, ...] = ()
    operating_points: tuple[dict[str, Any], ...] = ()
    # Optional identity enrichment — absent in legacy rows; loader defaults unchanged.
    manufacturer: str | None = None
    model: str | None = None
    part_number: str | None = None
    source_url: str | None = None
    identity_status: str | None = None


class ComponentLibrary:
    """Read-only access to the physical component/material database."""

    def __init__(self, library_root: Path | None = None) -> None:
        self._root = library_root or _LIBRARY_ROOT
        self._materials: dict[str, MaterialSpec] | None = None
        self._motors: dict[str, MotorSpec] | None = None
        self._batteries: dict[str, BatterySpec] | None = None
        self._propellers: dict[str, PropellerSpec] | None = None
        self._escs: dict[str, EscSpec] | None = None
        self._frames: dict[str, FrameSpec] | None = None

    # ── Materials ────────────────────────────────────────────────────────────

    def _load_materials(self) -> dict[str, MaterialSpec]:
        if self._materials is not None:
            return self._materials
        path = self._root / "materiales" / "_datos.json"
        if not path.exists():
            raise FileNotFoundError(
                f"Biblioteca de materiales no encontrada: {path}"
            )
        raw: dict[str, dict] = json.loads(path.read_text(encoding="utf-8"))
        self._materials = {
            _normalize_name(name): MaterialSpec(name=name, density_kg_m3=float(data["density_kg_m3"]))
            for name, data in raw.items()
        }
        return self._materials

    def get_material(self, name: str) -> MaterialSpec:
        """Return MaterialSpec for *name*.

        Raises KeyError with a clear message if the material is not in the
        library.  Callers that require graceful degradation should catch
        KeyError and show a user-friendly message.
        """
        canonical = _normalize_name(name)
        materials = self._load_materials()
        if canonical not in materials:
            available = ", ".join(sorted(materials))
            raise KeyError(
                f"Material '{name}' no está en la biblioteca. "
                f"Disponibles: {available}"
            )
        return materials[canonical]

    def list_materials(self) -> list[MaterialSpec]:
        """Return all known materials sorted by name."""
        return sorted(self._load_materials().values(), key=lambda m: m.name)

    def has_material(self, name: str) -> bool:
        """Return True if *name* is in the library (no exception)."""
        try:
            self.get_material(name)
            return True
        except KeyError:
            return False

    # ── Motors ─────────────────────────────────────────────────────────────

    @staticmethod
    def _motor_from_raw(name: str, data: dict) -> MotorSpec:
        thrust = float(data["thrust_n"])
        kv = int(data["kv_rating"])
        props = tuple(int(x) for x in data.get("compatible_prop_inch") or [])
        space = data.get("design_space") or {}
        # Default design space: ±20% thrust band, ±150 KV around the catalog point.
        min_thrust = float(space.get("min_thrust_n", thrust * 0.8))
        max_thrust = float(space.get("max_thrust_n", thrust * 1.25))
        kv_min = int(space.get("kv_min", max(0, kv - 150)))
        kv_max = int(space.get("kv_max", kv + 150))
        return MotorSpec(
            name=name,
            thrust_n=thrust,
            kv_rating=kv,
            weight_g=float(data["weight_g"]),
            max_watts=(
                float(data["max_watts"]) if data.get("max_watts") is not None else None
            ),
            compatible_prop_inch=props,
            min_thrust_n=min_thrust,
            max_thrust_n=max_thrust,
            kv_min=kv_min,
            kv_max=kv_max,
            is_generic=bool(data.get("is_generic", name.startswith("generic_"))),
            manufacturer=data.get("manufacturer"),
            model=data.get("model"),
            max_current_a=(
                float(data["max_current_a"]) if data.get("max_current_a") is not None else None
            ),
            voltage_min=(
                float(data["voltage_min"]) if data.get("voltage_min") is not None else None
            ),
            voltage_max=(
                float(data["voltage_max"]) if data.get("voltage_max") is not None else None
            ),
            compatible_prop_ids=tuple(data.get("compatible_prop_ids") or ()),
            operating_points=tuple(data.get("operating_points") or ()),
            source_url=data.get("source_url"),
            part_number=data.get("part_number"),
            identity_status=data.get("identity_status"),
            source_note=data.get("source_note"),
        )

    def _load_motors(self) -> dict[str, MotorSpec]:
        if self._motors is not None:
            return self._motors
        path = self._root / "motores" / "_datos.json"
        if not path.exists():
            raise FileNotFoundError(f"Biblioteca de motores no encontrada: {path}")
        raw: dict[str, dict] = json.loads(path.read_text(encoding="utf-8"))
        self._motors = {
            _normalize_name(name): self._motor_from_raw(name, data)
            for name, data in raw.items()
        }
        return self._motors

    def get_motor(self, name: str) -> MotorSpec:
        """Return exact motor by name. KeyError if not found."""
        canonical = _normalize_name(name)
        motors = self._load_motors()
        if canonical not in motors:
            available = ", ".join(sorted(motors))
            raise KeyError(
                f"Motor '{name}' no está en la biblioteca. Disponibles: {available}"
            )
        return motors[canonical]

    def list_motors(self) -> list[MotorSpec]:
        """Return all motors sorted by name."""
        return sorted(self._load_motors().values(), key=lambda m: m.name)

    def find_motors_by_kv(self, kv: int, tolerance: int = 150) -> list[MotorSpec]:
        """Return motors whose kv_rating is within *tolerance* of *kv*.

        IMPORTANT: for suggestion-only — never auto-apply thrust from this result.
        Generics sort last.
        """
        matches = [
            m for m in self._load_motors().values()
            if abs(m.kv_rating - kv) <= tolerance
        ]
        return sorted(matches, key=lambda m: (m.is_generic, abs(m.kv_rating - kv), m.name))

    def find_motors_for_requirements(
        self,
        *,
        min_thrust_n: float | None = None,
        kv: int | None = None,
        prop_inch: float | None = None,
    ) -> list[MotorSpec]:
        """Return motors whose design-space covers the requested requirements (D8).

        Never auto-apply — suggestion / gap reporting only.
        """
        results = [
            m
            for m in self._load_motors().values()
            if _motor_covers_requirements(
                m, min_thrust_n=min_thrust_n, kv=kv, prop_inch=prop_inch
            )
        ]
        return sorted(
            results,
            key=lambda m: (
                m.is_generic,
                abs(m.thrust_n - (min_thrust_n or m.thrust_n)),
                m.name,
            ),
        )

    def has_motor(self, name: str) -> bool:
        """Return True if *name* is in the motor library (no exception)."""
        try:
            self.get_motor(name)
            return True
        except KeyError:
            return False

    # ── Batteries (Catalog v1 — Impl A) ───────────────────────────────────────

    @staticmethod
    def _battery_from_raw(name: str, data: dict) -> BatterySpec:
        chemistry = data.get("chemistry")
        energy_wh = data.get("energy_wh")
        mass_g = data.get("mass_g")
        if chemistry is None or energy_wh is None or mass_g is None:
            raise ValueError(
                f"Battery '{name}' está incompleta en la biblioteca: "
                "chemistry, energy_wh y mass_g son obligatorios."
            )
        cells = data.get("cells")
        nominal_voltage = data.get("nominal_voltage")
        if cells is None and nominal_voltage is None:
            raise ValueError(
                f"Battery '{name}' no declara identidad de voltaje: "
                "se requiere 'cells' y/o 'nominal_voltage'."
            )
        design_space = data.get("design_space")
        return BatterySpec(
            name=name,
            chemistry=str(chemistry),
            energy_wh=float(energy_wh),
            mass_g=float(mass_g),
            cells=int(cells) if cells is not None else None,
            nominal_voltage=float(nominal_voltage) if nominal_voltage is not None else None,
            capacity_mah=(
                float(data["capacity_mah"]) if data.get("capacity_mah") is not None else None
            ),
            max_continuous_current_a=(
                float(data["max_continuous_current_a"])
                if data.get("max_continuous_current_a") is not None
                else None
            ),
            c_rating=float(data["c_rating"]) if data.get("c_rating") is not None else None,
            design_space=dict(design_space) if design_space is not None else None,
            operating_points=tuple(data.get("operating_points") or ()),
            manufacturer=data.get("manufacturer"),
            model=data.get("model"),
            part_number=data.get("part_number"),
            source_url=data.get("source_url"),
            identity_status=data.get("identity_status"),
            pack_configuration=data.get("pack_configuration"),
            max_continuous_current_source=data.get("max_continuous_current_source"),
            source_note=data.get("source_note"),
        )

    def _load_batteries(self) -> dict[str, BatterySpec]:
        if self._batteries is not None:
            return self._batteries
        path = self._root / "baterias" / "_datos.json"
        if not path.exists():
            raise FileNotFoundError(f"Biblioteca de baterías no encontrada: {path}")
        raw: dict[str, dict] = json.loads(path.read_text(encoding="utf-8"))
        self._batteries = {
            _normalize_name(name): self._battery_from_raw(name, data)
            for name, data in raw.items()
        }
        return self._batteries

    def get_battery(self, name: str) -> BatterySpec:
        """Return exact battery by name. KeyError if not found."""
        canonical = _normalize_name(name)
        batteries = self._load_batteries()
        if canonical not in batteries:
            available = ", ".join(sorted(batteries))
            raise KeyError(
                f"Batería '{name}' no está en la biblioteca. Disponibles: {available}"
            )
        return batteries[canonical]

    def list_batteries(self) -> list[BatterySpec]:
        """Return all batteries sorted by name."""
        return sorted(self._load_batteries().values(), key=lambda b: b.name)

    def has_battery(self, name: str) -> bool:
        """Return True if *name* is in the battery library (no exception)."""
        try:
            self.get_battery(name)
            return True
        except KeyError:
            return False

    def find_batteries(
        self,
        *,
        min_energy_wh: float | None = None,
        chemistry: str | None = None,
    ) -> list[BatterySpec]:
        """Return batteries matching the given minimal deterministic filters.

        No design-space matching (unlike motors' D8) — Impl A ships plain
        threshold/equality filters only. Never auto-apply — suggestion /
        gap reporting only, same discipline as ``find_motors_for_requirements``.
        """
        results: list[BatterySpec] = []
        for b in self._load_batteries().values():
            if min_energy_wh is not None and b.energy_wh < min_energy_wh:
                continue
            if chemistry is not None and _normalize_name(b.chemistry) != _normalize_name(chemistry):
                continue
            results.append(b)
        return sorted(results, key=lambda b: (b.energy_wh, b.name))

    # ── Propellers (Catalog v1 — Impl A) ──────────────────────────────────────

    @staticmethod
    def _propeller_from_raw(name: str, data: dict) -> PropellerSpec:
        diameter_in = data.get("diameter_in")
        pitch_in = data.get("pitch_in")
        if diameter_in is None or pitch_in is None:
            raise ValueError(
                f"Propeller '{name}' está incompleta en la biblioteca: "
                "diameter_in y pitch_in son obligatorios."
            )
        kv_band = data.get("compatible_kv_band")
        return PropellerSpec(
            name=name,
            diameter_in=float(diameter_in),
            pitch_in=float(pitch_in),
            mass_g=float(data["mass_g"]) if data.get("mass_g") is not None else None,
            ct=float(data["ct"]) if data.get("ct") is not None else None,
            cp=float(data["cp"]) if data.get("cp") is not None else None,
            compatible_kv_band=(
                (int(kv_band[0]), int(kv_band[1])) if kv_band is not None else None
            ),
            tags=tuple(data.get("tags") or ()),
            operating_points=tuple(data.get("operating_points") or ()),
            manufacturer=data.get("manufacturer"),
            model=data.get("model"),
            part_number=data.get("part_number"),
            source_url=data.get("source_url"),
            identity_status=data.get("identity_status"),
        )

    def _load_propellers(self) -> dict[str, PropellerSpec]:
        if self._propellers is not None:
            return self._propellers
        path = self._root / "helices" / "_datos.json"
        if not path.exists():
            raise FileNotFoundError(f"Biblioteca de hélices no encontrada: {path}")
        raw: dict[str, dict] = json.loads(path.read_text(encoding="utf-8"))
        self._propellers = {
            _normalize_name(name): self._propeller_from_raw(name, data)
            for name, data in raw.items()
        }
        return self._propellers

    def get_propeller(self, name: str) -> PropellerSpec:
        """Return exact propeller by name. KeyError if not found."""
        canonical = _normalize_name(name)
        propellers = self._load_propellers()
        if canonical not in propellers:
            available = ", ".join(sorted(propellers))
            raise KeyError(
                f"Hélice '{name}' no está en la biblioteca. Disponibles: {available}"
            )
        return propellers[canonical]

    def list_propellers(self) -> list[PropellerSpec]:
        """Return all propellers sorted by name."""
        return sorted(self._load_propellers().values(), key=lambda p: p.name)

    def has_propeller(self, name: str) -> bool:
        """Return True if *name* is in the propeller library (no exception)."""
        try:
            self.get_propeller(name)
            return True
        except KeyError:
            return False

    def find_propellers(
        self,
        *,
        diameter_in: float | None = None,
        tolerance: float = 1.0,
    ) -> list[PropellerSpec]:
        """Return propellers within *tolerance* inches of *diameter_in*.

        No design-space matching — plain deterministic distance filter.
        Never auto-apply — suggestion / gap reporting only.
        """
        results: list[PropellerSpec] = []
        for p in self._load_propellers().values():
            if diameter_in is not None and abs(p.diameter_in - diameter_in) > tolerance:
                continue
            results.append(p)
        return sorted(
            results,
            key=lambda p: (abs(p.diameter_in - (diameter_in or p.diameter_in)), p.name),
        )

    # ── ESCs (Catalog v1 — Phase 2 foundation) ───────────────────────────────

    @staticmethod
    def _esc_from_raw(name: str, data: dict) -> EscSpec:
        continuous = data.get("continuous_current_a")
        if continuous is None:
            raise ValueError(
                f"ESC '{name}' está incompleto en la biblioteca: "
                "continuous_current_a es obligatorio."
            )
        return EscSpec(
            name=name,
            continuous_current_a=float(continuous),
            burst_current_a=(
                float(data["burst_current_a"]) if data.get("burst_current_a") is not None else None
            ),
            continuous_current_source=data.get("continuous_current_source"),
            voltage_min=float(data["voltage_min"]) if data.get("voltage_min") is not None else None,
            voltage_max=float(data["voltage_max"]) if data.get("voltage_max") is not None else None,
            cells_min=int(data["cells_min"]) if data.get("cells_min") is not None else None,
            cells_max=int(data["cells_max"]) if data.get("cells_max") is not None else None,
            esc_topology=data.get("esc_topology"),
            channels=int(data["channels"]) if data.get("channels") is not None else None,
            mass_g=float(data["mass_g"]) if data.get("mass_g") is not None else None,
            manufacturer=data.get("manufacturer"),
            model=data.get("model"),
            part_number=data.get("part_number"),
            source_url=data.get("source_url"),
            identity_status=data.get("identity_status"),
            source_note=data.get("source_note"),
        )

    def _load_escs(self) -> dict[str, EscSpec]:
        if self._escs is not None:
            return self._escs
        path = self._root / "esc" / "_datos.json"
        if not path.exists():
            self._escs = {}
            return self._escs
        raw: dict[str, dict] = json.loads(path.read_text(encoding="utf-8"))
        self._escs = {
            _normalize_name(name): self._esc_from_raw(name, data)
            for name, data in raw.items()
        }
        return self._escs

    def get_esc(self, name: str) -> EscSpec:
        """Return exact ESC by name. KeyError if not found."""
        canonical = _normalize_name(name)
        escs = self._load_escs()
        if canonical not in escs:
            available = ", ".join(sorted(escs)) or "(vacío)"
            raise KeyError(
                f"ESC '{name}' no está en la biblioteca. Disponibles: {available}"
            )
        return escs[canonical]

    def list_escs(self) -> list[EscSpec]:
        """Return all ESCs sorted by name."""
        return sorted(self._load_escs().values(), key=lambda e: e.name)

    def has_esc(self, name: str) -> bool:
        """Return True if *name* is in the ESC library (no exception)."""
        try:
            self.get_esc(name)
            return True
        except KeyError:
            return False

    # ── Frame (Structure Catalog Foundation IC-1 — schema+seed only) ────────

    @staticmethod
    def _frame_from_raw(name: str, data: dict) -> FrameSpec:
        mass_g = data.get("mass_g")
        if mass_g is None:
            raise ValueError(
                f"Frame '{name}' está incompleto en la biblioteca: "
                "mass_g es obligatorio."
            )
        size_class_inch = data.get("size_class_inch")
        if size_class_inch is None:
            raise ValueError(
                f"Frame '{name}' está incompleto en la biblioteca: "
                "size_class_inch es obligatorio."
            )
        return FrameSpec(
            name=name,
            mass_g=float(mass_g),
            size_class_inch=float(size_class_inch),
            manufacturer=data.get("manufacturer"),
            model=data.get("model"),
            material=data.get("material"),
            part_number=data.get("part_number"),
            source_url=data.get("source_url"),
            identity_status=data.get("identity_status"),
            source_note=data.get("source_note"),
            wheelbase_mm=(
                float(data["wheelbase_mm"]) if data.get("wheelbase_mm") is not None else None
            ),
            configuration=data.get("configuration"),
            arm_count=(int(data["arm_count"]) if data.get("arm_count") is not None else None),
            arm_material=data.get("arm_material"),
            arm_thickness_mm=(
                float(data["arm_thickness_mm"]) if data.get("arm_thickness_mm") is not None else None
            ),
            plate_count=(int(data["plate_count"]) if data.get("plate_count") is not None else None),
            plate_material=data.get("plate_material"),
            cage_material=data.get("cage_material"),
            standoff_count=(
                int(data["standoff_count"]) if data.get("standoff_count") is not None else None
            ),
            standoff_material=data.get("standoff_material"),
            plates=ComponentLibrary._parse_plates(name, data.get("plates")),
        )

    # Frame Assembly Physical Model B2, N7 lock: frame_plate + frame_plate_2
    # ... frame_plate_8 — at most 8 ordinal plate siblings. Enforced here
    # (load time), not silently truncated at projection time.
    _MAX_PLATES = 8

    @staticmethod
    def _parse_plates(name: str, raw: Any) -> list[PlateSeed] | None:
        if raw is None:
            return None
        if not isinstance(raw, list):
            raise ValueError(
                f"Frame '{name}': 'plates' debe ser una lista, no {type(raw).__name__}."
            )
        if len(raw) > ComponentLibrary._MAX_PLATES:
            raise ValueError(
                f"Frame '{name}': 'plates' declara {len(raw)} entradas, "
                f"máximo {ComponentLibrary._MAX_PLATES} (frame_plate..frame_plate_8)."
            )
        return [
            PlateSeed(
                label=entry.get("label"),
                thickness_mm=(
                    float(entry["thickness_mm"]) if entry.get("thickness_mm") is not None else None
                ),
                material=entry.get("material"),
            )
            for entry in raw
        ]

    def _load_frames(self) -> dict[str, FrameSpec]:
        if self._frames is not None:
            return self._frames
        path = self._root / "frames" / "_datos.json"
        if not path.exists():
            self._frames = {}
            return self._frames
        raw: dict[str, dict] = json.loads(path.read_text(encoding="utf-8"))
        self._frames = {
            _normalize_name(name): self._frame_from_raw(name, data)
            for name, data in raw.items()
        }
        return self._frames

    def get_frame(self, name: str) -> FrameSpec:
        """Return exact frame by name. KeyError if not found."""
        canonical = _normalize_name(name)
        frames = self._load_frames()
        if canonical not in frames:
            available = ", ".join(sorted(frames)) or "(vacío)"
            raise KeyError(
                f"Frame '{name}' no está en la biblioteca. Disponibles: {available}"
            )
        return frames[canonical]

    def list_frames(self) -> list[FrameSpec]:
        """Return all frames sorted by name."""
        return sorted(self._load_frames().values(), key=lambda f: f.name)

    def has_frame(self, name: str) -> bool:
        """Return True if *name* is in the frame library (no exception)."""
        try:
            self.get_frame(name)
            return True
        except KeyError:
            return False

    # ── Motor ↔ propeller compatibility (Catalog v1 — Impl A) ────────────────

    def match_motor_propeller(self, motor_id: str, prop_id: str) -> bool:
        """Return True if *motor_id* and *prop_id* are compatible.

        Deterministic rule, no aerodynamic model (Design §5):
          1. Explicit ``motor.compatible_prop_ids`` — exact membership.
          2. Else ``motor.compatible_prop_inch`` vs the propeller's
             ``diameter_in`` — within 1.0" (same tolerance ``find_motors_for_requirements``
             already uses for the reverse lookup).
          3. Neither present → False. A missing match is never fabricated as True.
        """
        motor = self.get_motor(motor_id)
        prop = self.get_propeller(prop_id)
        if motor.compatible_prop_ids:
            normalized_ids = {_normalize_name(x) for x in motor.compatible_prop_ids}
            return _normalize_name(prop.name) in normalized_ids
        if motor.compatible_prop_inch:
            return any(abs(p_in - prop.diameter_in) <= 1.0 for p_in in motor.compatible_prop_inch)
        return False


# ── Phase 2 P2-1 — Operating Point lookup ────────────────────────────────────

_OP_VOLTAGE_EPSILON_V = 0.05


@dataclass(frozen=True)
class ResolvedOperatingPoint:
    """Result of resolve_operating_point — always typed, never a bare float.

    ``resolution_type`` tells the caller (and, ultimately, the CLI/estado
    surface) exactly how trustworthy ``thrust_n`` is:
      - ``exact_operating_point``    — real motor+propeller[+voltage] combo
        matched a curated ``operating_points[]`` row (fallback_only=False).
      - ``fallback_operating_point`` — a ``fallback_only=True`` row matched
        (motor-only headline point; NOT propeller-independent physics).
      - ``legacy_estimate``          — no operating_points match; falls back
        to the bare ``MotorSpec.thrust_n`` catalog peak, exactly today's
        pre-Phase-2 numeric behavior.
    """

    thrust_n: float
    resolution_type: Literal[
        "exact_operating_point", "fallback_operating_point", "legacy_estimate"
    ]
    source_type: str
    confidence: float
    selection_reason: str | None
    voltage_v: float | None
    rpm: float | None
    current_a: float | None
    power_w: float | None
    efficiency_gf_per_w: float | None
    propeller_sku: str | None
    fallback_only: bool
    source_reference: str | None
    source_note: str | None
    motor_sku: str


def _resolved_from_op_row(
    motor_sku: str,
    row: dict[str, Any],
    resolution_type: Literal["exact_operating_point", "fallback_operating_point"],
    selection_reason: str | None,
) -> ResolvedOperatingPoint:
    return ResolvedOperatingPoint(
        thrust_n=float(row["thrust_n"]),
        resolution_type=resolution_type,
        source_type=str(row.get("source_type") or "estimated"),
        confidence=float(row.get("confidence") or 0.0),
        selection_reason=selection_reason,
        voltage_v=(float(row["voltage_v"]) if row.get("voltage_v") is not None else None),
        rpm=(float(row["rpm"]) if row.get("rpm") is not None else None),
        current_a=(float(row["current_a"]) if row.get("current_a") is not None else None),
        power_w=(float(row["power_w"]) if row.get("power_w") is not None else None),
        efficiency_gf_per_w=(
            float(row["efficiency_gf_per_w"]) if row.get("efficiency_gf_per_w") is not None else None
        ),
        propeller_sku=row.get("propeller_sku"),
        fallback_only=bool(row.get("fallback_only", False)),
        source_reference=row.get("source_reference"),
        source_note=row.get("source_note"),
        motor_sku=motor_sku,
    )


def resolve_operating_point(
    motor_sku: str,
    *,
    propeller_sku: str | None = None,
    voltage_v: float | None = None,
    library: ComponentLibrary | None = None,
) -> ResolvedOperatingPoint | None:
    """Resolve real thrust for a catalog motor from curated ``operating_points[]``.

    Priority (★6 resolver contract, locked; voltage gate tightened by the
    Motor OP Voltage Coherence IC, ★1):
      1. Exact match: a ``fallback_only=False`` row whose ``propeller_sku``
         equals *propeller_sku* AND ``voltage_v`` is known (not None) AND
         (the row has no voltage_v of its own, or both are within
         ``_OP_VOLTAGE_EPSILON_V``). An unknown query voltage
         (``voltage_v=None`` — e.g. no battery bound yet) can never match an
         exact row; it falls through to fallback/legacy below. This closes
         the stale-lock-in bug where an exact resolution made before the
         real battery voltage was known could survive un-revalidated
         indefinitely (investigation_report_dse_motor_op_dual_truth.md).
         Multiple exact matches → the one with the highest ``thrust_n``
         wins, ``selection_reason="v1_max_thrust"`` (v1 provisional policy).
      2. Fallback: any ``fallback_only=True`` row for the motor. If
         *voltage_v* is given and at least one fallback row's voltage is
         within epsilon, prefer that subset; otherwise any fallback row is
         eligible. Highest ``thrust_n`` wins among the eligible set.
      3. Legacy: no operating_points match at all → the bare
         ``MotorSpec.thrust_n`` catalog peak, labeled ``legacy_estimate`` /
         ``source_type="estimated"`` — numerically identical to today's
         pre-Phase-2 behavior (regression contract).

    Returns ``None`` only when *motor_sku* itself isn't in the library —
    every known motor always resolves to at least a ``legacy_estimate``.
    """
    lib = library or default_library
    try:
        motor = lib.get_motor(motor_sku)
    except KeyError:
        return None

    canonical_prop = _normalize_name(propeller_sku) if propeller_sku else None

    exact_matches: list[dict[str, Any]] = []
    fallback_matches: list[dict[str, Any]] = []
    for row in motor.operating_points:
        # Curated rows on HOLD (evidence_status) stay on file for audit but
        # must never participate in exact or fallback resolution.
        if row.get("evidence_status") == "hold":
            continue
        row_voltage = row.get("voltage_v")
        # ★1 (Motor OP Voltage Coherence IC): an unknown query voltage no
        # longer auto-matches every row — only a KNOWN, compatible voltage
        # (or a row with no voltage_v of its own) qualifies for an exact
        # match. This only gates the exact-match branch below; fallback
        # matching (further down) keeps its own, separate voltage handling.
        voltage_matches = (
            voltage_v is not None
            and (
                row_voltage is None
                or abs(float(row_voltage) - voltage_v) <= _OP_VOLTAGE_EPSILON_V
            )
        )
        if bool(row.get("fallback_only", False)):
            fallback_matches.append(row)
            continue
        row_prop = row.get("propeller_sku")
        if canonical_prop is None or row_prop is None:
            continue
        if _normalize_name(str(row_prop)) != canonical_prop:
            continue
        if not voltage_matches:
            continue
        exact_matches.append(row)

    if exact_matches:
        best = max(exact_matches, key=lambda r: float(r["thrust_n"]))
        reason = "v1_max_thrust" if len(exact_matches) > 1 else None
        return _resolved_from_op_row(motor_sku, best, "exact_operating_point", reason)

    if fallback_matches:
        if voltage_v is not None:
            voltage_matched = [
                r for r in fallback_matches
                if r.get("voltage_v") is not None
                and abs(float(r["voltage_v"]) - voltage_v) <= _OP_VOLTAGE_EPSILON_V
            ]
            pool = voltage_matched or fallback_matches
        else:
            pool = fallback_matches
        best = max(pool, key=lambda r: float(r["thrust_n"]))
        return _resolved_from_op_row(motor_sku, best, "fallback_operating_point", None)

    return ResolvedOperatingPoint(
        thrust_n=motor.thrust_n,
        resolution_type="legacy_estimate",
        source_type="estimated",
        confidence=0.5,
        selection_reason=None,
        voltage_v=None,
        rpm=None,
        current_a=None,
        power_w=None,
        efficiency_gf_per_w=None,
        propeller_sku=None,
        fallback_only=False,
        source_reference=None,
        source_note="Bare catalog peak thrust_n; no operating_points[] match on file.",
        motor_sku=motor_sku,
    )


# ── Phase 2.5 — Hover Flight Energy Model (★★4-★★6/★★9 locked) ──────────────
#
# resolve_operating_point (above) answers "what is this motor's feasibility/
# max-thrust bench point" — it is the bind-time, thrust-demand-blind resolver
# and stays untouched (regression contract, ★9 of the investigation). This
# section answers a DIFFERENT question, at a DIFFERENT moment (calc time,
# once a hover thrust DEMAND is known): "what does this motor+propeller+
# voltage combo draw at a SPECIFIC target thrust" — via bounded linear
# interpolation over the same operating_points[] rows, never proportional
# scaling or extrapolation. See investigation_report_phase25_hover_autonomy.md
# Gate D/I and implementation_contract_phase25_hover_autonomy.md §2.2-§2.3.

_THRUST_EXACT_EPSILON_N = 0.01


@dataclass(frozen=True)
class ResolvedHoverOperatingPoint:
    """Result of resolve_operating_point_at_thrust — always typed, never a
    bare float. Deliberately NOT ResolvedOperatingPoint (different Literal
    space — "interpolated"/"unverifiable" have no meaning for the bind-time
    feasibility resolver, and reusing that dataclass would risk a schema
    migration touching the Motor OP Voltage Coherence regression contract).

    ``source_type``:
      - ``manufacturer_test`` / ``measured_test`` — target_thrust_n matched
        (within ``_THRUST_EXACT_EPSILON_N``) a single curated row's own
        thrust_n; power_w/current_a are that row's real values, unchanged.
      - ``interpolated``      — target_thrust_n fell strictly between two
        eligible rows; power_w/current_a are bounded linear interpolations
        on the thrust_n axis (★★4); ``source_points`` names both.
      - ``unverifiable``      — no honest answer exists: zero eligible rows
        for this exact (motor, propeller, voltage) identity, only one
        eligible row and no exact match, or target_thrust_n outside
        [min, max] of the eligible set (★★5 — no extrapolation, ever).
        power_w/current_a are None.
    """

    target_thrust_n: float
    thrust_n: float | None
    current_a: float | None
    power_w: float | None
    source_type: Literal[
        "manufacturer_test", "measured_test", "interpolated", "unverifiable"
    ]
    interpolation_axis: str | None
    method: str | None
    bounded: bool
    source_points: tuple[dict[str, float], ...] | None
    motor_sku: str
    propeller_sku: str | None
    voltage_v: float | None
    selection_reason: Literal[
        "exact_thrust", "bracket_interpolate", "below_min", "above_max",
        "insufficient_rows", "no_matching_rows", "unknown_motor",
    ]


def _eligible_hover_rows(
    motor: "MotorSpec", *, propeller_sku: str | None, voltage_v: float | None,
) -> list[dict[str, Any]]:
    """Rows usable for hover-thrust resolution (★★4 preconditions): real
    motor+propeller+voltage identity match, never a fallback headline point,
    never a HOLD-staged row, and only sourced ("manufacturer_test" /
    "measured_test") electrical data — a row missing power_w/current_a
    cannot anchor an interpolation regardless of its source_type label."""
    canonical_prop = _normalize_name(propeller_sku) if propeller_sku else None
    eligible: list[dict[str, Any]] = []
    for row in motor.operating_points:
        if row.get("evidence_status") == "hold":
            continue
        if bool(row.get("fallback_only", False)):
            continue
        if str(row.get("source_type") or "") not in ("manufacturer_test", "measured_test"):
            continue
        row_prop = row.get("propeller_sku")
        if canonical_prop is None or row_prop is None:
            continue
        if _normalize_name(str(row_prop)) != canonical_prop:
            continue
        row_voltage = row.get("voltage_v")
        if (
            voltage_v is None
            or row_voltage is None
            or abs(float(row_voltage) - voltage_v) > _OP_VOLTAGE_EPSILON_V
        ):
            continue
        if row.get("power_w") is None or row.get("current_a") is None or row.get("thrust_n") is None:
            continue
        eligible.append(row)
    return eligible


def resolve_operating_point_at_thrust(
    motor_sku: str,
    *,
    propeller_sku: str | None = None,
    voltage_v: float | None = None,
    target_thrust_n: float,
    library: ComponentLibrary | None = None,
) -> ResolvedHoverOperatingPoint:
    """Phase 2.5 (★★4-★★6/★★9/★★12): resolve honest motor input power/
    current at a SPECIFIC target thrust — exact match, bounded linear
    interpolation between two bracketing rows, or an honest
    ``unverifiable`` when neither is possible. Never extrapolates (★★5),
    never proportionally scales (★★11), never returns a bare float.
    """
    lib = library or default_library

    def _unverifiable(reason: Literal[
        "below_min", "above_max", "insufficient_rows", "no_matching_rows", "unknown_motor",
    ]) -> ResolvedHoverOperatingPoint:
        return ResolvedHoverOperatingPoint(
            target_thrust_n=target_thrust_n, thrust_n=None, current_a=None,
            power_w=None, source_type="unverifiable", interpolation_axis=None,
            method=None, bounded=False, source_points=None, motor_sku=motor_sku,
            propeller_sku=propeller_sku, voltage_v=voltage_v, selection_reason=reason,
        )

    try:
        motor = lib.get_motor(motor_sku)
    except KeyError:
        return _unverifiable("unknown_motor")

    eligible = _eligible_hover_rows(motor, propeller_sku=propeller_sku, voltage_v=voltage_v)
    if not eligible:
        # Distinct from "insufficient_rows" (a dataset exists for this exact
        # identity but can't bracket this target): here there is NO Discrete
        # Operating Point Dataset at all for this (motor, propeller, voltage)
        # combo — calc-time callers use this to fall back to the pre-Phase-
        # 2.5 bench-rating autonomy path rather than reporting a hover claim
        # this motor was never curated to support (investigation §Gate D/H).
        return _unverifiable("no_matching_rows")

    eligible.sort(key=lambda r: float(r["thrust_n"]))

    for row in eligible:
        if abs(float(row["thrust_n"]) - target_thrust_n) <= _THRUST_EXACT_EPSILON_N:
            return ResolvedHoverOperatingPoint(
                target_thrust_n=target_thrust_n, thrust_n=target_thrust_n,
                current_a=float(row["current_a"]), power_w=float(row["power_w"]),
                source_type=str(row.get("source_type")),  # type: ignore[arg-type]
                interpolation_axis=None, method=None, bounded=False,
                source_points=None, motor_sku=motor_sku, propeller_sku=propeller_sku,
                voltage_v=voltage_v, selection_reason="exact_thrust",
            )

    min_thrust = float(eligible[0]["thrust_n"])
    max_thrust = float(eligible[-1]["thrust_n"])
    if target_thrust_n < min_thrust:
        return _unverifiable("below_min")
    if target_thrust_n > max_thrust:
        return _unverifiable("above_max")

    if len(eligible) < 2:
        # A single eligible row covers exactly one thrust point (handled by
        # the exact-match loop above) — anything else in [min, max] for a
        # one-row set has no second point to bracket against (★★4).
        return _unverifiable("insufficient_rows")

    row_low = max((r for r in eligible if float(r["thrust_n"]) <= target_thrust_n), key=lambda r: float(r["thrust_n"]))
    row_high = min((r for r in eligible if float(r["thrust_n"]) >= target_thrust_n), key=lambda r: float(r["thrust_n"]))
    if row_low is row_high:
        # target_thrust_n landed exactly on a row already covered above —
        # unreachable in practice (exact-match loop returns first), kept as
        # a defensive no-op-interpolation guard.
        return _unverifiable("insufficient_rows")

    t_low, t_high = float(row_low["thrust_n"]), float(row_high["thrust_n"])
    frac = (target_thrust_n - t_low) / (t_high - t_low)
    power_w = float(row_low["power_w"]) + frac * (float(row_high["power_w"]) - float(row_low["power_w"]))
    current_a = float(row_low["current_a"]) + frac * (float(row_high["current_a"]) - float(row_low["current_a"]))

    return ResolvedHoverOperatingPoint(
        target_thrust_n=target_thrust_n, thrust_n=target_thrust_n,
        current_a=round(current_a, 4), power_w=round(power_w, 4),
        source_type="interpolated", interpolation_axis="thrust_n", method="linear",
        bounded=True,
        source_points=(
            {"thrust_n": t_low, "power_w": float(row_low["power_w"]), "current_a": float(row_low["current_a"])},
            {"thrust_n": t_high, "power_w": float(row_high["power_w"]), "current_a": float(row_high["current_a"])},
        ),
        motor_sku=motor_sku, propeller_sku=propeller_sku, voltage_v=voltage_v,
        selection_reason="bracket_interpolate",
    )


# Shared singleton — safe for single-process use (tests override via constructor)
default_library = ComponentLibrary()
