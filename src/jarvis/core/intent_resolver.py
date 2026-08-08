from __future__ import annotations

import re
import unicodedata
from typing import Literal

from jarvis.schemas.action_schema import ActionName


IntentType = Literal[
    "create_project",
    "iterate",
    "define_params",
    "calculate",
    "simulate",
    "analyze",
    "project_status",
    "explore_design_space",
    "apply_exploration_result",
    "ambiguous",
    "unknown",
]


class IntentResolver:
    QUESTION_PATTERNS = (
        "como",
        "por que",
        "que pasa",
        "explica",
        "explicame",
        "influye",
        "impacto",
        "afecta",
        "cual es mejor",
        "es mejor",
        "diferencia",
    )
    STATUS_PATTERNS = (
        "estado del proyecto",
        "estado proyecto",
        "estado actual",
        "estado",
        "resumen del proyecto",
        "situacion actual",
        "como va el proyecto",
        "donde estamos",
        "donde estoy",
        "que falta",
        "que nos falta",
        "situacion del proyecto",
        "resumen",
        # FN-003: project comprehension — not analyze/impacto
        "detalles del proyecto",
        "dame detalles",
        "dame detalles del proyecto",
        "cuentame el proyecto",
        "cuenta el proyecto",
        "explica el proyecto",
        "describe el proyecto",
        "resume el diseno",
        "resume el proyecto",
        "como esta el proyecto",
        # Bug 39: navigation phrases that request orientation (not LLM fallback)
        "siguiente paso",
        "que hago",
        "como sigo",
        "que puedo hacer",
        "que debo hacer",
        "por donde empiezo",
        "como continuo",
        # A' Project Continuity — reopen / “what now” without LLM
        "y ahora",
        "ahora que",
        "que sigue",
        "donde quedamos",
        "por que no puedo comprar",
        "por que no puedo montar",
        # Bug CLI-1: guidance phrases ("guíame hasta completar") routed to iterate via
        # "completar" in ITERATE_PATTERNS — must be caught here first.
        "guiame",
        "guia",
        "guiame hasta",
        "ayudame a completar",
        "como completo",
        "como termino el proyecto",
        "que me falta completar",
        "que me falta",
        # UX-B: navigation phrases for advancing to the next block — must not fall to LLM.
        "sigamos",
        "vamos con el siguiente",
        "continua",
        "continuamos",
        "siguiente bloque",
    )
    # Precompiled word-boundary regexes for STATUS_PATTERNS.
    # Built once at class definition — avoids recompiling on every call.
    # re.escape is safe for multi-word phrases: spaces are not escaped in Python 3.7+.
    _STATUS_PATTERNS_RE = tuple(
        re.compile(r"\b" + re.escape(p) + r"\b")
        for p in STATUS_PATTERNS
    )
    ANALYZE_PATTERNS = (
        r"\b(?:analiza|analizar|analisis|evalua|evaluar|evaluacion|revisa|revisar|informe|diagnostica|diagnosticar)\b",
        r"\b(?:orientame|orientar|ayudame|dame opciones|que opciones|como hago|como puedo|que deberia)\b",
    )
    CALCULATE_PATTERNS = (
        r"\b(?:calcula|calcular|recalcula|recalcular)\b",
    )
    SIMULATE_PATTERNS = (
        r"\b(?:simula|simular|vuela|volar|comprueba|comprobar|valida|validar)\b",
    )
    # Bug 41 / E1: Explicit param-definition requests — two strictness levels.
    # Level 1 (safe): explicit verb + subject — unambiguous.
    # Level 2: "parámetros de X" phrase — still unambiguous but no verb required.
    # NOT included: "batería" alone — would capture "cambiar la batería" (iterate).
    # E1: terrestrial domain keywords (motor, transmisión, torque, rueda, tracción)
    #     added alongside aerial. Guard: inputs with a numeric value are NOT routed
    #     here — they belong to iterate (e.g. "definir torque a 50 Nm" → iterate).
    DEFINE_PARAMS_PATTERNS = (
        # ── Aerial domain ────────────────────────────────────────────────────
        r"\b(?:definir?|configurar|declarar|especificar)\b.*\bbater[ii]a\b",
        r"\b(?:definir?|configurar|declarar|especificar)\b.*\benerg[ii]a\b",
        r"\b(?:definir?|configurar|declarar|especificar)\b.*\bh[ee]lice[s]?\b",
        r"\bpar[aa]metros?\s+de\s+bater[ii]a\b",
        r"\bpar[aa]metros?\s+de\s+energ[ii]a\b",
        r"\bpar[aa]metros?\s+de\s+h[ee]lices?\b",
        # ── Terrestrial domain (E1) ──────────────────────────────────────────
        r"\b(?:definir?|configurar|declarar|especificar)\b.*\b(?:motor(?:es)?|transmisi[oó]n|torque|rueda[s]?|tracci[oó]n)\b",
        r"\bpar[aa]metros?\s+de\s+(?:motor(?:es)?|transmisi[oó]n|torque|rueda[s]?|tracci[oó]n)\b",
    )
    # Precompiled regex to detect a numeric value in the input.
    # Used to guard DEFINE_PARAMS routing: inputs that already contain a value
    # (e.g. "definir torque a 50 Nm") are iterate actions, not setup requests.
    _NUMERIC_VALUE_RE = re.compile(
        r"\b\d+(?:[.,]\d+)?\s*(?:nm|n\b|w\b|kg|\bm\b|rpm|v\b|ah|wh|%|pulgadas?)?\b"
    )
    ITERATE_PATTERNS = (
        r"\b(?:reduce|reducir|mejora|mejorar|optimiza|optimizar)\b",
        r"\b(?:aumenta|aumentar|incrementa|incrementar|sube|subir)\b",
        r"\b(?:define|definir|establece|establecer|usar|seleccionar|cambia|cambiar|modifica|modificar)\b",
        r"\b(?:completar|completar|especificar|enriquecer)\b",
        r"\bespecificaci[oó]n\b",
        # "itera" / "iterar" as shortcut verbs (e.g. "itera" after loading a project).
        r"\biter(ar?)?\b",
    )
    # DSE: explicit exploration/optimization requests that target a known goal.
    # These patterns are evaluated BEFORE ITERATE to avoid false routing to the wizard.
    # They must contain a strong exploration verb AND a goal keyword to be unambiguous.
    EXPLORE_PATTERNS = (
        r"\b(?:optimiza|optimizar|encuentra|busca|buscar|explora|explorar|prueba|probar)\b.*\b(?:mejor|optim|configuracion|configuraciones)\b",
        r"\b(?:mejor|optim)\b.*\b(?:configuracion|combinacion|opcion)\b",
        r"\bcual\b.*\b(?:mejor|optima)\b.*\b(?:configuracion|combinacion|opcion)\b",
        r"\bexplora(?:r)?\s+(?:el\s+)?(?:espacio|diseno|opciones)\b",
        r"\bencuentra(?:r)?\s+(?:la\s+)?(?:mejor|optima)\b",
        # Bug 65 + calibración 2026-08-05: verb + known DSE goal domain.
        # Covers all EXPLORATION_GRIDS goals so "optimiza para payload" /
        # "mejora la estabilidad" do not fall through to ITERATE_PATTERNS.
        # Verbs intentionally exclude aumenta/sube (those stay as iterate mutations).
        r"\b(?:optimiza(?:r)?|mejora(?:r)?|maximiza(?:r)?)\b.*\b(?:"
        r"autonomia|eficiencia|rendimiento|potencia|"
        r"payload|carga\s+util|"
        r"estabilidad|margen(?:\s+de\s+seguridad)?|"
        r"masa|peso"
        r")\b",
        r"\b(?:reducir?|minimiza(?:r)?)\b.*\b(?:masa|peso)\b",
    )
    # DSE v1.1: apply the best candidate from the last exploration.
    # Checked BEFORE EXPLORE so "aplica la mejor" doesn't fall into explore.
    APPLY_PATTERNS = (
        r"\bapl(?:ica|icar)\b",
        r"\busa\s+(?:esta|esa|la\s+mejor|la\s+optima)\b",
        r"\bqueda(?:te)?\s+con\s+(?:esa|esta|la\s+mejor)\b",
        r"\bguarda\s+(?:esta|esa|la\s+mejor|la\s+optima)?\s*configuraci[oó]n\b",
        r"\baplica(?:r)?\s+(?:la\s+)?(?:mejor|optima)\b",
        r"\baplica(?:r)?\s+(?:el\s+)?resultado\b",
        r"\baplica(?:r)?\s+(?:la\s+)?configuraci[oó]n\b",
    )
    # Bug CLI-1: guidance phrases that share verbs with ITERATE (e.g. "completar")
    # must be caught BEFORE iterate and resolve to project_status.
    # Checked inside _resolve_strong_action_intent immediately before ITERATE_PATTERNS.
    GUIDANCE_PATTERNS = (
        r"\bguia(?:me)?(?:\s+hasta)?\b",
        r"\bayudame\s+a\s+completar\b",
        r"\bcomo\s+(?:completo|termino)(?:\s+el\s+proyecto)?\b",
        r"\bque\s+me\s+falta(?:\s+completar)?\b",
        # UX-B: phrases for moving to the next block in natural language.
        r"\bsigamos(?:\s+con)?(?:\s+(?:el\s+)?siguiente(?:\s+bloque)?)?\b",
        r"\bvamos(?:\s+con)?(?:\s+(?:el\s+)?siguiente(?:\s+bloque)?)?\b",
        r"\bcontinua(?:mos)?\b",
        # Bug 69: analytical questions that previously fell through to the LLM.
        # Route to project_status instead of spending 30 s in Ollama.
        r"\bque\s+(?:me\s+)?(?:falt[a-z]*|queda[s]?)\b",       # "qué me falta", "qué falta"
        r"\bque\s+parametros?\b",                                # "qué parámetros me faltan"
        r"\bque\s+(?:hay\s+)?pendiente[s]?\b",                  # "qué hay pendiente"
        r"\bque\s+(?:me\s+)?(?:falta|queda)\s+(?:definir|completar|configurar)\b",
    )
    _GUIDANCE_PATTERNS_RE = tuple(
        re.compile(p) for p in GUIDANCE_PATTERNS
    )

    CREATE_PATTERNS = (
        r"\b(?:quiero|deseo|necesito)\s+(?:disenar|crear|hacer)\b",
        r"\b(?:crear|nuevo)\s+proyecto\b",
        r"\b(?:disenar)\b",
    )
    DOMAIN_HINT_PATTERNS = (
        r"\b(?:dron|drone|robot|material|peso|carga|payload|resistencia|estructura)\b",
    )
    # Bug 49: patterns for dismissing / skipping the current top suggestion.
    DISMISS_SUGGESTION_PATTERNS = (
        r"\bno\s+(?:aplica|quiero|me\s+interesa|es\s+relevante)\b",
        r"\bignora(?:r|lo)?\b",
        r"\b(?:descarta|descartar)\b",
        r"\bsiguiente\s+sugerencia\b",
        r"\b(?:omite|omitir|salta|saltar)\s+(?:eso|esta|la\s+sugerencia)?\b",
        r"\beso\s+no\s+aplica\b",
        r"\bno\s+es\s+(?:relevante|aplicable|para\s+mi|mi\s+caso)\b",
        r"\bya\s+(?:esta|están|lo\s+tengo)\b.*\bcorrect\w+\b",
        r"\bcorrect\w+\b.*\bsiguiente\b",
    )
    _DISMISS_SUGGESTION_PATTERNS_RE = tuple(
        re.compile(r"\b" + p if not p.startswith(r"\b") else p)
        for p in DISMISS_SUGGESTION_PATTERNS
    )
    # ── Semantic intent classes (for classify_input_intent) ──────────────────
    INFORMATION_SEEKING_KEYWORDS = (
        "dime",
        "cuales",
        "cual",
        "que son",
        "que es",
        "que significa",
        "por que",
        "explica",
        "explicame",
        "warnings",
        "advertencias",
        "fallo",
        "error",
        "problema",
        "significa",
        "como va",
        "como funciona",
        "que recomiendas",
        "que harías",
        "que harias",
        "siguiente paso",
    )
    ACTION_SEEKING_KEYWORDS = (
        "cambia",
        "cambiar",
        "reduce",
        "reducir",
        "aumenta",
        "aumentar",
        "mejora",
        "mejorar",
        "optimiza",
        "optimizar",
        "define",
        "definir",
        "añade",
        "anadir",
        "pon",
        "sube",
        "subir",
        "modifica",
        "modificar",
    )

    def resolve_intent(self, user_input: str) -> IntentType:
        normalized = self._normalize_text(user_input)
        if not normalized:
            return "unknown"

        strong_action_intent = self._resolve_strong_action_intent(normalized)
        if strong_action_intent is not None:
            return strong_action_intent

        if self._looks_like_status_query(normalized):
            return "project_status"

        if self._looks_like_question(normalized):
            return "analyze"

        if self._matches_any(normalized, self.DOMAIN_HINT_PATTERNS):
            return "ambiguous"

        return "unknown"

    def resolve_explore_goal(self, user_input: str) -> str | None:
        """Extrae el goal_key de un input de tipo explore_design_space.

        Reutiliza detect_goal() del goal_planner para consistencia.
        Returns None si no se detecta ningún goal conocido.
        """
        from jarvis.core.goal_planner import detect_goal
        return detect_goal(user_input)

    def resolve_action_request(self, user_input: str, intent: IntentType | None = None) -> dict | None:
        resolved_intent = intent or self.resolve_intent(user_input)
        normalized = self._normalize_text(user_input)

        if resolved_intent == "create_project":
            return {
                "action": ActionName.CREATE_PROJECT.value,
                "parameters": {},
                "raw_user_input": None,
            }

        if resolved_intent == "calculate":
            return {
                "action": ActionName.CALCULATE.value,
                "parameters": {},
                "raw_user_input": None,
            }

        if resolved_intent == "simulate":
            return {
                "action": ActionName.SIMULATE.value,
                "parameters": {},
                "raw_user_input": None,
            }

        # Bug 41: route to param-definition wizard based on subject detected.
        if resolved_intent == "define_params":
            if self._matches_any(normalized, (
                r"\bbater[ii]a\b",
                r"\benerg[ii]a\b",
            )):
                return {
                    "action": "define_missing_parameters",
                    "parameters": {"reason": "missing_energy_parameters"},
                    "raw_user_input": user_input,
                }
            if self._matches_any(normalized, (
                r"\bh[ee]lices?\b",
                r"\bpropell\w+\b",
            )):
                return {
                    "action": "define_missing_parameters",
                    "parameters": {"reason": "missing_propeller_parameters"},
                    "raw_user_input": user_input,
                }
            # E1: terrestrial domain — route to full transmission parameter set.
            # All terrestrial sub-keywords (motor, torque, rueda, tracción) map to
            # missing_transmission_parameters because the full set is always needed:
            # per_actuator_torque_nm + motors + wheel_radius_m + gear_ratio.
            # Sub-granular reasons (missing_motor_parameters, etc.) are not defined
            # in REQUIREMENT_REASONS yet — adding them would be a future extension.
            if self._matches_any(normalized, (
                r"\bmotor(?:es)?\b",
                r"\btransmisi[oó]n\b",
                r"\btorque\b",
                r"\brueda[s]?\b",
                r"\btracci[oó]n\b",
            )):
                return {
                    "action": "define_missing_parameters",
                    "parameters": {"reason": "missing_transmission_parameters"},
                    "raw_user_input": user_input,
                }
            return None

        if resolved_intent == "iterate":
            parameters: dict[str, str] = {}

            # Enrichment path: "completar especificación de motor"
            is_enrich = any(
                keyword in normalized for keyword in ("completar", "especific", "enriquecer")
            )
            if is_enrich:
                parameters["operacion"] = "define"
                parameters["variable"] = "componentes"
                # Extract component name: "completar especificación de/del X [Y Z]" → "X Y Z"
                match = re.search(r"\bdel?\s+([\w][\w\s]*?)$", normalized)
                if match:
                    parameters["enrich_component"] = match.group(1)
                return {
                    "action": ActionName.ITERATE.value,
                    "parameters": parameters,
                    "raw_user_input": None,
                }

            is_define = any(
                keyword in normalized for keyword in ("define", "definir", "establec", "usar", "seleccion")
            )
            if is_define:
                parameters["operacion"] = "define"

            if any(keyword in normalized for keyword in ("material", "materiales")) and any(
                keyword in normalized for keyword in ("define", "definir", "establec", "usar", "seleccion")
            ):
                parameters["objetivo"] = "material"
                parameters["variable"] = "material"
                parameters["operacion"] = "define"
                return {
                    "action": ActionName.ITERATE.value,
                    "parameters": parameters,
                    "raw_user_input": None,
                }
            if any(keyword in normalized for keyword in ("componente", "componentes", "unidad de potencia", "power unit")):
                parameters["variable"] = "componentes"
            if "carga" in normalized or "payload" in normalized:
                parameters["objetivo"] = "carga"
            elif "peso" in normalized:
                parameters["objetivo"] = "peso"
            if any(keyword in normalized for keyword in ("aument", "increment", "sub")):
                parameters["operacion"] = "aumentar"
            if "reduc" in normalized:
                parameters["operacion"] = "reducir"
            elif "mejor" in normalized or "optim" in normalized:
                parameters["operacion"] = "mejorar"

            # Extract noun phrase after verb when objetivo not yet detected.
            # Mirrors the exact verb forms declared in ITERATE_PATTERNS.
            if "objetivo" not in parameters:
                verb_match = re.search(
                    r"\b(?:reduce|reducir|mejora|mejorar|optimiza|optimizar"
                    r"|aumenta|aumentar|incrementa|incrementar|sube|subir"
                    r"|cambia|cambiar|modifica|modificar)\s+([\w][\w\s]*?)$",
                    normalized,
                )
                if verb_match:
                    parameters["objetivo"] = verb_match.group(1).strip()

            return {
                "action": ActionName.ITERATE.value,
                "parameters": parameters,
                "raw_user_input": None,
            }

        return None

    def _resolve_strong_action_intent(self, normalized: str) -> IntentType | None:
        # Bug CLI-1: guidance phrases FIRST — they share verbs with both ANALYZE
        # ("ayudame") and ITERATE ("completar"). Must be caught before either.
        if any(rx.search(normalized) for rx in self._GUIDANCE_PATTERNS_RE):
            return "project_status"

        if self._matches_any(normalized, self.ANALYZE_PATTERNS):
            return "analyze"

        if self._matches_any(normalized, self.CALCULATE_PATTERNS):
            return "calculate"

        if self._matches_any(normalized, self.SIMULATE_PATTERNS):
            return "simulate"

        # Bug 41: DEFINE_PARAMS before ITERATE so that "definir batería" does not
        # fall into the generic iterate path (both share the verb "definir").
        # E1 guard: if the input already contains a numeric value the user is
        # making a parametric change (iterate), not a setup request.
        if self._matches_any(normalized, self.DEFINE_PARAMS_PATTERNS):
            if not self._NUMERIC_VALUE_RE.search(normalized):
                return "define_params"

        # Bug 49: dismiss before ITERATE so "no quiero aumentar X" does not
        # open the iterate wizard.
        if any(rx.search(normalized) for rx in self._DISMISS_SUGGESTION_PATTERNS_RE):
            return "dismiss_suggestion"

        # DSE v1.1: apply_exploration_result BEFORE explore — "aplica la mejor" must not
        # fall into explore_design_space, which expects exploration verbs + goal keywords.
        if self._matches_any(normalized, self.APPLY_PATTERNS):
            return "apply_exploration_result"

        # DSE: check explore intent BEFORE iterate — EXPLORE_PATTERNS require both
        # an exploration verb AND a goal/config keyword, so they are more specific
        # than bare ITERATE_PATTERNS and must take priority.
        if self._matches_any(normalized, self.EXPLORE_PATTERNS):
            return "explore_design_space"

        if self._matches_any(normalized, self.ITERATE_PATTERNS):
            return "iterate"

        if self._matches_any(normalized, self.CREATE_PATTERNS):
            return "create_project"

        return None

    def classify_input_intent(
        self, user_input: str
    ) -> Literal["information", "action", "hybrid"]:
        """Classify input by semantic class regardless of action resolution.

        - information: input seeks facts, explanations, or status
        - action: input requests a change or operation
        - hybrid: contains both information and action keywords → treated as information

        ACTION keywords are matched with word boundaries (consistent with ITERATE_PATTERNS)
        to avoid false positives from substrings ("definición" ≠ "define",
        "mejoramiento" ≠ "mejora").
        """
        normalized = self._normalize_text(user_input)
        has_info = (
            any(
                re.search(r"\b" + re.escape(kw) + r"\b", normalized)
                for kw in self.INFORMATION_SEEKING_KEYWORDS
            )
            or self._looks_like_question(normalized)
        )
        has_action = any(
            re.search(r"\b" + re.escape(kw) + r"\b", normalized)
            for kw in self.ACTION_SEEKING_KEYWORDS
        )
        if has_info and has_action:
            return "hybrid"
        if has_info:
            return "information"
        return "action"

    def _looks_like_question(self, normalized: str) -> bool:
        if "?" in normalized:
            return True
        return any(pattern in normalized for pattern in self.QUESTION_PATTERNS)

    def _looks_like_status_query(self, normalized: str) -> bool:
        return any(rx.search(normalized) for rx in self._STATUS_PATTERNS_RE)

    def _normalize_text(self, text: str) -> str:
        lowered = text.strip().lower()
        normalized = unicodedata.normalize("NFKD", lowered)
        without_diacritics = "".join(char for char in normalized if not unicodedata.combining(char))
        # Correct common character-swap typos before pattern matching.
        return self._fix_common_typos(without_diacritics)

    @staticmethod
    def _fix_common_typos(text: str) -> str:
        """Correct the most common transposition typos for simulate/calculate.

        Scope is deliberately narrow: only unambiguous misspellings of the two
        most-affected verbs.  Words like 'similar' or 'simpatia' must NOT be
        affected — hence the strict word-boundary anchors.
        """
        _TYPO_MAP = (
            # simulate typos: simluar, simlar, simlua, simlur …
            # Any word starting with 'siml' is an unambiguous transposition
            # of 'simular' — no Spanish word starts with 'siml' legitimately.
            (r"\bsiml\w+\b", "simular"),
            # calculate typos: calcluar, calclua, calucar, caluclar…
            (r"\bcal(?:cluar?|clua|ucar?|uclar?)\b", "calcular"),
            # Bug 46: 'augmentar' is a direct anglicism (augment) for 'aumentar'.
            (r"\baugment\w*\b", "aumentar"),
        )
        for pattern, replacement in _TYPO_MAP:
            text = re.sub(pattern, replacement, text)
        return text

    def _matches_any(self, text: str, patterns: tuple[str, ...]) -> bool:
        return any(re.search(pattern, text) for pattern in patterns)
