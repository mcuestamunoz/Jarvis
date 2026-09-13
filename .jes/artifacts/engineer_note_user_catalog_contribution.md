# Engineer note — User catalog contribution (cola after #4)

**Date:** 2026-09-10  
**Authority:** Engineer — developer can edit `library/` JSON; a normal user cannot add a reusable catalog component  
**Status:** COLA — **after #4 sourced dims** · no IC · no PRIORIDAD · no `src/`  
**Parents:**
- [#4 sourced lock](engineer_lock_sourced_envelope_to_3d.md) — cite → Class A bag → seed; never invent  
- [Physical Component Catalog v1](../docs/PHYSICAL_COMPONENT_CATALOG_V1.md) — catalog = identity + bind, not freeform SoT  
- Freeform declare + Board Situar already let users **use** undeclared parts in a project  

---

## Pain

Today catalog growth is **developer-curated** (`library/**/_datos.json`). A non-developer Engineer/user who declares a real part on the Board (dims, material, pose) has no path to **promote** that identity into a reusable catalog entry without editing code.

---

## Direction (not a Buy yet)

Do **not** open a catalog CMS or Conversation Engine.

Preferred shape when ★ opens (investigation B0 first):

1. **Project-local draft** — persist “this declared component is mine” in the workspace (optional).  
2. **Promote → catalog candidate** — only with `source_url` + Class A bag + `identity_status: user_declared` (never auto-`verified`).  
3. **Verified seed** — remains curated merge into shared `library/` (human review).  

Board / Continuity writers stay the SoT for declared props; contribution is a **promote path**, not a second geometry invent.

---

## Gate relative to #4

| Order | Why |
|---|---|
| **#4 first** | Establishes cite → seed → bind → Board for Class A keys |
| **Then this** | Reuses the same citation honesty; avoids user rows without a sourced method |

Forbidden without ★: writing user rows straight into shared `library/` as `verified` · inventing dims · crawler · Platform Capability packages.

---

## When ★

Open investigation contract **User catalog contribution B0** (boundaries + trust model). IC only after Buy shape locked.
