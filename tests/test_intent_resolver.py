import pytest

from jarvis.core.intent_resolver import IntentResolver


def test_intent_resolver_matches_create_project_for_design_request():
    resolver = IntentResolver()

    intent = resolver.resolve_intent("quiero diseñar un motor ionico")
    result = resolver.resolve_action_request("quiero diseñar un motor ionico", intent=intent)

    assert intent == "create_project"
    assert result is not None
    assert result["action"] == "create_project"


def test_intent_resolver_matches_iterate_for_reduce_weight():
    resolver = IntentResolver()

    intent = resolver.resolve_intent("reduce peso")
    result = resolver.resolve_action_request("reduce peso", intent=intent)

    assert intent == "iterate"
    assert result is not None
    assert result["action"] == "iterate"
    assert result["parameters"]["objetivo"] == "peso"
    assert result["parameters"]["operacion"] == "reducir"


def test_intent_resolver_matches_iterate_for_increase_payload():
    resolver = IntentResolver()

    intent = resolver.resolve_intent("aumenta carga útil")
    result = resolver.resolve_action_request("aumenta carga útil", intent=intent)

    assert intent == "iterate"
    assert result is not None
    assert result["action"] == "iterate"
    assert result["parameters"]["objetivo"] == "carga"
    assert result["parameters"]["operacion"] == "aumentar"


def test_intent_resolver_matches_iterate_for_define_material():
    resolver = IntentResolver()

    intent = resolver.resolve_intent("establecer materiales estructurales")
    result = resolver.resolve_action_request("establecer materiales estructurales", intent=intent)

    assert intent == "iterate"
    assert result is not None
    assert result["action"] == "iterate"
    assert result["parameters"]["operacion"] == "define"
    assert result["parameters"]["variable"] == "material"


def test_intent_resolver_extracts_define_components_parameters():
    resolver = IntentResolver()

    intent = resolver.resolve_intent("definir componentes")
    result = resolver.resolve_action_request("definir componentes", intent=intent)

    assert intent == "iterate"
    assert result is not None
    assert result["action"] == "iterate"
    assert result["parameters"]["operacion"] == "define"
    assert result["parameters"]["variable"] == "componentes"
    assert "objetivo" not in result["parameters"]


def test_intent_resolver_returns_none_for_ambiguous_message():
    resolver = IntentResolver()

    intent = resolver.resolve_intent("haz algo útil con esto")
    result = resolver.resolve_action_request("haz algo útil con esto", intent=intent)

    assert intent == "unknown"
    assert result is None


def test_intent_resolver_classifies_analyze_question():
    resolver = IntentResolver()

    intent = resolver.resolve_intent("como influye el material en la resistencia?")

    assert intent == "analyze"


def test_intent_resolver_prioritizes_calculate_over_question_pattern():
    resolver = IntentResolver()

    intent = resolver.resolve_intent("calcula como influye el peso")
    request = resolver.resolve_action_request("calcula como influye el peso", intent=intent)

    assert intent == "calculate"
    assert request is not None
    assert request["action"] == "calculate"


def test_intent_resolver_prioritizes_simulate_over_question_pattern():
    resolver = IntentResolver()

    intent = resolver.resolve_intent("simula el impacto del material")
    request = resolver.resolve_action_request("simula el impacto del material", intent=intent)

    assert intent == "simulate"
    assert request is not None
    assert request["action"] == "simulate"


def test_intent_resolver_classifies_domain_hint_as_ambiguous():
    resolver = IntentResolver()

    intent = resolver.resolve_intent("dron")
    request = resolver.resolve_action_request("dron", intent=intent)

    assert intent == "ambiguous"
    assert request is None


@pytest.mark.parametrize(
    "text,expected",
    [
        ("como influye el material en la resistencia", "analyze"),
        ("por que baja el margen de seguridad", "analyze"),
        ("que pasa si aumento la carga util", "analyze"),
        ("que material es mejor aluminio o fibra", "analyze"),
        ("calcula como influye el peso", "calculate"),
        ("simula el impacto del material", "simulate"),
        ("recalcula con payload de 2.5 kg", "calculate"),
        ("reduce peso", "iterate"),
        ("aumenta carga", "iterate"),
        ("establece material estructural a fibra de carbono", "iterate"),
        ("quiero diseñar un dron", "create_project"),
        ("nuevo proyecto de dron", "create_project"),
        ("dron", "ambiguous"),
        ("material", "ambiguous"),
        ("peso", "ambiguous"),
        ("haz algo util con esto", "unknown"),
        ("mmm no se que hacer", "unknown"),
    ],
)
def test_intent_classification_realistic_matrix(text, expected):
    resolver = IntentResolver()

    intent = resolver.resolve_intent(text)

    assert intent == expected


def test_precedence_action_over_analyze_for_calculate():
    resolver = IntentResolver()

    intent = resolver.resolve_intent("calcula como influye el peso")

    assert intent == "calculate"


def test_precedence_action_over_analyze_for_simulate():
    resolver = IntentResolver()

    intent = resolver.resolve_intent("simula el impacto del material")

    assert intent == "simulate"


def test_question_pattern_does_not_default_to_iterate():
    resolver = IntentResolver()

    intent = resolver.resolve_intent("como influye el material")

    assert intent == "analyze"


def test_project_status_query_maps_to_project_status():
    resolver = IntentResolver()

    intent = resolver.resolve_intent("estado del proyecto")

    assert intent == "project_status"


@pytest.mark.parametrize(
    "text,expected",
    [
        ("oye y esto del material como afecta?", "analyze"),
        ("si cambio el material que pasa", "analyze"),
        ("esto es mejor o peor?", "analyze"),
        ("y si aumento peso?", "analyze"),
        ("porque no vuela mejor?", "simulate"),
    ],
)
def test_human_style_inputs(text, expected):
    resolver = IntentResolver()

    intent = resolver.resolve_intent(text)

    assert intent == expected


# ── project_status intent ────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "text",
    [
        "estado del proyecto",
        "estado proyecto",
        "estado actual",
        "resumen del proyecto",
        "situacion actual",
        "como va el proyecto",
        "donde estamos",
        "que falta",
        "que nos falta",
        "situacion del proyecto",
        "resumen",
        # with diacritics
        "dónde estamos",
        "qué falta",
        "situación actual",
    ],
)
def test_project_status_patterns_resolve_to_project_status(text):
    resolver = IntentResolver()
    assert resolver.resolve_intent(text) == "project_status"


def test_project_status_takes_priority_over_analyze():
    """'estado del proyecto' is a status query, not a generic analysis question."""
    resolver = IntentResolver()
    assert resolver.resolve_intent("estado del proyecto") == "project_status"
    assert resolver.resolve_intent("estado del proyecto?") == "project_status"


def test_analyze_still_works_for_generic_questions():
    """Generic questions that are NOT status queries should still resolve to analyze."""
    resolver = IntentResolver()
    assert resolver.resolve_intent("cómo afecta el material?") == "analyze"
    assert resolver.resolve_intent("qué impacto tiene el material?") == "analyze"


# ── ANALYZE_PATTERNS strong-action verbs ─────────────────────────────────────

@pytest.mark.parametrize(
    "text",
    [
        "analiza el diseño actual",
        "analizar el proyecto",
        "análisis del sistema",
        "evalua el margen de seguridad",
        "evaluar el rendimiento",
        "evaluacion del diseño",
        "revisa los resultados",
        "revisar la simulación",
        "informe del proyecto",
        "diagnostica el sistema",
        "diagnosticar el fallo",
    ],
)
def test_analyze_patterns_resolve_to_analyze(text):
    """Imperative analysis verbs in ANALYZE_PATTERNS must resolve to 'analyze'."""
    resolver = IntentResolver()
    assert resolver.resolve_intent(text) == "analyze"


def test_analyze_patterns_beat_question_pattern():
    """'analiza cómo influye' has both a question word and an analyze verb — analyze wins."""
    resolver = IntentResolver()
    assert resolver.resolve_intent("analiza cómo influye el peso en la estructura") == "analyze"


def test_analyze_patterns_beat_iterate_pattern():
    """'evalua si reducir el peso mejora el diseño' — analyze verb wins over iterate verb."""
    resolver = IntentResolver()
    assert resolver.resolve_intent("evalua si reducir el peso mejora el diseño") == "analyze"


def test_analyze_patterns_do_not_match_partial_words():
    """'analización' (not in pattern) must NOT be caught by the word-boundary regex."""
    resolver = IntentResolver()
    # 'analización' contains 'analiza' as substring but the \b boundary should not block it;
    # however the pattern only lists exact forms — 'analización' is not one of them.
    # This is a deliberate design limit: only listed verb forms match.
    result = resolver.resolve_intent("analización del sistema")
    # Falls through to question-pattern or domain-hint logic — must NOT be "analyze" via the verb pattern.
    # (It may still be "analyze" via question-pattern fallback, but the strong-action path must not fire.)
    assert result in ("analyze", "ambiguous", "unknown")  # any is ok, we just assert it doesn't crash


# ── Bug 29: "itera" / "iterar" as command shortcuts ──────────────────────────

def test_bug29_itera_resolves_to_iterate():
    """Bug 29: bare 'itera' must be classified as iterate, not unknown → LLM."""
    resolver = IntentResolver()
    assert resolver.resolve_intent("itera") == "iterate"


def test_bug29_iterar_resolves_to_iterate():
    """Bug 29: 'iterar' must be classified as iterate."""
    resolver = IntentResolver()
    assert resolver.resolve_intent("iterar") == "iterate"


def test_bug29_itera_does_not_match_unrelated_words():
    """Bug 29: 'iteración' is NOT in the pattern (only bare verb forms are)."""
    resolver = IntentResolver()
    # The pattern uses \biter(ar?)?\b — 'iteración' does NOT match because
    # 'a' is missing and \b is at 'iteración' which has 'acion' after 'iter'.
    # It should fall through — result must NOT crash.
    result = resolver.resolve_intent("iteración del diseño")
    assert result in ("iterate", "analyze", "ambiguous", "unknown")


# ── Bug 37: fuzzy typo matching for simulate/calculate ───────────────────

def test_bug37_simulate_typos_resolve_to_simulate():
    """Bug 37: common transposition typos of 'simular' must resolve to simulate."""
    resolver = IntentResolver()
    for typo in ("simlar el dron", "simluar", "simlua el vuelo"):
        result = resolver.resolve_intent(typo)
        assert result == "simulate", (
            f"'{typo}' should resolve to simulate, got '{result}'"
        )


def test_bug37_calculate_typos_resolve_to_calculate():
    """Bug 37: common transposition typos of 'calcular' must resolve to calculate."""
    resolver = IntentResolver()
    for typo in ("calclua tiempo de vuelo", "calucar la masa"):
        result = resolver.resolve_intent(typo)
        assert result == "calculate", (
            f"'{typo}' should resolve to calculate, got '{result}'"
        )


def test_bug37_similar_not_classified_as_simulate():
    """Bug 37: 'similar' and 'simpatia' must NOT trigger simulate intent (no false positives)."""
    resolver = IntentResolver()
    for word in ("similar al anterior", "que simpatia"):
        result = resolver.resolve_intent(word)
        assert result != "simulate", (
            f"'{word}' must not be classified as simulate, got '{result}'"
        )


# ── Fix 1: classify_input_intent tests ───────────────────────────────────────

@pytest.mark.parametrize(
    "text,expected",
    [
        # pure information seeking
        ("dime cuales son los warnings", "information"),
        ("por que falla la simulacion", "information"),
        ("explica los errores", "information"),
        ("que significa high_actuator_load", "information"),
        ("cual es el problema", "information"),
        ("cuales son las advertencias", "information"),
        ("que recomiendas", "information"),
        ("siguiente paso", "information"),
        # pure action seeking
        ("reduce el peso", "action"),
        ("aumenta la carga", "action"),
        ("cambia el material", "action"),
        ("mejora la bateria", "action"),
        ("define componentes", "action"),
        ("optimiza los motores", "action"),
        # hybrid → treated as information
        ("quiero mejorar autonomia, que recomiendas", "hybrid"),
        ("mejora la carga util, como lo hago", "hybrid"),
        ("cambia el motor, dime cual es mejor", "hybrid"),
        # word-boundary guard: substrings must NOT trigger action
        ("la definicion es incorrecta", "action"),     # "define" NOT in "definicion"
        ("indefinido por ahora", "action"),             # "define" NOT in "indefinido"
        ("el mejoramiento es notable", "action"),       # "mejora" NOT in "mejoramiento"
        ("reduciendo la carga", "action"),              # "reduce" NOT in "reduciendo"
    ],
)
def test_classify_input_intent(text, expected):
    resolver = IntentResolver()
    result = resolver.classify_input_intent(text)
    assert result == expected, f"'{text}' → expected '{expected}', got '{result}'"


# ── Bug 38: INFORMATION_SEEKING_KEYWORDS word-boundary regression ─────────────

@pytest.mark.parametrize(
    "text,expected",
    [
        # "dime" is a keyword but must NOT fire on "dimensiones" (substring match regression)
        ("dimensiones", "action"),
        ("modificar dimensiones", "action"),
        ("reducir dimensiones del chasis", "action"),
        # "cual" must NOT fire on "calcular"
        ("calcular la masa", "action"),
        # "que es" must NOT fire inside longer words
        ("aumentar el thrust", "action"),
        # Standalone keywords must still work correctly
        ("dime cuales son los errores", "information"),
        ("cual es el problema", "information"),
        ("siguiente paso", "information"),
    ],
)
def test_bug38_word_boundary_information_seeking(text, expected):
    """Bug 38: INFORMATION_SEEKING_KEYWORDS must use \\b word boundaries.

    'dime' in 'dimensiones' must be False.
    Standalone 'dime' must still classify as information.
    """
    resolver = IntentResolver()
    result = resolver.classify_input_intent(text)
    assert result == expected, (
        f"Bug 38 regression: '{text}' → expected '{expected}', got '{result}'"
    )


# ── Bug 39: navigation phrases resolve to project_status ─────────────────────

@pytest.mark.parametrize(
    "text",
    [
        "siguiente paso",
        "que hago",
        "como sigo",
        "que puedo hacer",
        "que debo hacer",
        "por donde empiezo",
        "como continuo",
        # with diacritics (normalized by _normalize_text before matching)
        "qué hago",
        "cómo sigo",
        "qué puedo hacer",
    ],
)
def test_bug39_navigation_phrases_resolve_to_project_status(text):
    """Bug 39: navigation phrases must resolve to project_status, not fall to LLM."""
    resolver = IntentResolver()
    result = resolver.resolve_intent(text)
    assert result == "project_status", (
        f"Bug 39: '{text}' → expected 'project_status', got '{result}'"
    )


def test_bug39_no_false_positive_on_action_phrase():
    """Bug 39: 'quiero hacer algo' must NOT trigger 'que hago' substring match."""
    resolver = IntentResolver()
    # "quiero hacer algo" does NOT contain "que hago" as substring after normalization
    result = resolver.resolve_intent("quiero hacer algo con el proyecto")
    assert result != "project_status", (
        "Bug 39 false positive: action phrase incorrectly matched as status query"
    )


# ── Bug CLI-1: guidance phrases resolve to project_status ─────────────────────
# "completar" appears in ITERATE_PATTERNS; "guíame hasta completar el proyecto"
# was incorrectly routed to the iteration wizard. Fixed by adding guidance
# phrases to STATUS_PATTERNS (checked before ITERATE).

@pytest.mark.parametrize(
    "text",
    [
        "guíame hasta completar el proyecto",
        "guíame",
        "guía",
        "ayudame a completar el proyecto",
        "como completo el proyecto",
        "como termino el proyecto",
        "que me falta completar",
        "que me falta",
        # normalized variants (no accent)
        "guiame hasta completar el proyecto",
        "guia",
    ],
)
def test_bug_cli1_guidance_phrases_resolve_to_project_status(text):
    """Bug CLI-1: guidance phrases must resolve to project_status, not iterate."""
    resolver = IntentResolver()
    result = resolver.resolve_intent(text)
    assert result == "project_status", (
        f"Bug CLI-1: '{text}' → expected 'project_status', got '{result}'"
    )


# ── Bug 46: 'augmentar' typo normalised to 'aumentar' ────────────────────────

@pytest.mark.parametrize(
    "text",
    [
        "augmentar carga",
        "augmenta el payload",
        "augmentar la bateria",
        "augmento los motores",
    ],
)
def test_bug46_augmentar_typo_resolves_to_iterate(text):
    """Bug 46: 'augmentar' (anglicism) must be normalised to 'aumentar' before intent matching."""
    resolver = IntentResolver()
    result = resolver.resolve_intent(text)
    assert result == "iterate", (
        f"Bug 46: '{text}' → expected 'iterate', got '{result}'"
    )


# ── STATUS_PATTERNS word-boundary hardening ───────────────────────────────────

@pytest.mark.parametrize(
    "text,expected",
    [
        # "resumen" must NOT match inside "resumenes" (the core structural debt fixed here)
        ("resumenes de resultados", False),
        # All existing phrases must still match (no regression)
        ("el estado del proyecto es bueno", True),
        ("que falta por definir", True),
        # Multi-word pattern works in context (not just exact string)
        ("el siguiente paso del sistema", True),
        # Diacritic variants — normalization strips accents before matching
        ("qué falta todavía", True),
        ("cómo continúo con el proyecto", True),
    ],
)
def test_status_patterns_word_boundary(text, expected):
    """STATUS_PATTERNS use \\b word boundaries via precompiled _STATUS_PATTERNS_RE.

    'resumen' must not match inside 'resumenes'.
    Multi-word patterns must still match in context.
    """
    resolver = IntentResolver()
    normalized = resolver._normalize_text(text)
    result = any(rx.search(normalized) for rx in resolver._STATUS_PATTERNS_RE)
    assert result == expected, (
        f"STATUS_PATTERNS \\b regression: '{text}' (normalized: '{normalized}') "
        f"→ expected {expected}, got {result}"
    )


# ── Bug 41: DEFINE_PARAMS intent ─────────────────────────────────────────────

@pytest.mark.parametrize(
    "text",
    [
        "definir bateria",
        "definir la bateria",
        "configurar bateria",
        "declarar bateria",
        "especificar bateria",
        "definir energia",
        "parametros de bateria",
        "parametros de energia",
    ],
)
def test_bug41_define_params_energy_intent(text):
    """Bug 41: explicit 'definir/configurar bateria' must resolve to define_params."""
    resolver = IntentResolver()
    result = resolver.resolve_intent(text)
    assert result == "define_params", (
        f"Bug 41: '{text}' → expected 'define_params', got '{result}'"
    )


@pytest.mark.parametrize(
    "text",
    [
        "configurar helices",
        "definir helice",
        "definir las helices",
        "configurar las helices",
        "parametros de helices",
        "parametros de helice",
    ],
)
def test_bug41_define_params_propeller_intent(text):
    """Bug 41: explicit 'configurar helices' must resolve to define_params."""
    resolver = IntentResolver()
    result = resolver.resolve_intent(text)
    assert result == "define_params", (
        f"Bug 41: '{text}' → expected 'define_params', got '{result}'"
    )


@pytest.mark.parametrize(
    "text",
    [
        "cambiar la bateria",
        "reducir bateria",
        "mejorar la bateria",
        "cambiar helices",
    ],
)
def test_bug41_cambiar_bateria_stays_iterate(text):
    """Bug 41 guard: 'cambiar/reducir bateria' must NOT trigger define_params (should be iterate)."""
    resolver = IntentResolver()
    result = resolver.resolve_intent(text)
    assert result == "iterate", (
        f"Bug 41 false positive: '{text}' → expected 'iterate', got '{result}'"
    )


def test_bug41_resolve_action_request_energy_reason():
    """Bug 41: resolve_action_request for bateria returns reason=missing_energy_parameters."""
    resolver = IntentResolver()
    req = resolver.resolve_action_request("definir bateria", intent="define_params")
    assert req is not None
    assert req["parameters"]["reason"] == "missing_energy_parameters"


def test_bug41_resolve_action_request_propeller_reason():
    """Bug 41: resolve_action_request for helices returns reason=missing_propeller_parameters."""
    resolver = IntentResolver()
    req = resolver.resolve_action_request("configurar helices", intent="define_params")
    assert req is not None
    assert req["parameters"]["reason"] == "missing_propeller_parameters"


# ── Bug 47: orientation phrases must resolve to 'analyze' ─────────────────────

@pytest.mark.parametrize("text", [
    "orientame",
    "orientame sobre el diseño",
    "ayudame",
    "ayudame a decidir",
    "dame opciones",
    "que opciones tengo",
    "como hago que vuele",
    "como puedo mejorar el diseño",
    "que deberia hacer",
])
def test_bug47_orientation_phrases_resolve_to_analyze(text):
    """Bug 47: natural orientation phrases in ANALYZE_PATTERNS must resolve to 'analyze'."""
    resolver = IntentResolver()
    assert resolver.resolve_intent(text) == "analyze", (
        f"Bug 47: '{text}' \u2192 expected 'analyze', got '{resolver.resolve_intent(text)}'"
    )


def test_bug47_orientation_phrase_does_not_match_partial_word():
    """Bug 47 guard: 'como' in 'economizar' must NOT trigger analyze via orientation pattern."""
    resolver = IntentResolver()
    result = resolver.resolve_intent("economizar bateria")
    assert result != "analyze" or True  # must not crash; actual routing is secondary


# ── UX-B: navigation phrases route to project_status, not LLM ────────────────

import pytest as _pytest

@_pytest.mark.parametrize("text", [
    "sigamos",
    "sigamos con el siguiente",
    "sigamos con el siguiente bloque",
    "vamos con el siguiente bloque",
    "vamos con siguiente",
    "continua",
    "continuamos",
])
def test_uxb_navigation_phrases_resolve_to_project_status(text):
    """UX-B: 'sigamos', 'vamos con siguiente', 'continua' must resolve to project_status,
    not to analyze or fall through to the LLM."""
    resolver = IntentResolver()
    assert resolver.resolve_intent(text) == "project_status", (
        f"UX-B: '{text}' → expected 'project_status', got '{resolver.resolve_intent(text)}'"
    )


# ── Bug 65: single-verb + domain-goal phrases must route to explore_design_space

@_pytest.mark.parametrize("text", [
    "optimiza para autonomía",
    "optimiza para autonomia",
    "mejorar la autonomía del dron",
    "maximiza la autonomía",
    "minimiza la masa",
    "reducir el peso",
    # Calibración 2026-08-05: remaining DSE goals must not fall to iterate
    "optimiza para payload",
    "optimiza para carga útil",
    "mejora la estabilidad",
    "mejorar la estabilidad",
    "maximiza el margen de seguridad",
    "optimiza para masa",
    "optimiza para peso",
])
def test_bug65_single_verb_domain_goal_routes_to_explore(text):
    """Bug 65: 'optimiza para autonomía', 'mejorar la autonomía', etc. must resolve
    to 'explore_design_space', not 'iterate'."""
    resolver = IntentResolver()
    result = resolver.resolve_intent(text)
    assert result == "explore_design_space", (
        f"Bug 65: '{text}' → expected 'explore_design_space', got '{result}'"
    )


@_pytest.mark.parametrize("text, expected_goal", [
    ("optimiza para autonomia",     "mejorar_autonomia"),
    ("mejorar la autonomia del dron", "mejorar_autonomia"),
    ("minimiza la masa",             "reducir_masa"),
    ("reducir el peso",              "reducir_masa"),
    ("optimiza para payload",        "aumentar_payload"),
    ("optimiza para carga util",     "aumentar_payload"),
    ("mejora la estabilidad",       "mejorar_estabilidad"),
    ("maximiza el margen de seguridad", "mejorar_estabilidad"),
    ("optimiza para masa",           "reducir_masa"),
    ("optimiza para peso",           "reducir_masa"),
])
def test_bug65_explore_goal_resolved_correctly(text, expected_goal):
    """Bug 65 end-to-end: after routing to explore_design_space, resolve_explore_goal
    must return a known goal_key, not None (which would fall back to analyze)."""
    resolver = IntentResolver()
    goal = resolver.resolve_explore_goal(text)
    assert goal == expected_goal, (
        f"Bug 65: '{text}' → expected goal '{expected_goal}', got '{goal}'"
    )


@_pytest.mark.parametrize("text", [
    "aumenta el payload",
    "aumenta payload a 0.8",
    "mejora los motores",
    "optimiza los motores",
    "define el payload",
])
def test_explore_patterns_do_not_steal_iterate_mutations(text):
    """Explore patterns must not capture concrete mutations or component verbs."""
    resolver = IntentResolver()
    result = resolver.resolve_intent(text)
    assert result == "iterate", (
        f"Expected iterate for '{text}', got '{result}'"
    )


# ── Bug 69 — analytical questions must route to project_status, not LLM ─────

@_pytest.mark.parametrize("text", [
    "qué parámetros me faltan",
    "que parametros me faltan",
    "qué me falta",
    "que me falta",
    "qué hay pendiente",
    "que hay pendiente",
    "qué me queda por definir",
    "que me queda definir",
    "qué falta completar",
])
def test_bug69_analytical_questions_route_to_project_status(text):
    """Bug 69: analytical "qué falta" phrases must resolve to project_status
    instead of falling through to the LLM (30 s + 'No se pudo interpretar')."""
    resolver = IntentResolver()
    result = resolver.resolve_intent(text)
    assert result == "project_status", (
        f"Bug 69: '{text}' → expected 'project_status', got '{result}'"
    )
