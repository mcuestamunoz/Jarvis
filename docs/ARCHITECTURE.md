# Jarvis Architecture

> **Turn order, authority, and handoff status are now maintained in [`docs/system_map/`](system_map/README.md) (SYS-MAP-002)** — a navigable tree: master picture, a first-class `C-xxx` connection registry with evidence, an authority table, reference flows (`FLOW-001`…`007`), and per-subsystem module/function detail. This file remains the conceptual/narrative overview; update the system map first when routing or authority changes.
>
> **Target vision (to-be):** [`docs/ENGINEERING_READINESS_VISION.md`](ENGINEERING_READINESS_VISION.md) (engineering readiness / assembly-ready).  
> **Platform vision (to-be):** [`docs/PLATFORM_CAPABILITY_VISION.md`](PLATFORM_CAPABILITY_VISION.md) (skills / capabilities / physical systems — directional only).  
> Keep this file as as-is architecture; move only implemented/validated behavior here.

## Modelo conceptual del sistema

Jarvis transforma en tres pasos:

```text
Design intent (declarativo)
↓  component_resolver — bridge declarativo → físico
Physical parameters (computables)
↓  calculation_engine — modelo físico
Evaluation (simulación)
↓  simulator — evaluación de viabilidad
```

Este modelo es domain-agnostic: el mismo pipeline sirve para cualquier dominio físico.
Lo que cambia entre dominios es el vocabulario de `output_magnitude` y las reglas del `ComponentRuleRegistry`.
El núcleo (resolver, engine, simulator) no conoce el dominio.

## Visión General

Jarvis está estructurado como un motor de ingeniería por capas, no como un chatbot.

La idea central es separar claramente:

- interpretación de intención
- control del flujo
- memory ligera de decisiones explícitas
- mutación del diseño
- cálculo
- simulación
- sugerencias deterministas
- persistencia

Flujo conceptual actual:

```text
Arranque CLI
↓
_list_existing_projects → proyectos en disco
  ├─ ninguno → "Cuéntame qué quieres diseñar"
  └─ hay proyectos → mostrar lista + opción n/1/2...
       ├─ n → instrucción libre (loop normal)
  └─ 1..N / texto ordinal ("continuar", "el más reciente", "uno"...) → touch(state.json) + build_startup_context() [sin LLM]
       └─ Engineering Readiness (9 líneas + TOP GAPS, ERF-2) + Continuity (situation / evidence / next_useful_step)
Input de usuario
  │
  ├─ sesión activa (CREATE_PROJECT_INTERACTIVE)
  │     └─ interactive_session.answer(session, input)          [sin LLM]
  │           └─ confirmado → create_project → SYSTEM_DEFINITION
  │
  ├─ sesión activa (SYSTEM_DEFINITION)
  │     └─ system_definition_session.answer(input)             [sin LLM]
  │           └─ completado → stubs + system_priority → bridge → DEFINE_MISSING_PARAMETERS
  │
  ├─ sesión activa (DEFINE_MISSING_PARAMETERS)                 [sin LLM]
  │     ├─ soft-interrupt project_status / analyze
  │     ├─ FN-013/014/015: re-prompt bloque activo / help-define pendiente
  │     ├─ FN-016: "atrás"/"volver" → cancel (no valor)
  │     ├─ descripción de componente (+ Brief FN-018; bare size FN-019 si aplica)
  │     └─ param_definition_session.answer / component path
  │           └─ al completar último bloque → clear → IDLE (FN-021)
  │
  ├─ sesión activa (ITERATE_INTERACTIVE)
  │     ├─ classify_input_intent → "information" / "hybrid" → _handle_analyze
  │     └─ classify_input_intent → "action" → iterate_interactive_session.answer
  │
  ├─ IDLE — Acquisition Target (FN-014/015): "definir/declarar <bloque|componente>"
  │     └─ resolve_acquisition_mention → DEFINE_MISSING / Brief          [sin LLM]
  │
  ├─ intent_resolver: project_status / GUIDANCE
  │     ("estado…", "siguiente paso", "ayúdame con el siguiente paso" FN-023…)
  │     └─ build_startup_context() + Continuity                          [sin LLM]
  │
  ├─ intent_resolver: explore_design_space ("optimiza para autonomía"…)
  │     └─ _handle_explore → DesignExplorer                              [sin LLM]
  │
  ├─ intent_resolver: apply_exploration_result ("aplica la mejor"…)
  │     └─ _handle_apply_exploration → calculate → simulate → save       [sin LLM]
  │
  ├─ IDLE — Engineering Intent (FN-022): intención sin valor numérico
  │     ("aumentar el empuje", …) → is_engineering_intention
  │     └─ format_goal_plan + CTA (0 LLM; DSE solo si luego exploran)
  │
  ├─ intent_resolver: acción clara (calcular, simular, iterate con valor…)
  │     └─ ActionRequest local                                           [sin LLM]
  │
  ├─ intent_resolver: analyze (pregunta, "qué pasa si"…)
  │     └─ LLM (puede anteponer format_goal_plan si detect_goal)         [LLM]
  │
  └─ intent_resolver: ambiguous / unknown
        └─ LLM → JSON → ActionRequest → Mutation / Calculation / Simulation
```

> **Autoridad:** el estado del proyecto / Continuity / Acquisition Target eligen el *siguiente objetivo de ingeniería*. El LLM interpreta lenguaje; no inventa el gap pendiente. Sin Conversation Engine. Step D (Guided Engineering ampliado) y Create→BOM: fuera de este mapa hasta aprobación explícita — ver `docs/PROJECT_CONTINUITY.md` e `IMPLEMENTATION_TASKS.md`.

**Visor espacial (as-is):** `jarvis board` → `ui/spatial-board/` (`127.0.0.1:5173`). `workspace/spatial_board.project_spatial_nodes` proyecta `ProjectState` a cards (`component`/`part`/`slot`) y DTOs de visor (`geometry`, `declaredBoxPose`, `solidCopies` / `solidCopyOffsetsMm`). Solo lectura (GETs); mutación = CLI / writers / Continuity IDLE.

**Feature de producto — Continuity spatial assembly** (*situar el mapa*) — **checkpoint `v0.4.0` + patch `v0.4.1`:** envelopes tipados/citados + pose Continuity (origen = caja; multi-hop) + Main Plate assembly root + copias de visor (motores/hélices/brazos L-aware / adaptador en quad-X; standoffs ×4 en esquinas de Main Plate) + Board **Situar** (**C-113**: drag → mismo writer que `declara…`; free camera; plano pantalla). `mounted_on` guía relación, **no** milímetros. Screening AABB ≠ fit VERIFIED. El LLM no inventa cotas. SoT: [`.jes/artifacts/engineer_lock_continuity_spatial_assembly_feature.md`](../.jes/artifacts/engineer_lock_continuity_spatial_assembly_feature.md). Layout 2D de cards `{x,y,w,h}` = `localStorage` (no es pose).

**Craft montage honesty layer (2026-09-13→16, `v0.4.1` era):** estimated-temporary plate · Path F · layout pack · mount-standard · silhouette · fit-relations · disk-axial Visor · `library/fc`+`sensors` · block gate · mission payload identity · **disk-station reach** (`motors`↔`frame_arm` L vs wheelbase radius + human seal) · **user guide** [`USER_GUIDE_CRAFT_MONTAGE.md`](USER_GUIDE_CRAFT_MONTAGE.md). Suite **2968** · UI **105** at that point.

**Fase M — mission craft software, CLOSED (2026-09-16→18, tag `v0.4.2`):** `library/cameras/` (RunCam Phoenix 2) + `library/vtx/` (HGLRC Zeus 800) as full catalog families (pick → bind → `catalog_ref` + mass mirror → `cambiar`/`actualiza`, same ESC-shaped path as every other family) · mission Continuity ladder — identity → mass (`mission_payload_mass_kg`) → mount → autonomy target → power (`mission_accessory_power_w`, cameras/radio only — never invented from a VTX's RF milliwatts) → VTX → soft margin — see [`system_map/08_continuity/CONTINUITY_MAP.md`](system_map/08_continuity/CONTINUITY_MAP.md). Suite **3166** · UI **105** at M7.

**Pre–Fase C workshop, CLOSED (2026-09-18→20, tip tag `v0.4.3`):** docs/` truth-sync · Board **Taller 3D** (Grafo tab · inspector + cadena `mountedOn` → placa · chips) — [v0.4.3 note](../.jes/artifacts/engineer_note_v0_4_3_pre_fase_c_close.md). Suite **3166** · UI **132**. **PRIORIDAD:** Fase C @ **`0.5.0`** on first Engineer ★ Buy; physical plate-box/Path N/HD-* still parked. Queue: [`IMPLEMENTATION_TASKS.md`](IMPLEMENTATION_TASKS.md).

## Capas Del Sistema

### 1. Contratos y schemas

Los contratos viven en `schemas/`.

- `action_schema.py`
  Define acciones, modos del orquestador, drafts temporales y parámetros estructurados.
- `state_schema.py`
  Define el estado persistente del proyecto, `design_properties` y el estado temporal de runtime.
  Campos clave de `ProjectState`:
  - `current_parameters: dict` — parámetros de entrada del usuario (payload, motores, restricciones, material como etiqueta).
  - `design_properties: DesignProperties` — propiedades estructurales del diseño. `structure.density` y `structure.volume` son la **fuente canónica** de las propiedades físicas del material; `_build_mutable_state` las lee aquí con fallback a `current_parameters` para compatibilidad con estado antiguo.
  - `parsed_constraints: dict[str, float]` — restricciones parseadas a tipo. Clave actual: `autonomy_min` / `max_weight_kg`. Poblado automáticamente en carga vía `@model_validator` que extrae minutos/peso de la cadena libre `restrictions`/`objective`. **IC 1:** `restrictions_explicitly_none()` + `requirements_declared()` permiten `"no"` / `"ninguna"` como requisito satisfecho sin fabricar claves numéricas — `parsed_constraints` sigue `{}`. Mid-session: actualizar `current_parameters["restrictions"]` vía `ParamDefinitionSession` (G26) re-deriva `parsed_constraints` en cada save. El simulador recibe `autonomy_threshold: float | None` — nunca el string crudo.
- `tool_schema.py`
  Define `ToolResult`, `CalculationBundle` y el contrato rico de simulación.

Esto evita lógica difusa y fuerza entradas y salidas explícitas.

### 1a. Fase C en lenguaje llano — qué significa “scaffold” / “andamiaje”

Esta sección es la **lectura humana** de §§1b–1d. El detalle normativo de cada Buy sigue abajo; aquí el significado.

**Scaffold (andamiaje) Python** = estructura mínima en el monorepo (carpetas, tipos, APIs, tests) para **organizar** la plataforma de operación **sin** entregar aún el software que hace volar el vehículo.

Analogía: el plano de una casa marca “aquí irá la cocina”; aún no hay fregadero ni electricidad. Jarvis tiene ya los **nombres y las puertas**; no tiene el **flight controller de producción**.

| Idea | En Jarvis hoy |
|---|---|
| Plano / etiquetas | Paquetes `capabilities/`, `flight_software/`, `vehicle_profiles/` bajo `src/jarvis/` |
| Sensor de mentira para probar el plano | `SimulatedImuHal` (números inventados, repetibles) |
| Portero que no deja pasar a nadie | `RejectAllSafetyGate` — Safety siempre `reject` |
| Órdenes escritas en un papel, nunca ejecutadas | `propose_command` / `submit_command` → `not_attempted` |
| FC / firmware real (rápido, cerca del hardware) | **C++ — futuro IC**; no está en estos `.py` |

**Dos dimensiones (no confundir):**

1. **Craft** (`core/`, Continuity, Board, `library/`) — diseñar el vehículo (BOM, montaje, física). SoT de diseño @ tip craft `v0.4.3`.  
2. **Platform / Fase C** — operar sistemas físicos algún día. Hoy solo andamiaje. **Tip git tagged:** `v0.5.33` (C35 denser `step` tests CLOSED; not flying). C34 `probe_rx` CLOSED (not gyro). **Next visor:** Taller CSS cuboid faces IC READY. See [process lock after C6](../.jes/artifacts/engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) · [bench note](../.jes/artifacts/engineer_note_fase_c_bench_before_silicon_2026_09_24.md).

**Qué hace cada zona de archivos (mapa mental):**

| Carpeta / archivo | En una frase |
|---|---|
| `capabilities/schemas.py` + `registry.py` | Lista tipada de “qué podría hacer la plataforma”; hoy **vacía** a propósito |
| `capabilities/intent.py` | Papelito “alguien pidió X”; solo terminal rellena uno de verdad |
| `capabilities/safety.py` | El portero; hoy rechaza todo |
| `flight_software/flight_control/types.py` | Formato de una lectura IMU (dato, no hardware) |
| `flight_software/flight_control/hal.py` | Contrato: “un sensor debe poder `read_imu()`” |
| `flight_software/flight_control/sim_imu_hal.py` | IMU falso para tests |
| `flight_software/autonomy/types.py` | Catálogo de verbos HOLD/LAND/… |
| `flight_software/autonomy/surface.py` | Pedir un verbo y pasarlo por el portero (siempre no) |
| `vehicle_profiles/` | Perfil de humo de tests: “este vehículo espera el peldaño HAL+IMU” |
| `capabilities/radio.py` (si está en el árbol) | Radio **simulada** dual Intent\|Authority — **no** es ELRS real; pendiente formalizar ACCEPT |

**Frase a memorizar:** *Scaffold Python ≠ el dron ya vuela.* Nadie arma, nadie escribe PWM, nadie decodifica ELRS real en estos paquetes. Cuando deje de ser scaffold, un IC lo dirá explícitamente.

Visión / briefing: [`PLATFORM_CAPABILITY_VISION.md`](PLATFORM_CAPABILITY_VISION.md) · [briefing Fase C](../.jes/artifacts/engineer_briefing_fase_c_global_context.md).

### 1b. `capabilities/` — Fase C · C1+C2+C5 scaffold (registry + Intent/Safety/Radio stubs, no runtime)

`src/jarvis/capabilities/` (`B1-fase-c-capability-registry-scaffold`, package `0.5.0`) define los contratos tipados `CapabilityRecord` / `ProviderRecord` / `SkillRecord` (Pydantic) y un `CapabilityRegistry` con API de solo-consulta (`.capabilities()`, `.providers()`, `.get_capability(id)`, `.providers_offering(id)`, `.load_default()`). **Es un scaffold, no un runtime**: `load_default()` devuelve siempre un registro vacío (0/0/0), el enum `availability` solo admite `stub`/`not_implemented` en C1 (nunca `available`), y no existe ningún método o campo `execute`/`dispatch`/`command_esc` en todo el paquete. No toca Continuity, el orquestador, el Board ni `library/` — el SoT de craft sigue siendo la superficie `v0.4.3`.

**C2** (`B1-fase-c-intent-safety-stub`, package sigue `0.5.0`) añade `intent.py` y `safety.py` al mismo paquete. `intent.py` define `Intent`/`Task` y cuatro adaptadores de canal (`terminal`/`voice`/`radio`/`api`) — **solo `TerminalIntentAdapter.parse(texto)` construye un `Intent` real**; `Voice`/`Radio`/`Api` siempre lanzan `NotImplementedError` con `"not_implemented"` en el mensaje, nunca producen una "intención de vuelo exitosa". `safety.py` define `SafetyGate` (Protocol), `SafetyRequest`/`SafetyDecision`/`AuthoritySignal`, y `default_safety_gate()` — la **única** fábrica de gate en `src/`, que siempre devuelve `RejectAllSafetyGate` (outcome `reject`, reason `"not_implemented"`). **No existe `AllowAllSafetyGate` en `src/`.** `run_intent_through_safety(intent, gate)` es la única función-puente y termina siempre en `gate.evaluate(...)` — no hay ningún paso de "ejecución" después.

**Scaffold @ 0.5.0 ≠ Flight Software entregado**: un runtime vivo de vehículo/dispositivo, decodificación **real** ELRS/CRSF, y cualquier camino Intent→actuador quedan para ICs futuras. El dual-role radio tipado (C5) está en §1e @ `v0.5.3`. Ver [`PLATFORM_CAPABILITY_VISION.md`](PLATFORM_CAPABILITY_VISION.md) §13, el [C1 report](../.jes/artifacts/implementation_report_fase_c_capability_registry_scaffold_b1.md) y el [C2 report](../.jes/artifacts/implementation_report_fase_c_intent_safety_stub_b1.md).

### 1c. `flight_software/` + `vehicle_profiles/` — Fase C · C3 (primer peldaño, solo sensado)

**Enmienda del Engineer (sobre el IC C3, no lo sustituye): Python scaffold / sim only — production flight_control runtime is C++ (future IC).** Todo lo que esta Buy escribe bajo `flight_software/` y `vehicle_profiles/` es andamiaje de plataforma en Python (contratos, `SimulatedImuHal`, smoke de perfil) — **no** es el flight controller de producción. El runtime/firmware de `flight_control` real será C++, en Buys posteriores con su propio IC (path/build TBD ahí). Esta Buy **no** crea árbol C++ ni CMake en ningún sitio del repo — verificado por `tests/test_fase_c_first_fc_rung_b1.py::test_no_cpp_or_cmake_tree_created`.

`src/jarvis/flight_software/` y `src/jarvis/vehicle_profiles/` (`B1-fase-c-first-fc-rung`, package `0.5.1`) existen **en disco por primera vez** desde esta Buy — C0/C1/C2 lo tenían explícitamente prohibido hasta ahora. `flight_software/flight_control/` trae `ImuHal` (Protocol de solo-lectura: `read_imu() -> ImuSample`), `SimulatedImuHal` (muestras sintéticas deterministas por `seed`, sin bus real, sin red) e `ImuSample` (`t_s`/`accel_mps2`/`gyro_rad_s`, sin campo de actuador). **No** hay estimación de estado, control de actitud/rate/posición, mezclador, ni ESC/PWM — nada de eso existe en este paquete todavía (ver el segundo peldaño de filtrado más abajo, C6). `vehicle_profiles/` trae `VehicleProfile` (mínimo: `id`/`vehicle_class`/`rung`/`notes`) y un único perfil de humo `smoke_quad_hal_imu` (`rung="hal_imu"`) + `run_hal_imu_smoke()` — no ligado a ningún workspace/BOM/SKU de catálogo craft.

**Separación de nombres (honestidad crítica):** el `flight_controller` del catálogo craft (`library/flight_controller/`, identidad BOM) y `flight_software.flight_control` (este paquete, la columna de control de la clase de vehículo) son sistemas de verdad distintos y **nunca deben confundirse** — ver el docstring de `flight_software/__init__.py`.

`default_safety_gate()` sigue siendo `RejectAllSafetyGate` sin cambios; sensar/leer el IMU no requiere `allow` (no es actuación). No se tocó `orchestrator.py`, el Board, ni `library/`. **Peldaño stub @ 0.5.1 ≠ vuelo controlado**: estimación/control/mezclador/ESC quedan para ICs futuras. Ver [`PLATFORM_CAPABILITY_VISION.md`](PLATFORM_CAPABILITY_VISION.md) §13 y el [implementation report](../.jes/artifacts/implementation_report_fase_c_first_fc_rung_b1.md).

**C6** (`B1-fase-c-imu-filtering-rung`, **ACCEPT CLOSED** @ tag **`v0.5.4`**) añade el **segundo** peldaño de `flight_control/`: `filter.py` trae `ImuLowPassFilter` — media móvil exponencial (EMA) de primer orden, determinista, parámetro `alpha` (por defecto `0.2`, rechaza valores fuera de `(0, 1]`), aplicada eje-a-eje sobre `accel_mps2`/`gyro_rad_s`. `filter_sample(raw: ImuSample) -> ImuSample` **reutiliza** `ImuSample` de C3 sin tipo paralelo; la primera muestra tras construir o `reset()` siembra el filtro sin suavizar. **Esto es post-proceso de sensado, no estimación**: no hay cuaternión, ángulos de Euler, ni salida tipo Madgwick/Mahony/EKF — eso pertenece a un peldaño de estimación futuro y separado. `read_filtered(hal, filt)` encadena `SimulatedImuHal.read_imu()` con el filtro; `vehicle_profiles.run_hal_imu_filter_smoke()` es el camino de humo visible en pytest. No se creó `flight_software/estimation/`. **Peldaño de filtrado @ 0.5.4 ≠ actitud / ≠ vuelo controlado**. Ver [review](../.jes/artifacts/implementation_review_fase_c_imu_filtering_rung_b1.md) · [report](../.jes/artifacts/implementation_report_fase_c_imu_filtering_rung_b1.md). Después de C6: [process lock](../.jes/artifacts/engineer_note_fase_c_process_lock_after_c6_2026_09_20.md).

**C7** (`B1-fase-c-attitude-estimation-rung`, **ACCEPT CLOSED** @ tag **`v0.5.5`**) añade el **tercer** peldaño de `flight_control/`: `attitude.py` trae `ComplementaryAttitudeEstimator` — integración giroscópica fusionada con la inclinación derivada del acelerómetro mediante una corrección proporcional de ángulo pequeño, parámetro `gain` (por defecto `0.02`, rechaza valores fuera de `(0, 1]`). **Un único algoritmo** — explícitamente **no** es Mahony/Madgwick/EKF/UKF/MEKF por nombre (sin término de sesgo/integral, sin descenso de gradiente, sin covarianza). `update(sample: ImuSample) -> AttitudeState` emite un cuaternión unitario `(w, x, y, z)` que mapea cuerpo → marco mundo **`enu`** (bloqueado) más la tasa angular del cuerpo. **Corte duro**: sin magnetómetro, sin GPS/baro, sin aprendizaje online de sesgo de giroscopio, sin posición/velocidad — el yaw solo se integra por giroscopio, sin referencia absoluta. Reutiliza `ImuLowPassFilter`/`ImuSample` de C6/C3 directamente, sin reimplementar el EMA dentro del estimador. `read_attitude(hal, filt, estimator)` y `vehicle_profiles.run_hal_imu_attitude_smoke()` son los caminos de pipeline/humo (reutilizan el perfil `smoke_quad_hal_imu` existente, sin cambio de esquema). **Limitación honesta del simulador**: `SimulatedImuHal` no es consciente de la actitud — siempre emite gravedad en dirección fija, así que la corrección del test de nivelación se valida con secuencias `ImuSample` sintéticas de inclinación conocida, no solo vía el HAL simulado compartido. No se creó `flight_software/estimation/`. **Peldaño de actitud @ 0.5.5 ≠ actitud verificada en vuelo / ≠ vuelo controlado**: controlador, mezclador y ESC quedan para ICs futuras, cada uno su propio frente. Ver [implementation report](../.jes/artifacts/implementation_report_fase_c_attitude_estimation_rung_b1.md).

**C8** (`B1-fase-c-attitude-controller-rung`, **ACCEPT CLOSED** @ tag **`v0.5.6`**) añade el **cuarto** peldaño de `flight_control/`: `controller.py` trae `PdAttitudeController` — `omega_cmd = kp * e_rot - kd * omega_measured`, donde `e_rot` es el vector de rotación de ángulo pequeño en el marco del cuerpo desde la estimación C7 hacia un `AttitudeSetpoint` (extraído de la cuaternión de error de camino más corto), y `omega_measured` es `AttitudeState.omega_body_rad_s`. `kp` (por defecto `6.0`) debe ser `> 0`; `kd` (por defecto `0.6`) debe ser `>= 0`; ambos finitos. **Un único controlador** — sin PID de tasa en cascada, sin LQR, MPC, ni INDI. `compute(setpoint, state) -> BodyRateCommand` — la salida es **solo un número de velocidad angular del cuerpo**: sin empuje de motor, sin matriz de mezclador, sin PWM/ESC, sin canal de empuje colectivo, sin lazo de posición/velocidad. No conectado a C4: `AutonomyVerb.HOLD` nunca se enruta automáticamente aquí, y este módulo nunca llama a `submit_command`. `level_setpoint(t_s)` es un cuaternión identidad para tests/humo, sin ninguna afirmación sobre empuje de hover. **Peldaño de controlador @ 0.5.6 ≠ volar / ≠ comandos de motor**. Ver [implementation report](../.jes/artifacts/implementation_report_fase_c_attitude_controller_rung_b1.md).

**C9** (`B1-fase-c-mixer-rung`, **ACCEPT CLOSED** @ tag **`v0.5.7`**) añade el **quinto** peldaño de `flight_control/`: `mixer.py` trae `QuadXMixer` — matriz de asignación lineal fija para **un único layout documentado, quadrotor-X** (motores `0..3` = FR/FL/RL/RR, a 45° de los ejes del cuerpo). `mix(collective, rates: BodyRateCommand) -> MotorForceCommand` recorta `collective` a `[0, 1]` y emite cuatro fuerzas de motor normalizadas, también recortadas a `[0, 1]`. **Simplificación honesta y documentada explícitamente**: `BodyRateCommand.omega_body_rad_s` de C8 es una tasa corporal, no un par (torque) real — este mezclador B1 la trata directamente como los canales de mezcla roll/pitch/yaw para enseñar la geometría de asignación, sin afirmar que tasa ≡ par físicamente y sin inventar un segundo controlador para salvar esa brecha. `roll_scale`/`pitch_scale`/`yaw_scale` (por defecto `0.05` cada uno) deben ser finitos y `>= 0`. No conectado a C4: sin auto-enrutado de `AutonomyVerb.HOLD`. **Peldaño de mezclador @ 0.5.7 ≠ ESC / ≠ volar**: sin PWM, DShot, UART de ESC, ni GPIO en ningún sitio, y sin afirmación de que ningún motor gire. Ver [implementation report](../.jes/artifacts/implementation_report_fase_c_mixer_rung_b1.md).

**C10** (`B1-fase-c-esc-pwm-stub-rung`, **ACCEPT CLOSED** @ tag **`v0.5.8`**) añade el **sexto** peldaño de `flight_control/`: `esc.py` trae `encode_motor_forces(forces, *, min_us=1000, max_us=2000) -> EscPwmCommand` — mapa lineal de cada fuerza de motor de C9 a un ancho de pulso PWM en microsegundos (`force=0 → min_us`, `force=1 → max_us`; `min_us`/`max_us` deben ser finitos con `min_us < max_us`). **Una única codificación** — PWM clásico en µs; sin DShot/Oneshot/Multishot como producto embarcado en esta Buy. `SimulatedEscSink` registra el `EscPwmCommand` resultante **solo en memoria** (`armed` empieza en `False`; `apply(cmd)` siempre registra el comando pero solo reporta `applied=True` mientras esté armado — sin I/O de `RPi.GPIO`/`pigpio`/serial/socket en ningún sitio). No conectado a C4. **Peldaño ESC/PWM @ 0.5.8 ≠ ESC de hardware / ≠ volar**: armar es solo una bandera en memoria; no existe ningún pin, puerto, ni socket, y no se afirma que ningún motor gire. Ver [implementation report](../.jes/artifacts/implementation_report_fase_c_esc_pwm_stub_rung_b1.md).

**C11** (`B1-fase-c-controlled-flight-sim-tip`, **ACCEPT CLOSED** @ tag **`v0.5.9`**) cierra el **tip de la escalera de madera** de C0 §7: `plant.py` trae `ToyQuadAttitudePlant` — dinámica de actitud pura, juguete, explícitamente **no física de producto**, que avanza desde `MotorForceCommand` (fuerzas de C9, **no** PWM) y emite el siguiente `ImuSample` **consistente con su propia actitud verdadera** — cerrando C3→C10 en un lazo cerrado real. `run_controlled_flight_sim_smoke()` demuestra recuperación medible: desde una inclinación inicial documentada de 15°, el error real de inclinación baja de 2° en 200 pasos; `run_open_loop_baseline_smoke()` muestra que el mismo plant sin corrección se mantiene constante en 15° (sin enderezamiento pasivo), probando que el lazo hace trabajo real. **Rate ≠ torque sigue abierto**: el mezclador de C9 sigue tratando la tasa de cuerpo como su canal de mezcla, y este plant no inserta silenciosamente un controlador rate→torque para ocultarlo — usa su propio mapa juguete fuerza→aceleración angular, documentado por separado.

**También corregido, revelado (no el alcance principal de esta Buy, pero necesario para que su propio criterio de aceptación sea honestamente alcanzable):** un bug de signo real en el `ComplementaryAttitudeEstimator` de C7 (etiquetado `v0.5.5`, ACCEPT CLOSED) — el orden de argumentos del producto cruzado en su corrección por acelerómetro estaba invertido, haciendo que la estimación convergiera **alejándose** de la inclinación real para cualquier entrada no nivelada (confirmado incluso a 0.1°). Ningún test previo de C7 alimentó nunca un acelerómetro no nivelado, así que nunca se ejerció este camino. Corrección de una línea (orden de argumentos intercambiado) más un nuevo test de regresión en el propio archivo de tests de C7. Ver [implementation report](../.jes/artifacts/implementation_report_fase_c_controlled_flight_sim_tip_b1.md) para la prueba completa antes/después.

**Tip de lazo cerrado simulado ≠ volar / ≠ vuelo verificado en hardware / ≠ simulación físicamente precisa**: es una demostración juguete de que la escalera de software se cierra sobre sí misma en simulación; ningún motor gira, ningún vehículo real existe.

**C12** (`B1-fase-c-rate-torque-bridge`, **ACCEPT CLOSED** @ tag **`v0.5.10`**) **cierra el hueco rate ≠ torque** que C9/C11 dejaron abierto deliberadamente: `rate_torque.py` trae `LinearRateTorqueBridge.convert(rates: BodyRateCommand) -> BodyTorqueCommand` — **un único mapa feedforward** (`tau_i = gain_i * omega_cmd_i` por eje, ganancia escalar o por eje, cada una finita y `> 0`) — **no** un PID de tasa en cascada (sin término `kp * (omega_cmd - omega_medido)`, sin estado integral/derivativo en ningún sitio). `BodyTorqueCommand.tau_body` es explícitamente **normalizado/adimensional, tipo par**, nunca reclamado como Newton-metros de un vehículo real. `QuadXMixer.mix(collective, torques: BodyTorqueCommand)` está **migrado** — ya no acepta un `BodyRateCommand` sin envolver en absoluto, sin API dual silenciosa (verificado: pasar una tasa directamente lanza `AttributeError`, no una interpretación silenciosa incorrecta). El tip de lazo cerrado de C11 se re-verificó a través del puente y quedó sin cambios (`15° → 0.252°` en 200 pasos, idéntico a antes de la migración) — **no hizo falta reajustar ninguna ganancia**, porque la ganancia por defecto del puente (`1.0`) es un no-op matemático respecto al paso directo anterior del mezclador. Ver [implementation report](../.jes/artifacts/implementation_report_fase_c_rate_torque_bridge_b1.md).

**Puente ≠ producto de lazo de tasa / ≠ N·m físicos / ≠ volar**: ahora existe un paso nombrado y explícito en vez de una suposición implícita rate-como-torque; nada aquí reclama unidades de par reales, un lazo de tasa cerrado en hardware, ni vuelo.

**C13** (`B1-fase-c-cpp-flight-control-scaffold`, **ACCEPT CLOSED** @ tag **`v0.5.11`**) abre el **primer scaffold C++ material** de `flight_control`: **`native/flight_control/`** — árbol C++17, **solo host**, construido con CMake ≥ 3.16, fuera de `src/jarvis/` (ruta bloqueada por el IC). Refleja la escalera de madera Python módulo a módulo (`filter`/`attitude`/`controller`/`rate_torque`/`mixer`/`plant`), incorporando desde el primer día la corrección de signo de C11 Amendment A, y trae un ejecutable `fc_closed_loop_smoke` que corre el mismo tip de lazo cerrado: partiendo de 15° de inclinación, el error real se recupera a **0.252°** en 200 pasos — mismo resultado numérico que la escalera Python, porque ambas portan las mismas fórmulas, aunque la identidad bit a bit no era requisito del IC (solo que el error disminuya y se recupere). Sin GPIO/pigpio/`/dev/mem`/serial/DShot/socket en ningún sitio del árbol (verificado por grep), sin PX4/ArduPilot vendorizado, sin flasheo de MCU ni bring-up de placa en esta Buy. `flight_software/` en Python queda **intacto salvo un puntero en su docstring** — sigue siendo la guía de diseño y la plataforma del craft; nada aquí lo reemplaza. Ver [implementation report](../.jes/artifacts/implementation_report_fase_c_cpp_flight_control_scaffold_b1.md).

**Scaffold C++ ≠ volar / ≠ controlador de vuelo de hardware / ≠ firmware en ninguna placa / ≠ reemplazo del craft SoT Python**: es una build de escritorio que prueba la misma escalera algorítmica en un segundo lenguaje, nada más.

**C14** (`B1-fase-c-cpp-esc-pwm-stub`, package/tag **`v0.5.12`**, **★ ACCEPT CLOSED**) cierra la **paridad de peldaño** que faltaba en el árbol C++: `esc.hpp`/`esc.cpp` portan `encode_motor_forces`/`SimulatedEscSink` de Python C10 — mismo mapa lineal fuerza→PWM-µs (`force=0 → min_us`, `force=1 → max_us`, `1000`–`2000` por defecto, `min_us < max_us` obligatorio) y el mismo sink en memoria (`armed` empieza `false`; `apply(cmd)` siempre registra el comando pero solo reporta `applied=true` armado, `applied=false`/`reason="disarmed"` si no). Un ejecutable **separado** `fc_esc_pwm_smoke` (18 comprobaciones, todas en verde) mantiene el smoke del tip de C13 enfocado — `fc_closed_loop_smoke` se re-ejecutó y quedó **idéntico**: `15° → 0.252°` en 200 pasos, sin cambios. Sin GPIO/pigpio/`/dev/mem`/serial/DShot/Oneshot/Multishot/socket en ningún sitio de las fuentes nuevas (verificado por grep). Python `esc.py` queda intacto — re-verificado con los mismos valores antes/después. Ver [implementation report](../.jes/artifacts/implementation_report_fase_c_cpp_esc_pwm_stub_b1.md).

**ESC C++ ≠ escritura de hardware / ≠ ESC en línea / ≠ motores girando**: esto cierra la paridad de módulos del árbol C++ con la escalera de madera Python (filter/attitude/controller/rate_torque/mixer/esc, más el tip del plant); nada aquí escribe a un ESC real ni afirma que una hélice gira.

**C15** (`B1-fase-c-cpp-unit-tests`, package/tag **`v0.5.13`**, **★ ACCEPT CLOSED**) **profundiza la verificación host en C++**: framework real — **Catch2 v3, fijado al tag de release `v3.7.1`** (commit `fa43b77429ba76c462b1898d6cd2f2d7a9416b14`), traído vía `FetchContent` de CMake (red necesaria una sola vez al primer configure; sin red después) — más **26 `TEST_CASE` / ~494 asserts**, al menos uno por peldaño de acero (filter, attitude, controller, rate_torque, mixer, esc) bajo `native/flight_control/tests/`. `ctest` corre ahora **28 entradas**: los 26 casos unitarios (descubiertos individualmente vía `catch_discover_tests`) más los dos smokes existentes, todo en verde. **Congelación de comportamiento respetada al pie de la letra**: `git diff --stat` en cada fuente de peldaño ya existente (`filter.cpp`…`esc.cpp`/`plant.cpp`/todas las cabeceras) queda vacío — esta Buy solo añadió cobertura, no se expuso ningún bug, así que no hizo falta parar a preguntar al Engineer. Los dos smokes quedan intactos; `fc_closed_loop_smoke` se re-verificó idéntico (`15° → 0.252°`). Ver [implementation report](../.jes/artifacts/implementation_report_fase_c_cpp_unit_tests_b1.md).

**Tests C++ ≠ volar / ≠ verificación MCU / ≠ producción endurecida / ≠ cambio de algoritmo**: una corrida `ctest` de escritorio con un framework real en vez de dos mains de smoke a mano, nada más; la matemática de los peldaños no cambió.

**C16** (`B1-fase-c-cpp-mcu-cross-compile`, package/tag **`v0.5.14`**, **★ ACCEPT CLOSED**) trae el **primer scaffold de cross-compile a MCU**: `native/flight_control/cmake/toolchains/arm-none-eabi.cmake` — `CMAKE_SYSTEM_NAME Generic`, Cortex-M4 genérico (`-mcpu=cortex-m4 -mthumb -mfloat-abi=soft`, sin afirmar silicio de ninguna placa concreta) — y un build aparte (`build/flight_control_mcu`) que produce **solo** `libjarvis_fc.a` para ese triple, con la puerta puesta en CMake (sin `#ifdef` en las fuentes de peldaño) para que Catch2/el binario de tests/ambos smokes nunca se construyan en el camino MCU. Se realizó y verificó una **compilación cruzada real**: `arm-none-eabi-objdump` confirma `file format elf32-littlearm, architecture: armv7e-m` sobre el archivo producido — código objetivo genuino, no un fallback nativo silencioso. **Se encontró y reveló un problema real de completitud del toolchain**: la fórmula Homebrew `arm-none-eabi-gcc` a secas no trae `newlib`/`libstdc++` y falla al compilar `<optional>`; la build que funcionó usó el release xPack `arm-none-eabi-gcc` v15.2.1-1.1 (trae libstdc++ C++17 completo) — ambos desenlaces (toolchain completo vs. incompleto) quedan ejercitados por el nuevo wrapper de pytest, que se salta con una pista de instalación concreta en vez de fallar duro cuando el compilador está presente pero incompleto. El host se re-verificó intacto: `ctest` sigue 28/28 en verde. **Sin** flasheo, **sin** GPIO, **sin** BSP/SDK de fabricante (STM32Cube/CMSIS/ChibiOS/FreeRTOS/PX4/ArduPilot, todos ausentes). Ver [implementation report](../.jes/artifacts/implementation_report_fase_c_cpp_mcu_cross_compile_b1.md).

**Cross-compile a MCU ≠ flasheado / ≠ volar / ≠ firmware corriendo en un controlador de vuelo / ≠ verificado por GPIO**: una prueba en tiempo de compilación de que las fuentes de la escalera de acero compilan freestanding para un target clase Cortex-M4, nada más; ninguna placa ha corrido este código.

**C17** (`B1-fase-c-safety-real-policy`, package/tag **`v0.5.15`**, **★ ACCEPT CLOSED**) trae el **primer portero Safety real**: `ArmedAllowlistSafetyGate` en `src/jarvis/capabilities/safety.py` — **opt-in**, empieza **desarmado** (siempre rechaza, razón `"disarmed"`) y, una vez `arm()`ado a propósito, permite **solo** `HOLD` y `LAND` (parseados de la forma `autonomy:{verb}:{id}` que `submit_command` ya construye); cualquier otro verbo, o un `action_id` malformado, también se rechaza (`"verb_not_allowed"` / `"unparseable_action_id"` — ninguno reutiliza el `"not_implemented"` de `RejectAllSafetyGate`). **`default_safety_gate()` queda intacto byte a byte** — confirmado por `git diff`, cero líneas tocadas en `RejectAllSafetyGate` ni en la factory; el default de producto sigue siendo "rechazar todo." `evaluate()` nunca lee `authority_signal_id` — Authority (C5) sigue siendo solo trazabilidad, incapaz de voltear una decisión en este o cualquier otro gate. La rama `allow` de `submit_command`, inalcanzable en código embarcado desde C4, ya resolvía a `execution="not_implemented"` — esta Buy no necesitó tocar `flight_software/autonomy/surface.py`/`types.py` para cumplir "allow ≠ execute"; verificado en runtime vía `typing.get_args(ExecutionState) == {"not_attempted", "not_implemented"}`. Un `smoke_policy_gate_hold_and_land()` delgado demuestra el camino armado de punta a punta. Sin `AllowAllSafetyGate`, sin acople a `SimulatedEscSink`/GPIO, sin cableado craft/CLI. Ver [implementation report](../.jes/artifacts/implementation_report_fase_c_safety_real_policy_b1.md).

**Allow de política ≠ volar / ≠ autonomía ejecutada / ≠ Safety de hardware / ≠ "seguro para volar"**: ahora existe un gate de software real, opt-in y de alcance estrecho junto al default RejectAll sin cambios; nada aquí despacha a ningún actuador, y ningún gate embarcado en `src/` puede devolver jamás `execution="executed"`.

**C18** (`B1-fase-c-cpp-mcu-freestanding-elf`, package/tag **`v0.5.16`**, **★ ACCEPT CLOSED**) trae el **primer `.elf` freestanding enlazado**: `native/flight_control/mcu/` — script de linker Cortex-M4 genérico (`FLASH` en `0x00000000` / `RAM` en `0x20000000`, las regiones Code/SRAM genéricas de la arquitectura ARM, no la dirección de arranque remapeada de ningún fabricante; tamaños ilustrativos de 256 KiB/64 KiB, explícitamente ficticios) + tabla de vectores ARMv7-M de 16 entradas + `Reset_Handler` + stubs mínimos de syscalls de newlib (`_sbrk`/`_write`/`_exit`/… — sin semihosting, sin I/O real) + un punto de entrada delgado que **enlaza `jarvis_fc`** — reutilizando sin cambios el toolchain de C16 — en un único ELF ARM inspectable, `fc_mcu_stub.elf`. Se realizó y verificó un **enlace real**: `readelf -h` muestra `Machine: ARM`, `Type: EXEC`, un entry point real, ABI de punto flotante soft; `nm` confirma que `jarvis::fc::ImuLowPassFilter::filter_sample` y `encode_motor_forces` quedan enlazados como símbolos definidos (no solo referenciados). **Las excepciones de C++ se mantuvieron activas** (IC §0 decisión 8, opción (a)) — los `throw std::invalid_argument(...)` de las fuentes de peldaño quedan intactos; el runtime de C++ se resuelve enlazando contra el libstdc++/newlib propio del toolchain más los stubs de syscalls de esta Buy, no desactivando excepciones. **Se encontró y reveló un hueco real del sistema de build**: las fuentes `.c` de startup/syscalls nunca se compilaban en silencio (`project()` solo CXX) hasta añadir C como lenguaje del proyecto — antes del arreglo el linker avisaba `cannot find entry symbol Reset_Handler`; después, el aviso desaparece y el entry point es correcto. El host se re-verificó intacto: `ctest` sigue 28/28 en verde. **Sin** flasheo, **sin** BSP de fabricante, **sin** afirmar que arranca en una FC real. Ver [implementation report](../.jes/artifacts/implementation_report_fase_c_cpp_mcu_freestanding_elf_b1.md).

**`.elf` freestanding ≠ flasheado / ≠ arranca en hardware / ≠ motores / ≠ GPIO**: un ejecutable ARM enlazado, inspectable, solo de escritorio, que prueba que toda la cadena (startup, script de linker, stubs de syscalls, runtime de C++, código real de `jarvis_fc`) encaja, nada más; esta imagen nunca ha corrido en ninguna placa.

**C19** (`B1-fase-c-crsf-link-stub`, package/tag **`v0.5.17`**, **★ ACCEPT CLOSED**) — ver §1f arriba para el detalle completo. Resumen: `crsf_stub.py` nuevo, separado de `radio.py`; parsea envelope CRSF + CRC8 + RC_CHANNELS_PACKED + LINK_STATISTICS desde fixtures; cero I/O; `RadioIntentAdapter`/Safety/craft/`native/` todos sin cambios. Ver [implementation report](../.jes/artifacts/implementation_report_fase_c_crsf_link_stub_b1.md).

**CRSF de fixture ≠ ELRS en vivo ≠ link de piloto ≠ producto driver CRSF**: parsear bytes, nada más.

**C20** (`B1-fase-c-crsf-dual-role-bridge`, package/tag **`v0.5.18`**, **★ ACCEPT CLOSED**) — ver §1g arriba para el detalle completo. Resumen: `crsf_dual_role.py` nuevo, tercer módulo separado de `radio.py`; puentea RC channels decodificados hacia `RadioStubFrame`/Authority bajo política canal-aux→`kill`; Authority sigue sin poder abrir Safety (probado explícitamente); `radio.py`/`intent.py`/`safety.py` todos sin cambios. Ver [implementation report](../.jes/artifacts/implementation_report_fase_c_crsf_dual_role_bridge_b1.md).

**Puente CRSF ≠ ELRS en vivo ≠ link de piloto ≠ Safety allow**: un mapa determinista y documentado de bytes ya decodificados a un frame dual-role tipado, nada más.

**C21** (`B1-fase-c-crsf-byte-stream`, package/tag **`v0.5.19`**, **★ ACCEPT CLOSED**) — ver §1h arriba para el detalle completo. Resumen: `crsf_stream.py` nuevo, cuarto módulo separado de `radio.py`; `CrsfByteStreamAssembler` reensambla frames CRSF desde bytes en chunks arbitrarios llamando al `parse_crsf_frame` de C19 sin cambios (sin segunda implementación de CRC); espera en ventanas incompletas, descarta-y-resincroniza un byte en ventanas completas inválidas, nunca propaga `CrsfParseError`; helper opcional reutiliza el `ingest_rc_channels` de C20 sin cambios. `radio.py`/`crsf_stub.py`/`crsf_dual_role.py`/`intent.py`/`safety.py` todos sin cambios. Ver [implementation review](../.jes/artifacts/implementation_review_fase_c_crsf_byte_stream_b1.md).

**Ensamblador de stream ≠ UART abierto ≠ ELRS en vivo ≠ link de piloto ≠ Safety allow**: un buffer puro en memoria que prueba que bytes entregados en chunks se reensamblan en los mismos frames que C19 ya parsea desde un buffer completo, nada más.

**C22** (`B1-fase-c-crsf-host-serial`, package/tag **`v0.5.20`**, **★ ACCEPT CLOSED**) — ver §1i arriba para el detalle completo. Resumen: `crsf_serial.py` nuevo, quinto módulo separado de `radio.py`; `CrsfHostSerialIngress` extrae bytes de un FD/ruta y alimenta el ensamblador de C21 sin cambios; toda la suite de tests usa un `pty` POSIX, sin RX físico requerido; sin `pyserial`, sin baud 420000 configurado (diferido). `radio.py`/`crsf_stub.py`/`crsf_dual_role.py`/`crsf_stream.py`/`intent.py`/`safety.py` todos sin cambios. Ver [implementation review](../.jes/artifacts/implementation_review_fase_c_crsf_host_serial_b1.md).

**Ingest serial de host ≠ ELRS en vivo ≠ RX conectado ≠ driver UART ≠ Safety allow**: un lector basado en pull de un FD/ruta, verificado enteramente vía loopback `pty`, nada más.

**C23** (`B1-fase-c-crsf-host-baud`, package/tag **`v0.5.21`**, **★ ACCEPT CLOSED**) — ver §1i arriba para el detalle completo. Resumen: extiende `crsf_serial.py` (sin sexto módulo) con `configure_host_baud`/`configure_baud` opt-in — Darwin `IOSSIOSPEED` **420000** derivado + raw 8N1; falla cerrado fuera de Darwin; sin `pyserial`; probado enteramente con `fcntl.ioctl` simulado, más un caso sin simular contra un `pty` que se espera que falle (no es un UART). `attach_fd`/`attach_path` siguen sin auto-configurar baud; C22 re-verificado sin cambios de comportamiento. Ver [implementation review](../.jes/artifacts/implementation_review_fase_c_crsf_host_baud_b1.md).

**Baud de host 420000 ≠ ELRS en vivo ≠ RX conectado ≠ driver UART ≠ Safety allow**: Darwin puede configurarse al ritmo típico de ELRS en un FD ya adjunto, probado sin hardware vía ioctl simulado, nada más.

**C24** (`B1-fase-c-control-loop-tick`, package/tag **`v0.5.22`**, **★ ACCEPT CLOSED**) extrae el **tick de control con nombre**: `loop.py` trae `FlightControlLoop.step(sample, setpoint, collective) -> ControlTickResult` — exactamente el cuerpo que C11/C13 ya corrían **inlined** (`filter_sample -> estimator.update -> controller.compute -> bridge.convert -> mixer.mix`), ahora con un nombre, sin ninguna matemática nueva: cada peldaño existente (C6-C10/C12) se llama, nunca se reimplementa. `ControlTickResult` agrupa la muestra filtrada, el `AttitudeState`, el `BodyRateCommand`, el `BodyTorqueCommand`, el `MotorForceCommand` y un `EscPwmCommand` (codificado con `encode_motor_forces` de C10, solo para visibilidad — `SimulatedEscSink.apply` nunca se llama dentro de `step`). **`step` no llama al plant, no lee un HAL real, ni escribe un pin** — quien llama sigue pasando su propio `ImuSample` y consumiendo `MotorForceCommand` fuera, exactamente como antes de la extracción (`plant.step(result.forces, dt)` sigue en el `for` del llamador). **Sin `dt`** como argumento (el estimador/controlador siguen derivando su propio tiempo de `ImuSample.t_s`, sin ISR de 1 kHz en esta Buy) y **sin RC** (`AttitudeSetpoint`/`collective` son argumentos planos; mapear sticks a ellos es C25). El twin C++ — `native/flight_control/include/jarvis/fc/loop.hpp` + `src/loop.cpp`, añadido a `jarvis_fc` — replica el mismo orden con las mismas clases existentes (`filter.hpp`…`esc.hpp`), sin cabecera/CMake nuevos fuera de ese árbol. `run_controlled_flight_sim_smoke` (C11, Python) y `fc_closed_loop_smoke` (C13, C++) quedan **refactorizados para llamar a `step`** en vez de tener la cadena inlined — verificado bit-a-bit idéntico al comportamiento pre-refactor: `15° → 0.252°` en 200 pasos, sin retocar ninguna ganancia. `mcu/stub_main.cpp` sigue **sin** `ControlLoop`/llamada a `step` — ningún `Reset_Handler` corre este tick. `radio.py`/`crsf_*.py`/`intent.py`/`safety.py`/`autonomy/` todos sin cambios (`git diff --stat` vacío). Ver [implementation review](../.jes/artifacts/implementation_review_fase_c_control_loop_tick_b1.md).

**Tick de control con nombre ≠ volar ≠ ISR de MCU ≠ motores ≠ sticks de RC**: un ciclo nombrado, IMU+consigna+collective → fuerzas de motor, reutilizando C6-C12/C13 sin cambios; el plant, el pin de ESC y el mapeo de RC siguen siendo cola futura.

**C25** (`B1-fase-c-rc-setpoint`, package/tag **`v0.5.23`**, **★ ACCEPT CLOSED**) trae el **primer mapa de canales RC ya decodificados hacia los argumentos de `step`**: `rc_setpoint.py` trae `map_rc_to_loop_inputs(channels, *, t_s) -> RcLoopInputs` — un mapa AETR ilustrativo (no un modelo de ningún TX real): `RC_CH_ROLL`/`RC_CH_PITCH`/`RC_CH_THROTTLE` = índices `0`/`1`/`2`; el canal de yaw (índice `3` convencional en AETR) queda **sin usar** esta Buy (C7 no tiene magnetómetro, así que no hay referencia absoluta de rumbo que un stick de yaw pudiera comandar honestamente). `CRSF_CH_MIN`/`CRSF_CH_MID`/`CRSF_CH_MAX` = `172`/`992`/`1811` (la misma convención ilustrativa de 11 bits ya usada alrededor de la política de C20). El throttle se mapea linealmente a `collective ∈ [0, 1]`, recortado — el mid-stick (`992`) da **≈0.5003, no exactamente 0.5** (los extremos no son perfectamente simétricos alrededor de 992), documentado sin redondear. Roll/pitch se miden como deflexión desde 992, escalada para alcanzar exactamente `RC_MAX_TILT_RAD` (`π/6`, 30°) en cada extremo, recortada más allá de ese límite, y compuesta en `q_body_to_world_desired` vía la fórmula estándar de Euler-a-cuaternión 3-2-1 (yaw-pitch-roll) con yaw fijo en `0`. El twin C++ — `native/flight_control/include/jarvis/fc/rc_setpoint.hpp` + `src/rc_setpoint.cpp`, añadido a `jarvis_fc` — replica los mismos umbrales y la misma fórmula, pero usando `std::vector<int>` en vez de un tipo `CrsfRcChannels` (ese árbol no porta tipos CRSF; el lock de C21-C23 de **cero menciones a CRSF/ELRS bajo `native/`** se mantiene, incluso en comentarios — las constantes se llaman `kRcChMin`/`kRcChMid`/`kRcChMax`, sin el prefijo del protocolo). Un helper opcional `step_with_rc(loop, sample, channels)` mapea y luego llama a `FlightControlLoop.step` de C24 sin tocar su matemática (`git diff --stat` en `loop.py`/`loop.hpp`/`loop.cpp` queda vacío) — nunca llama al plant, a `SimulatedEscSink`, ni a `SafetyGate.evaluate`. La política `CrsfDualRolePolicy` de C20 (aux → Authority `kill`) queda intacta y no se importa desde este módulo. `radio.py` sigue sin API de sticks (lock T5 de C5). Ver [implementation report](../.jes/artifacts/implementation_review_fase_c_rc_setpoint_b1.md).

**RC→consigna ≠ volar ≠ sticks mueven motores ≠ Safety allow ≠ heading lock**: un mapa determinista y documentado de unidades de canal ya decodificadas hacia los dos argumentos que `step` ya aceptaba; ningún piloto vuela nada, ningún motor gira, y el yaw stick no implica ningún heading-hold (no existe).

**C26** (`B1-fase-c-esc-output-hal`, package/tag **`v0.5.24`**, **★ ACCEPT CLOSED**) **nombra el puerto de salida ESC** que C10/C14 ya implementaban como un sink concreto: `esc.py`/`esc.hpp` ganan `EscOutput` — Python `abc.ABC`, C++ base abstracta con destructor virtual — con `apply_forces(forces: MotorForceCommand) -> EscApplyResult` más `arm()`/`disarm()`/`armed` (misma semántica que C10). `SimulatedEscSink` **es-un** `EscOutput` en ambos lenguajes; su `apply(EscPwmCommand)` de C10 y su comportamiento de armado quedan **byte-idénticos** — `apply_forces` es un envoltorio delgado: `encode_motor_forces(forces)` y luego `self.apply(cmd)`/`apply(encode_motor_forces(forces))`. El diff en `esc.cpp` es **puramente aditivo** (verificado línea a línea: cero líneas eliminadas/cambiadas, solo 4 líneas nuevas) y `esc.py`/`esc.hpp` son los **únicos** archivos de peldaño tocados — `filter`/`attitude`/`controller`/`rate_torque`/`mixer`/`plant` quedan intactos (`git diff --stat` vacío). **El mixer sigue hablando solo fuerzas** — `mixer.py`/`mixer.hpp` no ganan conocimiento de PWM/DShot/pines (grep-verificado en código real, sin contar el docstring que ya lista esos términos como ausentes). **`step` sigue sin llamar** a `apply`/`apply_forces`/`SimulatedEscSink` — `loop.py`/`loop.hpp`/`loop.cpp` quedan byte-idénticos, re-verificado explícitamente en este Buy. **Solo una implementación embarcada** (`SimulatedEscSink`) — ningún sink GPIO, ninguna clase de pin sin implementar, ningún DShot esta Buy. Ver [implementation report](../.jes/artifacts/implementation_review_fase_c_esc_output_hal_b1.md).

**EscOutput HAL ≠ pin ≠ motores ≠ DShot**: existe un puerto nombrado; el sink simulado lo implementa; el mixer sigue sin saber el protocolo de cable. Nada aquí es un motor en un cable, un stream DShot, ni `step` actuando.

**C28** (`B1-fase-c-mcu-uart-hal-stub`, package/tag **`v0.5.26`**, **★ ACCEPT CLOSED**) **nombra el puerto UART del lado MCU**: `native/flight_control/include/jarvis/fc/uart.hpp` + `src/uart.cpp` traen `UartBytePort` — base abstracta con destructor virtual, `read(dst, n)`/`write(src, n)`, ninguno de los dos bloquea ni lanza en un puerto lleno/vacío — y `LoopbackUart`, la **única** implementación: una FIFO en memoria (capacidad por defecto `256`). Escribir más allá de la capacidad restante **recorta el conteo aceptado** (short write) en vez de crecer sin límite o sobrescribir bytes ya encolados — política elegida y probada, no accidental. **Cero registros USART, cero CMSIS, cero `IOSSIOSPEED`/`termios`, cero IRQ/DMA** en ningún sitio de estos dos archivos — grep-verificado en código real. `mcu/stub_main.cpp` sigue **sin** referenciar `UartBytePort`/`LoopbackUart` — ningún bucle de sondeo UART se añadió a `Reset_Handler`/`main` esta Buy; el `.elf` sigue enlazando con el toolchain ARM cuando está presente. `capabilities/crsf_serial.py` (host Mac, C22/C23) queda **byte-idéntico** — este Buy es exclusivamente C++ del árbol MCU, sin driver UART en Python. El lock de C21-C27 de **cero menciones a CRSF/ELRS bajo `native/`**, incluso en comentarios, se mantiene — re-verificado con grep en todo el árbol (grep proactivo en el header nuevo; el ID de esta Buy no contiene tokens de protocolo, no hizo falta reescribir). Ver [implementation review](../.jes/artifacts/implementation_review_fase_c_mcu_uart_hal_stub_b1.md).

**Stub UART de MCU ≠ USART de chip ≠ baud de Darwin ≠ ELRS en vivo**: existe un puerto de bytes nombrado; un loopback en memoria lo implementa. Nada aquí es un USART que habla con un receptor, ni el `IOSSIOSPEED` del Mac trasladado al chip, ni ELRS corriendo en el MCU.

**C29 B0** (`B0-fase-c-silicon-cited-flash-map`, investigación, **★ ACCEPT CLOSED**, sin tag) concluyó **park-until-named**: nadie había nombrado un MCU concreto todavía, así que el informe no reescribió el linker y recomendó esperar. El 2026-09-24 el Engineer nombró el hardware de mesa (stack **HGLRC F460 6S V1**, FC **HGLRC F405 8S V1**, línea MCU **STM32F405** impresa en el manual) — el disparador de "un MCU nombrado" que el B0 exigía — abriendo **C29 B1**.

**C29 B1** (`B1-fase-c-silicon-cited-flash-map`, package/tag **`v0.5.27`**, **★ ACCEPT CLOSED**) reemplaza la ficción de C18 en `mcu/linker_cortex_m4.ld` por el mapa **citado**: `FLASH` `1024K` en `0x08000000`, `RAM` `128K` en `0x20000000` (SRAM1+SRAM2 contiguas), tomado de **ST RM0090 Tabla 3** (STM32F405xx/07xx, "Memory map") — no del manual HGLRC (que nombra la línea MCU pero no imprime ORIGIN/LENGTH). La CCM (`0x10000000`, 64 KiB según RM0090) queda **fuera** de este bloque `MEMORY` a propósito — meterla en una región RAM plana sería su propia simplificación no revelada. El comentario de honestidad del linker cita explícitamente la identidad de mesa (HGLRC) y la fuente del mapa (RM0090), y el residual disclosed: el manual HGLRC no imprime el sufijo de order-code (RG vs VG) del STM32F405, pero la Tabla 3 de RM0090 aplica igual a toda la línea xx/07xx sin depender de ese sufijo. `mcu/stub_main.cpp` queda **byte-idéntico** — re-enlazado y verificado (`readelf -l` confirma `VirtAddr 0x08000000`, `Entry point 0x8000045`) pero sin ningún periférico nuevo tocado. `cmake/toolchains/arm-none-eabi.cmake` (flags C16) también queda **byte-idéntico** — el ABI `-mfloat-abi=soft` no cambia esta Buy. Sin CMSIS, sin STM32Cube, sin OpenOCD/J-Link en ningún archivo tocado. Ver [implementation review](../.jes/artifacts/implementation_review_fase_c_silicon_cited_flash_map_b1.md).

**Mapa FLASH citado ≠ flasheado ≠ arranca en la FC ≠ Betaflight HGLRCF405V2**: el linker ahora usa las direcciones que ST publica para este MCU, pero eso sigue siendo un hecho de compilación/enlace en el Mac, no una afirmación sobre la stack HGLRC.

**C30** (`B1-fase-c-mcu-flash-observable`, package/tag **`v0.5.28`**, **★ ACCEPT CLOSED**; LED **not observed** on desk) cierra los **dos** residuales que C29 B1 dejó sin corregir en código: (a) **idle silencioso** — `stub_main` corría el one-shot de `jarvis_fc` y luego un `while (true)` vacío, así que un `Reset_Handler` exitoso se veía igual que una placa muerta; (b) **N1 de CMake** — `-T` es un flag del linker, no una dependencia implícita de CMake, así que un `.ld` editado no forzaba un re-enlace (el T9 de C29 que borraba el `.elf` primero era un *workaround* de test, no el arreglo real). **(a)** se cierra con `mcu/hello_led.h`/`hello_led.c` — dos funciones (`hello_led_init`/`hello_led_spin`, MMIO `volatile` puro, sin CMSIS, sin HAL) que togglan **PC13**, citado del target unificado de Betaflight para esta FC (`HGLR-HGLRCF405V2.config`, línea `resource LED 1 C13`) — deliberadamente **no** PA8 (en ese mismo target V2, `resource MOTOR 6 A08`, un pin de timer de motor) ni PB1 (`LED_STRIP`, LEDs de cable, no el LED de estado). Las direcciones MMIO (`RCC_AHB1ENR` `0x40023830` bit 2, `GPIOC_MODER`/`GPIOC_BSRR` en `0x40020800`/`0x40020818`) están citadas de **RM0090**, transcritas a mano. El busy-wait entre toggles es explícitamente **sin calibrar** — "parpadeo visible a HSI 16 MHz de reset", nunca un periodo en milisegundos afirmado; sin PLL/HSE/`SystemInit`. **(b)** se cierra con `set_property(TARGET fc_mcu_stub.elf APPEND PROPERTY LINK_DEPENDS .../linker_cortex_m4.ld)` en `CMakeLists.txt` — verificado tocando el `.ld` y reconstruyendo **sin borrar** el `.elf` anterior: el mtime del `.elf` avanza, confirmando un re-enlace real. Un paso `POST_BUILD` con `arm-none-eabi-objcopy -O binary` produce `fc_mcu_stub.bin` (dirección de carga `0x08000000`, sin cambios respecto al mapa de C29) para **USB DFU** — documentado en el README de este árbol junto con el procedimiento de restauración (reflashear el target **HGLRCF405V2** desde Betaflight Configurator) y la advertencia de hélices/batería. `uart.hpp`/`crsf_serial.py` quedan **byte-idénticos**; `startup_cortex_m4.c`/`syscalls_stub.c`/el toolchain de C16 también. Sin NVIC/EXTI/IRQ/DMA, sin escritura a pines de motor. Ver [implementation review](../.jes/artifacts/implementation_review_fase_c_mcu_flash_observable_b1.md).

**LED flasheable ≠ LED visto en mesa ≠ volar ≠ DShot ≠ USART en vivo ≠ Betaflight HGLRCF405V2**: existe una imagen DFU cuyo idle togglea PC13; CMake re-enlaza si cambia el `.ld`. **No se flasheó en mesa** en el Buy.

**C31** (`B1-fase-c-dshot-encode-stub`, package/tag **`v0.5.29`**, **★ ACCEPT CLOSED**) nombra la **trama DShot de 16 bits** que el ESC de mesa (HGLRC 60A 6S, Bluejay, DShot150/300/600) algún día querrá: `src/jarvis/flight_software/flight_control/dshot.py` + `native/flight_control/include/jarvis/fc/dshot.hpp`/`src/dshot.cpp` traen `encode_dshot_frame(throttle, telemetry=False) -> uint16` — `value = (throttle << 1) | telemetry`, `checksum = (value ^ (value>>4) ^ (value>>8)) & 0xF`, `frame = (value << 4) | checksum`, `throttle` entero `[0, 2047]` obligatorio (fuera de rango lanza error tipado). **Vectores verificados en ambos lenguajes**: `throttle=0 → 0x0000`, `throttle=48 → 0x0606`, `throttle=2047 → 0xFFEE`. **Rango especial documentado, no implementado**: `0..47` son comandos DShot (beep, 3D, etc.) según el protocolo — este módulo codifica el campo de 11 bits tal cual se le pasa, sin tabla de comandos. Un helper opcional `encode_motor_forces_dshot(forces) -> 4× uint16` mapea fuerza `[0,1]` linealmente a throttle **`48..2047`** (nunca `0..2047` — el `0` colisionaría con el rango de comandos) — camino **paralelo**, no sustituye a `encode_motor_forces` (PWM-µs, C10/C14) ni a `EscOutput`/`SimulatedEscSink` (C26), que siguen exactamente igual (`git diff --stat` vacío, re-verificado explícitamente). `mcu/hello_led.h`/`hello_led.c`/`stub_main.cpp` (C30) quedan **byte-idénticos** — el idle sigue siendo PC13, no DShot. DShot150/300/600 aparece solo como nombre de protocolo citado en comentarios, nunca como periodo de timer o tasa de toggle GPIO — no existe temporización de ningún tipo en este módulo. Un test pre-existente de C13 (`test_t4_no_gpio_or_hardware_io_symbols_in_native_tree`) usaba "dshot" como token prohibido genérico desde antes de que existiera ningún código DShot legítimo en el árbol — se retargeteó, con exclusión explícita y documentada solo para los tres archivos que C31 autoriza, manteniendo el resto de la protección (incluido GPIO) intacta en esos mismos archivos y en todos los demás. Ver [implementation review](../.jes/artifacts/implementation_review_fase_c_dshot_encode_stub_b1.md).

**DShot encode ≠ pin ≠ motores ≠ volar**: existe un paquete DShot de 16 bits calculado en software. Nada aquí hace que un ESC vea una forma de onda.

**C32** (`B1-fase-c-mcu-spi-hal-stub`, package/tag **`v0.5.30`**, **★ ACCEPT CLOSED**) nombra el **puerto SPI del lado MCU**, mismo patrón que C28 con UART: `native/flight_control/include/jarvis/fc/spi.hpp`/`src/spi.cpp` traen `SpiBytePort` — base abstracta con destructor virtual, `transfer(tx, rx, n) -> size_t` (copia hasta `n` bytes de TX a RX, en orden, nunca bloquea) — y `LoopbackSpi`, la **única** implementación: RX = TX, capacidad por defecto `256`, una transferencia más allá de esa capacidad **recorta el conteo aceptado** (short count) en vez de crecer sin límite, la misma política de `LoopbackUart` (C28). A diferencia del FIFO persistente de `LoopbackUart`, `LoopbackSpi` **no guarda estado entre llamadas** — una transferencia SPI real es un intercambio síncrono único, no un stream asíncrono, así que no hace falta cola. **Cero registros SPI, cero CMSIS, cero GPIO de chip-select/NSS, cero IRQ/DMA** en ningún sitio de estos dos archivos — grep-verificado en código real. El gyro de la FC de mesa (cuando se cablee más adelante) es un **ICM42688P** sobre SPI — citado únicamente como identidad de mesa en el comentario de honestidad de `spi.hpp`, nunca en código real: sin lectura de `WHO_AM_I`, sin mapa de registros, sin muestra en ningún sitio de este Buy. `dshot.hpp`/`dshot.cpp`/`dshot.py` (C31), `hello_led.h`/`hello_led.c`/`stub_main.cpp` (C30) y `uart.hpp`/`uart.cpp` (C28) quedan **byte-idénticos** — el idle sigue siendo solo PC13, sin sondeo SPI en `main`. `SimulatedImuHal` (C3, Python) tampoco se toca — este Buy es exclusivamente C++ del árbol MCU. Ver [implementation review](../.jes/artifacts/implementation_review_fase_c_mcu_spi_hal_stub_b1.md).

**Stub SPI de MCU ≠ SPI de chip ≠ gyro en vivo ≠ volar**: existe un puerto de bytes SPI nombrado; un loopback en memoria lo implementa. Nada aquí lee el ICM42688P, nada abre un bus SPI de silicio, nada mete DShot en un pin.

**C33** (`B1-fase-c-spi-scripted-slave`, package/tag **`v0.5.31`**, **★ ACCEPT CLOSED**) añade una **segunda** implementación de `SpiBytePort`: `ScriptedSpi`. `LoopbackSpi` (C32) sólo hace eco de lo que se le envía; un dispositivo real contesta con **sus propios** bytes, independientes del TX. `ScriptedSpi` rellena RX desde un **script de bytes pregrabado** (`canned_rx`) en vez de desde TX — así es como un test simula "un dispositivo contestó" sin ningún chip real; TX nunca se inspecciona ni tiene que coincidir con nada. Cada llamada a `transfer(...)` rellena RX desde el **inicio** del script actualmente cargado (respuesta fija, no un stream que se consume entre llamadas) — `set_next_rx(...)` es la única forma de reprogramar lo que devuelven las siguientes transferencias. Si el script es más corto que `n`, la transferencia devuelve ese conteo más corto (misma política "rechaza el exceso" que `LoopbackSpi`) y la cola no tocada de `rx` queda exactamente como la pasó el llamador. `LoopbackSpi` queda **sin cambios de comportamiento** (RX = TX sigue igual), ambas viven en los mismos `spi.hpp`/`src/spi.cpp` existentes — sin archivo nuevo, sin registro nuevo en CMake. `WHO_AM_I`/`ICM42688P` aparecen solo en comentarios (p. ej. "a future gyro test could load 0x47 here"), nunca en código real — grep-verificado. `stub_main.cpp`, `hello_led.h`/`hello_led.c` (C30), `dshot.hpp`/`dshot.cpp`/`dshot.py` (C31) y `uart.hpp`/`uart.cpp` (C28) quedan **byte-idénticos**. Ver [implementation review](../.jes/artifacts/implementation_review_fase_c_spi_scripted_slave_b1.md).

**SPI scripted ≠ gyro en vivo ≠ SPI de chip ≠ volar**: existe un doble de test con RX pregrabado. Nada aquí lee un dispositivo real.

**C34** (`B1-fase-c-spi-scripted-gyro-probe`, package/tag **`v0.5.32`**, **★ ACCEPT CLOSED**) añade el primer **cliente** de `SpiBytePort`: `probe_rx`. C33 le dio al puerto una forma de mentir con bytes (`ScriptedSpi`, RX pregrabado); este Buy es la otra mitad — un llamador que pide `n` bytes al puerto y copia de vuelta lo que la implementación **actual** devuelva. `native/flight_control/include/jarvis/fc/spi_probe.hpp`/`src/spi_probe.cpp` (archivos **nuevos**, no plegados en `ScriptedSpi`) traen `probe_rx(SpiBytePort& port, uint8_t* rx, size_t n) -> size_t` — envía `n` bytes de TX **dummy, todos cero** (nunca una dirección de registro), luego `port.transfer(dummy_tx, rx, n)`, y devuelve ese conteo; `n==0` → `0`. `spi.hpp`/`spi.cpp` (C32/C33) quedan con **cero ediciones** — el puerto sigue siendo el puerto, `spi_probe.*` es el primer llamador. Sobre `ScriptedSpi` cargado con un byte fixture placeholder, `probe_rx` devuelve ese byte — prueba el camino RX de punta a punta; sobre `LoopbackSpi`, `probe_rx` devuelve ceros (el TX dummy hace eco) — prueba que el cliente está tipado al puerto, no atado a una sola implementación. Misma política de conteo corto que el puerto: si el script es más corto que `n`, cuenta corto y cola de `rx` sin tocar. **Cero registros SPI, cero CMSIS, cero GPIO CS/NSS, cero IRQ/DMA, cero CRSF/ELRS** en todo `native/`. `WHO_AM_I`/`ICM42688P`/dirección de registro `0x75` no aparecen en ningún sitio de `spi_probe.*`, ni siquiera en comentario — el byte fixture vive solo en tests, nunca en código de librería (grep-verificado, más estricto que la regla de comentario-OK de C33). `stub_main.cpp`, `hello_led.h`/`hello_led.c` (C30), `dshot.hpp`/`dshot.cpp`/`dshot.py` (C31), `uart.hpp`/`uart.cpp` (C28) y `loop.hpp`/`loop.cpp`/`loop.py` (C3/C4) quedan **byte-idénticos** — sin sondeo del probe en `main`, sin IMU metida en `step`. Ver [implementation review](../.jes/artifacts/implementation_review_fase_c_spi_scripted_gyro_probe_b1.md).

**Scripted gyro probe ≠ gyro en vivo ≠ SPI de chip ≠ WHO_AM_I ≠ volar**: existe una función que pide bytes al puerto; los tests pueden precargar esos bytes. Nada aquí lee el ICM42688P ni abre un bus SPI real.

**C35** (`B1-fase-c-step-failsafe-hold-ticks`, package/tag **`v0.5.33`**, **★ ACCEPT CLOSED**) es un Buy de **solo tests**: encadena lo que C24/C27 ya *permiten* pero no *encadenaban*. **Cero código de producción tocado** — `loop.py`/`loop.hpp`/`loop.cpp`, `rc_hold.hpp`/`rc_hold.cpp`, `crsf_failsafe.py` y `spi_probe.hpp`/`spi_probe.cpp` (C34) quedan **byte-idénticos**. Tests (Python + 4 casos Catch2 en `test_loop.cpp`): **1000** ticks de `step()` con un `ImuSample` de lata en nivel (`accel ≈ (0,0,-9.81)`, giro cero) y sin plant — cada tick, las cuatro fuerzas de motor son finitas y están en `[0, 1]`. Un watch **stale** (nunca notado, o pasado el timeout de 0.5 s) alimenta `failsafe_loop_inputs(t)` hacia ese mismo `step()` — el `collective` que entra es **0**. "Hold" significa seguir pasando `level_setpoint`, no que `AutonomyVerb.HOLD` llegue a ejecutarse. `probe_rx` (C34) **no** se usa como IMU. Ver [implementation review](../.jes/artifacts/implementation_review_fase_c_step_failsafe_hold_ticks_b1.md).

**Muchos ticks ≠ volar ≠ 6-DoF. Failsafe → step ≠ motores cortados ≠ HOLD ejecutado**: existen tests que llaman `step()` mil veces y que meten las entradas de failsafe en ese mismo `step()`. Nada aquí es una planta que vuela, un corte de motor, o un comando de autonomía ejecutado. **Siguiente visor:** Taller CSS cuboide [`B1-geometry-taller-css-cuboid-faces`](../.jes/artifacts/implementation_contract_geometry_taller_css_cuboid_faces_b1.md). Cola: puntos standoff. Parked hasta banco: DShot *wire* · USART on-chip · C30 desk DFU — ver el [process lock](../.jes/artifacts/engineer_note_fase_c_process_lock_after_c6_2026_09_20.md).

### 1d. `flight_software/autonomy/` — Fase C · C4 (superficie de comandos, sin autonomía viva)

**Misma disciplina de andamiaje del Engineer: "Python scaffold / sim only — production flight_control runtime is C++ (future IC)."** `src/jarvis/flight_software/autonomy/` (`B1-fase-c-autonomy-surface`) trae `AutonomyVerb` (`TAKEOFF`/`HOLD`/`GO_TO`/`FOLLOW`/`RETURN_HOME`/`LAND`/`PATROL`), `AutonomyCommand` (dato puro, sin campo de actuador) y `AutonomySubmissionResult`. `propose_command()` es un constructor puro que no llama a Safety; `submit_command(command, gate)` **siempre** llama primero a `SafetyGate.evaluate(...)` — con el único gate embarcado (`RejectAllSafetyGate`), el resultado es siempre `outcome="reject"` / `execution="not_attempted"`, probado end-to-end para `HOLD` y `LAND`. Incluso con un gate-falso local-de-test que devuelva `allow`, `execution` nunca puede ser `"executed"` — resuelve a `"not_implemented"` porque no existe ningún actuador en el paquete. No existe `flight_software/autonomy/executor.py`. No se amplió el peldaño IMU de C3, no cambió `CapabilityRegistry.load_default()` (sigue vacío), y cero imports desde `orchestrator.py`/`adapters/`.

**Superficie de comandos ≠ autonomía volable**: nada aquí sostiene, aterriza, despega, navega, ni actúa. **ACCEPT CLOSED** con C5 en un solo bloque @ tag **`v0.5.3`** (sin tag `v0.5.2`) — [truth-sync](../.jes/artifacts/engineer_note_docs_truth_sync_fase_c_2026_09_20.md). Ver [`PLATFORM_CAPABILITY_VISION.md`](PLATFORM_CAPABILITY_VISION.md) §13 y el [implementation report](../.jes/artifacts/implementation_report_fase_c_autonomy_surface_b1.md).

### 1e. `capabilities/radio.py` — Fase C · C5 (dual-role stub @ `v0.5.3`)

Modelo tipado `RadioStubFrame` / `SimulatedRadioIngress` / `RadioDualRoleResult` (Intent y/o Authority). `RadioIntentAdapter` sigue en `NotImplemented`. **No** hay decode ELRS/CRSF. Optional `SafetyRequest.authority_signal_id` — RejectAll sin cambios. **ACCEPT CLOSED** @ **`v0.5.3`** (mismo bloque que C4). [review](../.jes/artifacts/implementation_review_fase_c_radio_dual_role_b1.md) · [report](../.jes/artifacts/implementation_report_fase_c_radio_dual_role_b1.md) · IC: [`implementation_contract_fase_c_radio_dual_role_b1.md`](../.jes/artifacts/implementation_contract_fase_c_radio_dual_role_b1.md).

### 1f. `capabilities/crsf_stub.py` — Fase C · C19 (CRSF byte-fixture parse, package/tag **`v0.5.17`**, **★ ACCEPT CLOSED**)

Módulo **separado** de `radio.py` a propósito (el lock T5 de C5 — sin `decode_crsf`/`decode_elrs`/`open_serial` público en `radio.py` — queda intacto byte a byte, confirmado por `git diff`). Parsea el envelope CRSF (`[device_addr][frame_len][type][payload][crc8]`, CRC8 poly `0xD5` sobre `type+payload`) desde bytes de fixture ya incluidos en el repo, y decodifica dos tipos de frame: `0x16` `RC_CHANNELS_PACKED` (16 canales × 11 bits) y `0x14` `LINK_STATISTICS` (RSSI/LQ/SNR). Frames truncados o con CRC malo lanzan `CrsfParseError` tipado — sin éxito parcial silencioso. **Cero I/O en el módulo**: sin serial/socket/pty/USB/subprocess. `RadioIntentAdapter.parse(...)` sigue lanzando `NotImplementedError` incluso alimentado con bytes CRSF reales; `default_safety_gate()`/`ArmedAllowlistSafetyGate` sin cambios; nada decodificado aquí llega a `SimulatedRadioIngress`, `submit_command`, ni a ningún `SafetyGate`. **CRSF de fixture ≠ ELRS en vivo ≠ link de piloto**: este módulo sabe decodificar bytes, nada más — sin receptor "conectado", sin protocolo de aire, sin sticks de piloto moviendo nada. Ver [implementation report](../.jes/artifacts/implementation_report_fase_c_crsf_link_stub_b1.md).

### 1g. `capabilities/crsf_dual_role.py` — Fase C · C20 (CRSF decode → dual-role bridge, package/tag **`v0.5.18`**, **★ ACCEPT CLOSED**)

Tercer módulo **separado** de `radio.py` (también nunca plegado en él — `git diff` confirma `radio.py`/`intent.py`/`safety.py` intactos byte a byte). Puentea `CrsfRcChannels` (ya decodido por C19) hacia `RadioStubFrame`/`RadioDualRoleResult` de C5 bajo una política determinista y documentada: `CrsfDualRolePolicy` (un canal aux + umbral, defaults ilustrativos canal `4`/`1500`, no sacados de ningún hardware real) — igual o por encima del umbral emite **solo** `AuthorityKind="kill"` (Authority-only, nunca Intent); por debajo, devuelve `None`. El enriquecimiento opcional con `link_stats` mete LQ/RSSI/SNR en `RadioStubFrame.notes` sin afectar nunca si Authority dispara. **Authority de este puente sigue siendo solo trazabilidad frente a Safety** — probado explícitamente: meter el propio `AuthoritySignal.id` del puente en `SafetyRequest.authority_signal_id` sigue dando `reject` tanto en `RejectAllSafetyGate` como en un `ArmedAllowlistSafetyGate` armado; `default_safety_gate()` sin cambios. `RadioIntentAdapter.parse(...)` sigue lanzando `NotImplementedError` incluso alimentado con un frame real producido por el puente. El puente nunca llama a `submit_command` ni importa la superficie de autonomía. Ver [implementation report](../.jes/artifacts/implementation_report_fase_c_crsf_dual_role_bridge_b1.md).

### 1h. `capabilities/crsf_stream.py` — Fase C · C21 (CRSF byte-stream assembler, package/tag **`v0.5.19`**, **★ ACCEPT CLOSED**)

Cuarto módulo **separado** de `radio.py` (`git diff` confirma `radio.py`/`crsf_stub.py`/`crsf_dual_role.py`/`intent.py`/`safety.py` intactos byte a byte). `CrsfByteStreamAssembler.feed(data: bytes) -> list[CrsfFrame]` reensambla frames desde bytes entregados en **chunks arbitrarios** (la forma en que un UART entrega datos) cortando ventanas candidatas de exactamente `frame_len + 2` bytes y pasándolas, sin modificar, al `parse_crsf_frame` de C19 — sin una segunda implementación de CRC8/envelope (verificado: ningún `0xD5` en `crsf_stream.py`). Candidatos **incompletos** esperan en un buffer acotado (tope por defecto `256` bytes); ventanas **completas pero inválidas** (CRC malo, o un `frame_len` declarado fuera del rango plausible `[2, 64]`) nunca se propagan como excepción a quien llama — el ensamblador descarta exactamente un byte y resincroniza, en bucle, hasta encontrar un frame válido o agotar el buffer. Un helper opcional `ingest_stream_bytes(...)` reutiliza el `ingest_rc_channels(...)` de C20 **sin cambios** para cualquier frame `0x16` completado — la política de C20 (un canal aux, un umbral, solo `AuthorityKind="kill"`) no se profundiza ni reconfigura aquí. Cero I/O en el módulo — sin `serial`/`socket`/`pty`/USB/`open()`, sin ninguna clase con nombre tipo `Serial`/`UartPort`. Ver [implementation report](../.jes/artifacts/implementation_report_fase_c_crsf_byte_stream_b1.md).

### 1i. `capabilities/crsf_serial.py` — Fase C · C22 + C23 (CRSF host serial ingest + host baud, package/tag **`v0.5.21`**, **C22 ★ ACCEPT CLOSED @ `v0.5.20`; C23 ★ ACCEPT CLOSED @ `v0.5.21`**)

Quinto módulo **separado** de `radio.py` (`git diff` confirma `radio.py`/`crsf_stub.py`/`crsf_dual_role.py`/`crsf_stream.py`/`intent.py`/`safety.py` intactos byte a byte). `CrsfHostSerialIngress` extrae bytes de un descriptor de archivo ya abierto (`attach_fd`, propiedad de quien llama, nunca cerrado por este módulo) o de una ruta de dispositivo opt-in (`attach_path`, propiedad del ingress, cerrada en `.close()`), y `poll(...)` hace exactamente **una** lectura no bloqueante y alimenta lo que llegue al `CrsfByteStreamAssembler` de C21 sin cambios — sin hilo en segundo plano, sin bandera "conectado", sin escaneo automático de `/dev/cu.*`. **Todo PASS en la suite de tests de esta Buy usa un `pty` POSIX como loopback — no se requiere receptor físico ni adaptador USB serie**, verificado corriendo la suite completa sin nada enchufado. **No se añadió dependencia `pyserial`**. Se encontró y reveló una trampa real de los pty durante las pruebas de C22: por defecto están en modo canónico (con buffer por línea), que retenía silenciosamente bytes binarios CRSF hasta ver un salto de línea — arreglado enteramente en el arnés de test (`tty.setraw(...)`), no en el módulo entregado. Un helper opcional `poll_and_ingest(...)` reutiliza el `ingest_rc_channels(...)` de C20 sin cambios.

**C23 extiende este mismo módulo (sin un sexto módulo)** con configuración de baud **opt-in** en Darwin: `configure_host_baud(fd, baud=420000)` / `CrsfHostSerialIngress.configure_baud(...)`. En `sys.platform == "darwin"` aplica termios raw 8N1 y luego emite el ioctl real `IOSSIOSPEED` — el número de request **derivado** de la macro `_IOW('T', 2, speed_t)` (`sys/ioccom.h`), no copiado de `pyserial` ni de ninguna librería; verificado de forma independiente que equivale a `0x80085402`. En cualquier otra plataforma **falla cerrado** con `CrsfHostSerialError` tipado — sin `TCSETS2`/`BOTHER` de Linux, sin stack serie de Windows. `attach_fd`/`attach_path` **siguen sin** configurar baud automáticamente — el contrato "abrir = dame bytes" de C22 no cambia, re-verificado corriendo la suite de C22 sin modificar. **Ningún PASS requiere hardware**: el camino de éxito en Darwin se prueba enteramente vía un `fcntl.ioctl` simulado (mock); la única llamada de ioctl **sin simular** corre contra un `pty` POSIX real y se **espera que falle** (un pty no es un UART) — ese fallo es el resultado honesto esperado, no algo que se evita. Emitir el ioctl con éxito es un hecho de configuración del sistema operativo del host, nunca prueba de que exista un receptor. Ver [implementation report](../.jes/artifacts/implementation_report_fase_c_crsf_host_baud_b1.md).

### 1j. `capabilities/crsf_failsafe.py` — Fase C · C27 (stream-timeout failsafe, package/tag **`v0.5.25`**, **★ ACCEPT CLOSED**)

Sexto módulo **separado** de `radio.py` (`git diff` confirma `radio.py`/`crsf_stub.py`/`crsf_dual_role.py`/`crsf_stream.py`/`crsf_serial.py`/`intent.py`/`safety.py` intactos byte a byte). Es un **watch de edad**, no un parser: `CrsfRcHoldWatch` guarda solo la última marca de tiempo en que llegó un `0x16` válido; `note_rc(now_s)` la registra, `evaluate(now_s)`/`is_stale(now_s)` la comparan contra `timeout_s` (por defecto **`0.5` s**, ilustrativo, no una spec de ningún producto ExpressLRS real) — `age_s <= timeout_s` es fresco, `age_s > timeout_s` es stale, y nunca noted es stale con `reason="never"`. **`now_s` es siempre argumento del llamador** — este módulo nunca llama a `time.time()` como su propia fuente de verdad, lo que mantiene los tests deterministas. Pasar un `now_s` anterior a la última marca lanza `ValueError` tipado. `failsafe_loop_inputs(t_s)` devuelve el `level_setpoint(t_s)` de C8 más `collective=0.0` — un `RcLoopInputs` de C25 reutilizado sin cambios — y **nunca** llama a `FlightControlLoop.step`, `EscOutput.apply_forces`, ni a ningún `SafetyGate.evaluate`. El helper opcional `feed_and_note_rc(...)` llama al `assembler.feed(data)` de C21 sin cambios y marca `note_rc` solo si algún frame completado es `0x16` — nunca llama a `ingest_stream_bytes`, así que el helper por defecto de C21 queda intacto. El twin C++ — `native/flight_control/include/jarvis/fc/rc_hold.hpp` + `src/rc_hold.cpp`, añadido a `jarvis_fc` — es **deliberadamente agnóstico de protocolo**: ningún nombre de protocolo de radio aparece en ese árbol, ni siquiera en comentarios (mismo lock de C21-C26, re-verificado con grep en todo `native/`). La política `CrsfDualRolePolicy` de C20 (aux → Authority `kill`) y el mapa `map_rc_to_loop_inputs` de C25 quedan intactos — este Buy no los importa ni los reconfigura. Ver [implementation report](../.jes/artifacts/implementation_report_fase_c_crsf_stream_timeout_failsafe_b1.md).

**Failsafe de timeout ≠ motores cortados ≠ ELRS en vivo ≠ Safety allow**: existe un watch de edad; tras 0.5 s sin una muestra RC marcada, los sticks dejan de tratarse como vivos; la consigna recomendada es nivel + collective cero. Nada aquí es una radio que corta ESCs, un failsafe ExpressLRS como producto, ni Safety abriéndose por timeout. **Siguiente frente:** Engineer elige entre ejes parked — flasheo de placa · GPIO/DShot · craft↔FS — ver el [process lock](../.jes/artifacts/engineer_note_fase_c_process_lock_after_c6_2026_09_20.md).

### 2. Orquestación

El núcleo está en `core/orchestrator.py`.

Responsabilidades:

- recibir `ActionRequest`
- aceptar texto natural a través de la interfaz LLM
- detectar si hay sesión interactiva activa
- abrir `create_project_interactive` o `iterate_interactive`
- disparar acciones reales tras confirmación
- delegar en el router
- exponer planificación opcional mediante `build_plan(...)`

El mapeo `action -> handler` está en `core/action_router.py`.

#### Deuda técnica: dispersión de lógica de control

> **Estado: resuelto.** Ver `_handle_global_commands` a continuación.

En versiones anteriores, parte de la lógica de control global (escapes, shortcuts de arranque) estaba distribuida entre `main.py` y los session handlers. La regla de diseño aplicada: todo comando global vive en el orquestador, la CLI es un adaptador I/O puro.

#### `_handle_global_commands(user_input) → dict | None`

Primer check incondicional de `handle_user_text` — se ejecuta antes de cualquier modo de sesión, ingesta o intent resolver.

Maneja dos tipos de comandos:

- **Escape** (`cancelar`, `cancel`, `salir`, `abortar`, `abort`): llama a `state_manager.clear_runtime_session()` si hay sesión activa y devuelve `{status: "cancelled"}`. Si no hay sesión activa, devuelve `None` (el input cae al flujo normal — puede ser una pregunta válida).
- **Shortcut de creación** (`n`, `nuevo`, `nuevo proyecto`, `crear`): devuelve directamente `handle({action: create_project})` sin pasar por el LLM.

Los session handlers (`iterate_interactive_session`, `ParamDefinitionSession.answer`) mantienen su propio escape interno como fallback para callers directos (tests, tools). El orquestador coordina; los módulos internos siguen siendo coherentes por sí solos.

Orden de ejecución en `handle_user_text`:
```text
1. _handle_global_commands            ← comandos universales (escape, nuevo proyecto)
2. modo de sesión activo
   - CREATE_PROJECT_INTERACTIVE        ← delega a create_project wizard
   - ITERATE_INTERACTIVE               ← soft interrupt / classify / hard preempt / wizard
   - DEFINE_MISSING_PARAMETERS         ← soft-interrupt status; FN-013/015; nav-back FN-016;
                                         component description + Brief; param wizard
   - SYSTEM_DEFINITION                 ← system_definition_session
3. IDLE Acquisition Target (FN-014/015) ← mention gate / bare help-define → acquisition
4. intent resolver                    ← sin LLM (GUIDANCE/status antes que ANALYZE)
5. IDLE Engineering Intent (FN-022)   ← iterate|unknown + is_engineering_intention → goal_plan
6. acciones locales / explore / apply ← calculate, simulate, iterate-con-valor, DSE…
7. fallback LLM                       ← último recurso
```

Existe además una CLI mínima para validación humana real en `python -m jarvis.main --chat`.
Esa CLI usa Ollama local como cliente LLM real.
La integración actual usa dos modos:

- acciones estructuradas: `format=json`, `stream=false`
- `analyze`: texto natural (sin `format` en el payload)

### 2b. Human Layer Sprint v1 — capa conversacional

Módulos añadidos sobre el flujo base para hacer el sistema más comunicativo y orientado al usuario.

#### `intent_resolver.py` — `classify_input_intent(text)`
Clasificación ligera (sin LLM) de texto libre en tres categorías:
- `"information"`: preguntas, peticiones de estado, análisis → no mutan estado
- `"action"`: comandos de iteración, definición, cálculo → pueden mutar estado
- `"hybrid"`: combinación ambigua → tratado como `information` dentro de sesión activa

Uso principal: guardia en `ITERATE_INTERACTIVE` para evitar que preguntas informativas abran el wizard de iteración (Fix 1).

#### `main.py` — `WARNING_MESSAGES` / `_human_warning(code)`
Diccionario `WARNING_MESSAGES: dict[str, str]` que mapea códigos de warning del simulador (`low_margin`, `high_actuator_load`, `low_force_to_weight_ratio`, `autonomy_below_restriction`) a descripciones en español legibles por el usuario.

`_human_warning(code)` devuelve la descripción o el código sin cambios si no está en el diccionario.

#### `core/goal_planner.py` — Goal Planner híbrido
Detecta objetivos de diseño en lenguaje natural y genera planes estratégicos priorizados.

- `GOAL_STRATEGIES: dict[str, list[dict]]` — catálogo de estrategias por objetivo
- `detect_goal(text) → str | None` — keywords para `aumentar_payload`, `mejorar_autonomia`, `reducir_masa`, `mejorar_estabilidad` (incluye empuje/thrust → `mejorar_estabilidad`)
- `looks_like_numeric_mutate` / `is_engineering_intention` — FN-022: intención bare sin dígitos → `goal_key`; con valor numérico → cede a iterate
- `_prioritize_strategies(key, strategies, sim_context) → list[dict]` — reordena según `safety_margin_ratio` / warnings
- `format_goal_plan(key, sim_context) → str` — bloque determinista para el usuario
- `get_goal_context_for_llm(key) → str` — contexto inyectado al prompt LLM

**Dos usos:**
1. **IDLE Engineering Intent (FN-022):** gate en orquestador antes de iterate → `_handle_engineering_intent` → `format_goal_plan` + CTA a vocabulario DSE existente — **0 LLM**, sin auto-DSE.
2. **`_handle_analyze`:** si `detect_goal` → antepone `format_goal_plan` al análisis LLM.

Residual documentado: frases que ya matchean `EXPLORE_PATTERNS` (`mejorar estabilidad`…) siguen auto-DSE; no unificar en este mapa (ver `.jes/artifacts/residual_engineering_intent_plan_vs_explore.md`).

#### Acquisition Fluency + Continuity (FN-014…021, FN-023)

Módulos deterministas; el LLM no elige el siguiente target de adquisición.

| Módulo | Rol |
|---|---|
| `core/acquisition_target.py` | Autoridad de mención bloque∪componente; `COMPONENT_PROMPTS`; help-define / nav-back helpers |
| `core/acquisition_brief.py` | Brief fino (qué / qué sabe Jarvis / pregunta) reutilizado en open / re-prompt / help |
| `core/project_continuity.py` | `build_project_continuity` → situation / evidence / `next_useful_step` |
| `core/engineering_readiness.py` | ERF-1/ERF-2 — `build_engineering_readiness` → Gap Registry + 9-subsystem rollup (derived on read; C-107). ERF-2 adds `electronics` subsystem, `INCOMPATIBLE` verdicts, `electrical_compatibility.py` checks |
| `core/electrical_compatibility.py` | ERF-2 — pure deterministic checks: ESC presence, per-motor ESC vs motor current, battery discharge, prop↔motor match. No I/O, no LLM |
| `core/project_closure.py` | BOM + `classify_component` / `component_presence_tier` (FN-020); `build_component_bom` / `format_bom_lines` con `catalog_ref` / `sku_resolved` / `quantity` (Impl D + IC 3 + frame). `_bom_sku_resolved` re-checks motor/battery/propeller/**frame** SKUs — **display-only**. **Structure B:** hijos con `parent_key` nunca top-level; `_frame_part_sublines` muestra `└` para arm / placas ordinales (`label`+thickness) / cage / standoff. **Sensors honesty B1:** `_bom_sensors_declarative_tail` — GNSS vs bare `sensor_type` copy on `◇ sensors` (no Control PASS change) |
| `core/catalog_bind.py` | `bind_motor_from_catalog` / `bind_propeller_from_catalog` / `bind_battery_from_catalog` / `bind_esc_from_catalog` / `bind_frame_from_catalog` / `frame_part_specs_from_catalog` — única fuente de `ComponentSpec` + `catalog_ref` desde library; proyecta envelopes opcionales (Battery/ESC L×W×H; Motor stator/Ø/shaft) + `arm_thickness_mm` y `plates[]` curadas |
| `core/motor_catalog_assist.py` | Lista/sugerencias motor; pick UX en orchestrator (G21) |
| `core/battery_catalog_assist.py` | Lista/sugerencias batería; pick UX en orchestrator (IC 2) |
| `core/frame_catalog_assist.py` | Lista/sugerencias frame; pick UX (Structure Catalog IC-3) |
| `core/catalog_rebind_assist.py` | IDLE rebind B2+B3 — frase pura → reabrir catálogo de familia tras arquitectura 4/4 |
| `config.NAVIGATION_BACK_WORDS` | `atras`/`volver`/`vuelve` — solo wizards de adquisición (FN-016), no escape global |

Orquestador (IDLE / DEFINE_MISSING): gates FN-014…018, bare propeller vía `infer_component_for_key` (FN-019), clear a IDLE al cerrar arquitectura (FN-021). Detalle de field notes: `docs/PROJECT_CONTINUITY.md`.

### 3. Estado temporal vs persistente

Hay dos tipos de estado:

- estado temporal en memoria
- estado persistente en disco

#### Temporal

Lo mantiene `core/state_manager.py` mediante `runtime_state`.

Sirve para:

- modo actual del orquestador
- step actual
- drafts temporales

#### Persistente

Lo guarda `state.json` dentro de cada proyecto.

Sirve para:

- parámetros actuales del sistema
- resultados más recientes
- historial
- memory mínima del proyecto
- iteración activa

Separación clave:

- el draft no toca disco
- el estado real solo cambia tras confirmación y ejecución

### 4. Workspace como fuente de verdad

Cada proyecto vive como un workspace en disco.

Ruta por defecto actual para proyectos:

- `Projects/Jarvis/workspace/` (vía `JARVIS_WORKSPACE_ROOT` o default relativo al paquete)

`jarvis/runtime/` queda reservado para artefactos internos como `llm_logs`.

Estructura:

```text
proyecto/
├── state.json                ← ÚNICA fuente de verdad
├── views/                    ← representaciones derivadas (read-only, generadas automáticamente)
│   ├── objetivo.md
│   ├── sistema.md            ← refleja system_defined + system_blocks + components
│   ├── estado_actual.md      ← parámetros actuales + última simulación
│   └── reasoning.md          ← último output de ReasoningLayer (tras iterate/simulate)
├── history/                  ← trazabilidad append-only
│   ├── events.jsonl          ← log de eventos del sistema (append-only, timestamp UTC)
│   ├── iterations/           ← iter_NNN.json (JSON estructurado: change + mutation + impact + calcs + sim)
│   ├── simulations/          ← sim_NNN.json (resultado de simulación standalone)
│   └── calculations/         ← calc_NNN.json (resultado de cálculo standalone)
└── meta/
    └── project_config.json

```

Reglas de oro:
- `state.json` nunca se reconstruye desde archivos — es la fuente
- las vistas (`views/`) son siempre derivadas, nunca editables manualmente
- `events.jsonl` es append-only — no editar, no borrar
- `history/` ≠ estado
- **`workspace_path` repair (5 ago 2026):** al cargar via `StateManager.load(state_path)`, si `workspace_path` falta o no coincide con el directorio real de `state.json` (proyectos migrados / path legacy), se reescribe al path actual y se persiste. Evita `PermissionError` al guardar historia/vistas.

Todo esto lo gestiona `workspace/workspace_manager.py` (+ repair en `core/state_manager.py`).
Las vistas se generan con las funciones de `workspace/render_views.py`.
`file_writer.append_jsonl()` garantiza el contrato append-only del log de eventos.

## Flujo `create_project`

### Inicio

Puede entrar de dos formas:

1. Acción directa con parámetros completos.
2. Modo interactivo `create_project_interactive`.

### Draft temporal

La sesión guiada vive en `core/interactive_session.py`.

Tronco común (siempre):

1. tipo de sistema — normalizado via `_normalize_vehicle_type()` (`VEHICLE_TYPE_ALIASES`)
2. objetivo
3. payload
4. restricciones
5. nivel de detalle — `conceptual` aplica defaults de `structure_mass_factor` / `safety_factor`; `detallado` los pregunta

Ramas por dominio (`VEHICLE_TYPE_ALIASES` → aéreo `dron`/`uav` o terrestre `robot`/`coche`/`rover`):

- **Aéreo:** número de motores → vía de fuerza (`empuje` → `per_motor_max_thrust_n` | `hélices` → `propeller_diameter_in` + `propeller_rpm` | `no sé` → sin valores ficticios)
- **Terrestre:** número de actuadores (campo `motors`) → vía (`torque` → `per_actuator_torque_nm` | `fuerza` → `max_force_per_actuator_n` | `no sé`)
- **Desconocido:** salta la rama y va a confirmación

Confirmación (step 90). Durante el wizard no se calcula, no se simula, no se crea workspace ni se persiste.

### Ejecución real

La acción real vive en `actions/create_project.py`.

Qué hace:

- crea workspace
- inicializa parámetros base
- ejecuta `calculation_engine`
- ejecuta simulación
- genera sugerencias no vinculantes basadas en el resultado
- guarda artefactos
- actualiza `state.json`

## Flujo `iterate`

### Inicio

Cuando entra `iterate`, el sistema:

1. resuelve el proyecto activo
2. carga `state.json`
3. abre sesión interactiva

### Draft temporal + estado semántico

La sesión guiada vive en `core/iterate_interactive_session.py`.
Las constantes de dominio y validadores puros (vocabulario del sistema, dominio cerrado de variables válidas, materiales conocidos, normalización y fuzzy matching) viven en `core/iterate_domain.py`. Tras el Domain Registry refactor, `iterate_domain.py` es una **capa de adaptación**: sus símbolos públicos (`_VARIABLE_NORMALIZATION`, `_SEMANTIC_MUTATION_PARAMS`, `_VALID_VARIABLE_DOMAIN`) son vistas computadas desde `parameter_requirements.py` — no fuentes hardcodeadas. `IteratePrompt` (dataclass de preguntas UX) permanece en el archivo de sesión por ser flujo conversacional, no dominio.

Cada input del usuario pasa por dos fases antes del routing:

1. **Seed desde draft**: los campos ya confirmados en `IterationDraft` se añaden al
   `SemanticState` como slots `confirmed` (confianza 1.0). Esto garantiza que el
   estado semántico siempre sabe lo que ya está resuelto.
2. **Enriquecimiento**: `semantic_interpreter.update()` extrae slots del nuevo input
   y los fusiona al estado sin borrar información previa.

Tras el enriquecimiento, `semantic_interpreter.decide()` determina la acción:

- `proceed` (confianza ≥ 0.75 en todos los slots requeridos) → avanzar al paso 3 (restricciones)
- `confirm` (slots presentes, confianza media) → avanzar al paso 3 con mensaje de confirmación
- `clarify` (slot ausente o confianza < 0.4) → preguntar solo el slot que falta
- forzado tras `MAX_CLARIFICATION_ROUNDS = 2` → avanzar con lo disponible

El paso 3 (restricciones) siempre se muestra — nunca se salta. El paso 4 (impacto) solo se alcanza desde el paso 3.

Los slots requeridos son `operation` y `variable`. Con ellos `mutation_engine` puede ejecutar.
Las restricciones son siempre preguntadas pero opcionales — si el usuario no responde (enter vacío), el sistema las registra como `"ninguna"` y avanza.

### Tipos de variable en el wizard (Bugs 14/15)

`IterateInteractiveSession._classify_variable_type(variable, current_params)` clasifica la variable del paso 1 en una de 7 categorías para seleccionar la pregunta correcta en paso 2.  
**Esta clasificación gobierna solo el texto de la pregunta (UX) — no la ejecución.** La decisión de si una mutación es físicamente ejecutable sigue siendo responsabilidad exclusiva de `mutation_engine.is_physically_actionable()` (Bug 3).

| Categoría | Condición | Pregunta paso 2 |
|---|---|---|
| `semantic_mutation` | `PARAMETER_REQUIREMENTS.get(variable).variable_type == VariableType.SEMANTIC_MUTATION` (ej: `payload_kg`) — verificado PRIMERO vía registro; estos params existen también en `current_parameters` numéricamente pero su mutación es conceptual (reducir/aumentar), nunca set-to-value | `"¿Cómo quieres modificar el payload? Indica valor concreto (ej: +10%, -0.5 kg)"` |
| `numeric_direct` | Clave numérica en `current_parameters` — seguro aquí porque `semantic_mutation` ya filtró el registro; además fires antes de `structural_*` para que `"factor_estructura"` no caiga en `structural_abstract` | `"¿Cuál es el nuevo valor de X? (actual: Y)"` |
| `material` | `"material"` en variable | Genérica (sub-flujo captura nombre explícito) |
| `structural_physical` | `"dimension"`, `"volum"`, `"geometr"` — cuantificable | Avisa que se necesita factor cuantitativo; sin él el cambio queda declarativo |
| `structural_abstract` | `"estructur"`, `"forma"`, `"topolog"` — siempre declarativo | Avisa que no hay impacto físico computable |
| `component_define` | `_is_supported_define_variable()` — abre sub-flujo de definición | Pregunta de componente/material |
| `unknown` | Fallback | Pregunta genérica |

El orden de prioridad **más específico primero** garantiza que variables como `"factor_estructura"` (que contiene `"estructur"`) resuelven correctamente a `numeric_direct` porque el param existe en `current_parameters`.

**Escape global del wizard:** en cualquier paso del flujo `ITERATE_INTERACTIVE`, el usuario puede escribir `cancelar`, `cancel`, `salir`, `abortar` o `abort`. `IterateInteractiveSession.answer()` lo detecta como primera comprobación (antes de cualquier procesamiento de step) y devuelve `{status: "cancelled"}`. El orquestador (`handle_user_text`) llama entonces a `state_manager.clear_runtime_session()` para restaurar el modo `NONE`. Esta comprobación es incondicional — no depende del step actual ni de si hay un conflicto activo.

**Preempción de intents fuertes (calibración 2026-08-05):** si el wizard está abierto y el input resuelve a un intent de acción fuerte (`explore_design_space`, `calculate`, `simulate`, `create_project`, `define_params`, `iterate`, `dismiss_suggestion`) o a una descripción de componente (probe con sesión idle; el guard Bug 64 sigue bloqueando el intercept directo), el orquestador cierra la sesión, re-despacha el turno como idle y prefija el mensaje con un aviso (`preempted_iterate: true`). Excepción: no se preemptan componentes cuando el wizard **posee** el input (`DEFINE` en step 2, o `motor_suggestions` activo) — así el flujo de sugerencias de motor / define-component no se aborta. Respuestas de paso del wizard (`sí`, nombres de variable, etc.) no hacen match y siguen el flujo normal. `project_status` / `analyze` siguen siendo soft interrupt (Bug 7).

`SemanticState` se serializa en el dict de respuesta de cada turno (clave `"semantic_state"`) y se restaura en `_session_from_response` del orquestador. Esto garantiza que `focus`, `entities` y `active_intent` sobreviven entre inputs del usuario dentro de la misma sesión interactiva.

`SemanticState` incluye tres campos de contexto de sesión más allá de los slots:

- `focus`: componente activo sobre el que se está trabajando (se hereda entre pasos)
- `entities`: lista de entidades mencionadas en la sesión (componentes, materiales)
- `active_intent`: intención semántica detectada (`modify_component`, `define_components`...)

### Sub-loop multi-entidad

Cuando el usuario menciona dos o más componentes a la vez en el paso 2 (`define`):

1. `semantic_interpreter.extract_entities()` detecta las entidades
2. El sistema pregunta por cuál empezar (o "todos" para registrar con detalle bajo)
3. Los componentes restantes se guardan en `pending_entities`
4. El sub-loop procesa cada uno antes de avanzar al paso 3

### Enriquecimiento cruzado de sesión

Cuando el usuario escribe `"completar especificación del motor"` tras una sesión anterior:

1. `ITERATE_PATTERNS` detecta `completar|especificar|enriquecer`
2. `resolve_action_request` extrae `enrich_component` de la frase (`"de/del X"`)
3. El orquestador carga `project_state.design_properties.components` y lo pasa como `known_components`
4. `iterate_interactive_session.start()` llama a `_seed_semantic_from_state` con esos componentes
   y establece `focus = enrich_component` en `SemanticState`
5. La sesión arranca en el paso 2 directamente con la pregunta enfocada en ese componente

Esto evita reiniciar la sesión desde el paso 0 y mantiene el contexto del componente parcialmente definido.

Campos del draft que se completan durante la sesión:

- objetivo
- variable
- operación (siempre `IterationOperation` enum, nunca raw string)
- estrategia
- valor declarativo si aplica
- impacto estimado
- confirmación final

### Impacto estimado

Antes de ejecutar se muestra una estimación preliminar.

Esto no modifica estado real.
Solo sirve para interacción guiada.

### Mutación real

Tras confirmación entra `core/mutation_engine.py`.

Responsabilidad:

- traducir `iteration_draft -> state_patch + impact`

No hace:

- cálculo físico
- simulación
- persistencia

Estrategias v0:

- material
- volumen
- payload

Tipos actuales de iteración:

- física: `reducir`, `aumentar`, `mejorar`, `optimizar`
- declarativa: `define`

## Snapshot de estado del proyecto

### `build_startup_context()`

Ubicación: `core/orchestrator.py`

Función pública del orquestador que construye un snapshot estructurado del estado actual del proyecto **sin invocar el LLM**. Es la única fuente de verdad para describir el estado del proyecto — tanto el display automático de arranque como las consultas on-demand usan este mismo builder.

```text
build_startup_context(workspace_path?) → dict
```

Flujo:
1. `state_manager.load_active_project()` — lee `state.json` fresco (sin caché)
2. `_build_analyze_context()` — construye contexto estructurado del proyecto
3. `reasoning_layer.build(context)` — extrae señales deterministas
4. Aplica jerarquía de status (prioridad estricta):
   - `blocking` — `signals["missing_physics_parameters"]` (dominio terrestre sin params de transmisión)
   - `warning`  — `signals["has_warnings"]` (simulación con warnings)
   - `nominal`  — `signals["has_simulation"]` (simulación válida sin warnings)
   - `no_data`  — ninguna simulación previa
5. Selecciona `active_variables` (máx 3) según status:
   - blocking → `["motor_count", "per_actuator_torque_nm", "payload_kg"]`
   - warning/nominal → `["payload_kg", "motor_count", "safety_margin_ratio"]`
   - no_data → `["payload_kg", "motor_count", "safety_factor"]`
6. Genera `suggested_action` desde el top `ReasoningSuggestion` + `hint` accionable
7. **ERF-1/ERF-2:** `build_engineering_readiness(project_state)` — proyección derivada (Gap Registry + 9 subsystems + `overall`); expuesta como `"readiness"` en el dict; Continuity consume opcionalmente `readiness` para el ranking del catalog gap (C-108); no se persiste en disco. ERF-2 adds `electronics` subsystem, 4 electrical gap types (`GAP-ESC-MISSING`, `GAP-ESC-UNDERSIZED`, `GAP-BATTERY-DISCHARGE-EXCEEDED`, `GAP-PROP-MOTOR-MISMATCH`), `INCOMPATIBLE` verdicts with ★3 deterministic-evidence gate, and `electrical_compatibility.py` as pure fact provider

Estructura de retorno:
```python
{
    "has_project": True,
    "project_slug": str,
    "objective": str,
    "status_type": "blocking" | "warning" | "nominal" | "no_data",
    "status_reason": str | None,        # ej. "missing_transmission_parameters" | "missing_propulsion_parameters"
    "active_variables": dict[str, Any], # máx 3
    "suggested_action": {
        "label": str,
        "reason": str,
        "hint": str | None,             # ej. 'Puedes responder: "0.15 y 10"'
    } | None,
    "phase": str,                       # "definition" | "physical_validation" | "optimization" | "complete"
    "phase_description": str,
    "phase_confidence": float,
    "proactive_question": str | None,   # presente si hay parámetros bloqueantes ausentes
    "missing_params": list[str] | None, # parámetros que activan DEFINE_MISSING_PARAMETERS
    "param_definition_reason": str,     # reason code del trigger de parámetros
    # Arquitectura de sistema (None cuando system_defined=False)
    "architecture_progress": str | None,    # ej. "1/4"
    "next_architecture_block": str | None,  # clave del bloque pendiente
    "next_architecture_label": str | None,  # etiqueta humana del bloque
    "next_block_status": str | None,        # "not_started" | "in_progress"
    # ERF-1 Engineering Readiness (derived on read — not persisted)
    "readiness": dict,                      # gaps, subsystems (9 keys), overall, top_gap, prioritized_gaps
    "continuity": dict,                     # situation, evidence, next_useful_step, next_useful_why
}
```

**ERF-1/ERF-2 authority note:** `readiness` is authoritative over **gap aggregation and assembly-ready rollup**, not over physics/BOM/sim truth. ERF-2 adds `INCOMPATIBLE` verdicts (★3 deterministic-evidence gate) and `electrical_compatibility.py` as a pure fact provider for ESC/battery/prop-motor checks. See `docs/system_map/AUTHORITY.md` and `docs/system_map/CONNECTIONS.md` C-107–C-112.

**Project Closure arc (IC 1–3, `checkpoint-closure-policy`):** product contract ratified in `ENGINEERING_READINESS_VISION.md` §11 (snapshots A/B, family matrix, deferred G24/H5). **IC 1** — `requirements_declared()` / explicit-none semantics + G26 mid-session `restrictions` write + `is_derived` gate in `param_definition_session`. **IC 2** — live battery catalog pick (`battery_catalog_assist` + `bind_battery_from_catalog`); G27 battery Wh parsing scoped to `semantic_intent_adapter` (`battery_capacity_wh` only); battery bind **does not** re-call `set_motor_component` (OP downgrade regression locked). **IC 3** — `_bom_sku_resolved` propeller branch only (code); rollup rule unchanged. `ASSEMBLY_READY` = zero HIGH gaps + 9 subsystems PASS (or single accepted WARNING `CATALOG-GAP-DEMOTED-POST-PASS` on catalog/propulsion only).

### Startup display

Cuando el usuario selecciona un proyecto en la CLI (`run_chat()`), se llama `build_startup_context()` y el resultado se renderiza vía `render_startup_context()` (función pura en `main.py`, sin lógica) antes del primer turno.

Si el contexto incluye `proactive_question`, la CLI inicia automáticamente una sesión `DEFINE_MISSING_PARAMETERS`. Triggers (prioridad descendente):
1. Parámetros de transmisión ausentes (fase `definition` + `status_type=blocking`)
2. Parámetros de energía ausentes (`missing_energy_parameters` signal, cualquier fase)
3. Parámetros de hélice ausentes con hint (`propeller_status="missing_propeller_parameters"`)
4. Bloque de arquitectura composite `not_started` — Phase A: componentes; Phase B: parámetros numéricos
5. Bloque de arquitectura param-driven o component-driven pendiente

### Intent `project_status` (+ Continuity)

Cuando el usuario escribe frases como `"estado del proyecto"`, `"resumen"`, `"qué falta"`, `"siguiente paso"` o `"cómo va el proyecto"`, `IntentResolver` las clasifica como `project_status` (no `analyze`). El orquestador las atiende en `_handle_project_status()`, que delega en `build_startup_context()` — misma fuente de verdad, cero llamadas LLM. El contexto incluye `readiness` (ERF-2 — 9 líneas + TOP GAPS, con verdicts `INCOMPATIBLE` para gaps eléctricos) y `continuity` (`situation` / evidence / `next_useful_step`).

`STATUS_PATTERNS` vive separado de `QUESTION_PATTERNS`. `_looks_like_status_query()` se evalúa antes que `_looks_like_question()` cuando no hay strong-action previo.

**FN-023:** `"ayúdame con el siguiente paso"` (y variantes) iría a `analyze` por el `\bayudame\b` de `ANALYZE_PATTERNS`. Se corrige en `GUIDANCE_PATTERNS` (evaluados **antes** de ANALYZE en `_resolve_strong_action_intent`) → `project_status`. Continuity sigue siendo la única autoridad del siguiente paso; no hay recommender paralelo.

### Modo `DEFINE_MISSING_PARAMETERS`

Dos sub-modos bajo el mismo `OrchestratorMode.DEFINE_MISSING_PARAMETERS`, diferenciados por `param_definition_reason`:

**Sub-modo A — Component description** (`reason = MISSING_COMPONENT_DEFINITION`):  
Activado cuando el siguiente bloque de arquitectura es `component` o el siguiente bloque composite (Phase A) tiene componentes ausentes. La pregunta de apertura / re-prompt / help usa `acquisition_brief.build_acquisition_brief` + `acquisition_target.COMPONENT_PROMPTS` (no el genérico `¿Cuál es el valor de X?`). `_handle_component_description()` gestiona el input:
- `infer_components` y, si aplica, `infer_component_for_key` (FN-019: bare `"10x4.5"` con `propellers` en `expected_keys`)
- Rechazo de `generic_component` cuando hay `expected_keys` (FN-017)
- Routing por `suggested_key` → writers (`_set_motor_component`, `_set_propeller_component`, …)
- Cuando el bloque está completo → `_set_pending_next_block()`; si no hay siguiente bloque y el modo sigue DEFINE_MISSING → `clear_runtime_session()` → IDLE (FN-021)

**Sub-modo B — Param wizard numérico** (`reason ∈ {MISSING_PROPULSION_PARAMETERS, MISSING_ENERGY_PARAMETERS, MISSING_TRANSMISSION_PARAMETERS, MISSING_PROPELLER_PARAMETERS}`):  
Activado para blocks param-driven o composite Phase B (componentes ya completos, params ausentes).
1. `build_startup_context()` produce `proactive_question` + `missing_params` + `param_definition_reason`
2. La CLI inicia `JarvisOrchestrator.start_define_missing_params(missing_params, reason)`
3. Cada input pasa por `ParamDefinitionSession.answer()`:
   - Parseo semántico por keywords; fallback posicional
   - Acumula en `session.collected_params`
   - **Skip phrases** (`_SKIP_PHRASES`): si el usuario escribe `"no sé"`, `"omitir"`, `"skip"` u otras frases de deferimiento, el parámetro actual se omite (se elimina de `pending_param_definitions`) y se avanza al siguiente. Si todos los params han sido respondidos o omitidos, se llama a `apply_and_recalculate`. El param omitido no se escribe en `current_parameters` — queda como `None` hasta que el usuario lo defina posteriormente.
   - Cuando completo → `apply_and_recalculate()` → parchea `current_parameters` → recalcula → persiste

El campo `param_definition_reason` incluye: `"missing_transmission_parameters"`, `"missing_propulsion_parameters"`, `"missing_energy_parameters"`, `"missing_propeller_parameters"`, `"missing_component_definition"`.

Este flujo no toca `mutation_engine` ni `IterateInteractiveSession`.

**Escape global:** `cancelar` / `cancel` / `salir` / `abortar` → `clear_runtime_session()`.

**Navegación de adquisición (FN-016):** `atrás` / `volver` / `vuelve` (`NAVIGATION_BACK_WORDS`) cancelan el wizard de DEFINE_MISSING sin tratarse como valor numérico ni como escape global fuera de adquisición. Las claves de componente nunca reciben un float posicional.

### Bloque de arquitectura composite — Wizard de dos fases

Bloques composite (actualmente `energy` y `propulsion`) requieren AND-strict: `params_ok AND components_ok`. El wizard se orquesta vía `_set_pending_next_block()` y `build_startup_context()`:

```text
Phase A (not_started, componentes ausentes)
  build_startup_context → proactive_question + missing_params=["motors","propellers"]
  _set_pending_next_block → session.pending_missing_reason = MISSING_COMPONENT_DEFINITION
  → _handle_component_description procesa cada componente
  → cuando todos presentes → _set_pending_next_block → Phase B

Phase B (in_progress, componentes OK, params ausentes)
  build_startup_context → next_block_status="in_progress"
  _set_pending_next_block → session.pending_missing_reason = MISSING_PROPULSION_PARAMETERS
  → ParamDefinitionSession recoge motor_count + per_motor_max_thrust_n
  → apply_and_recalculate → bloque pasa a complete
```

`_block_progress_status(block, design_properties, params)` implementa la lógica AND-strict:
- `not_started`: ni params ni componentes definidos
- `in_progress`: uno de los dos satisfecho
- `complete`: ambos satisfechos

## Modo `SYSTEM_DEFINITION`

Transición de "intención" → "arquitectura de sistema estructurada". Se lanza automáticamente
tras confirmar `create_project`. Puebla `design_properties.components` con stubs declarados
antes de entrar en cálculo/iteración.

### Flujo

```text
create_project confirmado
↓
system_definition_session.start(vehicle_type, project_state)
  ├─ dominio conocido → step=0 (oferta A/B/C con bloques base del catálogo)
  └─ dominio desconocido → step=1 (modo B directo)

answer(user_input)
  step=0 → A (aceptar base) | B (añadir bloques) | C (saltar)
  step=1 → recoge bloques custom hasta "listo" | alias → gate `block_components_are_resolvable()` → si resuelve: bloque canónico; si no: rechazo honesto sin persistir (`_refuse_unresolvable_block`) | texto libre → registrado sin expandir
  → _apply_and_finish() → persiste stubs + system_priority, cierra sesión
  → bridge: priority[0] → get_param_reason_for_block() → ParamDefinitionSession.start()
```

Gate B1 (2026-09-15): un alias solo se acepta si todas las component keys de `BLOCK_TO_COMPONENTS[block]` tienen `suggested_key` match en `aerial_registry.known_suggested_keys()`. Hoy: `propulsion`/`energy`/`structure`/`control` **y** `perception`/`communication` (identity `cameras`/`radio_module`) resuelven; `payload`/`manipulation`/`actuation`/`transmission` se rechazan sin crear stub. `perception` expande solo a `["cameras"]` (lidar = deuda nombrada). Ver `block_components_are_resolvable()` en `system_architecture_catalog.py`.

### Catálogos de datos (sin imports de jarvis.schemas)

`core/system_architecture_catalog.py`:
- `SYSTEM_ARCHITECTURES` — bloques base + etiquetas por dominio (`dron`, `uav`, `robot`, `coche`, `rover`)
- `BLOCK_TYPE` — tipo de bloque: `"param"` | `"component"` | `"composite"`. Estado actual:
  - `"composite"`: `propulsion` (Fase 6: motors + propellers + params), `energy` (Fase 4: battery + motors + params)
  - `"component"`: `structure`, `control`
  - `"param"`: `actuation`, `transmission`
- `BLOCK_TO_COMPONENTS` — bloque → component keys (strings primitivos)
- `BLOCK_TO_PARAM_REASON` — bloque → reason code; entradas: `propulsion`, `actuation`, `energy`
- `COMPONENT_MIRRORED_PARAMS` — frozenset de params que son mirror de `components[*].properties`; solo escribibles via helpers (`battery_capacity_wh`, `motor_power_w`, `propeller_diameter_in`)
- `VEHICLE_TYPE_ALIASES` — normaliza aliases (`"drone"` → `"dron"`, `"quadcopter"` → `"dron"`, etc.)
- `BLOCK_ALIASES` — texto libre del usuario → bloque canónico (22 entradas)
- API pública: `get_domain_architecture()`, `blocks_to_component_keys()`, `normalize_block_alias()`, `get_param_reason_for_block()`, `get_block_type()`, `block_components_are_resolvable(block, registry=None)` (B1 gate)

`core/system_dependency_catalog.py`:
- `SYSTEM_DEPENDENCIES` — dependencias entre bloques por dominio
- Normalización via `VEHICLE_TYPE_ALIASES` — misma clave canónica que `system_architecture_catalog`
- API pública: `get_domain_dependencies(vehicle_type)`

### DependencyGraph y PriorityEngine

`core/system_dependency_graph.py`:
- `DependencyGraph` (frozen dataclass) — `dependencies: dict[str, list[str]]`
- `get_dependencies(block)`, `get_dependents(block)`
- `build_dependency_graph(vehicle_type, blocks)` — filtra el catálogo a los bloques presentes; bloques custom sin entrada en catálogo reciben `deps=[]`

`core/priority_engine.py`:
- `compute_priority_order(graph)` — DFS topológico
- Protección ante ciclos: `visited` + `visiting`; ciclos emiten `warnings.warn`, sin crash
- Output: lista ordenada de menos a más dependiente, p.ej. `["propulsion", "energy", "structure", "control"]`

El orden derivado reemplaza el antiguo `recommended_start` hardcodeado en el catálogo de arquitecturas. El campo `system_priority: list[str]` se persiste en `DesignProperties`.

### Reglas de prioridad (no-sobrescritura de componentes)

`source:       user(2) > inferred(1) > declared(0)`
`completeness: high(2) > medium(1)   > low(0)`

`_should_skip(existing)` → `True` si `source_rank > 0` OR `completeness_rank > 0`. Los stubs nuevos (`completeness=low, source=declared`) nunca sobreescriben componentes ya enriquecidos.

### Estado persistido

`DesignProperties` gana tres campos:
- `system_defined: bool` — flag de sesión completada
- `system_blocks: list[str]` — bloques elegidos (base + custom)
- `system_priority: list[str]` — orden topológico derivado del grafo

### Riesgos conocidos (deuda técnica)

Physics gated on lab/datasheet (ESC η, battery C-rate, sag) lives in [`docs/HARDWARE_DEBT.md`](HARDWARE_DEBT.md) — not in this software-debt list.

1. `SYSTEM_DEPENDENCIES` es estático — no derivado de la física del proyecto
2. `compute_priority_order` ignora `payload`, `restrictions` y parámetros actuales — el orden es el mismo para todo proyecto del mismo dominio
3. `ReasoningLayer` no consume `system_priority` ni `DependencyGraph` — los insights causales ("no puedes mejorar autonomía sin tocar propulsión") están diferidos

## Sistema multi-dominio

### Principio de diseño

El sistema fue inicialmente diseñado para drones (dominio aéreo). La capa de componentes
estaba acoplada al vocabulario propulsivo (motores brushless, hélices, KV). La arquitectura
multi-dominio desacopla esa taxonomía del núcleo y la convierte en un artefacto intercambiable.

Principio rector: **"primero cambias el significado, luego cambias el nombre"**. Todos los
renames destructivos están diferidos hasta que un caller real genere confusión semántica.
Mientras tanto se usan aliases y frozensets.

### ComponentRule y ComponentRuleRegistry

Ubicación: `core/component_rules.py`

Contratos de comportamiento (Protocols, `runtime_checkable`):

- `PropertyExtractor(normalized: dict) → dict` — extrae propiedades de un componente normalizado
- `CompletenessEvaluator(props: dict) → tuple[str, list[str]]` — devuelve `(nivel, campos_faltantes)`

`ComponentRule` (frozen dataclass):

- `keywords: tuple[str, ...]` — palabras clave que identifican este tipo de componente
- `component_type: str` — tipo semántico (`"propulsion_active"`, `"traction_active"`, etc.)

`_COMPONENT_PROMPTS: dict[str, str]` — prompts UX por component key (`"frame"`, `"battery"`, `"motors"`, `"propellers"`, `"flight_controller"`, `"sensors"`). Usados en `_component_prompt_for_first_missing()` para guiar al usuario.

`_BLOCK_COMPONENT_HINTS: dict[str, str]` — hints de Phase A por bloque composite/component, usados en `build_startup_context()` para el `proactive_question` inicial. Entradas: `"structure"`, `"control"`, `"energy"`, `"propulsion"`.
- `suggested_key: str` — clave sugerida para el componente
- `inference_confidence: float` — confianza base del match
- `property_extractor: PropertyExtractor | None`
- `completeness_evaluator: CompletenessEvaluator | None`
- `missing_field_hints: tuple[str, ...]` — preguntas de completeness
- `extra_hints: tuple[str, ...]` — preguntas adicionales opcionales
- `output_magnitude: str | None` — clave de la propiedad que representa la magnitud física de salida del componente (ej. `"thrust_n"` para motor aéreo, `"torque_nm"` para motor de tracción). El resolver la usa para parametrizar elegibilidad y resolución de fuerza sin hardcodear nombres de dominio.
- `matches(normalized: dict, name_lc: str) → bool` — matching por keywords

`ComponentRuleRegistry`:

- lista ordenada de `ComponentRule`
- `first-match-wins`
- `register(rule)`, `match(normalized, name_lc) → ComponentRule | None`, `known_suggested_keys() → frozenset[str]` — todo `suggested_key` que la registry puede resolver (B1 gate)

### Dominio aéreo

Ubicación: `domains/aerial.py`

Siete reglas registradas en `aerial_registry = ComponentRuleRegistry([...])` (orden = first-match-wins):

| Tipo | `component_type` | `suggested_key` | Propiedades extraídas |
|---|---|---|---|
| Hélice | `propulsion_passive` | `propellers` | `diameter_in`, `pitch_in`, `count` |
| Motor brushless | `propulsion_active` | `motors` | `kv`, `thrust_n`, `motor_count`, `watts` |
| ESC | `power_control` | `esc` | `current_a` |
| Batería | `energy_storage` | `battery` | capacidad, celdas |
| Frame | `structure` | `frame` | material, masa |
| Flight controller | `flight_controller` | `flight_controller` | modelo |
| Sensores/GPS | `sensors` | `sensors` | tipo, modelo |

`known_suggested_keys()` sobre este registry devuelve exactamente `{propellers, motors, esc, battery, frame, flight_controller, sensors}` — el set que gatea `SYSTEM_DEFINITION` (ver gate B1 arriba).

`_set_propeller_component(project_state, spec)` — extraído a `core/component_writers.py` (D6). Escribe en `components["propellers"]` y hace el bridge físico: lee `spec.properties["diameter_in"]` y escribe `current_parameters["propeller_diameter_in"]` (o elimina la clave si el valor es `None`). El engine recibe `propeller_diameter_in` como parámetro normal.

Extractores usan regex sobre el nombre normalizado del componente (sin LLM).

Campo `output_magnitude`: solo motor brushless → `"thrust_n"`; las otras seis reglas → `None`.

### Dominio terrestre

Ubicación: `domains/ground.py`

Dos reglas registradas en `ground_registry = ComponentRuleRegistry([traction_active_rule, rolling_passive_rule])`:

| Tipo | `component_type` | Propiedades extraídas |
|---|---|---|
| Motor de tracción | `traction_active` | `motor_count`, `torque_nm`, `rpm` |
| Rueda pasiva | `rolling_passive` | `wheel_count` |

Campo `output_magnitude`: motor de tracción → `"torque_nm"` · rueda pasiva → `None`.

Decisión de diseño: `torque_nm` se extrae en el resolver pero la conversión a fuerza ocurre
en el engine. El resolver inyecta `per_actuator_torque_nm` via `apply_to` al dict de parámetros.
El engine lee `per_actuator_torque_nm + wheel_radius_m + gear_ratio` de `current_parameters`, que
el usuario debe declarar explícitamente (sin fallback implícito). Si faltan, el engine registra
`missing_transmission_parameters` en `tool_results` y devuelve `available_total_thrust_n = None`.

Para vehículos aéreos sin ninguna ruta de fuerza (sin thrust declarado, sin torque, sin geometría de hélice), el engine registra `missing_propulsion_parameters` con los parámetros `["motor_count", "per_motor_max_thrust_n"]`. La decisión de dominio está centralizada en `AERIAL_VEHICLE_TYPES` (frozenset en `calculation_engine.py`) — un único punto de decisión sin lógica duplicada downstream.

### Routing de dominio (registry_selector)

Ubicación: `domains/registry_selector.py`

```python
def get_registry(vehicle_type: str | None = None, text: str | None = None) → ComponentRuleRegistry
```

Tres niveles de prioridad:

1. **vehicle_type explícito** — si está en `_VEHICLE_TYPE_MAP` determina el dominio de forma
   determinísta, sin importar el contenido del texto. **Anula completamente la heurística.**
2. **Heurística de texto** — cuenta hits de keywords en `_AERIAL_KEYWORDS` y `_GROUND_KEYWORDS`
   sobre el texto normalizado; gana el dominio con más hits (sin ties)
3. **Default** — `aerial_registry` (compatibilidad hacia atrás)

`_VEHICLE_TYPE_MAP` incluye: `drone/dron/uav/quadcopter/multirotor` → aéreo;
`rover/car/coche/vehicle/ground/robot/ugv` → terrestre.

Hooks de integración:

- `mutation_engine.py` lee `state.get("vehicle_type")` y pasa el registro correcto a `infer_component`
- `IterateInteractiveSession._registry_for_session(session, text)` — helper que lee
  `session.memory_context.get("vehicle_type")` y llama a `get_registry`; todos los call sites
  de `infer_component` en `iterate_interactive_session.py` usan este helper (5 sitios)

Persistencia de `vehicle_type` — dos gaps cerrados para garantizar que el tipo de dominio
llega correctamente a ambos hooks:

- `actions/iterate.py` → `_build_mutable_state`: incluye `"vehicle_type"` en el dict
  mutable para que `mutation_engine` lo lea directamente
- `core/orchestrator.py` → seed de `iterate_interactive_session.start()`: `memory_context`
  incluye `vehicle_type` de `current_parameters` además de `ProjectMemory`

### Component inference (dispatcher)

Ubicación: `core/component_inference.py`

Dispatcher puro (~60 líneas). El registro se inyecta en cada llamada:

```python
infer_component(raw_name, raw_value=None, registry: ComponentRuleRegistry | None = None)
```

- `registry=None` usa `_DEFAULT_REGISTRY = aerial_registry` (compatibilidad hacia atrás)
- Fallback genérico cuando ninguna regla coincide: `suggested_key="generic_component"`, `confidence=0.4`
- Propaga `rule.output_magnitude` al `ComponentSpec` resultante; `None` si no hay regla coincidente o si la regla no define magnitud

### Component resolver (puente declarativo → físico)

Ubicación: `core/component_resolver.py`

**Es el único componente que traduce intención declarativa en parámetros físicos utilizables por el motor de cálculo.** Sin él, todo lo declarado en `design_properties.components` es invisible para la física.

Función:

- convertir `design_properties.components` en overrides efímeros de parámetros de actuadores
- actuar como puente entre el mundo declarativo (ComponentSpec) y el modelo físico (CalculationBundle)

**Los overrides son estrictamente efímeros**: se calculan en RAM, se aplican una vez antes
de `calculation_engine.build()` y nunca se persisten en `state.json`.

Cambios de la arquitectura multi-dominio:

- `_ACTIVE_ACTUATOR_TYPES = frozenset({"propulsion_active", "traction_active"})` — reemplaza
  la constante `"propulsion_active"` para soportar ambos dominios sin cambio destructivo
- `PhysicalOverride` — clase principal; `PropulsionOverride = PhysicalOverride` como alias
- `resolve_physical_parameters` — función principal; `resolve_propulsion_parameters` como alias

`PhysicalOverride` mantiene los campos originales (`motors`, `per_motor_max_thrust_n`, `per_actuator_torque_nm`) para
compatibilidad, y expone aliases genéricos como propiedades:

```python
@property def actuator_count(self) → int | None: return self.motors
@property def max_force_per_actuator_n(self) → float | None: return self.per_motor_max_thrust_n
```

Campo `per_actuator_torque_nm: float | None = None` — se extrae del componente cuando `output_magnitude == "torque_nm"` y el valor está declarado con `source="declared"`. Se inyecta al dict de parámetros via `apply_to`, donde el engine lo toma para la conversión.

Regla de elegibilidad de un componente:

- `component_type in _ACTIVE_ACTUATOR_TYPES`, Y
- `completeness in ("medium", "high")` O la propiedad identificada por `output_magnitude` declarada con `source="declared"`
- Componentes con `completeness="low"` y sin valor declarado explícito son ignorados

Resolución de `motors` / `actuator_count`:

1. `properties["motor_count"].value` si existe explícitamente
2. Conteo de entries elegibles como fallback

Resolución de `per_motor_max_thrust_n` / `max_force_per_actuator_n`:

- Solo cuando `output_magnitude == "thrust_n"` — fuerza lineal directa (dominio aéreo)
- Lee `properties["thrust_n"].value` con `source="declared"`
- Otros `output_magnitude` (ej. `"torque_nm"`) producen conteo de actuadores pero no override de fuerza
- Sin heurísticas de texto — si no está declarado con `source="declared"`, no se aplica override

Principio rector: **el resolver extrae, el engine interpreta**. La conversión de magnitudes (torque → fuerza, etc.) no es responsabilidad del resolver.

Trazabilidad — cuatro estados semánticos del resolver, mutuamente excluyentes:

```text
skipped              → no pasó elegibilidad (completeness bajo, sin declaración explícita)
count_only           → elegible y contado en motors, output_magnitude sin valor declarado o magnitud no conocida
missing_parameters   → elegible, contado, torque extraído y pasado al engine — conversión pendiente de parámetros externos
force_resolved       → fuerza extraída de properties["thrust_n"] con source="declared"
```

El trace incluye:
- `force_resolution_status` — estado global (máximo rango entre todos los entries elegibles)
- `force_resolution_detail` — lista con una entrada por componente elegible (`key` + `force_resolution_status` + `reason`)
  - `reason` valores: `missing_transmission_parameters` | `thrust_n_declared` | `thrust_n_not_declared` | `output_magnitude=<magnitud>`
- `eligible_for_count_only` — lista original con `reason` y `torque_nm_extracted` si aplica
- `skipped` — componentes descartados antes de elegibilidad

Rango de precedencia: `force_resolved (3) > missing_parameters (2) > count_only (1)`

- `skipped` — componente descartado en elegibilidad (completeness bajo, sin declaración)
- `eligible_for_count_only` — componente elegible y contado en `motors`, pero `output_magnitude` no soporta conversión directa a fuerza; cuando `output_magnitude == "torque_nm"` y el valor está declarado, se añade `torque_nm_extracted` a la entrada; el valor extraído se propaga a `PhysicalOverride.per_actuator_torque_nm`. En `force_resolution_detail` estos componentes aparecen como `missing_parameters`.
- fuerza resuelta — `per_motor_max_thrust_n` extraído de `properties["thrust_n"]`. En `force_resolution_detail` aparecen como `force_resolved`.

### Remap API → params internos (`workspace_manager.py`)

La API pública (`CreateProjectParams`) usa `motors: int | None` como nombre del campo (convención de la acción `create_project`). Al crear el workspace, `workspace_manager.create_project()` hace el remap:

```python
if "motors" in _params_dict:
    _params_dict["motor_count"] = _params_dict.pop("motors")
```

Esto ocurre **una sola vez en la frontera de entrada**. Todo el código downstream usa `motor_count`. La key `components["motors"]` (ComponentSpec) no se toca — son objetos y namespaces distintos.

### Recálculo

El recálculo vive en `core/calculation_engine.py`.

API dual-vocabulario:

- Acepta `actuator_count` o `motor_count` (el primero tiene precedencia). `motor_count` es el key canónico interno desde Fase 6 — el remap de `motors` → `motor_count` ocurre en `workspace_manager.create_project()`.
- Acepta `max_force_per_actuator_n` o `per_motor_max_thrust_n` (el primero tiene precedencia)

Esto permite usar el mismo motor de cálculo desde dominios aéreo y terrestre sin cambio destructivo.

Resolución de `per_motor_max_thrust_n` / `max_force_per_actuator_n`:

- **Ruta aérea** (prioridad): si `max_force_per_actuator_n` o `per_motor_max_thrust_n` están en `parameters` → fuerza directa
- **Ruta terrestre**: si `per_actuator_torque_nm` + `wheel_radius_m` + `gear_ratio` están en `parameters` → llama `calculate_traction_force_from_torque` → fuerza de tracción
- **Ruta incompleta (terrestre)**: `per_actuator_torque_nm` presente pero faltan parámetros de transmisión → registra `ToolResult(tool_name="missing_transmission_parameters")` en `tool_results`; `available_total_thrust_n = None`
- **Ruta hélice**: sin fuerza directa ni torque → acepta `propeller_diameter_in` (alias en pulgadas, se convierte `× 0.0254 → propeller_diameter_m`) o `propeller_diameter_m` (canónico interno) + `propeller_rpm` → llama `calculate_thrust_from_propeller`
- **Ruta incompleta (aéreo, hint presente)**: vehicle_type aéreo + algún param de `_PROPELLER_HINT_PARAMS` (`propeller_diameter_m`, `propeller_diameter_in`, `propeller_rpm`) presente pero incompleto → registra `ToolResult(tool_name="missing_propeller_parameters")`; `available_total_thrust_n = None`
- **Ruta incompleta (aéreo, sin hint)**: vehicle_type aéreo sin ningún dato de hélice → registra `ToolResult(tool_name="missing_propulsion_parameters")`; `available_total_thrust_n = None`
- Sin heurísticas de texto — si no está declarado con `source="declared"`, no se aplica override

`_PROPELLER_HINT_PARAMS: frozenset = {"propeller_diameter_m", "propeller_diameter_in", "propeller_rpm"}` — detecta si el usuario inició la ruta hélice aunque incompleta. Determina qué reason code se emite (específico vs. genérico). Un único punto de decisión sin lógica duplicada downstream.

`available_total_thrust_n` es `float | None` — puede ser `None` en dominio terrestre con parámetros de transmisión ausentes.

### Simulación

La validación vive en `simulation/simulator.py`.

Clase principal: `FeasibilitySimulator` (renombrada de `FlightSimulator`).
`FlightSimulator = FeasibilitySimulator` como alias de compatibilidad.

En la versión actual:

- compara fuerza disponible frente a requerida
- calcula `safety_margin_ratio`
- calcula `thrust_to_weight_ratio` (alias `force_to_weight_ratio` en schema)
- calcula `per_motor_load_ratio`
- deriva `quality = fail | risky | acceptable | good`
- emite `warnings` deterministas
- cuando `available_total_thrust_n is None` → rama `missing_parameters`: devuelve `SimulationResult` estructurado con `physics_status="missing_parameters"`, `quality="fail"`, warning con el **reason code emitido por el engine** (leído de `tool_results`), sin crash

`SimulationResult.physics_status: Literal["valid", "missing_parameters"]` — siempre presente, valor por defecto `"valid"`. Permite a UX y tests distinguir si la física fue evaluable o no.

`SimulationResult.propeller_status: Literal["valid", "missing_propeller_parameters"]` — campo **independiente** de `physics_status`. Se deriva exclusivamente de `tool_results`: si algún `ToolResult.tool_name == "missing_propeller_parameters"` → `propeller_status="missing_propeller_parameters"`, en cualquier otro caso `"valid"`. No entra en `warnings`. Patrón simétrico a `energy_status`.

`physics_status` fluye a la capa de razonamiento vía `simulation.model_dump()["physics_status"]` en `last_simulation`. `ReasoningLayer._extract_signals` lo convierte en la señal `missing_physics_parameters`, **con exclusión mutua**: si `propeller_status == "missing_propeller_parameters"`, la señal `missing_physics_parameters` se suprime y en su lugar se activa `missing_propeller_parameters`. El usuario recibe el mensaje específico, nunca dos mensajes solapados.

Cuando la señal `missing_propeller_parameters` es `True`:
- `_build_insights`: genera insight específico de hélice (nombrando `propeller_diameter_in` y `propeller_rpm`)
- `_build_tradeoffs`: añade tradeoff con nota sobre modelo Ct≈0.12
- `_build_suggested_actions`: devuelve acción de prioridad 0.99 (`Declarar propeller_diameter_in y propeller_rpm`) **antes** del bloque de física genérica

Cuando la señal `missing_physics_parameters` es `True` (propeller_status no activo):
- `_build_insights`: genera insight nombrando los params ausentes leídos desde `current_parameters`
- `_build_tradeoffs`: añade tradeoff sobre la imposibilidad de evaluar viabilidad
- `_build_suggested_actions`: devuelve acción de prioridad 0.99 (`Declarar <params>`) antes que cualquier otra ruta
- `_build_explanation`: usa rama específica ("El sistema no puede evaluar la viabilidad física…")

La lista de parámetros requeridos se deriva de `core/parameter_requirements.py`: un catálogo declarativo `reason_code → [params]` con labels, hints y keywords. Entradas actuales: `missing_transmission_parameters`, `missing_propulsion_parameters`, `missing_energy_parameters`, `missing_propeller_parameters`. El helper `_get_missing_force_reason(context)` lee el reason code de `simulation.warnings` — fuente única emitida por el engine — y lo usa para lookups del catálogo. Añadir un nuevo dominio de conversión (ej. hidráulico) solo requiere una nueva entrada en el catálogo.

`SimulationAnalysis.available_thrust_n` es `float | None` para acomodar el caso de parámetros ausentes.

Códigos de warning genéricos:

- `"low_force_to_weight_ratio"` (antes `"low_thrust_to_weight_ratio"`)
- `"high_actuator_load"` (antes `"high_motor_load"`)

### Abstracción de magnitudes físicas

`output_magnitude` es la abstracción que permite al sistema operar sobre diferentes dominios
sin conocer sus unidades específicas. Es el contrato entre el mundo declarativo y el físico.

Ejemplos actuales:

| `output_magnitude` | Dominio | Componente |
|---|---|---|
| `"thrust_n"` | aéreo | motor brushless |
| `"torque_nm"` | terrestre | motor de tracción |
| `None` | genérico | hélice, ESC, rueda pasiva |

El resolver utiliza esta clave para:
1. decidir elegibilidad de forma paramétrica (sin hardcodear nombres)
2. extraer el valor correcto de `properties`
3. decidir si puede producir un override de fuerza o solo conteo

Cuando se añada un nuevo dominio, solo hace falta definir un nuevo valor de `output_magnitude`
en la regla correspondiente — sin modificar el resolver.

### Limitaciones actuales del modelo físico

- El motor de cálculo soporta torque → fuerza, pero requiere `wheel_radius_m` + `gear_ratio` declarados explícitamente en `current_parameters`. Sin estos, `available_total_thrust_n` queda `None`.
- Modelo energético en tres capas (producto cerrado; lab = [`HARDWARE_DEBT.md`](HARDWARE_DEBT.md)): L1 `hover_energy_autonomy_min` = nameplate Wh / potencia de entrada de motor (Combo A ≈ 1.32 min — **no** es tiempo de vuelo ni cota inferior física). `calculate_autonomy_min` sigue siendo `(wh/w)×60` para el campo sim `autonomy_min`. Phase 2.6 (`P_battery`) y 2.7-A (autonomía *validada* bajo carga) **congelados**. L2 envelope **ESTIMATIVO** (4S, caller opt-in / product writer) es visible en `calcular`/`estado` — no SKU, no curva de descarga, no C-rate usable. `energy_status` / `autonomy_min` no entran en `warnings`.
- No existe acoplamiento componente auxiliar ↔ actuador: hélice (aéreo) y transmisión (terrestre) no se modelan todavía como parámetros físicos derivados.

El sistema soporta múltiples magnitudes vía `output_magnitude`. Para aéreo: conversión completa.
Para terrestre: conversión posible con parámetros de transmisión declarados.

### Herramientas de mecánica genérica

Ubicación: `tools/mechanics.py`

Funciones canónicas:

- `calculate_required_force(weight_n, safety_factor)` → `required_force_n`
- `calculate_force_per_actuator(required_force_n, actuator_count)` → `force_per_actuator_required_n`
- `calculate_traction_force_from_torque(torque_nm, wheel_radius_m, gear_ratio)` → `traction_force_n`
  Fórmula: `F = (torque_nm × gear_ratio) / wheel_radius_m`

Aliases semánticos aéreos (sin lógica propia — delegan a las canónicas):

- `calculate_required_thrust` → alias de `calculate_required_force`
- `calculate_thrust_per_motor` → alias de `calculate_force_per_actuator`

### Herramientas de electricidad / energía

Ubicación: `tools/electricity.py`

Funciones:

- `calculate_autonomy_min(battery_capacity_wh, total_power_w)` → `autonomy_min` (minutos)
  Fórmula: `t = (wh / w) × 60`
- `estimate_loaded_endurance(...)` — L2 **opt-in** (Phase 2.7-B). Fórmula parametrizada; **no** inventa Voc/R/I por defecto. El grid de producto 4S vive en `core/endurance_sweep_writer.py` (no en este archivo). DSE no llama al writer.

### Herramientas de aerodinámica

Ubicación: `tools/aerodynamics.py`

Funciones:

- `calculate_thrust_from_propeller(diameter_m, rpm, ct=0.12, air_density=1.225)` → `thrust_n` (N)
  Fórmula: `T = Ct · ρ · n² · D⁴` donde `n = rpm / 60`
  Modelo simplificado — Nivel 1. Coeficiente `Ct` típico para UAV: 0.12.
  El parámetro `ct` puede sobreescribirse vía `propeller_ct` en `parameters`.

Parámetros del proyecto que activan la ruta de inferencia en `calculation_engine`:

| Parámetro              | Tipo    | Descripción                                        |
|------------------------|---------|-----------------------------------------------------|
| `propeller_diameter_m` | float   | Diámetro de hélice en metros (canónico interno)    |
| `propeller_diameter_in`| float   | Diámetro de hélice en pulgadas (alias de entrada, convertido `× 0.0254`) |
| `propeller_rpm`        | float   | RPM del motor                                      |
| `propeller_ct`       | float   | Ct personalizado (opcional, def. 0.12)   |
| `air_density_kg_m3`  | float   | Densidad del aire (opcional, def. 1.225) |

Prioridad de resolución de `per_motor_max_thrust_n` en el motor de cálculo:

1. Declarado directo (`per_motor_max_thrust_n` / `max_force_per_actuator_n`)
2. Torque → tracción (`per_actuator_torque_nm` + conversión)
3. **Inferencia aerodinámica** (`propeller_diameter_m` + `propeller_rpm` → `calculate_thrust_from_propeller`)

El campo `SimulationResult.propeller_thrust_inferred: bool` indica si el empuje fue estimado
desde la hélice. El `ReasoningLayer` lee este campo y emite insight + tradeoff específicos.

### Aliases genéricos en schemas

Ubicación: `schemas/tool_schema.py`

`CalculationBundle` expone propiedades genéricas sobre los campos originales:

```python
@property def actuator_count(self) → int: return self.motors
@property def required_force_n(self) → float: return self.required_thrust_n
@property def available_total_force_n(self) → float: return self.available_total_thrust_n
@property def force_per_actuator_required_n(self) → float: return self.thrust_per_motor_required_n
```

`SimulationResult` expone:

```python
@property def constraints_satisfied(self) → bool: return self.can_fly
@property def force_to_weight_ratio(self) → float: return self.thrust_to_weight_ratio
```

Principio: los campos originales nunca se eliminan; los aliases permiten que código nuevo
use vocabulario neutro sin romper código existente.

### Persistencia

### Mirrored Param Contract

> **Regla estructural activa — no diferible.**

Todo writer que gestione un componente físico tiene la obligación de escribir en **dos lugares simultáneamente**:

| Capa | Dónde | Por qué |
|------|-------|---------|
| Canónica | `design_properties.components[key]` | Fuente única de verdad del componente |
| Bridge físico | `current_parameters[param]` | Mirror para que `calculation_engine` consuma el valor |

Si la capa bridge falta, el engine calcula con datos desactualizados **sin lanzar ningún error** (fallo silencioso).

**Flujo garantizado:**

```
ComponentSpec → writer → current_parameters → calculation_engine
                  └───→ design_properties.components
```

**Params mirrored actuales** (`COMPONENT_MIRRORED_PARAMS` en `system_architecture_catalog.py`):

| Param | Writer | Key en components |
|-------|--------|-------------------|
| `battery_capacity_wh` | `set_battery_component` | `components["battery"]` |
| `motor_power_w` | `set_motor_component` | `components["motors"]` |
| `propeller_diameter_in` | `set_propeller_component` | `components["propellers"]` |

**Checklist para añadir un nuevo mirrored param:**

1. Añadir la clave a `COMPONENT_MIRRORED_PARAMS`
2. Crear (o extender) su writer en `component_writers.py` cumpliendo ambas capas
3. Añadir spec builder `_make_*_spec` en `param_definition_session.py`
4. Añadir rama en el bloque `if blocked:` de `apply_and_recalculate`
5. Añadir test `test_mirrored_param_contract_*` en `test_d4_param_gatekeeper.py` verificando `(1)` y `(2)`

**Enforcement:** `test_d4_param_gatekeeper.py::TestParamGatekeeper` — tres tests nombrados `test_mirrored_param_contract_*` verifican que tras `save_state` tanto `design_properties.components[key]` como `current_parameters[param]` contienen el valor declarado.

---

### Component writers

Ubicación: `core/component_writers.py`

Funciones puras extraídas de `JarvisOrchestrator` para eliminar el import circular `orchestrator → design_explorer → orchestrator` (prerequisito DA2).

Cada función es el único punto de escritura para su componente — recibe `ProjectState` y devuelve un `ProjectState` nuevo sin persistir.

| Función | Escribe en |
|---|---|
| `set_frame_material(state, mass_kg, material)` | `components["frame"]` + `current_parameters["structure_mass_override_kg"]` |
| `set_battery_component(state, spec, capacity_wh)` | `components["battery"]` + `current_parameters["battery_capacity_wh"]` |
| `set_motor_component(state, spec, power_w)` | `components["motors"]` + `current_parameters["motor_power_w"]` — preserva `motor_count` de la declaración anterior si el nuevo spec no lo incluye (Bug 78: doble write de motores no pierde el conteo) |
| `set_propeller_component(state, spec)` | `components["propellers"]` + `current_parameters["propeller_diameter_in"]` (D6 bridge) |
| `set_control_component(state, spec)` | `components[key]` genérico (sin params derivados) |
| `apply_components_delta(state, components_delta)` | Orquesta todos los writers en `_APPLY_ORDER` (DA2) |

**`apply_components_delta(project_state, components_delta) → ProjectState`** (DA2):
- `_APPLY_ORDER = ("frame", "battery", "motors", "propellers")` — orden determinista independiente del dict de entrada
- Para cada clave en `_APPLY_ORDER`: usa el spec del delta si existe; si no, re-aplica el componente existente en `design_properties.components` (normalización de baseline)
- Claves fuera de `_APPLY_ORDER` (flight_controller, sensores…) → `set_control_component`
- Con delta vacío `{}`: re-deriva todos los params desde componentes existentes — normalización de baseline
- Acceso defensivo a `design_properties` vía `getattr` para compatibilidad con `SimpleNamespace` de tests legacy
- Pura: no persiste ni dispara efectos secundarios

La acción real de `iterate` vive en `actions/iterate.py`.

Pipeline:

1. cargar proyecto real
2. construir estado mutable base (`_build_mutable_state` — lee `design_properties.structure` como fuente canónica, fallback a `current_parameters` para retrocompat)
3. aplicar mutación
4. si la iteración es física:
   - `_apply_mutation_to_parameters` — actualiza `current_parameters` (payload, material como etiqueta, overrides numéricos)
   - `_apply_design_property_mutation` — actualiza `design_properties.structure` con `density`/`volume` del mutated_state
   - aplicar overrides efímeros de propulsión desde `component_resolver` (si hay componentes elegibles)
   - recalcular con los parámetros resultantes
   - simular con `autonomy_threshold` desde `parsed_constraints`
5. si la iteración es declarativa: `_apply_design_property_mutation` únicamente y omitir cálculo/simulación
6. persistir estado con `design_properties` actualizado (ambos flujos)
7. generar sugerencias si hay contexto físico disponible
8. persistir artefactos
9. actualizar `state.json`
10. registrar historial

## Design Space Explorer (DSE)

Ubicación: `core/design_explorer.py`

### Visión general

El DSE explora automáticamente un conjunto de configuraciones alternativas a partir del estado actual del proyecto y un objetivo declarado. Es una operación 100% en memoria: no escribe en disco, no llama a `record_action` ni muta `state.json`.

Entradas: `project_state` + `goal_key` → Salida: `ExplorationResult`

### Objetivos soportados

| `goal_key` | Descripción | Score function |
|---|---|---|
| `mejorar_autonomia` | Maximizar autonomía de vuelo | `sim.autonomy_min` |
| `aumentar_payload` | Maximizar carga útil viable | `sim.safety_margin_ratio × calc.payload_kg` |
| `reducir_masa` | Minimizar masa total | `-calc.total_mass_kg` |
| `mejorar_estabilidad` | Maximizar margen de seguridad | `sim.safety_margin_ratio` |

### Grids de exploración

Hay dos tipos de grids, ambos evaluados en `explore()` y mezclados en el ranking final:

**`EXPLORATION_GRIDS`** — variaciones de `current_parameters` expresadas como deltas:
- `{param}_factor` → multiplica el valor actual por el factor
- `{param}_delta` → suma un entero al valor actual (para conteos discretos como `motor_count`)
- `{param}_value` → fija un valor absoluto

**`COMPONENT_VARIATION_RULES`** (G1) — tabla declarativa de variaciones de componentes. Cada regla define `component_key`, `component_type`, `property_name`, `unit` y `values`. `_build_component_candidates_for_goal(goal_key)` genera los `dict[component_key, ComponentSpec]` a partir de esta tabla — sin lógica de dominio en el generador.

Reglas actuales:

| Goal | Componente | Propiedad | Valores |
|---|---|---|---|
| `mejorar_autonomia` | `battery` | `battery_capacity_wh` | 300 / 500 / 800 / 1200 Wh |
| `aumentar_payload` | `motors` | `power_w` | 150 / 200 / 300 / 400 W |
| `reducir_masa` | `frame` | `mass_kg` | 0.280 / 0.350 / 0.450 kg |
| `mejorar_estabilidad` | `frame` | `mass_kg` | 0.500 / 0.700 kg |

Añadir un nuevo componente (rueda, depósito, brazo...) solo requiere una nueva entrada en `COMPONENT_VARIATION_RULES` — no se toca `_build_component_candidates_for_goal` ni `explore()`.

### `_apply_delta(base_params, delta) → dict | None`

Aplica un delta sobre `base_params` y devuelve un nuevo dict. Devuelve `None` si algún parámetro referenciado no existe en `base_params` — el candidato se omite sin error. Filtra `COMPONENT_MIRRORED_PARAMS` antes de aplicar: esos params solo llegan via `components_delta`.

### `_score_candidate(sim, calc, goal_key) → float`

Escalar de scoring. Mayor = mejor para todos los goals. Para `reducir_masa` se niega `total_mass_kg` para que el sort descendente funcione.

### `DesignExplorer.explore(project_state, goal_key) → ExplorationResult`

Flujo (DA2):
1. **Baseline normalizado**: `apply_components_delta(project_state, {})` re-deriva `current_parameters` desde los componentes existentes antes de calcular el baseline. Garantiza comparabilidad entre baseline y candidatos component-driven.
2. **Bucle params** (`EXPLORATION_GRIDS`): aplica `_apply_delta` → `_evaluate(params)` → `ExplorationCandidate(components_delta={})`
3. **Bucle componentes** (`COMPONENT_VARIATION_RULES`): `_build_component_candidates_for_goal(goal_key)` genera los deltas → aplica `apply_components_delta(normalized_state, comp_delta)` → extrae `current_parameters` → `_evaluate(params)` → `ExplorationCandidate(params_delta={})`
4. Candidatos con `_apply_delta = None`, `comp_delta` vacío, o que lanzan excepción se omiten
5. Candidatos `can_fly=True` van a `viable`; todos van a `candidates`
6. `viable.sort(key=score, reverse=True)` → top `MAX_VIABLE = 5`

**Cache**: `_evaluate(params)` usa `frozenset(params.items())` como clave — evita recalcular combinaciones idénticas entre ambos bucles dentro de una misma llamada a `explore()`.

### Helpers de spec y builder genérico

`_build_component_spec(component_key, component_type, property_name, unit, value) → ComponentSpec` — constructor genérico domain-agnostic. Produce specs con `completeness="medium"` y `source="declared"` — elegibles por `apply_components_delta`.

`_battery_spec(wh)`, `_motor_spec(w)`, `_frame_spec(kg)` — wrappers de conveniencia sobre `_build_component_spec`, usados directamente en tests de fixture.

### Schemas

- `ExplorationCandidate` — `params_delta`, `components_delta` (DA2), `generation_metadata` (reservado v2), `calculations`, `simulation`, `score`, `label`, `improvement`
- `ExplorationResult` — `goal_key`, `goal_label`, `baseline_score`, `baseline_calculations`, `baseline_simulation`, `candidates`, `viable`

### Labels

- `_build_label(delta, applied)` — label para candidatos params-driven: `"batería (Wh)=800"`
- `_build_label_components(components_delta)` (DA2) — label para candidatos component-driven: `"battery: battery_capacity_wh=800.0"`

### Intent routing (DSE v1)

`IntentResolver.EXPLORE_PATTERNS` — expresiones regulares que detectan solicitudes de exploración. Evaluadas **antes** de `ITERATE_PATTERNS` para evitar falso routing al wizard de iteración.

`resolve_explore_goal(text) → str | None` — detecta el `goal_key` del texto libre. Devuelve `None` si no se reconoce objetivo; el orquestador cae a `_handle_analyze`.

`_handle_explore` en el orquestador:
1. Carga `project_state` (FileNotFoundError → `_handle_analyze`)
2. Valida `goal_key` en `EXPLORATION_GRIDS` (None o ausente → `_handle_analyze`)
3. Llama `DesignExplorer.explore()`
4. Construye mensaje con tabla de candidatos viables
5. **Persiste `ExplorationResult` en `session.last_exploration_result`** (DSE v1.1)

### Apply (DSE v1.1 / DA2)

Cierra el loop: permite al usuario decir «aplica la mejor» tras una exploración para escribir `viable[0]` en el proyecto.

`IntentResolver.APPLY_PATTERNS` — detectado **antes** que `EXPLORE_PATTERNS` para que «aplica la mejor» no caiga en `explore_design_space`.

`_handle_apply_exploration` en el orquestador (con rama DA2):
1. Lee `session.last_exploration_result` (None → error)
2. Verifica `exploration.viable` no vacío
3. Carga `project_state` (FileNotFoundError → error)
4. `best = exploration.viable[0]` (mayor score)
5. **Rama `best.components_delta` no vacío** (DA2): `apply_components_delta(project_state, best.components_delta)` → `updated_project`; `canonical_params = dict(updated_project.current_parameters)`; `base_state_for_save = updated_project` (preserva componentes actualizados)
6. **Rama params-only** (original): `_apply_delta(base_params, best.params_delta)` → `canonical_params` (None → error + instrucción manual); `base_state_for_save = project_state`
7. `calculation_engine.build(canonical_params)` → `calculations`
8. `simulator.evaluate(calculations, autonomy_threshold)` → `simulation`
9. `workspace_manager.save_iteration_snapshot(...)` — `history/iterations/iter_NNN.json`
10. `state_manager.record_action(...)` sobre `base_state_for_save.model_copy(update={"current_parameters": canonical_params})` + `workspace_manager.save_state()` — `state.json` actualizado
11. `workspace_manager.append_event("dse_apply", ...)` — `history/events.jsonl`
12. `workspace_manager.render_views(...)` — vistas Markdown regeneradas
13. Mensaje con params cambiados + resultados reales; aviso si `best.score <= baseline_score`; `⚠` warning inline si `_check_constraint_violations` detecta que la nueva masa total viola `max_weight_kg` (mismo patrón U5 — informativo, nunca bloquea).

**Garantía DA2:** cuando el candidato es component-driven, `base_state_for_save` ya tiene `design_properties.components` actualizado → se persiste tanto el componente como los params derivados en un único `record_action`.

**Garantías de trazabilidad:** el apply sigue los mismos 5 pasos de persistencia que una iteración física (`save_iteration_snapshot → record_action → save_state → append_event → render_views`). El audit trail queda completo.

**`session.last_exploration_result: Any | None`** — campo en `InteractiveSessionState` (`Any` para evitar ciclo de importación `action_schema → design_explorer → calculation_engine`). Se escribe en `_handle_explore` y se lee en `_handle_apply_exploration`. No se persiste en `state.json` — es temporal de sesión.

## Flujo `calculate`

La acción real vive en `actions/calculate.py`.

Pipeline:

1. resolver proyecto activo
2. cargar `state.json`
3. recalcular usando `current_parameters`
4. guardar snapshot en `history/calculations/calc_NNN.json`
5. registrar evento en `history/events.jsonl`
6. renderizar vistas en `views/`
7. actualizar historial sin crear nueva iteración

## Flujo `simulate`

La acción real vive en `actions/simulate.py`.

Pipeline:

1. resolver proyecto activo
2. reutilizar cálculos persistidos o recalcular si faltan
3. ejecutar simulación
4. generar sugerencias no vinculantes
5. guardar snapshot en `history/simulations/sim_NNN.json`
6. registrar evento en `history/events.jsonl`
7. renderizar vistas en `views/`
8. actualizar historial sin crear nueva iteración

## Motores del sistema

### Mutation engine

Ubicación: `core/mutation_engine.py`

Función:

- convertir intención de alto nivel en cambios de variables base
- convertir definiciones declarativas en parches sobre `design_properties`

No debe:

- calcular física
- simular
- escribir en disco

### Calculation engine

Ubicación: `core/calculation_engine.py`

Función:

- recalcular dependencias técnicas a partir de variables base

### Planner v0

Ubicación: `core/planner.py`

Función:

- generar planes compuestos a nivel de acción
- validar coherencia mínima del plan
- no expandir pipelines internos como `iterate`

Regla de uso:

- acciones simples se ejecutan directamente por el orquestador
- el planner solo se usa para objetivos compuestos

Casos soportados:

- `create_and_simulate`
- `recalculate_and_simulate`
- `iterate_and_validate`

### Historial conversacional

Ubicación: campo `conversation_history` en `RuntimeState` (solo RAM, no persiste).

Función:

- guardar los últimos N intercambios usuario/asistente de la sesión actual
- inyectarlos como mensajes anteriores en el payload del LLM (rutas `analyze` y fallback `unknown`)
- permitir que el LLM resuelva referencias contextuales (`"mi próximo cambio"`, `"el mismo material"`, etc.)

Reglas:

- máximo configurable: `MAX_HISTORY_TURNS = 6` (3 intercambios)
- nunca entra en `mutation_engine`, `calculation_engine` ni `simulator`
- no entra en sesiones interactivas (`ITERATE_INTERACTIVE`, `CREATE_PROJECT_INTERACTIVE`) — usan contexto estructurado propio
- se limpia al cargar un proyecto nuevo desde la CLI

### Memory v0

Ubicación:

- `memory/memory_manager.py`
- `state.json`

Función:

- guardar resoluciones explícitas de conflicto
- guardar preferencias binarias explícitas derivadas de esas resoluciones
- reutilizar esa información solo en mensajes de interacción

No debe:

- decidir por el usuario
- modificar motores
- introducir lógica implícita

### Simulator

Ubicación: `simulation/simulator.py`

Función:

- validar la viabilidad técnica y la calidad básica de la configuración

API: `evaluate(calculations: CalculationBundle, autonomy_threshold: float | None = None) → SimulationResult`

El simulador no parsea strings. Las restricciones llegan como `float | None` (leer desde `project_state.parsed_constraints`). El warning `autonomy_below_restriction` se emite cuando `autonomy_min < autonomy_threshold`.

### Suggestion engine v0

Ubicación: `suggestions/suggestion_engine.py`

Función:

- leer cálculos y simulación ya generados
- proponer opciones posibles de mejora
- no modificar estado
- no ejecutar iteraciones
- no usar LLM

## Acciones actuales

### Implementadas

- `create_project`
- `calculate`
- `simulate`
- `iterate`

## Estado actual del sistema

Implementado:

- workspace persistente
- `state.json`
- `create_project` directo
- `create_project_interactive`
- `calculate`
- `simulate`
- `iterate_interactive`
- ejecución real de `iterate`
- `mutation_engine`
- `calculation_engine`
- `planner` v0
- planner solo para secuencias compuestas
- LLM interface validada
- `FeasibilitySimulator` v1+ con métricas y warnings genéricos (`FlightSimulator` como alias)
- `suggestion_engine` v0 con sugerencias no vinculantes
- `design_properties` tipadas y persistidas en `state.json`
- `memory` v0 mínima en `state.json`
- CLI mínima de terminal para prueba real conectada a Ollama
- historial por iteraciones
- `SemanticState` + `SemanticInterpreter` — interpretación acumulativa slot-driven
- flujo `decide()` en iterate: proceed / confirm / clarify con límite de clarificación
- bienvenida contextual en CLI con selección de proyecto existente
- **arquitectura multi-dominio** — `ComponentRule` + `ComponentRuleRegistry` + Protocols
- dominio aéreo: `domains/aerial.py` — 7 reglas (motores, hélices, ESC, batería, frame, flight controller, sensores) con extractores regex
- dominio terrestre: `domains/ground.py` — motores de tracción, ruedas pasivas, torque/rpm
- `domains/registry_selector.py` — routing híbrido (vehicle_type + heurística de texto + default aéreo)
- `component_inference.py` refactorizado como dispatcher con registro inyectable
- `component_resolver.py` — `PhysicalOverride` genérico + `_ACTIVE_ACTUATOR_TYPES` frozenset + `reason` field en `force_resolution_detail`
- `calculation_engine.py` — vocabulario dual (`actuator_count|motors`, `max_force_per_actuator_n|per_motor_max_thrust_n`)
- `tools/mechanics.py` — funciones genéricas `calculate_required_force` / `calculate_force_per_actuator`
- aliases genéricos en `schemas/tool_schema.py` (`actuator_count`, `constraints_satisfied`, `force_to_weight_ratio`)
- `component_inference` — inferencia determinista de tipo de componente
- componentes unificados como fuente única de verdad en `design_properties.components`
- `component_resolver` — puente determinista declarativo → físico (overrides efímeros de propulsión)
- `PhysicalOverride.per_actuator_torque_nm` — extracción de torque declarado; `apply_to` lo inyecta en `current_parameters`; engine convierte con `wheel_radius_m` + `gear_ratio`
- `tools/mechanics.py` — `calculate_traction_force_from_torque` — dominio terrestre completo
- `calculation_engine.py` — ruta terrestre: `torque → force`; ruta aerial (prioridad); ruta hélice (tercer nivel, acepta `propeller_diameter_in` alias con conversión `×0.0254`); `_PROPELLER_HINT_PARAMS` frozenset para intent detection; tres ramas de razón mutuamente excluyentes: `missing_propeller_parameters` (aéreo + hint), `missing_propulsion_parameters` (aéreo sin hint), `missing_transmission_parameters` (terrestre)
- `parameter_requirements.py` — catálogo declarativo único para `reason_code → parámetros → labels/hints/keywords` (entradas `missing_transmission_parameters`, `missing_propulsion_parameters`, `missing_energy_parameters`, `missing_propeller_parameters`); `MISSING_FORCE_REASONS` frozenset incluye `missing_propeller_parameters`
- `schemas/tool_schema.py` — `PropellerStatus = Literal["valid", "missing_propeller_parameters"]`; `propeller_status: PropellerStatus = "valid"` en `SimulationResult` (campo independiente, patrón simétrico a `energy_status`)
- `simulation/simulator.py` — `propeller_status` derivado exclusivamente de `tool_results`; no altera `physics_status` ni `warnings`
- `reasoning_layer.py` — señal `missing_propeller_parameters` con exclusión mutua (`missing_physics_parameters` suprimida cuando `missing_propeller_parameters` activa); insight + tradeoff + suggested action (priority 0.99) específicos de hélice; cero hardcoding de dominio downstream
- `phase_layer.py` — `PhaseLayer.infer(signals, simulation)`: 4 fases deterministas (`definition`, `physical_validation`, `optimization`, `complete`); reglas en prioridad estricta; reutiliza `HIGH_MARGIN_THRESHOLD` de `reasoning_layer`
- `build_startup_context()` — snapshot operativo sin LLM; jerarquía 4 niveles; `active_variables` y `suggested_action` con hint; `phase`/`phase_description`/`phase_confidence`; `proactive_question` + `missing_params` cuando blocking
- `OrchestratorMode.DEFINE_MISSING_PARAMETERS` — sesión ligera para recolección de parámetros numéricos + recalculo directo; sin LLM; sin `iterate_interactive`; `param_definition_reason` identifica el origen; `ParamDefinitionSession` usa `parameter_requirements.py` para parseo semántico con fallback posicional
- `IntentResolver` — `project_status` intent; `STATUS_PATTERNS` + `GUIDANCE_PATTERNS` (FN-023 next-step help) antes de `ANALYZE`; consultas de estado/orientación no entran por `analyze`
- **Acquisition Fluency + Continuity (FN-014…023)** — `acquisition_target` / `acquisition_brief` / `project_continuity` / `classify_component`; IDLE Engineering Intent (`is_engineering_intention` → `goal_plan`); session hygiene a IDLE (FN-021). Field notes: `PROJECT_CONTINUITY.md`. Create→BOM y Step D: aún no en este mapa.
- `knowledge/library.py` — capa de biblioteca determinista (no RAG): `ComponentLibrary` carga catálogos JSON desde `library/` (`motores`, `helices`, `baterias`, `esc`, `frames`, `kit_hardware`, `materiales`, **`fc`**, **`sensors`**). Lookups exactos (`get_material`, `get_motor`, `get_fc`, `get_sensor`, …), sugerencia por KV / espacio de diseño. Sin match → hueco honesto, nunca inventar SKU. FC/GPS L×W×H viven aquí — no en `domains/aerial.py`.
- `tools/mechanics.py` — (histórico) `calculate_autonomy_min` vivió aquí; canónico ahora en `electricity.py`
- `tools/electricity.py` — `calculate_autonomy_min` `(wh/w)×60`; `estimate_loaded_endurance` (L2 opt-in, sin Voc/R/I por defecto)
- `core/endurance_sweep_writer.py` — writer de producto 4S ESTIMATIVO (`build_with_estimative_sweep`); no persiste el sweep; DSE / wizard / create no lo llaman
- `schemas/tool_schema.py` — `EnergyStatus` type; `energy_status` + `autonomy_min` en `SimulationResult`; `autonomy_min: float | None` en `CalculationBundle`
- `calculation_engine.py` — bloque energético: `hover_energy_autonomy_min` (L1, siempre que aplique); `autonomy_min` `(wh/w)×60`; L2 envelope **solo** si el caller ya puso `battery_endurance_sweep` (el writer de producto no vive aquí)
- `simulation/simulator.py` — `energy_status` derivado del trace; campo independiente (no entra en `warnings`)
- `reasoning_layer.py` — señal `missing_energy_parameters`; insight + tradeoff + suggested action para energía; `_detect_missing_energy_params`; prioridad: `missing_physics_parameters` > `declarative_context` > `missing_energy_parameters`
- `parameter_requirements.py` — metadata de `battery_capacity_wh` y `motor_power_w`; proactive question de energía sin restricción de fase
- `main.py` — `render_startup_context`: warning de batería cuando `missing_energy_parameters` activo
- **FASE_LLM — intérprete semántico de iterate**: `SemanticIntentAdapter` (resolución de variable en 4 pasos: canonical → normalizado → alias → concepto; `AdaptRejection` para derivadas y desconocidas; `_parse_value` sanitiza unidades; `CONFIDENCE_THRESHOLD = 0.75`); `ActionPolicy._validate_iterate_variable` rechaza variables ausentes del registry antes del adapter; `orchestrator._semantic_preseed` routing confidence-based (≥ 0.75 → wizard paso 2, variable derivada → paso 0 + mensaje del registry, demás → paso 0 normal); `llm_client._build_semantic_trace` loguea `{variable, confidence, routing}` por cada evento iterate
- `conversation_history` en `RuntimeState` — `ConversationTurn`, máx 6 turnos; inyectado en `analyze` y fallback LLM; no persiste en disco; se limpia al cargar proyecto nuevo
- `SystemDefinitionSession` — transición de "parámetros sueltos" → "arquitectura estructurada"; lanzado post-`create_project`; catálogos de datos puros (`system_architecture_catalog.py`, `system_dependency_catalog.py`); `DependencyGraph` + `PriorityEngine` DFS topológico; `system_priority: list[str]` persistido en `DesignProperties`; bridge automático `SYSTEM_DEFINITION → DEFINE_MISSING_PARAMETERS`
- **Pipeline hélice activo (Fase 2)**: `PropellerStatus` en `SimulationResult`; conversión `propeller_diameter_in × 0.0254`; `_PROPELLER_HINT_PARAMS` intent detection; exclusión mutua en reasoning; proactive collection en `build_startup_context()`; `MISSING_FORCE_REASONS` ampliado; 27 tests en `test_propeller_pipeline.py`
- **Design Space Explorer (DSE v1)**: `core/design_explorer.py`; `DesignExplorer.explore()`; 4 objetivos (`mejorar_autonomia`, `aumentar_payload`, `reducir_masa`, `mejorar_estabilidad`); `EXPLORATION_GRIDS` con deltas `_factor`/`_delta`/`_value`; scoring por goal; `ExplorationCandidate` + `ExplorationResult` Pydantic; operación 100% en memoria sin mutación de estado; `EXPLORE_PATTERNS` antes que `ITERATE_PATTERNS` en `IntentResolver`; `resolve_explore_goal()` para detección de objetivo en lenguaje natural
- **Design Space Explorer (DSE v1.1)** — apply: `APPLY_PATTERNS` antes que `EXPLORE_PATTERNS`; `session.last_exploration_result: Any | None` en `InteractiveSessionState`; `_handle_apply_exploration()` aplica `viable[0]` con pipeline completo de persistencia (`save_iteration_snapshot → record_action → save_state → append_event → render_views`); aviso si `best.score <= baseline_score`; edge cases cubiertos (sin exploración, viable vacío, sin proyecto, `_apply_delta` None)
- **D6 — propellers physics bridge**: `set_propeller_component()` escribe `propeller_diameter_in` en `current_parameters` desde `spec.properties["diameter_in"]`; key añadida a `COMPONENT_MIRRORED_PARAMS`; 3 tests en `TestPropellersPhysicsBridge` (`test_propulsion_composite_wizard_flow.py`)
- **D4 — mirrored param bridge**: `ParamDefinitionSession.apply_and_recalculate()` intercepta `COMPONENT_MIRRORED_PARAMS` y los enruta a través de los component writers (battery/motor/propeller) en vez de escribirlos directamente — ver **Mirrored Param Contract**; `try_ingest()` ignora mirrored params en `missing_params`; `_apply_delta()` en `design_explorer.py` filtra mirrored params del delta antes de aplicar; 5 tests en `TestParamGatekeeper` (`test_d4_param_gatekeeper.py`) — 3 de ellos nombrados `test_mirrored_param_contract_*` como enforcement del contrato
- **DA2 — components_delta en DSE**: `core/component_writers.py` con 6 writers + `apply_components_delta()` (orden `_APPLY_ORDER`, baseline normalization, defensivo a SimpleNamespace); `ExplorationCandidate.components_delta` + `generation_metadata`; `_build_label_components`; `explore()` con baseline normalizado + cache param-hash + bucle componentes paralelo al bucle params; `_handle_apply_exploration` ramifica en `best.components_delta` → `apply_components_delta` → `base_state_for_save = updated_project`; 11 tests en `test_da2_components_delta.py`
- **G1 — COMPONENT_VARIATION_RULES**: tabla declarativa de variaciones de componentes reemplaza `COMPONENT_GRIDS`; `_build_component_spec` (builder genérico domain-agnostic); `_build_component_candidates_for_goal` (generador sin lógica de dominio); `_battery_spec`/`_motor_spec`/`_frame_spec` como wrappers de conveniencia para tests; `reducir_masa` + `mejorar_estabilidad` añaden variaciones de frame (0.280–0.700 kg); 3 nuevos tests en `TestFrameComponentGrid` en `test_da2_components_delta.py`; 1216 tests passing
- **Fase 4 (energy composite)**: `BLOCK_TYPE["energy"] = "composite"`; `_set_battery_component()` + `_set_motor_component()` como únicos puntos de escritura; `COMPONENT_MIRRORED_PARAMS` frozenset; `_block_progress_status` rama composite AND-strict; `_set_pending_next_block` Phase A/B; `build_startup_context` composite hint; DA-MOTORS-2 documentada
- **Fase 5 (wizard dinámico composite)**: `_set_pending_next_block` rama composite genérica; supresión de `missing_energy_parameters` en Phase A; `_BLOCK_COMPONENT_HINTS["energy"]` Phase A hint
- **Fase 6 (propulsion composite)**: `BLOCK_TYPE["propulsion"] = "composite"` (motors + propellers + params); DA-MOTORS-3 resuelto (`workspace_manager` remap `motors` → `motor_count`); `_set_propeller_component()` + routing en `_handle_component_description`; `_COMPONENT_PROMPTS["propellers"]` + `_BLOCK_COMPONENT_HINTS["propulsion"]`; `motor_count` key canónico en `parameter_requirements.py` con aliases `("motores", "num_motores", "motors")`; `calculation_engine` lee `motor_count` (con fallback `actuator_count`); DA-MOTORS-2 implementada (Opción B: componente compartido)
- **CLI Polish (checkpoint-continuity-polish, 2026-08-18)**: `project_continuity` G9-B catalog-gap demotion; `LIST_MOTORS_PATTERNS` + `_handle_list_motors`; aerial `definir motores` orchestrator gate (G18); force-motors when completeness `high` (G17 partial); `_fresh_pending_keys_for_block` (FN-013/G12 partial); reasoning label bridge to list-motors/DSE (G19). 1768 tests. Post-checkpoint micro-fix `d224dc1` closed G20/G20-B with dynamic composite in-progress labels. Residual: G17 IDLE bare phrase, G14 propeller routing — see `.jes/artifacts/cli_findings_post_catalog_bind_v1.md`.
- **Project Closure arc (IC 1–3, `checkpoint-closure-policy`, 2026-08-31)**: Requirements explicit-none + G26 write path (`checkpoint-requirements-closure`); battery catalog pick + G27 hardening (`checkpoint-battery-catalog-bind-ux`); closure policy doc sync + propeller `sku_resolved` display fix (`checkpoint-closure-policy`). Suite **1976**. Product contract: `ENGINEERING_READINESS_VISION.md` §11. Deferred at the time: G24, H5 ESC catalog, frame SKU catalog, `catalog_bound`→verdict wiring.
- **Structure representation arc (2026-09-04→05, post-`v0.3.6`):** Frame catalog IC-1→3 · honesty `PASS *` · Parts Graph Fase 1 · G-N1 · IDLE rebind B2+B3 · arm `thickness_mm` · plate multiplicity (`PlateSeed`/`plates[]`/ordinal siblings/`label`) — suite **2294** at Structure close. M0; Structure PASS evidence unchanged; free-text multi-plate + MEASURE wall = debt. Detail: `ENGINEERING_READINESS_VISION.md` §8 + `PHYSICAL_COMPONENT_CATALOG_V1.md` §13.
- **Spatial board (2026-09-05→06):** viewport + projector hotfix **v0.3.8** + B3 honest-absence slots — suite **2310**. Visor read-only; slots ≠ BOM. Layout still `localStorage`.
- **Geometry `representar` + sensors claim-copy (2026-09-06→07):** Battery/Motor/ESC catalog envelopes + FC Pixhawk 4 identity-linked dims + sensors BOM honesty — suite **2336**. Package **0.3.8**.
- **Continuity spatial assembly (2026-09-08→10) → tag `v0.4.0`; Board Situar patch → `v0.4.1`:** CSS 3D + click-inspect · Continuity pose · Scene3D-from-pose · multi-hop · assembly root · declared envelopes · visor X · standoff corners · **C-113** Situar drag (free camera, screen-plane) · standoff count gate. Feature lock: `.jes/artifacts/engineer_lock_continuity_spatial_assembly_feature.md`.
- **Craft montage arc (2026-09-13→14, still `v0.4.1`):** sourced-only catalog purge + MY5 frame · estimated-temporary plate · Path F + layout pack · mount-standard · silhouette Product B\* checklist · arm radial L-aware Visor · fit-relations checklist · **disk-axial Visor cylinders** · **`library/fc` + `library/sensors`** (P0 relocate out of `aerial.py`). Suite **2911** · UI **105**.
- **SYSTEM_DEFINITION block-gate (`B1-system-definition-block-gate`, 2026-09-15):** `block_components_are_resolvable()` + `ComponentRuleRegistry.known_suggested_keys()` — alias→bloque canónico gated; sin regla → rechazo sin stub. Suite **2938**.
- **Mission payload identity (`B1-mission-payload-identity`, 2026-09-15):** `ComponentRule`s identidad para `cameras` + `radio_module`; SYSTEM_DEFINITION B acepta `cámara`/`comunicación`. Suite **2945**.
- **Disk-station reach (`B1-disk-station-reach`, 2026-09-16):** `station_reach_screening` para `motors`↔`frame_arm`; `declaro verificado el motor` si reach-ok. Suite **2968**. Guía §9.
- **Fase M mission craft ladder (2026-09-16→18, tag `v0.4.2`):** `B1-mission-mass-energy` (mass → AUW) · `B1-library-cameras-seed` (RunCam Phoenix 2, full ESC-shaped catalog path) · `B1-mission-continuity-mount-endurance` (mount + autonomy-target ladder steps) · `B1-mission-power-w` (`mission_accessory_power_w`, cameras/radio only) · `B1-catalog-camera-power-w` (Phoenix P=I×V → catalog `power_w=1.0`) · `B1-mission-vtx-identity` (`library/vtx/` HGLRC Zeus 800, `video_link` block, mass-only mirror — never RF mW → electrical W). M7 closeout: [`engineer_note_fase_m_closeout_m7.md`](../.jes/artifacts/engineer_note_fase_m_closeout_m7.md). Suite **3166** · UI **105**. Tag **`v0.4.2`**; Fase M CLOSED; PRIORIDAD → Fase C (await Engineer ★).

Pendiente:

- D7: frases mixtas multi-componente (`"motores + hélices"` en un mensaje)
- más tools de ingeniería
- memoria de patrones de usuario ("palas" → "propellers")

### Deuda técnica documentada (no bloqueante — diferida a v2)

Los siguientes puntos están documentados y acotados. No requieren acción en v1.

**DT-1 — Separación semántica de `apply_components_delta`**
Ubicación: `core/component_writers.py`
La función actualmente cumple dos responsabilidades distintas: (a) aplicar un delta de componentes y (b) normalizar el estado re-derivando params desde componentes existentes cuando el delta es `{}`. Un caller futuro que pase `{}` esperando no-op obtendrá un recálculo completo. Refactor seguro cuando aparezca un segundo caller con expectativa distinta:
```python
normalize_state_from_components(state) -> ProjectState   # solo re-deriva
apply_components_delta(state, delta) -> ProjectState      # solo aplica delta
```

**DT-2 — Cache por hash de params en `_evaluate` (DSE)**
Ubicación: `core/design_explorer.py`, función `_evaluate` dentro de `explore()`
El cache usa `frozenset(params.items())` como clave. Es una aproximación: si dos `ComponentSpec` distintos derivan los mismos `current_parameters` (ej. motor A + hélice X = motor B + hélice Y = 10N de thrust), producirán la misma clave y el segundo candidato reutilizará el resultado del primero sin saberlo. Impacto actual: bajo (grids con valores muy distintos entre sí). Solución futura: incluir identidad de componentes en la clave de cache.

**DT-3 — `COMPONENT_VARIATION_RULES` estáticos (ciegos al estado)**
Ubicación: `core/design_explorer.py`
Las reglas actuales son valores fijos. No dependen del estado del proyecto: un dron de 200g probará baterías de 1200Wh igual que uno de 2kg. Esto hace la exploración sistemática pero no inteligente. El salto a reglas adaptativas requiere heurísticas de dominio o un `ComponentGenerator` que genere valores en función del estado actual.

## Papel del LLM

El LLM está integrado como interfaz validada y pluggable. No ejecuta física, no muta estado, no accede directamente a los motores. Interviene en dos casos.

### Cuándo interviene

**Routing de intent desconocido o ambiguo (`interpret`)**

Cuando `intent_resolver` no puede clasificar el input localmente, lo pasa al LLM. El LLM devuelve JSON estricto (`LLMActionRequest`) que pasa por `response_parser` + `ActionPolicy` + `SemanticIntentAdapter` antes de convertirse en acción.

Cuando el intent es `"ambiguous"` (keywords de dominio como `"dron"`, `"robot"`): si **no hay proyecto activo** → wizard `create_project_interactive` sin LLM; si **hay proyecto activo** → `analyze` con contexto del proyecto.

**Análisis y preguntas abiertas (`analyze`)**

Cuando el input parece una pregunta causal (`"qué pasa si"`, `"explica"`, `"influye"`...), `intent_resolver` lo clasifica como `"analyze"` y el LLM produce texto natural con el contexto del proyecto como base. No se ejecuta ningún motor.

### Routing semántico para `iterate` (FASE_LLM)

Cuando el LLM propone `action=iterate`, el output pasa por tres capas en secuencia antes de abrir el wizard:

```text
ActionPolicy._validate_iterate_variable
    → rechaza variables ausentes del registry (hallucinations) antes del adapter

SemanticIntentAdapter.adapt()
    → None: variable ausente → wizard paso 0
    → AdaptRejection("derived_variable"): variable no settable → wizard paso 0 + mensaje del registry
    → AdaptRejection("unknown_variable"): no llegará aquí (ya rechazado por ActionPolicy)
    → SemanticInterpretation(is_high_confidence=False): confidence < 0.75 → wizard paso 0
    → SemanticInterpretation(is_high_confidence=True): confidence ≥ 0.75 → wizard preseed paso 2

Reglas adicionales del adapter (calibración 2026-08-05):
- Si `raw_user_input` no contiene un token de anclaje de la variable propuesta (clave, alias o concept_alias, longitud ≥ 4), el confidence se cap a `< 0.75` aunque el LLM diga `1.0` (ej. `"más chicha"` → `battery_capacity_wh`).
- Si el usuario no escribió ningún número, el `valor` inventado por el LLM se descarta (`None`).

orchestrator._semantic_preseed()
    → traduce el resultado del adapter a parámetros de seed para iterate_interactive_session.start()
```

El wizard determinista (`iterate_interactive_session`) se abre siempre: la diferencia es si empieza en paso 0 o en paso 2 con los campos pre-rellenados. Los motores nunca reciben output LLM sin pasar por la validación del wizard.

**Logging de cada evento LLM (`interpret`):**

```json
{
  "prompt_version": "...",
  "user_input": "...",
  "llm_raw_output": "...",
  "parsed_output": {...},
  "semantic_trace": {"variable": "...", "confidence": 0.88, "routing": "preseed_step2"},
  "error": null
}
```

`routing` values: `preseed_step2 | fallback_wizard | rejected_derived | rejected_unknown | n/a`

### Cuándo NO interviene

- Selección inicial de proyecto por número (`1`, `2`...) — `main.py` lee `state.json` directamente
- Proyecto seleccionado → startup display — `build_startup_context()` es determinista
- **Consulta de estado / Continuity** (`"estado del proyecto"`, `"resumen"`, `"qué falta"`, `"siguiente paso"`, `"ayúdame con el siguiente paso"`…) — `project_status` → `build_startup_context()` sin LLM
- **Acquisition Target / Brief** (declarar bloque∪componente, help-define, nav-back) — orquestador + `acquisition_*` sin LLM
- **Engineering Intent** (intención bare sin valor) — `goal_plan` determinista (FN-022); no abre iterate
- Sesión interactiva activa — session handler (salvo soft-interrupt status/analyze)
- Intent claro (`calcular`, `simular`, iterate **con valor**, explore/apply…) — `ActionRequest` / DSE local
- Todos los pasos dentro de `create_project_interactive` e `iterate_interactive`
- Extracción de slots en `semantic_interpreter` — determinista por reglas

### Restricciones permanentes

- No calcula física.
- No simula.
- No persiste estado.
- No controla el flujo de sesión.
- El registry (`PARAMETER_REQUIREMENTS`) es el único árbitro de variables modificables.

La frontera LLM incluye: safe fallback para salidas inválidas, logging estructurado en `jarvis/runtime/llm_logs/`, versionado de prompt.



## SemanticState y SemanticInterpreter

### Propósito

Reemplazar el parsing rígido por keyword-rules con un estado acumulativo que
construye significado progresivamente a lo largo de la sesión.

Antes: cada input debía ser un comando válido completo.
Ahora: cada input aporta información parcial que se acumula.

### SemanticState

Ubicación: `schemas/semantic_schema.py`

**Runtime-only. Nunca se persiste en `state.json`.**

Campos clave:

```python
slots: dict[str, SlotValue]    # operation, variable, value, objective, restrictions
missing_slots: list[str]       # slots requeridos aún no resueltos
alternatives: list[str]        # interpretaciones posibles cuando hay ambigüedad
history: list[str]             # todos los inputs de la sesión
clarification_round: int       # rondas de clarificación ya usadas
forced: bool                   # True si se avanzó forzado por MAX_CLARIFICATION_ROUNDS
```

Cada `SlotValue` tiene:
- `value`: el valor extraído (o `None`)
- `confidence`: 0.0–1.0
- `source`: `"inferred"` | `"explicit"` | `"confirmed"`

Los slots con `source="confirmed"` nunca se sobreescriben.

### SemanticInterpreter

Ubicación: `core/semantic_interpreter.py`

Tres funciones públicas:

| Función | Entrada | Salida |
|---|---|---|
| `update(state, input)` | estado actual + nuevo input | estado enriquecido (nunca menos completo) |
| `decide(state)` | estado actual | `"proceed"` \| `"confirm"` \| `"clarify"` |
| `to_draft_patch(state)` | estado actual | dict compatible con `IterationDraft` |

Política de confianza en `decide()`:

| Condición | Decisión |
|---|---|
| todos los slots requeridos con confianza ≥ 0.75 | `proceed` |
| todos presentes, alguno entre 0.4–0.75 | `confirm` |
| algún slot ausente o confianza < 0.4 | `clarify` |
| `clarification_round >= 2` (forzado) | `proceed` |

`to_draft_patch` garantiza que `operation` siempre es `IterationOperation` enum o `None`.
Nunca emite un raw string — esto elimina el crash histórico de Pydantic.

### Integración en la sesión

En `iterate_interactive_session.answer()`:

1. `_seed_semantic_from_draft()` — añade campos confirmados del draft como slots `confirmed`
2. `sem.update()` — enriquece con el nuevo input
3. Routing por step (conflicto, definición, etc.)
4. En step 2: `sem.decide()` determina si proceder, confirmar o clarificar
5. `_operation_from_semantic()` — extrae operation del estado semántico, nunca raw string

## Principios de diseño

- Determinismo: mismo input, misma salida.
- Separación total de capas.
- Trazabilidad: nada importante se pierde.
- Escalabilidad: nuevas estrategias y dominios deben poder añadirse sin romper el núcleo.

## Uso conceptual

### Crear proyecto

```python
{
  "action": "create_project",
  "parameters": {}
}
```

o:

```python
{
  "action": "create_project",
  "parameters": {
    "vehicle_type": "dron",
    "objective": "dron que levante 2kg",
    "payload_kg": 2.0,
    "restrictions": "sin restricciones adicionales",
    "detail_level": "conceptual",
    "motors": 4,
    "per_motor_max_thrust_n": 15.0,
    "structure_mass_factor": 0.6,
    "safety_factor": 1.2
  }
}
```

### Iterar proyecto

```python
{
  "action": "iterate",
  "parameters": {
    "objetivo": "peso",
    "operacion": "reducir"
  }
}
```

Después el sistema abre el flujo guiado, pide confirmación y ejecuta la iteración real.

### Recalcular proyecto

```python
{
  "action": "calculate",
  "parameters": {
    "project_id": "abc123"
  }
}
```

### Simular proyecto

```python
{
  "action": "simulate",
  "parameters": {
    "project_id": "abc123"
  }
}
```

### Generar plan

```python
plan = orchestrator.build_plan("recalculate_and_simulate", {"project_id": "abc123"})
```
