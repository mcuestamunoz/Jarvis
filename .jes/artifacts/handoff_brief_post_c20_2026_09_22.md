# Handoff brief — post C20 (`v0.5.18`) · new agent cycle

**Date:** 2026-09-22  
**For:** next Cursor / Claude session (this chat hit memory limit)  
**Repo:** Jarvis · tip **`v0.5.18`** · branch `main` (local ahead of origin; **do not push** unless Engineer asks)

---

## 1. Who you are (roles)

| Agent | Does | Does not |
|---|---|---|
| **Cursor** | ICs, PRIORIDAD/cola, independent reviews after code exists | Implement `src/` / `ui/` / `tests/` / `library/` for an approved IC |
| **Claude Code** | Implements the ★ IC + implementation report | Define product architecture |
| **Engineer** | ★ Buy / ACCEPT / pick next front / tags on ACCEPT | — |

Exception: only if Engineer says Cursor should code (“implementa tú” / “Cursor code”).

---

## 2. Where tip is

- **Git tip tagged:** `v0.5.18`
- **Last ACCEPT:** C20 `B1-fase-c-crsf-dual-role-bridge` — CRSF decode → dual-role bridge
- **Suite:** **3444** passed, 1 skipped · UI **132** · Craft SoT **`v0.4.3`**
- **PRIORIDAD:** C20 CLOSED — awaiting Engineer pick for **one** C21+ front  
  Source of truth: `docs/IMPLEMENTATION_TASKS.md` (top section only)

**Process lock (mandatory):**  
`.jes/artifacts/engineer_note_fase_c_process_lock_after_c6_2026_09_20.md` — **one front at a time**; no premature flash / live ELRS / craft↔FS claims.

---

## 3. Fase C ladder (what exists)

### Platform scaffold (Python)
- C1 registry empty · C2 Intent + RejectAll · C3–C12 wooden FC ladder (filter→…→sim tip) · C4 autonomy behind Safety · C5 radio dual-role **sim** · C17 `ArmedAllowlistSafetyGate` (opt-in; default still RejectAll; allow ≠ execute)

### C++ / MCU (`native/flight_control/`)
- C13–C15 steel ladder + Catch2 · C16 `libjarvis_fc.a` arm-none-eabi · C18 `fc_mcu_stub.elf` freestanding (**≠ flashed**)

### Link / radio path (recent)
| # | Tag | What |
|---|---|---|
| C5 | `v0.5.3` | `radio.py` — `RadioStubFrame` / `SimulatedRadioIngress`; **no** CRSF in `radio.py` (T5) |
| C19 | `v0.5.17` | `crsf_stub.py` — fixture CRSF parse (CRC8 `0xD5`, `0x16` RC, `0x14` link stats); **≠ live ELRS** |
| C20 | `v0.5.18` | `crsf_dual_role.py` — aux ch→`kill` Authority bridge; Authority **≠** Safety allow |

**Honesty lines still true:** fixture CRSF ≠ ELRS on air · bridge ≠ pilot link · `.elf` ≠ flashed · Authority ≠ allow · `RadioIntentAdapter` still `NotImplemented`.

---

## 4. Candidate next fronts (Engineer picks ONE)

Natural deepen-after-C20 (recommended if continuing link):

1. **UART / byte-stream assembler** — host stub: bytes in → frames out → existing parse/bridge; still **no** product serial-to-real-RX as “live ELRS”
2. **Deepen bridge policy** — more kinds / channels / Intent path (only if Engineer wants; C20 locked Authority-only)

Other parked (orthogonal / premature without more honesty work):

3. **Board flash** — needs real memory map / BSP honesty; C18 map is fictional  
4. **Craft ↔ FS wiring** — Continuity/craft SoT ↔ flight_software; big scope jump

Do **not** open two of these in one IC.

---

## 5. How to start the next cycle

1. Read PRIORIDAD + process lock.  
2. Engineer names **one** front (or asks Cursor to recommend / draft IC).  
3. Cursor drafts IC → PRIORIDAD READY FOR ★ → Engineer ★.  
4. Claude implements + report.  
5. Cursor reviews (independent PASS) → Engineer ACCEPT + tag.  
6. No push unless asked. Tags only on ACCEPT.

---

## 6. Key paths to open first

```text
docs/IMPLEMENTATION_TASKS.md                          # PRIORIDAD AHORA
.jes/artifacts/engineer_note_fase_c_process_lock_after_c6_2026_09_20.md
.jes/artifacts/implementation_review_fase_c_crsf_dual_role_bridge_b1.md
src/jarvis/capabilities/{crsf_stub,crsf_dual_role,radio,safety}.py
native/flight_control/                                # C13–C18; don’t touch casually
CLAUDE.md + .cursor/rules/jes-cursor-claude-roles.mdc
```

---

## 7. Suggested paste for new chat

```text
Jarvis JES handoff post-C20. Tip v0.5.18. Cursor = IC/review only;
Claude Code = implement after ★. Read docs/IMPLEMENTATION_TASKS.md
PRIORIDAD + .jes/artifacts/handoff_brief_post_c20_2026_09_22.md.
C20 CLOSED (CRSF→dual-role bridge). Awaiting Engineer pick for one
C21+ front: UART stream · deepen policy · board flash · craft↔FS.
One front only. No push unless asked.
```

Then Engineer says which front (or “recomienda y redacta IC”).
