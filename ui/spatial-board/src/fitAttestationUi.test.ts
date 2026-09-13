import { describe, expect, it } from "vitest";
import { isOverlapScreeningCopy } from "./fitAttestationUi";

describe("isOverlapScreeningCopy", () => {
  it("true for overlap screening copy", () => {
    expect(
      isOverlapScreeningCopy(
        "Los sobres se solapan en los ejes declarados — screening, no verificado.",
      ),
    ).toBe(true);
  });

  it("false for no_overlap — must not match substring se solapan inside no se solapan", () => {
    expect(
      isOverlapScreeningCopy(
        "Los sobres no se solapan en los ejes declarados — screening, no verificado.",
      ),
    ).toBe(false);
  });

  it("false for incomplete / absence copy", () => {
    expect(
      isOverlapScreeningCopy(
        "Pose incompleta (faltan y, z); no se compara — screening, no verificado.",
      ),
    ).toBe(false);
  });
});
