/**
 * Board 3D-first workshop + mount-chain inspector B1
 * (`B1-board-3d-first-inspector`) — pure "summary" field selection for the
 * inspector dock's default (collapsed) view. `SpatialCard`'s own full `<dl>`
 * dump (every `node.fields` entry) stays available behind "Ver todo"; this
 * only picks a short, honest preview.
 *
 * Priority order (IC §2.2.1): montado en, mass_g, power_w, SKU, sobres,
 * origen pose — first match per label wins, in this fixed order, capped at
 * 5. Never invents a field the projector didn't already emit; never
 * reorders/reformats a value (both projected verbatim from
 * `spatial_board.py`'s own `_format_property`/label strings).
 */
import type { SpatialNode } from "./types";

const SUMMARY_LABEL_PRIORITY: readonly string[] = [
  "montado en",
  "mass_g",
  "power_w",
  "SKU",
  "sobres",
  "origen pose",
];

const SUMMARY_FIELD_CAP = 5;

export function pickSummaryFields(
  fields: SpatialNode["fields"],
): SpatialNode["fields"] {
  const byLabel = new Map(fields.map((f) => [f.label, f]));
  const picked: SpatialNode["fields"] = [];
  for (const label of SUMMARY_LABEL_PRIORITY) {
    const field = byLabel.get(label);
    if (field) picked.push(field);
    if (picked.length >= SUMMARY_FIELD_CAP) break;
  }
  return picked;
}
