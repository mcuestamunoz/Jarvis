"""Fase C · C43 (`B1-fase-c-craft-fs-bind`) — a one-way, READ-ONLY bind
from a `VehicleProfile` to craft identity (catalog SKU).

Python scaffold / sim only. **Direction locked (IC §0 decision 4):**
`vehicle_profiles` may READ craft identity via `ComponentLibrary`
(`jarvis.knowledge.library`, the existing, sole reader of `library/`
JSON — this module does not read `library/` JSON directly, does not
parse it a second way, and is not a second source of truth for frame
identity). Craft packages (`core`/`adapters`/Continuity/CLI/Board)
still never import `jarvis.flight_software`/`jarvis.vehicle_profiles` —
this is a **directed** seam, not a two-way bridge. This module never
writes `library/` and never mutates any craft workspace.

Binding a profile to a SKU is nothing more than looking up that SKU's
already-seeded identity fields (`manufacturer`/`model`/
`size_class_inch`) and attaching them, read-only, to a
`BoundVehicleProfile`. It does **not** explode a BOM, does **not**
compute geometry/mass/power, and does **not** invent a field absent
from the catalog row (IC §0 decision 5 — identity only). It does
**not** give `Continuity` any new turn that flashes, arms, or submits
into `flight_software`/`capabilities.autonomy`/`Safety` — no such
symbol is imported or referenced anywhere in this module.

**`BoundVehicleProfile`, not an extension of `VehicleProfile` itself
(IC §0 decision 6):** a small wrapper type is used instead of adding
`craft_*` fields directly onto `VehicleProfile`. This keeps the C3
schema (`extra="forbid"`, pinned by 40+ Buys' own smoke fixtures)
completely untouched, and makes "this profile view is bound to a real
catalog frame" a distinct, opt-in type a caller has to ask for, rather
than an always-present-but-usually-`None` field on every profile.
`load_smoke_profile()`/`smoke_quad_hal_imu` are unaffected — they still
return/declare a plain, unbound `VehicleProfile`, exactly as every
prior Buy in this ladder already relied on.

Craft identity in RAM != flash != arm != flying. Directed seam != craft
importing flight_software — this module imports `jarvis.knowledge.library`
(a craft READ surface), never the reverse; nothing in `src/jarvis/core`
or `src/jarvis/adapters` imports this module or `jarvis.flight_software`.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from jarvis.knowledge.library import ComponentLibrary
from jarvis.vehicle_profiles.schemas import VehicleProfile


class BoundVehicleProfile(BaseModel):
    """A `VehicleProfile` plus read-only craft identity fields mirrored
    from a catalog frame row. `craft_sku` is the catalog key exactly as
    stored in `library/frames/_datos.json` (e.g. `"hglrc_my5_5in"`);
    `craft_manufacturer`/`craft_model`/`craft_size_class_inch` mirror
    that row's own fields verbatim — never invented, never geometry/mass
    beyond size class (IC §0 decision 5)."""

    model_config = ConfigDict(extra="forbid")

    profile: VehicleProfile
    craft_sku: str
    craft_manufacturer: str | None = None
    craft_model: str | None = None
    craft_size_class_inch: float | None = None


def bind_profile_to_craft_identity(
    profile: VehicleProfile, craft_sku: str, library: ComponentLibrary | None = None
) -> BoundVehicleProfile:
    """Reads `craft_sku`'s identity fields from `library` (defaults to
    a fresh `ComponentLibrary()` — the same reader every craft path
    already uses) and returns a `BoundVehicleProfile`. Read-only: no
    write to `library/` or any workspace anywhere in this function.

    Raises `KeyError` — the same error `ComponentLibrary.get_frame`
    already raises, not a second, competing "frame not found" error
    type — if `craft_sku` is not a seeded catalog frame. Never returns
    a silently-empty or partially-invented bind on a miss."""
    active_library = library if library is not None else ComponentLibrary()
    frame = active_library.get_frame(craft_sku)
    return BoundVehicleProfile(
        profile=profile,
        craft_sku=frame.name,
        craft_manufacturer=frame.manufacturer,
        craft_model=frame.model,
        craft_size_class_inch=frame.size_class_inch,
    )
