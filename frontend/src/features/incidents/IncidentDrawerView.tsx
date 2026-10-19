import { CircleAlert, RotateCw, TriangleAlert } from "lucide-react";
import type { ReactNode } from "react";

import type { IncidentDetail } from "../../api/client";
import { formatDateTime } from "../../shared/format";
import { CATEGORY_LABELS } from "../../shared/labels";
import { Button } from "../../shared/ui/Button";
import { CategoryIcon } from "../../shared/ui/CategoryIcon";
import { CriticalityBadge } from "../../shared/ui/CriticalityBadge";
import { TableSkeleton } from "../../shared/ui/Skeleton";
import { ErrorState } from "../../shared/ui/StateMessage";
import { StatusLabel } from "../../shared/ui/StatusLabel";
import type { IncidentAction } from "./actions";

export interface IncidentDrawerViewProps {
  state: "loading" | "error" | "ready";
  errorMessage?: string;
  incident?: IncidentDetail;
  actions: IncidentAction[];
  pendingAction?: IncidentAction;
  conflict?: string;
  saveError?: string;
  onAction: (action: IncidentAction) => void;
  onRetrySave: () => void;
  now: Date;
}

const ACTION_LABELS: Record<IncidentAction, string> = {
  assume: "Assumir incidente",
  close: "Fechar",
  inconclusive: "Inconclusivo",
  reopen: "Devolver à fila",
};

export function IncidentDrawerView(props: IncidentDrawerViewProps) {
  const { state, incident } = props;
  if (state === "loading") return <TableSkeleton rows={5} />;
  if (state === "error" || incident === undefined) {
    return <ErrorState message={props.errorMessage ?? ""} />;
  }

  return (
    <div className="flex flex-col gap-5">
      {props.conflict !== undefined && (
        <p
          role="alert"
          className="flex gap-2 rounded-lg border border-warning-line bg-warning-soft px-3 py-2.5 text-sm text-warning-ink"
        >
          <TriangleAlert aria-hidden className="mt-0.5 size-4 shrink-0" />
          <span>
            <strong className="font-semibold">{props.conflict}</strong> Veja abaixo como ele está
            agora.
          </span>
        </p>
      )}

      <header className="flex flex-col gap-2">
        <div className="flex flex-wrap items-center gap-3 text-sm">
          <CriticalityBadge criticality={incident.criticality} />
          <StatusLabel status={incident.status} />
        </div>
        <h3 className="flex items-center gap-2 text-xl font-bold tracking-tight">
          <CategoryIcon category={incident.category} className="size-5 text-muted" />
          {CATEGORY_LABELS[incident.category]}
        </h3>
        <p className="text-muted">{incident.location}</p>
      </header>

      <p className="break-words whitespace-pre-line">{incident.description}</p>

      <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-2 border-y border-line py-4 text-sm">
        <Detail term="Reportado por">{incident.reporter.username}</Detail>
        <Detail term="Aberto em">{formatDateTime(incident.created_at, props.now)}</Detail>
        <Detail term="Atualizado em">{formatDateTime(incident.updated_at, props.now)}</Detail>
        <Detail term="Responsável">{incident.assignee?.username ?? "—"}</Detail>
        {incident.closed_by !== null && (
          <>
            <Detail term="Encerrado por">{incident.closed_by.username}</Detail>
            {incident.closed_at !== null && (
              <Detail term="Encerrado em">{formatDateTime(incident.closed_at, props.now)}</Detail>
            )}
            <Detail term="Motivo">{incident.closure_reason ?? "—"}</Detail>
          </>
        )}
      </dl>

      {props.saveError !== undefined && (
        <div
          role="alert"
          className="flex flex-wrap items-center justify-between gap-3 text-sm text-critical-ink"
        >
          <span className="flex items-center gap-2">
            <CircleAlert aria-hidden className="size-4 shrink-0" />
            {props.saveError}
          </span>
          <Button variant="secondary" onClick={props.onRetrySave}>
            <RotateCw aria-hidden className="size-4" />
            Tentar novamente
          </Button>
        </div>
      )}

      {props.actions.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {props.actions.map((action, index) => (
            <Button
              key={action}
              // The first action is the main one: assuming, or closing once assumed.
              variant={index === 0 ? "primary" : "secondary"}
              pending={props.pendingAction === action}
              disabled={props.pendingAction !== undefined}
              onClick={() => {
                props.onAction(action);
              }}
            >
              {ACTION_LABELS[action]}
            </Button>
          ))}
        </div>
      )}
    </div>
  );
}

function Detail({ term, children }: { term: string; children: ReactNode }) {
  return (
    <>
      <dt className="text-muted">{term}</dt>
      <dd className="break-words">{children}</dd>
    </>
  );
}
