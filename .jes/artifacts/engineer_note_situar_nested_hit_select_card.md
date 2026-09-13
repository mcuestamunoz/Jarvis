# Engineer note — Situar nested hit / select-from-card (2026-09-10)

**Field:** With Situar ON, overlapping boxes (ESC inside FC/plate) — click always hits the outer solid; ESC unreachable.

**Hotfix #2 (Cursor):** Hit-testing CSS 3D still misses the nested solid — clicks fall to the pane. With Situar ON + card selection, **mousedown anywhere in the 3D pane moves the selected piece**. **Alt+drag** = orbit. Selected solid also paints last.

**How to smoke:**
1. Situar ON  
2. Click card **esc**  
3. Drag anywhere in the 3D pane (not only on the yellow box) → ESC moves  
4. Alt+drag → orbit  

**Status:** **ACCEPT** (Engineer 2026-09-10: “Ahora sí”).
