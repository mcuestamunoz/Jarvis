import { describe, expect, it } from "vitest";
import {
  ASSEMBLY_ROOT_CANDIDATE_ID,
  formatOriginCandidateLabel,
  rankBoxOriginCandidates,
} from "./situarOriginCandidates";

const box = (id: string, mountedOn?: string, originKey?: string) => ({
  id,
  geometry: { shape: "box" as const },
  mountedOn,
  declaredBoxPose: originKey ? { originKey } : undefined,
});

const disk = (id: string) => ({
  id,
  geometry: { shape: "disk" as const },
});

// A non-box entity that can still be a legal mounted_on TARGET (frame
// parts never carry box geometry — that's the whole gap tiers 2/3 fix).
const nonBoxPart = (id: string) => ({ id, geometry: undefined });

describe("rankBoxOriginCandidates", () => {
  it("T1: mountedOn box is preferred first; self excluded", () => {
    const solids = [
      box("esc", "battery"),
      box("battery"),
      box("flight_controller"),
      box("sensors"),
    ];
    const ranked = rankBoxOriginCandidates("esc", solids);
    expect(ranked.map((c) => c.id)).toEqual([
      "battery",
      "flight_controller",
      "sensors",
    ]);
    expect(ranked[0]?.labelSuffix).toBe("montado en");
    expect(ranked.every((c) => c.id !== "esc")).toBe(true);
  });

  it("T2: empty mounts → all other boxes; frame_plate preferred when boxed", () => {
    const solids = [
      box("esc"),
      box("battery"),
      box(ASSEMBLY_ROOT_CANDIDATE_ID),
      box("sensors"),
    ];
    const ranked = rankBoxOriginCandidates("esc", solids);
    expect(ranked[0]).toEqual({ id: ASSEMBLY_ROOT_CANDIDATE_ID, labelSuffix: "placa raíz" });
    expect(ranked.map((c) => c.id).sort()).toEqual(
      ["battery", ASSEMBLY_ROOT_CANDIDATE_ID, "sensors"].sort(),
    );
    expect(ranked).toHaveLength(3);
  });

  it("T3: non-box / missing mount target never preferred; disks never candidates", () => {
    const solids = [
      box("esc", "motors"),
      disk("motors"),
      box("battery"),
      { id: "frame_plate", geometry: undefined },
    ];
    const ranked = rankBoxOriginCandidates("esc", solids);
    expect(ranked.map((c) => c.id)).toEqual(["battery"]);
    expect(ranked.every((c) => c.labelSuffix === "")).toBe(true);
  });

  // ── Situar multi-box UX B1 fix (2026-09-12) — tiers 2/3, mirroring live
  // project shapes where the original two-tier design was proven inert. ──

  it("T4 (5min-shaped): mount-siblings preferred when the shared target is NOT a box", () => {
    // Exact shape of autonomía-de-5min: esc + flight_controller both
    // mounted_on "frame_plate" — a frame part that never carries box
    // geometry. Tier 1 (direct mounted_on-as-box) cannot fire here.
    const solids = [
      box("esc", "frame_plate"),
      box("flight_controller", "frame_plate"),
      box("battery", "frame_plate_2"),
      nonBoxPart("frame_plate"),
      nonBoxPart("frame_plate_2"),
    ];
    const ranked = rankBoxOriginCandidates("esc", solids);
    expect(ranked[0]).toEqual({ id: "flight_controller", labelSuffix: "mismo montaje" });
    // battery shares no mount target with esc — plain fallback, no label.
    expect(ranked.find((c) => c.id === "battery")).toEqual({ id: "battery", labelSuffix: "" });
  });

  it("T5 (15min-shaped): already-an-origin preferred with zero mounted_on data anywhere", () => {
    // Exact shape of autonomía-15min: no mounted_on declared at all, but
    // esc's origin is battery, and battery's origin is flight_controller.
    const solids = [
      box("esc", undefined, "battery"),
      box("battery", undefined, "flight_controller"),
      box("flight_controller"),
      box("sensors"),
    ];
    const ranked = rankBoxOriginCandidates("sensors", solids);
    const ids = ranked.map((c) => c.id);
    expect(ids.slice(0, 2).sort()).toEqual(["battery", "flight_controller"].sort());
    expect(ranked.find((c) => c.id === "battery")?.labelSuffix).toBe("origen de otra pieza");
    expect(ranked.find((c) => c.id === "flight_controller")?.labelSuffix).toBe("origen de otra pieza");
    // esc itself is still a valid (unranked) fallback candidate for sensors.
    expect(ranked.find((c) => c.id === "esc")).toEqual({ id: "esc", labelSuffix: "" });
  });

  it("T6: tier priority — mount-sibling wins over already-an-origin for the same candidate", () => {
    const solids = [
      box("esc", "frame_plate", "flight_controller"),
      box("flight_controller", "frame_plate"),
      box("battery"),
    ];
    // flight_controller qualifies for BOTH tier 2 (same mount as esc) and
    // tier 3 (esc's own declared origin) — tier 2 must win (checked first).
    const ranked = rankBoxOriginCandidates("esc", solids);
    expect(ranked[0]).toEqual({ id: "flight_controller", labelSuffix: "mismo montaje" });
  });

  it("T7: never invents — no mounted_on and no pose anywhere still yields the full box list, unlabeled", () => {
    const solids = [box("esc"), box("battery"), box("sensors")];
    const ranked = rankBoxOriginCandidates("esc", solids);
    expect(ranked.map((c) => c.id).sort()).toEqual(["battery", "sensors"]);
    expect(ranked.every((c) => c.labelSuffix === "")).toBe(true);
  });

  it("formatOriginCandidateLabel", () => {
    expect(formatOriginCandidateLabel({ id: "battery", labelSuffix: "montado en" })).toBe(
      "battery (montado en)",
    );
    expect(formatOriginCandidateLabel({ id: "sensors", labelSuffix: "" })).toBe("sensors");
  });
});
