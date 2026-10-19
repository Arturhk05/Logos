import { Clock, Headset, type LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { Link } from "react-router";

import { formatDateTime } from "../../shared/format";
import { CATEGORY_LABELS, type IncidentStatus } from "../../shared/labels";
import { CategoryIcon } from "../../shared/ui/CategoryIcon";
import { CriticalityBadge } from "../../shared/ui/CriticalityBadge";
import { TableSkeleton } from "../../shared/ui/Skeleton";
import { EmptyState, ErrorState } from "../../shared/ui/StateMessage";
import { StatusLabel } from "../../shared/ui/StatusLabel";
import type { QueueItem } from "../queue/api";

type ActiveStatus = Extract<IncidentStatus, "OPEN" | "INVESTIGATING">;

// The driver's doubt is whether anyone saw the report, so each status in progress answers it in plain words.
const PROGRESS: Record<
  ActiveStatus,
  { Icon: LucideIcon; title: string; text: string; tone: string }
> = {
  OPEN: {
    Icon: Clock,
    title: "Aguardando a central",
    text: "Seu reporte chegou. Logo alguém da central vai assumir.",
    tone: "border-b border-warning-line bg-warning-soft text-warning-ink",
  },
  INVESTIGATING: {
    Icon: Headset,
    title: "A central está cuidando",
    text: "Fique de olho no WhatsApp: a central vai falar com você por lá.",
    tone: "bg-accent text-on-accent",
  },
};

function isActive(status: IncidentStatus): status is ActiveStatus {
  return status in PROGRESS;
}

export interface MyReportsViewProps {
  state: "loading" | "error" | "ready";
  errorMessage?: string;
  onRetry: () => void;
  items: QueueItem[];
  now: Date;
}

export function MyReportsView({ state, errorMessage, onRetry, items, now }: MyReportsViewProps) {
  // In the order the API sends within each group: the most recent first (US-09).
  const active = items.flatMap((item) =>
    isActive(item.status) ? [{ item, status: item.status }] : [],
  );
  const closed = items.filter((item) => !isActive(item.status));

  return (
    <section className="flex flex-col gap-4">
      <h1 className="text-xl font-bold tracking-tight">Meus reportes</h1>
      {state === "loading" && <TableSkeleton rows={4} />}
      {state === "error" && <ErrorState message={errorMessage ?? ""} onRetry={onRetry} />}
      {state === "ready" && items.length === 0 && (
        <EmptyState
          message="Você ainda não reportou nenhum incidente."
          action={
            <Link
              to="/reportar"
              className="flex min-h-11 items-center rounded-lg bg-accent px-4 font-semibold text-on-accent"
            >
              Reportar incidente
            </Link>
          }
        />
      )}
      {state === "ready" && items.length > 0 && (
        <>
          <ReportGroup title="Em andamento">
            {active.length === 0 ? (
              <p className="rounded-xl border border-dashed border-line p-4 text-sm text-muted">
                Nenhum reporte em andamento.
              </p>
            ) : (
              <ul className="flex flex-col gap-3">
                {active.map(({ item, status }) => (
                  <ActiveReport key={item.id} item={item} status={status} now={now} />
                ))}
              </ul>
            )}
          </ReportGroup>
          {closed.length > 0 && (
            <ReportGroup title="Encerrados">
              <ul className="flex flex-col gap-2">
                {closed.map((item) => (
                  <ClosedReport key={item.id} item={item} now={now} />
                ))}
              </ul>
            </ReportGroup>
          )}
        </>
      )}
    </section>
  );
}

function ReportGroup({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="flex flex-col gap-2">
      <h2 className="text-sm font-semibold text-muted">{title}</h2>
      {children}
    </section>
  );
}

function ActiveReport({ item, status, now }: { item: QueueItem; status: ActiveStatus; now: Date }) {
  const { Icon, title, text, tone } = PROGRESS[status];
  return (
    <li className="overflow-hidden rounded-xl border border-line-strong bg-surface">
      <div className={`flex gap-3 px-4 py-3 ${tone}`}>
        <Icon aria-hidden className="mt-0.5 size-5 shrink-0" />
        <div className="flex flex-col gap-0.5">
          <p className="font-semibold">{title}</p>
          <p className="text-sm">{text}</p>
        </div>
      </div>
      <div className="flex flex-col gap-2 p-4">
        <div className="flex items-start justify-between gap-2">
          <span className="flex items-center gap-2 font-semibold">
            <CategoryIcon category={item.category} className="size-4 text-muted" />
            {CATEGORY_LABELS[item.category]}
          </span>
          <span className="text-sm text-muted tabular-nums">#{item.id}</span>
        </div>
        <span className="text-sm">
          {item.location} ·{" "}
          <span className="text-muted">{formatDateTime(item.created_at, now)}</span>
        </span>
        <div className="flex items-center justify-between gap-2 text-sm">
          <StatusLabel status={item.status} />
          <CriticalityBadge criticality={item.criticality} />
        </div>
      </div>
    </li>
  );
}

function ClosedReport({ item, now }: { item: QueueItem; now: Date }) {
  return (
    <li className="flex flex-col gap-1 rounded-xl border border-line bg-surface px-3 py-2.5 text-sm">
      <div className="flex items-center justify-between gap-2">
        <span className="flex items-center gap-2 font-medium">
          <CategoryIcon category={item.category} className="size-4 text-muted" />
          {CATEGORY_LABELS[item.category]}
        </span>
        <span className="text-muted tabular-nums">#{item.id}</span>
      </div>
      <div className="flex items-center justify-between gap-2 text-muted">
        <StatusLabel status={item.status} />
        <span>{formatDateTime(item.created_at, now)}</span>
      </div>
    </li>
  );
}
