# Investigation Report — Part C: Synthesis (`INV-voice-llm-ci-audit`, CI-INV-0)

**Project:** Jarvis · **Date:** 2026-10-16 · **Investigator:** Claude Code (read-only)
**Contract:** [INV IC](investigation_contract_voice_llm_continuity_interpreter_audit_b0.md) · **Index:** [index](investigation_report_voice_llm_ci_audit_b0.md) · [Part A](investigation_report_voice_llm_ci_audit_part_a_voice_b0.md) · [Part B](investigation_report_voice_llm_ci_audit_part_b_llm_ci_b0.md)
**Status:** Implemented — awaiting Cursor review. No ACCEPT claim. Recommendations only; each maps to an existing CI-0 lock or says "needs new DC".

---

## C1 — Unified gap register

Severity: **blocker** (blocks an honest ★ on the current gate) · **high** · **medium** · **low** · **park**.

| ID | Surface | Gap | Sev | Evidence | Buy grain | Blocked-by | Maps to |
|---|---|---|---|---|---|---|---|
| **G-01** | LLM ingress | Gemma validates unclassified input (`hablar`, `Gracias.`, questions) as **`create_project`** → opens create wizard over the active project; Bug 52 guard covers `iterate` only. On `--voice-only`, STT hallucinations trigger it. Regression of the CI-1 default change; not in CI-1/1b smoke criteria | **blocker** | Part B B3-1; `orchestrator.py:2576-2590`; 9 Gemma-era logs; stub repro → `CREATE_PROJECT_INTERACTIVE` | **IC** (CI-1c) | — | CI-0 lock 5 (claim-before-LLM), lock 9 (quarantine `interpret`), Bug 52 precedent |
| **G-02** | LLM analyze | Bare goal tokens (`empuje`, `thrust`, `estabilidad`, `autonomia`, `bateria`) still prepend the strategy wall on explain-shaped asks outside the finite gate (`por qué…`, `en qué consiste…`, `cómo funciona…`, `dime la…`); `goal_context` still injected when gated | high | Part B B3-2/B6; CI-1b review N2/N3 | IC (F-1b-style direction-aware keywords) **or** fold into CI-4 | CI-1 ★ | CI-0 lock 9 (fold `analyze`) |
| **G-03** | Test hygiene | Pre-existing `run_chat()` tests reach **live Ollama** and write the real `llm_logs/`; suite timing depends on Ollama state; silent (tests pass either way) | high | Part A A6; Part B B7; proven: 2 tests → 2 live calls, 28.9 s | IC (small, tests-only + maybe a seam) | — | CLAUDE.md determinism; prerequisite for CI-0 lock 9 measurement |
| **G-04** | CI-5 measurement | `llm_logs` corpus unusable: 90/133 interpret rows are test `hablar`; rows lack resolver intent + call site | high | Part B B7 | IC (log fields) after G-03 | G-03 | CI-0 lock 9 |
| **G-05** | Voice egress | `analyze` LLM text spoken verbatim on `--voice-only` — unbounded, no Layer 2 discipline, unclassified in the map | high | Part A A3-g1; `main.py:611`, `main.py:1099-1100` | **DC** (CI-2) → IC | CI-1 ★ | CI-0 locks 3, 4, 6, 9 |
| **G-06** | Chat ∥ voice | `--chat` speaks nothing; CI-0 lock 4 wants spoken Continuity in both; DC Open #2 (always vs opt-in) unanswered | high | Part B B9; `main.py:954-958` | **DC** (CI-2) | Engineer answer Open #2 | CI-0 lock 4 |
| **G-07** | Voice egress | `[Wizard activo] {reprompt}` / dismiss notes printed but never spoken on `estado` walls | medium | Part A A3-g2; `main.py:585-593`; `spoken_continuity.py:261-263` | IC (could ride CI-2 or a tiny standalone) | — | T44-DC lock 1 (Layer 2 must not hide what the user needs) — **needs CI-2 DC call** whether suffixes are Layer 2 |
| **G-08** | Analyze quality | Gemma instruction echo ("En resumen, el usuario quiere que actúe como…") in every Gemma-era analyze log; CI-1b prompt fix **unmeasured live** | medium (gate) | Part B B5/B6; logs `20261015T135747`, `…135851`, `20261016T091434` | Engineer re-smoke (in flight) → CI-1b lock 6 post-filter only if still echoing | — | CI-1b IC |
| **G-09** | Voice journey | Spanish STT opt-in (`JARVIS_WHISPER_ARGS` empty by default) | low–medium | Part A A5-1; `whisper_stt.sh:80` | IC (operator wrapper default) | — | T49/T55 pattern |
| **G-10** | Docs | Spoken-continuity map: stale line numbers since T53, header "`0.7.4`", missing analyze + wall-suffix rows | low (but map is the CI-2 inventory) | Part A A3 | rides **CI-2** (CLAUDE.md norm) | — | CLAUDE.md § spoken map |
| **G-11** | Docs | Voice cola: consumed DCs still "DC ready"; T46 hybrid DC not marked retired; V8 section not marked historical | low | Part A A1 | docs hygiene (any next docs Buy) | — | cola maintenance rule |
| **G-12** | Docs | `LLM_MAP.md` "Known issues: None", no CI/Gemma; `FASE_LLM.md` documents removed prefill; anchors INV says default qwen | low | Part B B10 | docs (ride CI-2 DC or CI-1 ★ board) | — | CI-0 lock 11 |
| **G-13** | Ingress tag | Daily `--voice-only` runs `source=TERMINAL`; `VOICE` only on batch paths | low (latent) | Part A A4 T34-2/3 | note in CI-3 DC | CI-3 | CI-0 lock 5 |
| **G-14** | Voice | Silence cut level-based; arrow=Esc; POSIX; closed blank-marker set | park (accepted limits) | T54/T58/T59 reviews | — | — | — |
| **G-15** | World | `world/` / spoken destinations / craft voice UX | **park (T40)** | T34-8/9; no evidence of pressure | own DC later | — | CI-0 lock 12 |

## C2 — Roadmap coherence

Locked CI order: CI-1b → ★ CI-1 → CI-2 egress → CI-3 ingress → CI-4/CI-5 → CI-R4; T40 Parked.

| Row | Still correct? | Evidence / change |
|---|---|---|
| CI-1b → ★ CI-1 | **Correct but incomplete.** The ★ gate tests only analyze (`explicame el margen`). G-01 is a CI-1-caused regression on the `interpret` path that the gate never exercises | insert **CI-1c** before ★ `v0.8.7` |
| CI-2 egress after CI-1 ★ | correct | G-05/G-06/G-07/G-10 are all CI-2 DC inputs; CI-2 DC must also settle the T44-2 amendment scope (Part A conflict table) |
| CI-3 ingress after CI-2 | correct, with a note | G-01 is ingress-shaped, but is a **regression guard**, not CI-3 design — it must not wait for CI-3 |
| CI-4 fold `analyze` | correct; G-02 can be absorbed there if Engineer prefers not to do F-1b keyword hygiene | — |
| CI-5 retire `interpret` | correct ("measure first"), but **measurement is blocked** by G-03/G-04 | add G-03 → G-04 as CI-5 prerequisites |
| CI-R4 | correct (Later) | — |
| T40 | **stay Parked** | no evidence (Part A A8) |

Suggested reorder: **CI-1b re-smoke → CI-1c → ★ `v0.8.7` (CI-1+1b+1c) → G-03 hygiene (tiny, parallel OK) → CI-2 DC → …**

## C3 — The one next obvious step

**CI-1c — `B1-llm-interpret-unknown-guard` (IC, Cursor writes · Claude implements), before ★ `v0.8.7`.**

- **Why this one:** it is the only **blocker** in C1 (G-01). CI-1 changes the product default model; with that default, an unclassified line (a test `hablar`, a voice hallucination `Gracias.`, a free question) now passes `ActionPolicy` as `create_project` and **opens the create-project wizard over the user's active project**. Tagging `v0.8.7` without it ships that regression to daily `--chat` and `--voice-only`. Everything else in the CI epoch (CI-2 compose, CI-5 measurement) sits on top of a default model that must not hijack turns.
- **Shape (for the IC to decide, not designed here):** extend the existing Bug 52 guard (`orchestrator.py:2586-2589`) — resolver intent `unknown` + LLM verb that would open a wizard (`create_project`, possibly all non-`iterate` too) → the same honest non-mutating route Bug 52 already uses, or the `invalid_llm_output` message. Regression tests with a stub LLM returning `create_project` for `hablar` / `Gracias.` on an active project. Maps to CI-0 locks 5 and 9; no new verb, no ActionPolicy change.
- **Engineer action now:** during the in-flight CI-1b re-smoke, also type `hablar` and `gracias` with a project loaded. If either prints "Vamos a definir el proyecto paso a paso." → open CI-1c; do not ★ `v0.8.7` yet.

Alternatives (ranked):
- **#2 — G-03 test-LLM isolation** (tests-only IC: `run_chat`-level tests stub the LLM client and log root). Can run in parallel; prerequisite for CI-5 measurement and for deterministic CI-2 tests.
- **#3 — CI-2 DC (egress)** with Engineer answer to Open #2, absorbing G-05/G-06/G-07/G-10 and the T44-2 amendment scope.

## C4 — Stop conditions (must **not** be the next Buy)

| Not next | Why |
|---|---|
| ★ `v0.8.7` on CI-1b smoke alone | G-01 blocker unexercised by the current gate |
| CI-2 IC before CI-1 ★ (and before CI-2 **DC**) | CI-0 order; Open #2 unanswered; Layer 2 amendment scope unsettled |
| Deleting `interpret` / CI-5 | measurement corpus invalid (G-03/G-04); CI-0 lock 9 "measure first" |
| Widening/deleting ActionPolicy, 5th verb | fence holds; CI-0 locks 8, 12 |
| T40 unpark | no evidence |
| OpenClaw gateway · embeddings/RAG · Conversation Engine | CI-0 lock 12 / CLAUDE.md forbidden |
| Prompt-only "fix" of G-01 | relevance is an ingress/claim problem (lock 5), not a prompt problem; a prompt tweak is unmeasurable without G-03/G-04 |

## C5 — PRIORIDAD / cola / state wording (applied in this INV)

- **PRIORIDAD:** `CI-INV-0 Implemented` (Parts A/B/C) → await Cursor review. CI-1b still awaits Engineer re-smoke; INV recommends adding `hablar`/`gracias` probes and opening **CI-1c** before ★ `v0.8.7`.
- **CI cola:** CI-INV-0 → **Implemented · awaiting Cursor review**; new row **CI-1c** `B1-llm-interpret-unknown-guard` → ☐ proposed by INV (needs IC); CI-5 note "blocked by test-log pollution (G-03/G-04)".
- **state:** `execution_status = investigation_implemented_awaiting_review`; open questions = Cursor review of CI-INV-0 · Engineer re-smoke incl. probes · open CI-1c?
