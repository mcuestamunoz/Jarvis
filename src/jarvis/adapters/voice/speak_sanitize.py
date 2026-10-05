"""Skill-first phase C — speak-path sanitizer (`B1-assistant-voice-speak-sanitize`, T50).

A field note on live `--chat --voice-speak` / `--voice` use flagged that
the printed egress (Layer 1 — unchanged, always the full engineering
truth) carries visual-only decoration that reads badly aloud: rule lines
made of box-drawing/markdown characters, leading bullet/checkmark/tree
glyphs, and trailing footnote-reference asterisks. None of that carries
spoken information — it is purely a screen affordance.

`sanitize_for_speech` is a pure, deterministic, **no-LLM** text transform
applied only on the **speak** side, at the single seam every spoken
egress already passes through (`speak_egress`, T38) — never on the
**print** side. `render_startup_context`/`render_response` and every
`print(...)` call in `run_chat` stay byte-identical; this module is
never imported from `adapters/cli/main.py` or any `render_*` function.

Locked, narrow scope (T50 IC) — what this module does **not** do:
- no rewrite of `PROJECT STATUS`/`PASS`/gap-title wording (that is a
  later Buy's job, not this one's);
- no glossary beyond the single locked `C-rate`/`c-rate` glossary term;
- no LLM paraphrase or summarization of any kind.

T51 (`B1-assistant-voice-brief-spanish`) lock 5 / review note T50-N1:
the original `"tasa C"` substitution produced an awkward `"El tasa C"`/
`"la tasa C"` mismatch whenever the source text already carried a
Spanish article immediately before `c-rate` (`El C-rate` / `la c-rate`).
The glossary now resolves to `"la tasa C"` in every case and absorbs a
preceding `El`/`La` article into that same replacement first, so the
article is never duplicated.
"""

from __future__ import annotations

import re

# A line made up entirely of rule/separator glyphs (light/heavy
# box-drawing dashes, markdown-style `---`/`===`/`___` dividers) carries
# zero spoken content — drop the whole line rather than reading "guion
# guion guion..." aloud. The ASCII hyphen only qualifies here (a whole
# line of nothing but hyphens), never in the leading-marker set below —
# a line starting "-5kg margen" must keep its sign, not read as decor.
_RULE_LINE_RE = re.compile(r"^[ \t]*[─━=_-]{3,}[ \t]*$")

# Leading bullet / checkmark / diamond / tree-branch decoration at the
# start of a line (e.g. "  • Indicar...", "✓ Arquitectura completa",
# "   └ 2 motores", "├── sub-item") — strip the glyph(s) plus the
# whitespace right after them; the words that follow are spoken exactly
# as printed. Unicode box-drawing horizontal (─/━) is included here —
# unlike the ASCII hyphen, it never collides with a negative number or
# a dash-bullet, so it is safe to fold into "and similar tree junk."
_LEADING_DECORATION_RE = re.compile(r"^[ \t]*(?:[•*✓◇└├│─━][ \t]*)+")

# Trailing footnote-reference marker (e.g. "Control        PASS *",
# marking a footnote printed further down the same wall) — only strips
# an asterisk run that is preceded by whitespace or is the whole
# trailing token, so it never eats a "*" glued onto the end of a word.
_TRAILING_FOOTNOTE_RE = re.compile(r"(?:^|[ \t])\*+[ \t]*$")

# Locked glossary (T50 lock, article-absorption added T51 lock 5) —
# exactly one term, case-insensitive, word-bounded so it never matches
# inside a longer token (e.g. it must not touch "accelerate" or a
# hyphenated word that merely contains "c"). Matched in two passes:
# first a preceding Spanish article + the term together (so "El C-rate"
# becomes "la tasa C", not "El la tasa C"), then any remaining bare
# occurrence — both resolve to the same "la tasa C" string.
_C_RATE_WITH_ARTICLE_RE = re.compile(r"\b(?:el|la)\s+c-rate\b", re.IGNORECASE)
_C_RATE_RE = re.compile(r"\bc-rate\b", re.IGNORECASE)


def sanitize_for_speech(text: str) -> str:
    """Deterministic, speak-path-only cleanup of `text` before it is
    handed to an external TTS command. Drops rule-only lines, strips
    leading bullet/checkmark/diamond/tree glyphs and trailing footnote
    asterisks, collapses runs of blank lines to one, and applies the
    single locked `C-rate`/`c-rate` → `"la tasa C"` glossary
    substitution (absorbing a preceding `El`/`La` article first, so the
    result is never `"El tasa C"`/`"el tasa C"`).

    Returns `""` when there is nothing left to say after cleanup (e.g.
    the input was empty, whitespace-only, or entirely decoration) —
    callers must treat that as "speak nothing", never as a reason to
    invent filler speech.
    """
    if not text:
        return ""

    cleaned_lines: list[str] = []
    for line in text.split("\n"):
        if _RULE_LINE_RE.match(line):
            continue
        line = _LEADING_DECORATION_RE.sub("", line)
        line = _TRAILING_FOOTNOTE_RE.sub("", line)
        cleaned_lines.append(line)

    collapsed_lines: list[str] = []
    previous_was_blank = False
    for line in cleaned_lines:
        is_blank = line.strip() == ""
        if is_blank and previous_was_blank:
            continue
        collapsed_lines.append(line)
        previous_was_blank = is_blank

    result = "\n".join(collapsed_lines).strip("\n")
    result = _C_RATE_WITH_ARTICLE_RE.sub("la tasa C", result)
    result = _C_RATE_RE.sub("la tasa C", result)

    return result if result.strip() else ""
