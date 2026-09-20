import { describe, expect, it } from "vitest";
import { pickSummaryFields } from "./inspectorSummary";

describe("pickSummaryFields", () => {
  it("T6: picks known priority labels in the fixed order, ignores the rest", () => {
    const fields = [
      { label: "length_mm", value: "19 mm" },
      { label: "montado en", value: "frame_plate" },
      { label: "mass_g", value: "9 g" },
      { label: "model", value: "runcam" },
    ];
    expect(pickSummaryFields(fields)).toEqual([
      { label: "montado en", value: "frame_plate" },
      { label: "mass_g", value: "9 g" },
    ]);
  });

  it("T6: empty when none of the priority labels are present", () => {
    const fields = [{ label: "length_mm", value: "19 mm" }];
    expect(pickSummaryFields(fields)).toEqual([]);
  });

  it("caps at 5 even when more priority labels are present", () => {
    const fields = [
      { label: "montado en", value: "frame_plate" },
      { label: "mass_g", value: "9 g" },
      { label: "power_w", value: "1 W" },
      { label: "SKU", value: "runcam_phoenix_2" },
      { label: "sobres", value: "no se solapan" },
      { label: "origen pose", value: "frame_plate" },
    ];
    expect(pickSummaryFields(fields)).toHaveLength(5);
  });

  it("never invents a field absent from the input", () => {
    expect(pickSummaryFields([])).toEqual([]);
  });
});
