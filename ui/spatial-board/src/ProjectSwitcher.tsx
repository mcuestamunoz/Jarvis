import type { ProjectSummary } from "./projects";

type Props = {
  current: ProjectSummary | null;
  projects: ProjectSummary[];
  error: string | null;
  onSelect: (id: string) => void;
};

export function ProjectSwitcher({ current, projects, error, onSelect }: Props) {
  if (error) {
    return (
      <div className="sb-brand">
        <p className="sb-project__title">Pizarra</p>
        <p className="sb-project__slug">No se pudo leer workspace/</p>
      </div>
    );
  }

  if (projects.length === 0) {
    return (
      <div className="sb-brand">
        <p className="sb-project__title">Sin proyectos</p>
        <p className="sb-project__slug">Crea uno en el CLI — workspace/</p>
      </div>
    );
  }

  return (
    <div className="sb-brand">
      <p className="sb-project__title">{current?.title ?? "Proyecto"}</p>
      <label className="sb-project__switch">
        <span className="sb-project__slug">{current?.slug}</span>
        <select
          aria-label="Cambiar proyecto"
          value={current?.id ?? ""}
          onChange={(event) => onSelect(event.target.value)}
        >
          {projects.map((p) => (
            <option key={p.id} value={p.id}>
              {p.slug}
              {p.objective ? ` — ${p.objective}` : ""}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}
