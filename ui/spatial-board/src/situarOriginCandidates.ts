/**
 * Board Situar multi-box UX B1 — pure origin-picker ranking.
 * Never invents an origin; never drops the full box list when mounts are empty.
 * Preferred keys sort first; remaining boxes keep input order.
 */

export const ASSEMBLY_ROOT_CANDIDATE_ID = "frame_plate";

export type OriginCandidateSolid = {
  id: string;
  geometry?: { shape?: string } | null;
  mountedOn?: string;
  /** Situar multi-box UX B1 fix (2026-09-12) — read-only here: "already
   * anchoring something" (tier 3 below) needs every sibling's own declared
   * origin, not just the subject's. */
  declaredBoxPose?: { originKey: string };
};

export type RankedOriginCandidate = {
  id: string;
  /** Short Spanish suffix for the <option> label; empty = bare key. */
  labelSuffix: string;
};

function isBox(solid: OriginCandidateSolid): boolean {
  return solid.geometry?.shape === "box";
}

/**
 * Rank box origins for the origin picker of `subjectId`.
 *
 * Situar multi-box UX B1 fix (2026-09-12): the original two-tier design
 * (subject's own `mountedOn` if boxed, else `frame_plate` if boxed) proved
 * INERT on every real project — `mounted_on` always points at a frame part
 * (`frame_plate`/`frame`/etc.) and those never carry box geometry (the
 * still-open plate L×W citation gap), so tier 1 can never fire and tier 4
 * (`frame_plate` itself) never fires either. Verified against the live
 * `autonomía-de-5min`/`autonomía-15min` trees: every option came back with
 * an empty label. Two more tiers, using data that's ALREADY declared
 * (never inventing a millimetre or a plate footprint), fixed that:
 *
 *   1. Subject's own `mountedOn` target, when that target is itself a box
 *      (kept from the original design — stays dormant until some project
 *      states a boxed mount target, but costs nothing to keep).
 *   2. "Mount-siblings" — another box solid declared `mounted_on` the SAME
 *      target as the subject (e.g. `esc` and `flight_controller` both
 *      `mounted_on: "frame_plate"` on `autonomía-de-5min`) — fires whenever
 *      `mounted_on` is declared at all, even though the shared target
 *      itself is never a box.
 *   3. "Already an origin" — a box already used as ANOTHER sibling's
 *      `declared_box_pose.origin_key` (i.e. something is already anchored
 *      to it). This is the one tier that still fires when NO `mounted_on`
 *      relation exists anywhere on the project at all (e.g.
 *      `autonomía-15min` today, where `battery`/`flight_controller` are
 *      already pose origins for their own children).
 *   4. `frame_plate`, when boxed (unchanged — dormant until a plate L×W
 *      citation exists; never invented here).
 *
 * Tiers are checked in this exact priority order — a candidate already
 * claimed by an earlier tier keeps that tier's label. The full box
 * fallback (every remaining box, unranked, in input order) is NEVER
 * dropped, and no origin is ever silently chosen — the caller still
 * requires an explicit pick + "Fijar origen".
 */
export function rankBoxOriginCandidates(
  subjectId: string,
  solids: OriginCandidateSolid[],
): RankedOriginCandidate[] {
  const boxes = solids.filter((s) => s.id !== subjectId && isBox(s));
  const byId = new Map(solids.map((s) => [s.id, s]));
  const subject = byId.get(subjectId);

  const preferred = new Map<string, string>();
  const mount = subject?.mountedOn;

  // Tier 1 — direct mounted_on target, when that target is itself a box.
  if (mount && mount !== subjectId) {
    const target = byId.get(mount);
    if (target && isBox(target)) {
      preferred.set(mount, "montado en");
    }
  }

  // Tier 2 — mount-siblings: another box mounted_on the same (possibly
  // non-box) target as the subject.
  if (mount) {
    for (const b of boxes) {
      if (preferred.has(b.id)) continue;
      if (b.mountedOn === mount) {
        preferred.set(b.id, "mismo montaje");
      }
    }
  }

  // Tier 3 — already an origin: a box some OTHER sibling's declared_box_pose
  // already points at. Fires even with zero mounted_on data anywhere.
  const usedAsOrigin = new Set<string>();
  for (const s of solids) {
    if (s.id === subjectId) continue;
    const originId = s.declaredBoxPose?.originKey;
    if (originId) usedAsOrigin.add(originId);
  }
  for (const b of boxes) {
    if (preferred.has(b.id)) continue;
    if (usedAsOrigin.has(b.id)) {
      preferred.set(b.id, "origen de otra pieza");
    }
  }

  // Tier 4 — the assembly root plate, when it happens to be boxed.
  const root = byId.get(ASSEMBLY_ROOT_CANDIDATE_ID);
  if (root && isBox(root) && root.id !== subjectId) {
    if (!preferred.has(root.id)) {
      preferred.set(root.id, "placa raíz");
    }
  }

  const result: RankedOriginCandidate[] = [];
  const seen = new Set<string>();
  for (const [id, labelSuffix] of preferred) {
    if (boxes.some((b) => b.id === id)) {
      result.push({ id, labelSuffix });
      seen.add(id);
    }
  }
  for (const b of boxes) {
    if (seen.has(b.id)) continue;
    result.push({ id: b.id, labelSuffix: "" });
  }
  return result;
}

export function formatOriginCandidateLabel(c: RankedOriginCandidate): string {
  return c.labelSuffix ? `${c.id} (${c.labelSuffix})` : c.id;
}
