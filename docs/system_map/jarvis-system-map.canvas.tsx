/**
 * Jarvis System Map — interactive canvas (SYS-MAP-002 visual companion).
 *
 * Repo source of truth for this UI: docs/system_map/jarvis-system-map.canvas.tsx
 * To open live in Cursor beside chat, copy/sync to the project canvases folder:
 *   ~/.cursor/projects/<workspace>/canvases/jarvis-system-map.canvas.tsx
 *
 * Counts: 59 canonical registry edges (CONNECTIONS.md) + 8 forbidden (not C-xxx).
 * Updated 2026-08-10 by FN-024: C-042 fixed (BROKEN → CONNECTED), C-105/C-106 added.
 * Never report "65 connections" — that counted derived-table duplicates.
 */
import {
  Button,
  Callout,
  Card,
  CardBody,
  CardHeader,
  CollapsibleSection,
  Divider,
  Grid,
  H1,
  H2,
  H3,
  Pill,
  Row,
  Spacer,
  Stack,
  Stat,
  Table,
  Text,
  UsageBar,
  computeDAGLayout,
  useCanvasState,
  useHostTheme,
} from "cursor/canvas";

type Status = "connected" | "partial" | "broken";
type Filter = "all" | Status | "forbidden";

type Conn = {
  id: string;
  from: string;
  to: string;
  fromLabel: string;
  toLabel: string;
  status: Status;
  band: string;
};

/** Every registry edge from docs/system_map/CONNECTIONS.md quick index. */
const CONNECTIONS: Conn[] = [
  { id: "C-001", from: "user", to: "cli", fromLabel: "User", toLabel: "CLI adapter", status: "connected", band: "00 Entry" },
  { id: "C-002", from: "cli", to: "orch", fromLabel: "CLI/MCP", toLabel: "handle_user_text", status: "connected", band: "00 Entry" },
  { id: "C-003", from: "cli", to: "orch_handle", fromLabel: "CLI/MCP structured", toLabel: "orchestrator.handle", status: "connected", band: "00 Entry" },

  { id: "C-010", from: "orch", to: "g_cmds", fromLabel: "Runtime", toLabel: "Global commands", status: "connected", band: "01 Runtime" },
  { id: "C-011", from: "orch", to: "struct_c", fromLabel: "Runtime", toLabel: "FN-004 structural-confirm", status: "connected", band: "01 Runtime" },
  { id: "C-012", from: "orch", to: "pend_def", fromLabel: "Runtime", toLabel: "Bug 54 pending_define", status: "connected", band: "01 Runtime" },
  { id: "C-013", from: "orch", to: "comp_ix", fromLabel: "Runtime", toLabel: "Global component intercept", status: "connected", band: "01 Runtime" },
  { id: "C-014", from: "orch", to: "mode", fromLabel: "Runtime", toLabel: "Mode-branch dispatch", status: "connected", band: "01 Runtime" },
  { id: "C-015", from: "orch", to: "params_in", fromLabel: "Runtime", toLabel: "Parameter ingestion", status: "connected", band: "01 Runtime" },
  { id: "C-016", from: "orch_handle", to: "act_router", fromLabel: "orchestrator.handle", toLabel: "ActionRouter → Action.run", status: "connected", band: "01 Runtime" },

  { id: "C-020", from: "orch", to: "intent", fromLabel: "Runtime", toLabel: "IntentResolver", status: "connected", band: "02 Intent" },
  { id: "C-021", from: "intent", to: "h_status", fromLabel: "Intent project_status", toLabel: "_handle_project_status", status: "connected", band: "02 Intent" },
  { id: "C-022", from: "intent", to: "h_analyze", fromLabel: "Intent analyze", toLabel: "_handle_analyze", status: "connected", band: "02 Intent" },
  { id: "C-023", from: "intent", to: "def_params", fromLabel: "Intent define_params", toLabel: "start_define_missing bridge", status: "connected", band: "02 Intent" },
  { id: "C-024", from: "intent", to: "dismiss", fromLabel: "Intent dismiss", toLabel: "_handle_dismiss_suggestion", status: "connected", band: "02 Intent" },
  { id: "C-025", from: "help_goal", to: "h_analyze", fromLabel: "ayúdame + named goal", toLabel: "Intent → analyze", status: "broken", band: "02 Intent" },

  { id: "C-030", from: "orch", to: "motor", fromLabel: "Runtime IDLE", toLabel: "FN-005 motor help", status: "connected", band: "03 Acquisition" },
  { id: "C-031", from: "orch", to: "acq", fromLabel: "Runtime IDLE", toLabel: "FN-014 acquisition wizard", status: "connected", band: "03 Acquisition" },
  { id: "C-032", from: "orch", to: "pend_help", fromLabel: "Runtime IDLE", toLabel: "FN-015 pending-help", status: "connected", band: "03 Acquisition" },
  { id: "C-033", from: "orch", to: "acq_reprompt", fromLabel: "Runtime DEFINE_MISSING", toLabel: "FN-013 reprompt", status: "connected", band: "03 Acquisition" },
  { id: "C-034", from: "orch", to: "acq_nav", fromLabel: "Runtime DEFINE_MISSING", toLabel: "FN-016 cancel/nav", status: "connected", band: "03 Acquisition" },
  { id: "C-035", from: "intent", to: "h_status", fromLabel: "Intent FN-023 phrasing", toLabel: "_handle_project_status Continuity", status: "connected", band: "03 Acquisition" },
  { id: "C-036", from: "continuity", to: "acq", fromLabel: "Continuity", toLabel: "Acquisition _next_pending_block", status: "connected", band: "03 Acquisition" },
  { id: "C-037", from: "acq", to: "pend_next", fromLabel: "Acquisition complete", toLabel: "_set_pending_next_block", status: "connected", band: "03 Acquisition" },
  { id: "C-038", from: "acq", to: "acq_brief", fromLabel: "Acquisition open", toLabel: "acquisition_brief", status: "connected", band: "03 Acquisition" },

  { id: "C-040", from: "intent", to: "eng_intent", fromLabel: "Intent iterate/unknown", toLabel: "engineering_intent gate", status: "connected", band: "04 Engineering" },
  { id: "C-041", from: "eng_intent", to: "goal_plan", fromLabel: "_handle_engineering_intent", toLabel: "goal_planner.format_goal_plan", status: "connected", band: "04 Engineering" },
  { id: "C-042", from: "goal_plan", to: "dse", fromLabel: "Goal Plan CTA explora opciones", toLabel: "DSE goal binding (via handoff_context)", status: "connected", band: "04 Engineering" },
  { id: "C-043", from: "goal_plan", to: "iter", fromLabel: "Goal Plan lever", toLabel: "Iterate wizard preseed", status: "broken", band: "04 Engineering" },
  { id: "C-044", from: "help_goal", to: "goal_plan", fromLabel: "ayúdame + named goal", toLabel: "Plan/Explore", status: "broken", band: "04 Engineering" },
  { id: "C-045", from: "intent", to: "dse", fromLabel: "Intent explore_design_space", toLabel: "DesignExplorer.explore", status: "connected", band: "04 Engineering" },
  { id: "C-046", from: "dse", to: "apply_exp", fromLabel: "explore result", toLabel: "apply_exploration", status: "connected", band: "04 Engineering" },
  { id: "C-105", from: "eng_intent", to: "handoff_ctx", fromLabel: "engineering_intent success", toLabel: "create/replace handoff_context", status: "connected", band: "04 Engineering" },
  { id: "C-106", from: "handoff_ctx", to: "dse", fromLabel: "active handoff_context", toLabel: "_handle_explore goal bind", status: "connected", band: "04 Engineering" },

  { id: "C-050", from: "orch_handle", to: "iter", fromLabel: "orchestrator ITERATE", toLabel: "IterateInteractiveSession", status: "connected", band: "05 Iteration" },
  { id: "C-051", from: "iter", to: "soft_int", fromLabel: "ITERATE_INTERACTIVE", toLabel: "Bug 7 soft-interrupt", status: "connected", band: "05 Iteration" },
  { id: "C-052", from: "iter", to: "calib", fromLabel: "ITERATE_INTERACTIVE", toLabel: "Calibration preempt", status: "connected", band: "05 Iteration" },
  { id: "C-053", from: "iter", to: "semantic", fromLabel: "Iterate.answer", toLabel: "semantic_interpreter", status: "connected", band: "05 Iteration" },
  { id: "C-054", from: "iter", to: "mutation", fromLabel: "Iterate confirm", toLabel: "MutationEngine", status: "connected", band: "05 Iteration" },

  { id: "C-060", from: "curr_params", to: "calc", fromLabel: "current_parameters", toLabel: "CalculationEngine.build", status: "connected", band: "06 Calc/Sim" },
  { id: "C-061", from: "resolver", to: "calc", fromLabel: "component_resolver", toLabel: "Calculation override", status: "connected", band: "06 Calc/Sim" },
  { id: "C-070", from: "calc", to: "sim", fromLabel: "CalculationBundle", toLabel: "FeasibilitySimulator", status: "connected", band: "06 Calc/Sim" },
  { id: "C-071", from: "sim", to: "state_mgr", fromLabel: "SimulationResult", toLabel: "record_action / latest_results", status: "connected", band: "06 Calc/Sim" },

  { id: "C-080", from: "proj_state", to: "continuity", fromLabel: "ProjectState+BOM+req", toLabel: "build_project_continuity", status: "connected", band: "08 Continuity" },
  { id: "C-081", from: "sim", to: "continuity", fromLabel: "Sim safety_margin_ratio", toLabel: "Continuity next_useful_step", status: "partial", band: "08 Continuity" },
  { id: "C-082", from: "classify", to: "bom", fromLabel: "classify_component", toLabel: "BOM buckets", status: "connected", band: "08 Continuity" },
  { id: "C-083", from: "classify", to: "block_prog", fromLabel: "classify_component", toLabel: "_block_progress_status", status: "connected", band: "08 Continuity" },
  { id: "C-084", from: "proj_state", to: "phase", fromLabel: "ProjectState", toLabel: "PhaseLayer.infer", status: "connected", band: "08 Continuity" },
  { id: "C-085", from: "ctx", to: "reasoning", fromLabel: "Context (+phase)", toLabel: "ReasoningLayer.build", status: "connected", band: "08 Continuity" },

  { id: "C-090", from: "free_text", to: "infer", fromLabel: "Free text", toLabel: "component_inference", status: "connected", band: "09 Components/State" },
  { id: "C-091", from: "infer", to: "writers", fromLabel: "ComponentSpec", toLabel: "component_writers", status: "connected", band: "09 Components/State" },
  { id: "C-092", from: "orch", to: "state_mgr", fromLabel: "Orchestrator checkpoint", toLabel: "set/clear_runtime_session", status: "connected", band: "09 Components/State" },
  { id: "C-093", from: "proj_state", to: "ws_save", fromLabel: "ProjectState", toLabel: "save_state → state.json", status: "connected", band: "09 Components/State" },
  { id: "C-094", from: "proj_state", to: "ws_views", fromLabel: "ProjectState", toLabel: "render_views", status: "connected", band: "09 Components/State" },

  { id: "C-100", from: "orch", to: "llm_interp", fromLabel: "orchestrator", toLabel: "llm_interface.interpret", status: "connected", band: "10 LLM" },
  { id: "C-101", from: "prompt", to: "llm_client", fromLabel: "PromptBuilder messages", toLabel: "LLMClient.complete", status: "connected", band: "10 LLM" },
  { id: "C-102", from: "llm_raw", to: "parser", fromLabel: "Raw LLM response", toLabel: "LLMResponseParser / ActionPolicy", status: "connected", band: "10 LLM" },
  { id: "C-103", from: "action_req", to: "orch_handle", fromLabel: "Validated action_request", toLabel: "orchestrator.handle", status: "connected", band: "10 LLM" },
  { id: "C-104", from: "orch", to: "llm_analyze", fromLabel: "orchestrator", toLabel: "llm_interface.analyze", status: "connected", band: "10 LLM" },
];

/** Chain bridges so LLM path lays out as one flow (not in registry as separate C-ids). */
const LAYOUT_BRIDGES: Array<{ from: string; to: string }> = [
  { from: "orch_handle", to: "orch" },
  { from: "llm_interp", to: "prompt" },
  { from: "llm_client", to: "llm_raw" },
  { from: "parser", to: "action_req" },
  { from: "mutation", to: "curr_params" },
  { from: "writers", to: "proj_state" },
  { from: "phase", to: "ctx" },
];

const NODE_LABELS: Record<string, string> = {
  user: "USER",
  cli: "CLI/MCP",
  orch: "Runtime",
  orch_handle: "orch.handle",
  g_cmds: "Global cmds",
  struct_c: "Structural confirm",
  pend_def: "pending_define",
  comp_ix: "Component intercept",
  mode: "Mode dispatch",
  params_in: "Param ingest",
  act_router: "ActionRouter",
  intent: "IntentResolver",
  h_status: "project_status",
  h_analyze: "analyze",
  def_params: "define_params",
  dismiss: "dismiss",
  help_goal: "ayúdame+goal",
  motor: "Motor help",
  acq: "Acquisition",
  pend_help: "Pending help",
  acq_reprompt: "Acq reprompt",
  acq_nav: "Acq nav/cancel",
  acq_brief: "Acq brief",
  pend_next: "pending_next",
  eng_intent: "Eng. intent",
  goal_plan: "Goal Plan",
  dse: "DSE explore",
  apply_exp: "Apply explore",
  iter: "Iterate",
  soft_int: "Soft interrupt",
  calib: "Calibration",
  semantic: "Semantic slots",
  mutation: "MutationEngine",
  curr_params: "current_params",
  calc: "Calculation",
  resolver: "Comp. resolver",
  sim: "Simulation",
  state_mgr: "StateManager",
  continuity: "Continuity",
  classify: "classify_comp",
  bom: "BOM",
  block_prog: "block_progress",
  phase: "PhaseLayer",
  ctx: "Context",
  reasoning: "ReasoningLayer",
  free_text: "Free text",
  infer: "Comp. inference",
  writers: "Comp. writers",
  proj_state: "ProjectState",
  ws_save: "state.json",
  ws_views: "MD views",
  llm_interp: "LLM interpret",
  prompt: "PromptBuilder",
  llm_client: "LLMClient",
  llm_raw: "Raw LLM",
  parser: "ActionPolicy",
  action_req: "action_request",
  llm_analyze: "LLM analyze",
};

const FORBIDDEN = [
  ["LLM → acquisition target", "ActionPolicy closed set"],
  ["LLM → goal selection", "ActionPolicy closed set"],
  ["LLM → DSE configuration", "ActionPolicy closed set"],
  ["Continuity → mutate ProjectState", "zero I/O in continuity"],
  ["DSE → silent mutate", "only via C-046 apply"],
  ["Goal Planner → write params", "zero writes in goal_planner"],
  ["Inference → write components", "only via C-091 writers"],
  ["Analyze → choose next gap", "analyze returns string only"],
];

const BANDS = [
  "00 Entry",
  "01 Runtime",
  "02 Intent",
  "03 Acquisition",
  "04 Engineering",
  "05 Iteration",
  "06 Calc/Sim",
  "08 Continuity",
  "09 Components/State",
  "10 LLM",
];

const NODE_W = 108;
const NODE_H = 32;

function statusOfEdge(from: string, to: string, visible: Conn[]): Status | "bridge" {
  const hits = visible.filter((c) => c.from === from && c.to === to);
  if (hits.some((c) => c.status === "broken")) return "broken";
  if (hits.some((c) => c.status === "partial")) return "partial";
  if (hits.length) return "connected";
  return "bridge";
}

function edgeIds(from: string, to: string, visible: Conn[]): string {
  return visible
    .filter((c) => c.from === from && c.to === to)
    .map((c) => c.id.replace("C-", ""))
    .join(",");
}

function ConnectionGraph({ visible }: { visible: Conn[] }) {
  const theme = useHostTheme();

  const nodeIds = new Set<string>();
  for (const c of visible) {
    nodeIds.add(c.from);
    nodeIds.add(c.to);
  }
  // Keep LLM chain bridges only when both ends are present
  const bridges = LAYOUT_BRIDGES.filter(
    (b) => nodeIds.has(b.from) && nodeIds.has(b.to),
  );
  for (const b of bridges) {
    nodeIds.add(b.from);
    nodeIds.add(b.to);
  }

  const edges = [
    ...visible.map((c) => ({ from: c.from, to: c.to })),
    ...bridges,
  ];
  // Dedupe identical from→to for layout (labels still list all IDs)
  const seen = new Set<string>();
  const uniqueEdges = edges.filter((e) => {
    const k = `${e.from}→${e.to}`;
    if (seen.has(k)) return false;
    seen.add(k);
    return true;
  });

  const layout = computeDAGLayout({
    nodes: [...nodeIds].map((id) => ({ id })),
    edges: uniqueEdges,
    direction: "horizontal",
    nodeWidth: NODE_W,
    nodeHeight: NODE_H,
    rankGap: 72,
    nodeGap: 14,
    padding: 12,
  });

  const strokeFor = (from: string, to: string, isBack: boolean) => {
    const st = statusOfEdge(from, to, visible);
    if (st === "broken") return theme.category.red;
    if (st === "partial") return theme.category.yellow;
    if (st === "bridge" || isBack) return theme.stroke.tertiary;
    if (from.startsWith("llm") || to.startsWith("llm") || from === "prompt" || to === "parser" || from === "action_req" || to === "llm_analyze" || from === "llm_interp")
      return theme.stroke.secondary;
    return theme.stroke.primary;
  };

  return (
    <div style={{ overflowX: "auto", width: "100%" }}>
      <svg
        width={layout.width}
        height={layout.height}
        viewBox={`0 0 ${layout.width} ${layout.height}`}
        style={{ display: "block", minWidth: layout.width }}
      >
        {layout.edges.map((e, i) => {
          const st = statusOfEdge(e.from, e.to, visible);
          const broken = st === "broken";
          const ids = edgeIds(e.from, e.to, visible);
          const mx = (e.sourceX + e.targetX) / 2;
          const my = (e.sourceY + e.targetY) / 2 - 4;
          return (
            <g key={`e-${i}`}>
              <line
                x1={e.sourceX}
                y1={e.sourceY}
                x2={e.targetX}
                y2={e.targetY}
                stroke={strokeFor(e.from, e.to, e.isBackEdge)}
                strokeWidth={broken ? 2.5 : st === "partial" ? 2 : 1.25}
                strokeDasharray={
                  broken || st === "bridge" || e.isBackEdge ? "5 3" : undefined
                }
              />
              {ids ? (
                <text
                  x={mx}
                  y={my}
                  textAnchor="middle"
                  fill={
                    broken
                      ? theme.category.red
                      : st === "partial"
                        ? theme.category.yellow
                        : theme.text.tertiary
                  }
                  fontSize={9}
                  fontFamily="ui-monospace, monospace"
                >
                  {ids}
                </text>
              ) : null}
            </g>
          );
        })}
        {layout.nodes.map((n) => {
          const involvedBroken = visible.some(
            (c) =>
              c.status === "broken" && (c.from === n.id || c.to === n.id),
          );
          return (
            <g key={n.id}>
              <rect
                x={n.x}
                y={n.y}
                width={NODE_W}
                height={NODE_H}
                rx={3}
                fill={theme.fill.tertiary}
                stroke={
                  involvedBroken ? theme.category.red : theme.stroke.secondary
                }
                strokeWidth={involvedBroken ? 2 : 1}
              />
              <text
                x={n.x + NODE_W / 2}
                y={n.y + NODE_H / 2 + 4}
                textAnchor="middle"
                fill={theme.text.primary}
                fontSize={10}
                fontFamily="system-ui, sans-serif"
              >
                {NODE_LABELS[n.id] ?? n.id}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

function toneFor(status: Status): "success" | "warning" | "danger" {
  if (status === "broken") return "danger";
  if (status === "partial") return "warning";
  return "success";
}

export default function JarvisSystemMapCanvas() {
  const [filter, setFilter] = useCanvasState<Filter>("conn-filter", "all");

  const connected = CONNECTIONS.filter((c) => c.status === "connected").length;
  const partial = CONNECTIONS.filter((c) => c.status === "partial").length;
  const broken = CONNECTIONS.filter((c) => c.status === "broken").length;

  const visible =
    filter === "all" || filter === "forbidden"
      ? CONNECTIONS
      : CONNECTIONS.filter((c) => c.status === filter);

  const tableRows =
    filter === "forbidden"
      ? FORBIDDEN.map(([edge, why]) => [edge, "—", why, "NOT IMPLEMENTED"])
      : visible.map((c) => [c.id, c.fromLabel, c.toLabel, c.status.toUpperCase()]);

  const tableTone =
    filter === "forbidden"
      ? FORBIDDEN.map(() => "neutral" as const)
      : visible.map((c) => toneFor(c.status));

  return (
    <Stack gap={20}>
      <Stack gap={6}>
        <H1>Jarvis System Map — all connections</H1>
        <Text tone="secondary">
          SYS-MAP-002 · {CONNECTIONS.length} registry edges +{" "}
          {FORBIDDEN.length} forbidden · docs/system_map/CONNECTIONS.md
        </Text>
      </Stack>

      <Grid columns={5} gap={12}>
        <Stat value={String(CONNECTIONS.length)} label="Registry edges" />
        <Stat value={String(connected)} label="Connected" tone="success" />
        <Stat value={String(broken)} label="Broken" tone="danger" />
        <Stat value={String(partial)} label="Partial" tone="warning" />
        <Stat value={`+${FORBIDDEN.length}`} label="Forbidden (not C-xxx)" />
      </Grid>

      <UsageBar
        total={CONNECTIONS.length}
        topLeftLabel="Registry status"
        topRightLabel={`${connected} ok · ${partial} partial · ${broken} broken`}
        segments={[
          { id: "connected", value: connected, color: "green" },
          { id: "partial", value: partial, color: "yellow" },
          { id: "broken", value: broken, color: "red" },
        ]}
      />

      <Row gap={8} wrap>
        <Button
          variant={filter === "all" ? "primary" : "secondary"}
          onClick={() => setFilter("all")}
        >
          All ({CONNECTIONS.length})
        </Button>
        <Button
          variant={filter === "broken" ? "primary" : "secondary"}
          onClick={() => setFilter("broken")}
        >
          Broken ({broken})
        </Button>
        <Button
          variant={filter === "partial" ? "primary" : "secondary"}
          onClick={() => setFilter("partial")}
        >
          Partial ({partial})
        </Button>
        <Button
          variant={filter === "connected" ? "primary" : "secondary"}
          onClick={() => setFilter("connected")}
        >
          Connected ({connected})
        </Button>
        <Button
          variant={filter === "forbidden" ? "primary" : "secondary"}
          onClick={() => setFilter("forbidden")}
        >
          Forbidden ({FORBIDDEN.length})
        </Button>
      </Row>

      <Callout tone="warning" title="Authority">
        ProjectState / Acquisition / Continuity own what is next. LLM narrates
        only. ActionPolicy = CREATE_PROJECT | ITERATE | CALCULATE | SIMULATE.
      </Callout>

      {filter !== "forbidden" ? (
        <Card>
          <CardHeader
            trailing={
              <Pill size="sm">
                {visible.length} edges · scroll horizontally
              </Pill>
            }
          >
            Full connection graph
          </CardHeader>
          <CardBody>
            <ConnectionGraph visible={visible} />
            <Spacer height={8} />
            <Text tone="secondary" size="small">
              Edge labels = C-xxx ids (comma-joined if parallel). Red dashed =
              broken. Amber = partial. Gray dashed = layout bridges (LLM chain /
              write-path helpers), not registry IDs.
            </Text>
          </CardBody>
        </Card>
      ) : (
        <Callout tone="info" title="Forbidden transitions">
          Structurally absent today (desired). Checklist for future FN reviews —
          not current violations.
        </Callout>
      )}

      <H2>
        {filter === "forbidden"
          ? "Forbidden transitions"
          : `Connection registry (${tableRows.length})`}
      </H2>
      <Table
        headers={
          filter === "forbidden"
            ? ["Transition", "—", "Why blocked", "Status"]
            : ["ID", "From", "To", "Status"]
        }
        rows={tableRows}
        rowTone={tableTone}
        striped
        stickyHeader
      />

      <Divider />

      <H2>By subsystem band</H2>
      <Stack gap={4}>
        {BANDS.map((band) => {
          const rows = CONNECTIONS.filter((c) => c.band === band);
          const bandBroken = rows.filter((c) => c.status === "broken").length;
          return (
            <div key={band}>
              <CollapsibleSection
                title={band}
                count={rows.length}
                trailing={
                  bandBroken > 0 ? (
                    <Text size="small" tone="secondary">
                      {bandBroken} broken
                    </Text>
                  ) : undefined
                }
                defaultOpen={bandBroken > 0}
              >
                <Table
                  headers={["ID", "From", "To", "Status"]}
                  rows={rows.map((c) => [
                    c.id,
                    c.fromLabel,
                    c.toLabel,
                    c.status.toUpperCase(),
                  ])}
                  rowTone={rows.map((c) => toneFor(c.status))}
                  striped
                  framed={false}
                />
              </CollapsibleSection>
            </div>
          );
        })}
      </Stack>

      <H3>Intent precedence (C-025 root)</H3>
      <Text size="small" tone="secondary">
        GUIDANCE → ANALYZE (bare ayudame) → … → EXPLORE → ITERATE. FN-022 gate
        only sees iterate/unknown — ayudame+goal never reaches engineering
        intent (C-025 / C-044).
      </Text>

      <Callout tone="info" title="Next">
        Pick first RED (C-042 / C-025 / C-043), decide handoff-context
        lifecycle, then emit FN contract citing that C-xxx. Create→BOM paused.
      </Callout>
    </Stack>
  );
}
