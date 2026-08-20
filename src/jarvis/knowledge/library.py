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
from typing import Any

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
    max_watts: float
    compatible_prop_inch: tuple[int, ...]
    # Design-space region this product satisfies (defaults derived from point values).
    min_thrust_n: float = 0.0
    max_thrust_n: float = 0.0
    kv_min: int = 0
    kv_max: int = 0
    is_generic: bool = False
    # Catalog v1 (Impl A) — optional enrichment fields. Absent in existing rows;
    # loader defaults keep every pre-existing motor loading unchanged.
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


class ComponentLibrary:
    """Read-only access to the physical component/material database."""

    def __init__(self, library_root: Path | None = None) -> None:
        self._root = library_root or _LIBRARY_ROOT
        self._materials: dict[str, MaterialSpec] | None = None
        self._motors: dict[str, MotorSpec] | None = None
        self._batteries: dict[str, BatterySpec] | None = None
        self._propellers: dict[str, PropellerSpec] | None = None

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
            max_watts=float(data["max_watts"]),
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


# Shared singleton — safe for single-process use (tests override via constructor)
default_library = ComponentLibrary()
