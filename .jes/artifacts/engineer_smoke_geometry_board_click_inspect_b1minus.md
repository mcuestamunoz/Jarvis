# Engineer smoke — Board click-inspect B1− (2026-09-08)

**Status:** ACCEPT  
**Project:** `autonomía-de-10min` (`9ada1a1b0cca`)  
**Surface:** `jarvis board` (`http://127.0.0.1:5173/`)  
**Parents:** [IC](implementation_contract_geometry_board_click_inspect_b1minus.md) · [review](implementation_review_geometry_board_click_inspect_b1minus.md) PASS WITH NOTES @ suite **2429**

## Walk

| Step | Result |
|---|---|
| Board live, 14 cards, hint includes `click: seleccionar` | visor loads |
| Click card **esc** | recuadro azul **solo** en ESC (`hobbywing_xrotor_40a_6s`); campos ya visibles |
| Confirmed with Engineer | “solo debe verse el recuadro azul cuando tocas uno” — sí: una card, no glyphs, no minimapa-as-selection |

No 3D. No pose. No `"cabe"`. Selection is highlight over an already-open card.

## Verdict

**ACCEPT.** Click-inspect B1− closable.

## Next

3D solids rendering-tech investigation (not an IC). Pose / `"cabe"` later ★.
