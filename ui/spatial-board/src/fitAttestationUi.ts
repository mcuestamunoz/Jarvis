/**
 * Fit attestation B1 — Board button eligibility (UX only).
 * The writer still gates on `screen_posed_envelope == overlap`.
 *
 * Must NOT use bare `"se solapan"`: the no-overlap copy is
 * `"Los sobres no se solapan…"` and that substring would false-positive
 * (Engineer field: Declarar verificado shown on no_overlap cards).
 */
export function isOverlapScreeningCopy(sobresValue: string): boolean {
  return sobresValue.includes("Los sobres se solapan");
}
